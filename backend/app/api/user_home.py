"""
User Home Dashboard API
Personalized landing page for each user
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from app.db.models_saas import User
from app.db.leaderboard_models import LeaderboardEntry, Achievement, UserStats
from app.db.roi_models import ImpactRecord
from app.db.action_models import Action
from app.db.leaderboard_models import UserActivity
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.utils.time import utcnow
from app.services.prediction_summary import (
    empty_state_message, money, summarize_org_predictions,
)

router = APIRouter(prefix="/api/user", tags=["user-home"])


@router.get("/home")
def get_user_home(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized user home dashboard"""

    # Get this month's ROI data
    now = utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    impact_records = db.query(ImpactRecord).filter(
        ImpactRecord.organization_id == current_user.organization_id,
        ImpactRecord.predicted_at >= month_start
    ).all()

    total_impact = sum(r.value_amount for r in impact_records)
    revenue_saved = sum(r.value_amount for r in impact_records if r.impact_type == "revenue_saved")
    revenue_created = sum(r.value_amount for r in impact_records if r.impact_type == "revenue_created")

    # Get user stats
    stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()

    # Get leaderboard rank
    leaderboard = db.query(LeaderboardEntry).filter(
        LeaderboardEntry.user_id == current_user.id,
        LeaderboardEntry.period == "week"
    ).first()

    rank = leaderboard.rank if leaderboard else None
    rank_change = f"↑ +{leaderboard.rank_change}" if leaderboard and leaderboard.rank_change and leaderboard.rank_change > 0 else \
                  f"↓ {leaderboard.rank_change}" if leaderboard and leaderboard.rank_change and leaderboard.rank_change < 0 else "→"

    # Get achievements
    achievements = db.query(Achievement).filter(Achievement.user_id == current_user.id).all()

    # Get next badge to unlock
    next_badge = None
    if stats:
        if stats.total_customers_saved < 10:
            next_badge = {
                "name": "Churn Saver",
                "icon": "🛡️",
                "progress": stats.total_customers_saved,
                "target": 10
            }
        elif stats.total_expansions_closed < 5:
            next_badge = {
                "name": "Expansion King",
                "icon": "👑",
                "progress": stats.total_expansions_closed,
                "target": 5
            }
        elif stats.total_actions < 100:
            next_badge = {
                "name": "Action Master",
                "icon": "⚡",
                "progress": stats.total_actions,
                "target": 100
            }

    # What to do first comes from the latest scoring run, not from whatever
    # happens to be assigned: the model has an opinion about ordering and the
    # assignment queue doesn't.
    summary = summarize_org_predictions(db, current_user.organization_id)

    top_actions = []
    if summary is not None:
        ranked = sorted(
            summary.at_risk,
            key=lambda c: (c.revenue_at_stake is not None, c.revenue_at_stake or 0.0, c.score),
            reverse=True,
        )
        top_actions = [
            {
                "id": f"pred-{summary.model_id}-{c.customer_id}",
                "title": f"Contact {c.name} ({c.score * 100:.0f}% {summary.subject})",
                "icon": "🎯",
                "impact": money(c.revenue_at_stake) or "Unknown",
                "priority": c.band.upper(),
            }
            for c in ranked[:3]
        ]

    # Get recent wins (user activity)
    recent_activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.is_celebratory == True
    ).order_by(desc(UserActivity.created_at)).limit(5).all()

    recent_wins = [
        {
            "title": a.activity_title,
            "impact": (
                f"${a.revenue_impact:,.0f}" if a.revenue_impact
                else f"+{a.customers_affected} customers" if a.customers_affected
                else "🎉"
            ),
            "when": a.created_at.strftime("%m/%d")
        }
        for a in recent_activities
    ]

    # Forecast is a straight-line projection of this month's realized impact.
    # With nothing realized yet there is nothing to project from, so we say so
    # rather than extrapolating from zero and dressing it up with a confidence.
    if total_impact > 0:
        avg_daily_impact = total_impact / max((now - month_start).days, 1)
        days_remaining = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - now
        forecast_next_month = f"${total_impact + (avg_daily_impact * days_remaining.days):,.0f}"
    else:
        forecast_next_month = None

    # The prediction-grounded half of the dashboard.
    if summary is None:
        prediction_block = {
            "customers_scored": 0,
            "customers_at_risk": 0,
            "revenue_at_risk": None,
            "risk_distribution": None,
            "since_last_scoring": None,
            "model": None,
            "scored_at": None,
            "headline": empty_state_message(db, current_user.organization_id),
        }
    else:
        shift = summary.band_shift()
        if shift is None:
            since = "This is the first scoring run, so there's nothing to compare against yet."
        else:
            moved = shift["critical"] + shift["high"]
            since = (
                f"{abs(moved)} {'more' if moved > 0 else 'fewer' if moved < 0 else 'net change in'} "
                f"customers in the high or critical band since the previous run."
            )
        prediction_block = {
            "customers_scored": summary.total_customers,
            "customers_at_risk": len(summary.at_risk),
            "revenue_at_risk": money(summary.revenue_at_stake) if summary.revenue_known_for else None,
            "risk_distribution": summary.band_counts,
            "since_last_scoring": since,
            "model": summary.model_name,
            "scored_at": summary.scored_at.isoformat() if summary.scored_at else None,
            "headline": (
                f"{len(summary.at_risk)} of {summary.total_customers} customers are predicted "
                f"to be at {summary.subject}."
                if summary.at_risk else
                f"None of your {summary.total_customers} scored customers are in the high or "
                f"critical band right now."
            ),
        }

    return {
        "user_name": current_user.name.split()[0],
        **prediction_block,
        "this_month_impact": f"${total_impact:,.0f}",
        "revenue_saved": f"${revenue_saved:,.0f}",
        "revenue_created": f"${revenue_created:,.0f}",
        "rank": rank or 999,
        "rank_change": rank_change,
        "current_streak": stats.current_streak if stats else 0,
        "badges_earned": len(achievements),
        "next_badge": next_badge,
        "top_actions": top_actions,
        "forecast_next_month": forecast_next_month,
        # A projection needs an accuracy history to be worth a number. We don't
        # have one, so this stays empty instead of quoting a made-up percentage.
        "forecast_confidence": None,
        "recent_wins": recent_wins,
        # Playbook ROI would have to be measured, not assumed. Until it is, the
        # concrete thing to recommend is the top-scoring account.
        "recommended_playbooks": [],
    }


@router.get("/daily-summary")
def get_daily_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's daily summary (for email digest)"""

    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's actions
    today_actions = db.query(Action).filter(
        Action.assigned_to_id == current_user.id,
        Action.created_at >= today_start
    ).count()

    # Today's impact
    today_impacts = db.query(ImpactRecord).filter(
        ImpactRecord.organization_id == current_user.organization_id,
        ImpactRecord.predicted_at >= today_start
    ).all()

    today_impact = sum(r.value_amount for r in today_impacts)

    # Rank position
    leaderboard = db.query(LeaderboardEntry).filter(
        LeaderboardEntry.user_id == current_user.id,
        LeaderboardEntry.period == "day"
    ).first()

    return {
        "date": now.date().isoformat(),
        "actions_taken": today_actions,
        "impact_generated": f"${today_impact:,.0f}",
        "current_rank": leaderboard.rank if leaderboard else None,
        "message": f"Great work! You took {today_actions} actions and generated ${today_impact:,.0f} in impact today.",
        "email_subject": f"Your ForecastX Daily Summary - ${today_impact:,.0f} impact 🎉"
    }


@router.get("/insights-for-home")
def get_insights_for_home(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top insights to show on home dashboard"""

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "urgent_count": 0,
            "urgent_insight": None,
            "action": empty_state_message(db, current_user.organization_id),
        }

    critical = summary.band_counts["critical"]
    return {
        "urgent_count": critical,
        "urgent_insight": (
            f"{critical} customers are in the critical {summary.subject} band"
            if critical else None
        ),
        "action": "Check your Insights",
    }
