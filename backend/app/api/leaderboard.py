"""
Leaderboard & Gamification API
Drive engagement through competition and achievements
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.db.models_saas import User, Organization
from app.db.leaderboard_models import LeaderboardEntry, Achievement, UserStats, UserActivity
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_name: str
    score: float
    rank_change: int
    customers_saved: int
    expansions_closed: int
    actions_taken: int
    revenue_generated: float
    action_streak: int
    achievements: list

# ============================================================================
# GET LEADERBOARD
# ============================================================================

@router.get("/rankings")
def get_leaderboard(
    period: str = Query("week"),  # day, week, month, all_time
    metric: str = Query("score"),  # score, revenue, customers_saved, etc
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get team leaderboard rankings
    """

    org_id = current_user.organization_id

    # Determine period dates
    now = datetime.utcnow()
    if period == "day":
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        period_start = now - timedelta(days=now.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # all_time
        period_start = datetime(2020, 1, 1)

    # Get leaderboard entries
    entries = db.query(LeaderboardEntry).filter(
        LeaderboardEntry.organization_id == org_id,
        LeaderboardEntry.period == period,
        LeaderboardEntry.period_start >= period_start
    ).order_by(LeaderboardEntry.rank).limit(limit).all()

    # Get achievements for each user
    leaderboard = []
    for entry in entries:
        achievements = db.query(Achievement).filter(
            Achievement.user_id == entry.user_id
        ).all()

        current_user_entry = entry.user_id == current_user.id
        rank_trend = ""
        if entry.rank_change and entry.rank_change > 0:
            rank_trend = f"↑ +{entry.rank_change}"
        elif entry.rank_change and entry.rank_change < 0:
            rank_trend = f"↓ {entry.rank_change}"
        else:
            rank_trend = "→"

        medals = ["🥇", "🥈", "🥉"]
        medal = medals[entry.rank - 1] if entry.rank <= 3 else f"#{entry.rank}"

        leaderboard.append({
            "rank": entry.rank,
            "medal": medal,
            "user_id": entry.user_id,
            "user_name": entry.user.name,
            "score": entry.score,
            "rank_change": rank_trend,
            "customers_saved": entry.customers_saved,
            "expansions_closed": entry.expansions_closed,
            "actions_taken": entry.actions_taken,
            "revenue_generated": f"${entry.revenue_generated:,.0f}",
            "action_streak": entry.action_streak,
            "is_current_user": current_user_entry,
            "is_top_performer": entry.is_top_performer,
            "achievements": [
                {
                    "name": a.name,
                    "icon": a.icon,
                    "rarity": a.rarity
                }
                for a in achievements
            ]
        })

    return {
        "period": period,
        "leaderboard": leaderboard,
        "total_users": len(leaderboard),
        "current_user_position": next(
            (i for i, entry in enumerate(leaderboard, 1) if entry["is_current_user"]),
            None
        )
    }


# ============================================================================
# GET PERSONAL STATS
# ============================================================================

@router.get("/my-stats")
def get_personal_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed personal performance stats"""

    stats = db.query(UserStats).filter(
        UserStats.user_id == current_user.id
    ).first()

    if not stats:
        return {"error": "No stats found"}

    # Get current rank
    leaderboard = db.query(LeaderboardEntry).filter(
        LeaderboardEntry.user_id == current_user.id,
        LeaderboardEntry.period == "week"
    ).first()

    # Get achievements
    achievements = db.query(Achievement).filter(
        Achievement.user_id == current_user.id
    ).all()

    # Get recent activity
    recent_activity = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(desc(UserActivity.created_at)).limit(5).all()

    return {
        "user": {
            "name": current_user.name,
            "role": getattr(current_user, 'role', 'Team Member'),
        },
        "stats": {
            "total_predictions": stats.total_predictions,
            "total_actions": stats.total_actions,
            "customers_saved": stats.total_customers_saved,
            "expansions_closed": stats.total_expansions_closed,
            "leads_converted": stats.total_leads_converted,
            "total_revenue": f"${stats.total_revenue_generated:,.0f}",
            "this_month_actions": stats.this_month_actions,
            "this_week_actions": stats.this_week_actions,
            "prediction_accuracy": f"{stats.prediction_accuracy * 100:.1f}%",
            "action_success_rate": f"{stats.action_success_rate * 100:.1f}%",
            "avg_revenue_per_action": f"${stats.avg_revenue_per_action:,.0f}",
        },
        "engagement": {
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "days_active": stats.days_active,
            "current_rank": leaderboard.rank if leaderboard else None,
            "rank_percentile": f"Top {stats.rank_percentile * 100:.0f}%" if stats.rank_percentile else "N/A",
        },
        "achievements": {
            "total": len(achievements),
            "recent": [
                {
                    "name": a.name,
                    "icon": a.icon,
                    "rarity": a.rarity,
                    "earned_at": a.earned_at
                }
                for a in achievements[:10]
            ]
        },
        "recent_activity": [
            {
                "activity": a.activity_title,
                "description": a.activity_description,
                "revenue_impact": f"${a.revenue_impact:,.0f}" if a.revenue_impact else None,
                "when": a.created_at
            }
            for a in recent_activity
        ]
    }


# ============================================================================
# GET ACHIEVEMENTS
# ============================================================================

@router.get("/achievements")
def get_all_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available achievements and user's progress"""

    all_achievements = db.query(Achievement).filter(
        Achievement.organization_id == current_user.organization_id
    ).all()

    user_achievements = db.query(Achievement).filter(
        Achievement.user_id == current_user.id
    ).all()

    user_achievement_ids = {a.id for a in user_achievements}

    return {
        "achievements": [
            {
                "id": a.id,
                "name": a.name,
                "icon": a.icon,
                "description": a.description,
                "rarity": a.rarity,
                "earned": a.id in user_achievement_ids,
                "threshold": a.threshold,
                "metric_type": a.metric_type,
                "unlock_percentage": f"{a.unlock_percentage * 100:.1f}%" if a.unlock_percentage else "N/A",
            }
            for a in all_achievements
        ],
        "user_achievement_count": len(user_achievements),
        "total_achievement_count": len(all_achievements)
    }


# ============================================================================
# ACTIVITY FEED
# ============================================================================

@router.get("/activity-feed")
def get_activity_feed(
    current_user: User = Depends(get_current_user),
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """Get team's recent activity (for celebration/motivation)"""

    org_id = current_user.organization_id

    activities = db.query(UserActivity).filter(
        UserActivity.organization_id == org_id,
        UserActivity.is_public == True
    ).order_by(desc(UserActivity.created_at)).limit(limit).all()

    return {
        "activity": [
            {
                "id": a.id,
                "user": a.user.name,
                "activity": a.activity_title,
                "description": a.activity_description,
                "icon": "🎉" if a.is_celebratory else "📋",
                "revenue_impact": f"${a.revenue_impact:,.0f}" if a.revenue_impact else None,
                "reactions": a.reaction_count,
                "when": a.created_at,
                "is_celebratory": a.is_celebratory,
            }
            for a in activities
        ]
    }


# ============================================================================
# STREAK TRACKING
# ============================================================================

@router.get("/streaks")
def get_team_streaks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team members with active streaks"""

    org_id = current_user.organization_id

    stats = db.query(UserStats).filter(
        UserStats.organization_id == org_id,
        UserStats.current_streak > 0
    ).order_by(desc(UserStats.current_streak)).limit(10).all()

    return {
        "streaks": [
            {
                "user": s.user.name,
                "current_streak": s.current_streak,
                "longest_streak": s.longest_streak,
                "streak_message": f"🔥 {s.current_streak}-day streak!" if s.current_streak >= 7 else f"{s.current_streak}-day streak",
                "last_action": s.last_action_at,
            }
            for s in stats
        ]
    }


# ============================================================================
# TEAM COMPARISON
# ============================================================================

@router.get("/team-comparison")
def get_team_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare current user to team average"""

    org_id = current_user.organization_id

    user_stats = db.query(UserStats).filter(
        UserStats.user_id == current_user.id
    ).first()

    team_stats = db.query(UserStats).filter(
        UserStats.organization_id == org_id
    ).all()

    team_avg_actions = (sum(s.total_actions for s in team_stats) / len(team_stats)) if team_stats else 0
    team_avg_customers = (sum(s.total_customers_saved for s in team_stats) / len(team_stats)) if team_stats else 0
    team_avg_revenue = (sum(s.total_revenue_generated for s in team_stats) / len(team_stats)) if team_stats else 0

    if user_stats:
        actions_vs_avg = ((user_stats.total_actions / team_avg_actions - 1) * 100) if team_avg_actions > 0 else 0
        customers_vs_avg = ((user_stats.total_customers_saved / team_avg_customers - 1) * 100) if team_avg_customers > 0 else 0
        revenue_vs_avg = ((user_stats.total_revenue_generated / team_avg_revenue - 1) * 100) if team_avg_revenue > 0 else 0
    else:
        actions_vs_avg = customers_vs_avg = revenue_vs_avg = 0

    return {
        "you": {
            "actions": user_stats.total_actions if user_stats else 0,
            "customers_saved": user_stats.total_customers_saved if user_stats else 0,
            "revenue": f"${(user_stats.total_revenue_generated if user_stats else 0):,.0f}",
        },
        "team_average": {
            "actions": f"{team_avg_actions:.0f}",
            "customers_saved": f"{team_avg_customers:.0f}",
            "revenue": f"${team_avg_revenue:,.0f}",
        },
        "your_vs_average": {
            "actions": f"{actions_vs_avg:+.0f}%",
            "customers_saved": f"{customers_vs_avg:+.0f}%",
            "revenue": f"{revenue_vs_avg:+.0f}%",
        },
        "message": "You're crushing it! 🚀" if actions_vs_avg > 0 else "Keep pushing! 💪"
    }


# ============================================================================
# MILESTONE PROGRESS
# ============================================================================

@router.get("/milestones")
def get_milestone_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get progress toward next achievements"""

    stats = db.query(UserStats).filter(
        UserStats.user_id == current_user.id
    ).first()

    if not stats:
        return {"error": "No stats found"}

    milestones = [
        {
            "name": "Churn Saver",
            "progress": stats.total_customers_saved,
            "target": 10,
            "icon": "🛡️",
            "reward": "Badge + 100 points",
        },
        {
            "name": "Expansion King",
            "progress": stats.total_expansions_closed,
            "target": 5,
            "icon": "👑",
            "reward": "Badge + 100 points",
        },
        {
            "name": "Action Master",
            "progress": stats.total_actions,
            "target": 100,
            "icon": "⚡",
            "reward": "Badge + 50 points",
        },
        {
            "name": "Streak Champion",
            "progress": stats.current_streak,
            "target": 30,
            "icon": "🔥",
            "reward": "Badge + 200 points",
        },
    ]

    return {
        "milestones": [
            {
                **m,
                "percentage": min(100, (m["progress"] / m["target"]) * 100),
                "status": "completed" if m["progress"] >= m["target"] else "in_progress",
            }
            for m in milestones
        ]
    }
