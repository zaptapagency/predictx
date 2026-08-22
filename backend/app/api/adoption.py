"""
Adoption Tracker API
Team adoption metrics and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models_saas import User
from app.db.adoption_models import TeamAdoption, UserAdoption
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/adoption", tags=["adoption"])


@router.get("/team-summary")
def get_team_adoption_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team-wide adoption metrics"""

    adoption = db.query(TeamAdoption).filter(
        TeamAdoption.organization_id == current_user.organization_id
    ).first()

    if not adoption:
        adoption = TeamAdoption(organization_id=current_user.organization_id)
        db.add(adoption)
        db.commit()

    return {
        "team_size": adoption.total_team_size,
        "active_users": adoption.active_users,
        "adoption_rate": f"{adoption.adoption_rate * 100:.1f}%",
        "dau": adoption.daily_active_users,
        "wau": adoption.weekly_active_users,
        "mau": adoption.monthly_active_users,
        "avg_actions_per_user": f"{adoption.avg_actions_per_user:.1f}",
        "total_actions": adoption.total_actions,
        "playbooks_deployed": adoption.playbooks_deployed,
        "avg_playbooks_per_user": f"{adoption.avg_playbooks_per_user:.1f}",
        "health": "excellent" if adoption.adoption_rate > 0.8 else "good" if adoption.adoption_rate > 0.5 else "needs_improvement"
    }


@router.get("/user-breakdown")
def get_user_adoption_breakdown(
    stage: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get breakdown of users by adoption stage"""

    query = db.query(UserAdoption).filter(
        UserAdoption.organization_id == current_user.organization_id
    )

    if stage:
        query = query.filter(UserAdoption.stage == stage)

    users = query.all()

    stages = {}
    for u in users:
        stage_name = u.stage
        if stage_name not in stages:
            stages[stage_name] = []
        stages[stage_name].append(u)

    return {
        "breakdown": {
            stage_name: {
                "count": len(users),
                "percentage": f"{len(users) / len(users) * 100:.1f}%" if users else "0%",
                "avg_actions": f"{sum(u.total_actions for u in stage_users) / len(stage_users):.1f}" if stage_users else "0",
                "avg_engagement": f"{sum(u.engagement_score for u in stage_users) / len(stage_users):.1f}" if stage_users else "0",
            }
            for stage_name, stage_users in stages.items()
        },
        "funnel": {
            "onboarded": len([u for u in users if u.stage == "onboarded"]),
            "activated": len([u for u in users if u.stage == "activated"]),
            "habit_forming": len([u for u in users if u.stage == "habit_forming"]),
            "power_user": len([u for u in users if u.stage == "power_user"]),
            "churned": len([u for u in users if u.stage == "churned"]),
        }
    }


@router.get("/my-adoption")
def get_my_adoption(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's adoption metrics"""

    adoption = db.query(UserAdoption).filter(
        UserAdoption.user_id == current_user.id
    ).first()

    if not adoption:
        adoption = UserAdoption(
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        db.add(adoption)
        db.commit()

    return {
        "stage": adoption.stage,
        "engagement_score": f"{adoption.engagement_score:.1f}/100",
        "churn_risk": f"{adoption.churn_risk * 100:.0f}%",
        "days_active": adoption.days_active,
        "total_actions": adoption.total_actions,
        "total_predictions": adoption.total_predictions,
        "playbooks_deployed": adoption.playbooks_deployed,
        "features_used": adoption.features_used,
        "milestones": {
            "first_action": adoption.first_action_at.isoformat() if adoption.first_action_at else None,
            "first_value": adoption.first_value_at.isoformat() if adoption.first_value_at else None,
            "habit_formed": adoption.habit_formed_at.isoformat() if adoption.habit_formed_at else None,
        },
        "last_active": adoption.last_active_at.isoformat() if adoption.last_active_at else None,
    }


@router.get("/at-risk-users")
def get_at_risk_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get users at risk of churning"""

    at_risk = db.query(UserAdoption).filter(
        UserAdoption.organization_id == current_user.organization_id,
        UserAdoption.churn_risk > 0.5  # 50%+ churn risk
    ).order_by(desc(UserAdoption.churn_risk)).all()

    return {
        "at_risk_count": len(at_risk),
        "users": [
            {
                "user_id": u.user_id,
                "churn_risk": f"{u.churn_risk * 100:.0f}%",
                "stage": u.stage,
                "days_active": u.days_active,
                "last_active": u.last_active_at.isoformat() if u.last_active_at else None,
                "recommended_action": "Send re-engagement email" if u.days_active < 7 else "Schedule check-in call",
            }
            for u in at_risk
        ]
    }


@router.get("/power-users")
def get_power_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get power users (highest adoption)"""

    power_users = db.query(UserAdoption).filter(
        UserAdoption.organization_id == current_user.organization_id,
        UserAdoption.stage == "power_user"
    ).order_by(desc(UserAdoption.engagement_score)).limit(10).all()

    return {
        "power_users_count": len(power_users),
        "users": [
            {
                "user_id": u.user_id,
                "engagement_score": f"{u.engagement_score:.1f}/100",
                "total_actions": u.total_actions,
                "playbooks_deployed": u.playbooks_deployed,
                "role": "Adoption Champion",
                "recommended_action": "Ask for feedback, involve in new feature testing",
            }
            for u in power_users
        ]
    }


@router.post("/mark-stage/{user_id}/{stage}")
def mark_user_stage(
    user_id: int,
    stage: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a user as reaching a new adoption stage (admin only)"""

    adoption = db.query(UserAdoption).filter(
        UserAdoption.user_id == user_id,
        UserAdoption.organization_id == current_user.organization_id
    ).first()

    if not adoption:
        raise HTTPException(status_code=404, detail="User adoption record not found")

    old_stage = adoption.stage
    adoption.stage = stage

    db.commit()

    return {
        "status": "updated",
        "user_id": user_id,
        "old_stage": old_stage,
        "new_stage": stage,
        "message": f"User moved from {old_stage} to {stage}"
    }
