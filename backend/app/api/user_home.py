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
from app.db.activity_models import UserActivity
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/user", tags=["user-home"])


@router.get("/home")
def get_user_home(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized user home dashboard"""

    # Get this month's ROI data
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    impact_records = db.query(ImpactRecord).filter(
        ImpactRecord.user_id == current_user.id,
        ImpactRecord.created_at >= month_start
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

    # Get top 3 actions
    pending_actions = db.query(Action).filter(
        Action.assigned_to_id == current_user.id,
        Action.status == "pending"
    ).order_by(
        Action.priority.desc(),
        Action.estimated_impact.desc()
    ).limit(3).all()

    top_actions = [
        {
            "id": a.id,
            "title": a.title,
            "icon": "🎯",
            "impact": f"${a.estimated_impact:,.0f}" if a.estimated_impact else "TBD",
            "priority": "CRITICAL" if a.priority == "critical" else "HIGH" if a.priority == "high" else "MEDIUM"
        }
        for a in pending_actions
    ]

    # Get recent wins (user activity)
    recent_activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.is_celebratory == True
    ).order_by(desc(UserActivity.created_at)).limit(5).all()

    recent_wins = [
        {
            "title": a.activity_title,
            "impact": f"${a.revenue_impact:,.0f}" if a.revenue_impact else f"+{a.customers_affected} customers",
            "when": a.created_at.strftime("%m/%d")
        }
        for a in recent_activities
    ]

    # Forecast (simple linear growth)
    avg_daily_impact = total_impact / max((now - month_start).days, 1)
    days_remaining = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - now
    forecast_amount = total_impact + (avg_daily_impact * days_remaining.days)

    return {
        "user_name": current_user.name.split()[0],
        "this_month_impact": f"${total_impact:,.0f}",
        "revenue_saved": f"${revenue_saved:,.0f}",
        "revenue_created": f"${revenue_created:,.0f}",
        "rank": rank or 999,
        "rank_change": rank_change,
        "current_streak": stats.current_streak if stats else 0,
        "badges_earned": len(achievements),
        "next_badge": next_badge or {
            "name": "Revenue Maker",
            "icon": "💰",
            "progress": int(total_impact / 10000),
            "target": 10
        },
        "top_actions": top_actions if top_actions else [
            {
                "id": 1,
                "title": "No pending actions - take a quick win!",
                "icon": "⚡",
                "impact": "Varies",
                "priority": "MEDIUM"
            }
        ],
        "forecast_next_month": f"${forecast_amount:,.0f}",
        "forecast_confidence": "75%",
        "recent_wins": recent_wins if recent_wins else [
            {
                "title": "Welcome to ForecastX!",
                "impact": "Start taking actions to earn wins",
                "when": "Today"
            }
        ],
        "recommended_playbooks": [
            {
                "id": 1,
                "name": "Churn Prevention",
                "roi": "6.5x ROI",
                "reason": "Your highest-value use case based on data"
            },
            {
                "id": 2,
                "name": "Lead Scoring",
                "roi": "4.2x ROI",
                "reason": "Most adopted by your team - proven results"
            },
            {
                "id": 3,
                "name": "Expansion Detector",
                "roi": "3.8x ROI",
                "reason": "Complements your current playbooks perfectly"
            }
        ]
    }


@router.get("/daily-summary")
def get_daily_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's daily summary (for email digest)"""

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's actions
    today_actions = db.query(Action).filter(
        Action.assigned_to_id == current_user.id,
        Action.created_at >= today_start
    ).count()

    # Today's impact
    today_impacts = db.query(ImpactRecord).filter(
        ImpactRecord.user_id == current_user.id,
        ImpactRecord.created_at >= today_start
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

    from app.db.insights_models import Insight

    urgent_insights = db.query(Insight).filter(
        Insight.user_id == current_user.id,
        Insight.is_urgent == True,
        Insight.dismissed == False
    ).limit(1).all()

    return {
        "urgent_count": len(urgent_insights),
        "urgent_insight": urgent_insights[0].title if urgent_insights else None,
        "action": "Check your Insights"
    }
