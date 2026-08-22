"""
Team Activity Feed API
Social proof and celebration tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime

from app.db.models_saas import User
from app.db.activity_models import TeamActivity, ActivityReaction
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/activity-feed", tags=["activity-feed"])


@router.get("/team")
def get_team_activity(
    limit: int = Query(20),
    activity_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team activity feed (what everyone is doing)"""

    query = db.query(TeamActivity).filter(
        TeamActivity.organization_id == current_user.organization_id,
        TeamActivity.is_public == True
    )

    if activity_type:
        query = query.filter(TeamActivity.activity_type == activity_type)

    activities = query.order_by(desc(TeamActivity.created_at)).limit(limit).all()

    return {
        "activities": [
            {
                "id": a.id,
                "user": a.user.name,
                "title": a.title,
                "description": a.description,
                "type": a.activity_type,
                "entity_name": a.entity_name,
                "revenue_impact": f"${a.revenue_impact:,.0f}" if a.revenue_impact else None,
                "customers_affected": a.customers_affected,
                "reactions": a.reaction_count,
                "is_celebratory": a.is_celebratory,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ],
        "total": len(activities)
    }


@router.get("/{activity_id}")
def get_activity_detail(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific activity"""
    activity = db.query(TeamActivity).filter(
        TeamActivity.id == activity_id,
        TeamActivity.organization_id == current_user.organization_id
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    reactions = db.query(ActivityReaction).filter(
        ActivityReaction.activity_id == activity_id
    ).all()

    user_reacted = db.query(ActivityReaction).filter(
        ActivityReaction.activity_id == activity_id,
        ActivityReaction.user_id == current_user.id
    ).first()

    return {
        "id": activity.id,
        "user": activity.user.name,
        "title": activity.title,
        "description": activity.description,
        "type": activity.activity_type,
        "entity_name": activity.entity_name,
        "revenue_impact": f"${activity.revenue_impact:,.0f}" if activity.revenue_impact else None,
        "customers_affected": activity.customers_affected,
        "reactions": activity.reaction_count,
        "is_celebratory": activity.is_celebratory,
        "user_reacted": bool(user_reacted),
        "reaction_emoji": user_reacted.emoji if user_reacted else None,
        "created_at": activity.created_at.isoformat(),
        "user_reactions": [
            {"user": r.user.name, "emoji": r.emoji}
            for r in reactions[:10]
        ]
    }


@router.post("/{activity_id}/react")
def react_to_activity(
    activity_id: int,
    emoji: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """React to an activity with an emoji"""
    activity = db.query(TeamActivity).filter(TeamActivity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Remove existing reaction from this user
    existing = db.query(ActivityReaction).filter(
        ActivityReaction.activity_id == activity_id,
        ActivityReaction.user_id == current_user.id
    ).first()

    if existing:
        db.delete(existing)
        activity.reaction_count -= 1

    # Add new reaction
    if emoji:
        reaction = ActivityReaction(
            activity_id=activity_id,
            user_id=current_user.id,
            emoji=emoji
        )
        db.add(reaction)
        activity.reaction_count += 1

    db.commit()
    return {"status": "reacted", "emoji": emoji, "total_reactions": activity.reaction_count}


@router.get("/celebratory/feed")
def get_celebratory_activities(
    limit: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get only celebratory/high-impact activities"""
    activities = db.query(TeamActivity).filter(
        TeamActivity.organization_id == current_user.organization_id,
        TeamActivity.is_public == True,
        TeamActivity.is_celebratory == True
    ).order_by(desc(TeamActivity.created_at)).limit(limit).all()

    return {
        "celebrations": [
            {
                "user": a.user.name,
                "title": a.title,
                "revenue_impact": f"${a.revenue_impact:,.0f}" if a.revenue_impact else None,
                "reactions": a.reaction_count,
                "created_at": a.created_at.isoformat(),
            }
            for a in activities
        ]
    }
