"""
AI Copilot API
Smart recommendations for actions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.db.models_saas import User
from app.db.copilot_models import CopilotRecommendation, CopilotFeedback
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.get("/recommendations")
def get_recommendations(
    limit: int = Query(5),
    executed_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI copilot recommendations for user"""

    query = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.user_id == current_user.id,
        CopilotRecommendation.is_dismissed == False
    )

    if executed_only:
        query = query.filter(CopilotRecommendation.was_executed == True)

    recommendations = query.order_by(desc(CopilotRecommendation.created_at)).limit(limit).all()

    return {
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "reasoning": r.reasoning,
                "suggested_action": r.suggested_action,
                "action_type": r.action_type,
                "estimated_impact": f"${r.estimated_impact:,.0f}" if r.estimated_impact else None,
                "success_probability": f"{r.success_probability * 100:.0f}%" if r.success_probability else None,
                "confidence": f"{r.confidence * 100:.0f}%" if r.confidence else None,
                "was_executed": r.was_executed,
                "created_at": r.created_at.isoformat(),
            }
            for r in recommendations
        ],
        "pending_count": db.query(CopilotRecommendation).filter(
            CopilotRecommendation.user_id == current_user.id,
            CopilotRecommendation.was_executed == False,
            CopilotRecommendation.is_dismissed == False
        ).count()
    }


@router.post("/{recommendation_id}/execute")
def execute_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a copilot recommendation"""
    rec = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.id == recommendation_id,
        CopilotRecommendation.user_id == current_user.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.was_executed = True
    rec.execution_date = datetime.utcnow()
    rec.execution_outcome = "pending"

    db.commit()

    return {
        "status": "executed",
        "recommendation_id": recommendation_id,
        "action": rec.suggested_action,
        "message": f"Executing: {rec.suggested_action}"
    }


@router.post("/{recommendation_id}/dismiss")
def dismiss_recommendation(
    recommendation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss a copilot recommendation"""
    rec = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.id == recommendation_id,
        CopilotRecommendation.user_id == current_user.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.is_dismissed = True
    db.commit()

    return {"status": "dismissed"}


@router.post("/{recommendation_id}/feedback")
def provide_feedback(
    recommendation_id: int,
    was_helpful: bool,
    rating: int = Query(None),
    feedback_text: str = Query(None),
    actual_outcome: str = Query(None),
    actual_impact: float = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Provide feedback on a recommendation"""
    rec = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.id == recommendation_id,
        CopilotRecommendation.user_id == current_user.id
    ).first()

    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    feedback = CopilotFeedback(
        recommendation_id=recommendation_id,
        user_id=current_user.id,
        was_helpful=was_helpful,
        rating=rating,
        feedback_text=feedback_text,
        actual_outcome=actual_outcome,
        actual_impact=actual_impact
    )

    db.add(feedback)

    # Update recommendation outcome
    if actual_outcome:
        rec.execution_outcome = actual_outcome
    if actual_impact:
        rec.estimated_impact = actual_impact

    db.commit()

    return {"status": "feedback_recorded", "message": "Thank you for the feedback! This helps improve recommendations."}


@router.get("/insights")
def get_copilot_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI copilot insights about user's performance"""

    recommendations = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.user_id == current_user.id
    ).all()

    executed = sum(1 for r in recommendations if r.was_executed)
    success_rate = (executed / len(recommendations) * 100) if recommendations else 0

    return {
        "message": "Here's what the AI Copilot is recommending for you:",
        "total_recommendations": len(recommendations),
        "executed": executed,
        "execution_rate": f"{success_rate:.1f}%",
        "next_action": recommendations[0].suggested_action if recommendations else None,
        "estimated_impact": f"${sum(r.estimated_impact or 0 for r in recommendations if r.was_executed):,.0f}"
    }
