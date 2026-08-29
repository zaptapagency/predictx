"""
Insights Feed API

The feed is derived from the organization's latest scoring run rather than
stored rows: an insight is an observation about the current predictions, and a
stale observation is worse than none. See app/services/prediction_summary.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime
from typing import Any, Dict, List

from app.db.models_saas import User
from app.db.insights_models import Insight, InsightPreference
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.utils.time import utcnow
from app.services.prediction_summary import (
    PredictionSummary, empty_state_message, money, summarize_org_predictions,
)

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


def _derive_insights(summary: PredictionSummary) -> List[Dict[str, Any]]:
    """
    Turn a scoring run into observations worth reading.

    Ordered most-actionable first. Anything we can't compute from the run is
    simply left out rather than filled in.
    """
    insights: List[Dict[str, Any]] = []
    subject = summary.subject
    at_risk = summary.at_risk
    total = summary.total_customers

    # 1. How concentrated the risk is. This is the headline number for the tab.
    if at_risk:
        share = len(at_risk) / total * 100 if total else 0
        description = (
            f"{len(at_risk)} of {total} scored customers ({share:.0f}%) are in the "
            f"high or critical {subject} band according to {summary.model_name}."
        )
        if summary.revenue_known_for:
            description += (
                f" {money(summary.revenue_at_stake)} of annual revenue sits behind them"
                f" (revenue known for {summary.revenue_known_for} of {len(at_risk)})."
            )
        insights.append({
            "id": "risk-concentration",
            "title": f"{len(at_risk)} customers need attention",
            "description": description,
            "icon": "🚨",
            "recommended_action": "Work the Action Center from the top down",
            "estimated_impact": money(summary.revenue_at_stake) if summary.revenue_known_for else None,
            "confidence": None,
            "is_urgent": summary.band_counts["critical"] > 0,
            "is_read": False,
            "related_entity": summary.model_name,
        })
    else:
        insights.append({
            "id": "risk-concentration",
            "title": "No customers in the high or critical band",
            "description": (
                f"{summary.model_name} scored {total} customers and none landed above the "
                f"high-{subject} threshold. This is a prediction, not an outcome — keep scoring "
                f"as new data arrives."
            ),
            "icon": "✅",
            "recommended_action": "Re-score once you have fresher data",
            "estimated_impact": None,
            "confidence": None,
            "is_urgent": False,
            "is_read": False,
            "related_entity": summary.model_name,
        })

    # 2. What is actually driving the risk, aggregated across the cohort.
    for driver in summary.drivers[:2]:
        average = driver["average_value"]
        description = (
            f"'{driver['feature']}' accounts for {driver['share_of_risk'] * 100:.0f}% of the "
            f"modelled {subject} across {driver['customers_affected']} customers."
        )
        if average is not None:
            description += f" Their average {driver['feature']} is {average:,.2f}."
        insights.append({
            "id": f"driver-{driver['feature']}",
            "title": f"{driver['feature']} is the biggest driver" if driver is summary.drivers[0]
                     else f"{driver['feature']} is also pulling scores up",
            "description": description,
            "icon": "📊",
            "recommended_action": f"Look at {driver['feature']} for the flagged accounts",
            "estimated_impact": None,
            "confidence": None,
            "is_urgent": False,
            "is_read": False,
            "related_entity": driver["feature"],
        })

    # 3. Movement since the previous run, only when there is a previous run.
    shift = summary.band_shift()
    if shift is not None:
        worse = shift["critical"] + shift["high"]
        direction = "more" if worse > 0 else "fewer" if worse < 0 else "the same number of"
        insights.append({
            "id": "risk-shift",
            "title": f"{abs(worse) if worse else 'No'} change in at-risk customers",
            "description": (
                f"Compared with the previous scoring run this org has {abs(worse)} {direction} "
                f"customers in the high or critical band "
                f"(critical {shift['critical']:+d}, high {shift['high']:+d})."
            ),
            "icon": "📈" if worse > 0 else "📉" if worse < 0 else "➖",
            "recommended_action": "Compare the two runs on the Predictions tab",
            "estimated_impact": None,
            "confidence": None,
            "is_urgent": worse > 0,
            "is_read": False,
            "related_entity": summary.model_name,
        })

    # 4. The single account that costs the most to lose.
    valued = [c for c in at_risk if c.revenue_at_stake is not None]
    if valued:
        top = max(valued, key=lambda c: c.revenue_at_stake)
        insights.append({
            "id": f"top-account-{top.customer_id}",
            "title": f"{top.name} is your most expensive risk",
            "description": (
                f"{top.name} scores {top.score * 100:.0f}% {subject} ({top.band}) on "
                f"{money(top.annual_revenue)} of annual revenue"
                + (f", driven by {', '.join(top.drivers)}." if top.drivers else ".")
            ),
            "icon": "💰",
            "recommended_action": f"Contact {top.name}",
            "estimated_impact": money(top.revenue_at_stake),
            "confidence": f"{top.confidence * 100:.0f}%" if top.confidence else None,
            "is_urgent": top.band == "critical",
            "is_read": False,
            "related_entity": top.name,
        })

    return insights


@router.get("/feed")
def get_insights_feed(
    limit: int = Query(10),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's insights feed, derived from the latest scoring run"""

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "insights": [],
            "unread_count": 0,
            "message": empty_state_message(db, current_user.organization_id),
        }

    insights = _derive_insights(summary)[:limit]

    return {
        "insights": insights,
        "unread_count": len(insights),
        "model": summary.model_name,
        "scored_at": summary.scored_at.isoformat() if summary.scored_at else None,
        "customers_scored": summary.total_customers,
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
    today = utcnow().date()

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "digest_date": today.isoformat(),
            "insight_count": 0,
            "urgent_count": 0,
            "insights": [],
            "message": empty_state_message(db, current_user.organization_id),
        }

    insights = _derive_insights(summary)[:5]
    urgent = sum(1 for i in insights if i["is_urgent"])

    return {
        "digest_date": today.isoformat(),
        "insight_count": len(insights),
        "urgent_count": urgent,
        "insights": [
            {
                "title": i["title"],
                "description": i["description"],
                "icon": i["icon"],
                "is_urgent": i["is_urgent"],
            }
            for i in insights
        ],
        "message": f"You have {len(insights)} insights today. {urgent} are urgent."
    }
