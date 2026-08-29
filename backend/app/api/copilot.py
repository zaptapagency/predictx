"""
AI Copilot API

Recommendations are derived from the latest scoring run: the copilot's job is to
answer "who do I call next", and that ordering is score x revenue at stake. See
app/services/prediction_summary.py. Stored CopilotRecommendation rows are still
used for the execute/dismiss/feedback loop below.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.db.models_saas import User
from app.db.copilot_models import CopilotRecommendation, CopilotFeedback
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.utils.time import utcnow
from app.services.prediction_summary import (
    empty_state_message, money, summarize_org_predictions,
)

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

# The next step that fits each band, mirroring the recommended_action scoring writes.
_ACTION_COPY = {
    "reach_out_now": ("call", "Call {name} today"),
    "offer_discount": ("email", "Email {name} a retention offer"),
    "schedule_qbr": ("meeting", "Book a business review with {name}"),
    "monitor": ("task", "Keep {name} on your watchlist"),
}


@router.get("/recommendations")
def get_recommendations(
    limit: int = Query(5),
    executed_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get copilot recommendations, ranked by what the latest scoring run says is at stake"""

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "recommendations": [],
            "pending_count": 0,
            "message": empty_state_message(db, current_user.organization_id),
        }

    # Revenue at stake is the ranking key, but customers whose value the upload
    # never told us about must still be reachable, so they fall back to score.
    candidates = sorted(
        summary.at_risk,
        key=lambda c: (c.revenue_at_stake is not None, c.revenue_at_stake or 0.0, c.score),
        reverse=True,
    )

    recommendations = []
    for customer in candidates[:limit]:
        action_type, title = _ACTION_COPY.get(
            customer.recommended_action, ("task", "Follow up with {name}")
        )
        drivers = customer.drivers
        reasoning = (
            f"{summary.model_name} put {customer.name} in the {customer.band} band at "
            f"{customer.score * 100:.0f}% {summary.subject}"
            + (f", {customer.percentile:.0f}th percentile of the cohort" if customer.percentile is not None else "")
            + "."
        )
        if drivers:
            reasoning += f" The strongest drivers on this account are {', '.join(drivers)}."
        if customer.annual_revenue is None:
            reasoning += " Their annual revenue isn't in the uploaded data, so impact is unknown."

        recommendations.append({
            "id": f"pred-{summary.model_id}-{customer.customer_id}",
            "title": title.format(name=customer.name),
            "description": (
                f"{customer.name} is one of the highest-stakes accounts in this scoring run."
                + (f" Losing them would put {money(customer.annual_revenue)} of annual revenue in play."
                   if customer.annual_revenue is not None else "")
            ),
            "reasoning": reasoning,
            "suggested_action": title.format(name=customer.name),
            "action_type": action_type,
            "estimated_impact": money(customer.revenue_at_stake),
            "success_probability": None,  # We have no outcome history, so we don't claim one.
            "confidence": f"{customer.confidence * 100:.0f}%" if customer.confidence else None,
            "was_executed": False,
            "customer_id": customer.customer_id,
            "entity_email": customer.email,
            "created_at": summary.scored_at.isoformat() if summary.scored_at else None,
        })

    return {
        "recommendations": recommendations,
        "pending_count": len(candidates),
        "model": summary.model_name,
        "scored_at": summary.scored_at.isoformat() if summary.scored_at else None,
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
    rec.execution_date = utcnow()
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
    """Get AI copilot insights about what the latest scoring run is recommending"""

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "message": empty_state_message(db, current_user.organization_id),
            "total_recommendations": 0,
            "executed": 0,
            "execution_rate": "0.0%",
            "next_action": None,
            "estimated_impact": None,
        }

    # Execution is tracked on the stored recommendations the user has acted on.
    executed = db.query(CopilotRecommendation).filter(
        CopilotRecommendation.user_id == current_user.id,
        CopilotRecommendation.was_executed == True
    ).count()

    at_risk = summary.at_risk
    next_up = max(at_risk, key=lambda c: (c.revenue_at_stake or 0.0, c.score)) if at_risk else None

    return {
        "message": (
            f"{summary.model_name} flagged {len(at_risk)} of {summary.total_customers} "
            f"customers in its latest run."
        ),
        "total_recommendations": len(at_risk),
        "executed": executed,
        "execution_rate": f"{executed / len(at_risk) * 100:.1f}%" if at_risk else "0.0%",
        "next_action": f"Contact {next_up.name}" if next_up else None,
        "estimated_impact": money(summary.revenue_at_stake) if summary.revenue_known_for else None,
    }
