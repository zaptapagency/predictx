"""
Insights Feed API
Daily reminders and personalized recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime

from app.db.models_saas import User
from app.db.insights_models import Insight, InsightPreference
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/insights", tags=["insights"])


class InsightResponse(BaseModel):
    id: int
    title: str
    description: str
    icon: str
    recommended_action: str
    estimated_impact: float
    is_urgent: bool
    is_read: bool


@router.get("/feed")
def get_insights_feed(
    limit: int = Query(10),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's insights feed (daily reminders)"""

    query = db.query(Insight).filter(
        Insight.user_id == current_user.id,
        Insight.dismissed == False
    )

    if unread_only:
        query = query.filter(Insight.is_read == False)

    insights = query.order_by(desc(Insight.is_urgent), desc(Insight.created_at)).limit(limit).all()

    return {
        "insights": [
            {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "icon": i.icon,
                "recommended_action": i.recommended_action,
                "estimated_impact": f"${i.estimated_impact:,.0f}" if i.estimated_impact else None,
                "confidence": f"{i.confidence * 100:.0f}%" if i.confidence else None,
                "is_urgent": i.is_urgent,
                "is_read": i.is_read,
                "related_entity": i.related_entity,
            }
            for i in insights
        ],
        "unread_count": db.query(Insight).filter(
            Insight.user_id == current_user.id,
            Insight.is_read == False,
            Insight.dismissed == False
        ).count()
    }


@router.post("/mark-read/{insight_id}")
def mark_insight_read(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark insight as read"""
    insight = db.query(Insight).filter(
        Insight.id == insight_id,
        Insight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.is_read = True
    db.commit()
    return {"status": "marked_read"}


@router.post("/dismiss/{insight_id}")
def dismiss_insight(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss insight"""
    insight = db.query(Insight).filter(
        Insight.id == insight_id,
        Insight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.dismissed = True
    db.commit()
    return {"status": "dismissed"}


@router.get("/preferences")
def get_insight_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's insight preferences"""
    pref = db.query(InsightPreference).filter(
        InsightPreference.user_id == current_user.id
    ).first()

    if not pref:
        pref = InsightPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()

    return {
        "daily_email_enabled": pref.daily_email_enabled,
        "in_app_notifications": pref.in_app_notifications,
        "slack_notifications": pref.slack_notifications,
        "digest_time": pref.digest_time,
        "include_recommendations": pref.include_recommendations,
        "include_reminders": pref.include_reminders,
        "include_milestones": pref.include_milestones,
        "include_team_updates": pref.include_team_updates,
    }


@router.put("/preferences")
def update_insight_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's insight preferences"""
    pref = db.query(InsightPreference).filter(
        InsightPreference.user_id == current_user.id
    ).first()

    if not pref:
        pref = InsightPreference(user_id=current_user.id)

    for key, value in preferences.items():
        if hasattr(pref, key):
            setattr(pref, key, value)

    db.add(pref)
    db.commit()
    return {"status": "updated"}


@router.get("/daily-digest")
def get_daily_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's digest (summary of all insights)"""
    today = datetime.utcnow().date()

    insights = db.query(Insight).filter(
        Insight.user_id == current_user.id,
        Insight.dismissed == False
    ).order_by(desc(Insight.is_urgent)).limit(5).all()

    return {
        "digest_date": today.isoformat(),
        "insight_count": len(insights),
        "urgent_count": sum(1 for i in insights if i.is_urgent),
        "insights": [
            {
                "title": i.title,
                "description": i.description,
                "icon": i.icon,
                "is_urgent": i.is_urgent,
            }
            for i in insights
        ],
        "message": f"You have {len(insights)} insights today. {sum(1 for i in insights if i.is_urgent)} are urgent."
    }
