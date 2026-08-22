"""
ROI Tracker API
Track financial impact and prove value of ForecastX
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import defaultdict

from app.db.models_saas import User, Organization
from app.db.roi_models import ImpactRecord, ROISummary, PlaybookROI, CustomerImpact, ROIForecast
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/roi", tags=["roi"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ImpactRecordCreate(BaseModel):
    impact_type: str  # revenue_saved, revenue_created, efficiency_gain
    impact_category: str  # churn_prevention, expansion, etc
    entity_type: str  # customer, lead, employee
    entity_name: str
    value_amount: float
    is_annual: bool = False
    is_recurring: bool = False
    annual_value: float = None
    confidence_level: float = 0.85

# ============================================================================
# ROI DASHBOARD
# ============================================================================

@router.get("/dashboard")
def get_roi_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive ROI dashboard
    """

    if not current_user.organization_id:
        return {"error": "User not part of organization"}

    org_id = current_user.organization_id

    # Get this month's summary
    this_month = datetime.utcnow().strftime("%Y-%m")
    summary = db.query(ROISummary).filter(
        ROISummary.organization_id == org_id,
        ROISummary.period == "month",
        ROISummary.period_start >= datetime.utcnow().replace(day=1)
    ).first()

    if not summary:
        # Calculate on the fly if not cached
        summary = calculate_roi_summary(org_id, db)

    # Get all-time summary
    all_time = db.query(ROISummary).filter(
        ROISummary.organization_id == org_id,
        ROISummary.period == "all_time"
    ).first()

    # Get top playbooks
    top_playbooks = db.query(PlaybookROI).filter(
        PlaybookROI.organization_id == org_id
    ).order_by(desc(PlaybookROI.total_value)).limit(5).all()

    # Get top customers
    top_customers = db.query(CustomerImpact).filter(
        CustomerImpact.organization_id == org_id
    ).order_by(desc(CustomerImpact.total_impact)).limit(5).all()

    # Get forecast for next month
    next_month = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m")
    forecast = db.query(ROIForecast).filter(
        ROIForecast.organization_id == org_id,
        ROIForecast.forecast_month == next_month
    ).first()

    return {
        "summary": {
            "period": "this_month",
            "revenue_saved": summary.revenue_saved if summary else 0,
            "revenue_created": summary.revenue_created if summary else 0,
            "efficiency_gain": summary.efficiency_gain if summary else 0,
            "total_impact": summary.total_impact if summary else 0,
            "forecastx_cost": summary.forecastx_cost if summary else 0,
            "net_value": summary.net_value if summary else 0,
            "roi_multiplier": summary.roi_multiplier if summary else 0,
            "roi_percentage": summary.roi_percentage if summary else 0,
        },
        "all_time": {
            "total_impact": all_time.total_impact if all_time else 0,
            "revenue_saved": all_time.revenue_saved if all_time else 0,
            "revenue_created": all_time.revenue_created if all_time else 0,
            "customers_saved": all_time.customers_saved if all_time else 0,
            "expansions_closed": all_time.expansions_closed if all_time else 0,
            "roi_multiplier": all_time.roi_multiplier if all_time else 0,
        },
        "top_playbooks": [
            {
                "playbook_id": p.playbook_id,
                "executions": p.executions,
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "total_value": p.total_value,
                "value_per_execution": p.value_per_execution,
                "rank": p.rank_by_value
            }
            for p in top_playbooks
        ],
        "top_customers": [
            {
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "revenue_saved": c.revenue_saved,
                "revenue_created": c.revenue_created,
                "total_impact": c.total_impact,
                "playbooks_used": c.playbooks_used,
            }
            for c in top_customers
        ],
        "forecast_next_month": {
            "forecasted_impact": forecast.forecasted_impact if forecast else None,
            "confidence": forecast.confidence if forecast else None,
            "trend": forecast.trend if forecast else None,
        }
    }


# ============================================================================
# RECORD IMPACT
# ============================================================================

@router.post("/record-impact")
def record_impact(
    payload: ImpactRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record an impact event (customer saved, revenue created, etc.)
    """

    impact = ImpactRecord(
        organization_id=current_user.organization_id,
        impact_type=payload.impact_type,
        impact_category=payload.impact_category,
        entity_type=payload.entity_type,
        entity_id=payload.entity_name.lower().replace(" ", "-"),
        entity_name=payload.entity_name,
        value_amount=payload.value_amount,
        confidence_level=payload.confidence_level,
        is_annual=payload.is_annual,
        is_recurring=payload.is_recurring,
        annual_value=payload.annual_value or payload.value_amount,
        predicted_at=datetime.utcnow()
    )

    db.add(impact)
    db.commit()

    return {
        "success": True,
        "impact_id": impact.id,
        "message": f"Recorded impact: ${payload.value_amount:,.0f}"
    }


# ============================================================================
# CONFIRM IMPACT
# ============================================================================

@router.put("/confirm-impact/{impact_id}")
def confirm_impact(
    impact_id: int,
    outcome_note: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm that an impact actually happened
    User verified customer stayed, expansion closed, etc.
    """

    impact = db.query(ImpactRecord).filter(
        ImpactRecord.id == impact_id,
        ImpactRecord.organization_id == current_user.organization_id
    ).first()

    if not impact:
        raise HTTPException(status_code=404, detail="Impact record not found")

    impact.is_confirmed = True
    impact.confirmation_note = outcome_note
    impact.value_realized_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "impact_id": impact.id,
        "confirmed": True,
        "message": "Impact confirmed"
    }


# ============================================================================
# ROI HISTORY (Trend over time)
# ============================================================================

@router.get("/history")
def get_roi_history(
    months: int = Query(12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ROI summary history (monthly trend)"""

    org_id = current_user.organization_id

    summaries = db.query(ROISummary).filter(
        ROISummary.organization_id == org_id,
        ROISummary.period == "month"
    ).order_by(desc(ROISummary.period_start)).limit(months).all()

    return {
        "history": [
            {
                "month": s.period_start.strftime("%Y-%m"),
                "revenue_saved": s.revenue_saved,
                "revenue_created": s.revenue_created,
                "efficiency_gain": s.efficiency_gain,
                "total_impact": s.total_impact,
                "forecastx_cost": s.forecastx_cost,
                "net_value": s.net_value,
                "roi_multiplier": s.roi_multiplier,
            }
            for s in reversed(summaries)
        ]
    }


# ============================================================================
# PLAYBOOK PERFORMANCE
# ============================================================================

@router.get("/playbook-performance")
def get_playbook_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ROI performance per playbook"""

    org_id = current_user.organization_id

    playbooks = db.query(PlaybookROI).filter(
        PlaybookROI.organization_id == org_id
    ).order_by(desc(PlaybookROI.total_value)).all()

    return {
        "playbooks": [
            {
                "playbook_id": p.playbook_id,
                "executions": p.executions,
                "successful_outcomes": p.successful_outcomes,
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "total_value": p.total_value,
                "value_per_execution": f"${p.value_per_execution:,.0f}",
                "value_per_success": f"${p.value_per_success:,.0f}",
                "rank_by_value": p.rank_by_value,
            }
            for p in playbooks
        ]
    }


# ============================================================================
# CUSTOMER IMPACT ANALYSIS
# ============================================================================

@router.get("/customer-analysis")
def get_customer_analysis(
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get which customers generated most value"""

    org_id = current_user.organization_id

    customers = db.query(CustomerImpact).filter(
        CustomerImpact.organization_id == org_id
    ).order_by(desc(CustomerImpact.total_impact)).limit(limit).all()

    total_impact = db.query(func.sum(CustomerImpact.total_impact)).filter(
        CustomerImpact.organization_id == org_id
    ).scalar() or 0

    return {
        "total_impact": total_impact,
        "customer_count": len(customers),
        "customers": [
            {
                "customer_id": c.customer_id,
                "customer_name": c.customer_name,
                "customer_revenue": c.customer_revenue,
                "revenue_saved": c.revenue_saved,
                "revenue_created": c.revenue_created,
                "total_impact": c.total_impact,
                "percentage_of_total": f"{(c.total_impact / total_impact * 100):.1f}%" if total_impact > 0 else "0%",
                "playbooks_used": c.playbooks_used,
                "actions_taken": c.actions_taken,
            }
            for c in customers
        ]
    }


# ============================================================================
# ROI BREAKDOWN (By category)
# ============================================================================

@router.get("/breakdown")
def get_roi_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ROI breakdown by impact category"""

    org_id = current_user.organization_id

    impacts = db.query(ImpactRecord).filter(
        ImpactRecord.organization_id == org_id,
        ImpactRecord.is_confirmed == True
    ).all()

    breakdown = defaultdict(float)
    by_type = defaultdict(float)

    for impact in impacts:
        breakdown[impact.impact_category] += impact.value_amount
        by_type[impact.impact_type] += impact.value_amount

    return {
        "by_category": {
            "churn_prevention": breakdown.get("churn_prevention", 0),
            "expansion": breakdown.get("expansion", 0),
            "lead_conversion": breakdown.get("lead_conversion", 0),
            "fraud_prevention": breakdown.get("fraud_prevention", 0),
            "other": breakdown.get("other", 0),
        },
        "by_type": {
            "revenue_saved": by_type.get("revenue_saved", 0),
            "revenue_created": by_type.get("revenue_created", 0),
            "efficiency_gain": by_type.get("efficiency_gain", 0),
        },
        "total": sum(breakdown.values())
    }


# ============================================================================
# ROI FORECAST
# ============================================================================

@router.get("/forecast")
def get_roi_forecast(
    months_ahead: int = Query(3),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ROI forecast for upcoming months"""

    org_id = current_user.organization_id

    forecasts = []
    for i in range(months_ahead):
        month = (datetime.utcnow() + timedelta(days=30*i)).strftime("%Y-%m")
        forecast = db.query(ROIForecast).filter(
            ROIForecast.organization_id == org_id,
            ROIForecast.forecast_month == month
        ).first()

        if forecast:
            forecasts.append({
                "month": month,
                "forecasted_impact": forecast.forecasted_impact,
                "confidence": forecast.confidence,
                "trend": forecast.trend,
                "growth_rate": forecast.growth_rate,
            })

    return {
        "forecasts": forecasts,
        "recommendation": "Expand playbooks to maintain/grow impact"
    }


# ============================================================================
# ROI COMPARISON (This month vs last month)
# ============================================================================

@router.get("/comparison")
def get_roi_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare this month vs last month vs year-over-year"""

    org_id = current_user.organization_id

    # This month
    this_month_start = datetime.utcnow().replace(day=1)
    this_month = db.query(ROISummary).filter(
        ROISummary.organization_id == org_id,
        ROISummary.period_start == this_month_start
    ).first()

    # Last month
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    last_month = db.query(ROISummary).filter(
        ROISummary.organization_id == org_id,
        ROISummary.period_start == last_month_start
    ).first()

    # Calculate growth
    if this_month and last_month:
        growth = ((this_month.total_impact - last_month.total_impact) / last_month.total_impact * 100) if last_month.total_impact > 0 else 0
    else:
        growth = 0

    return {
        "this_month": {
            "total_impact": this_month.total_impact if this_month else 0,
            "revenue_saved": this_month.revenue_saved if this_month else 0,
            "revenue_created": this_month.revenue_created if this_month else 0,
        },
        "last_month": {
            "total_impact": last_month.total_impact if last_month else 0,
            "revenue_saved": last_month.revenue_saved if last_month else 0,
            "revenue_created": last_month.revenue_created if last_month else 0,
        },
        "growth": {
            "percentage": f"{growth:+.1f}%",
            "direction": "↑" if growth > 0 else "↓" if growth < 0 else "→",
            "message": f"ROI {'growing' if growth > 0 else 'declining' if growth < 0 else 'stable'}"
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_roi_summary(org_id: int, db: Session):
    """Calculate ROI summary for organization"""

    impacts = db.query(ImpactRecord).filter(
        ImpactRecord.organization_id == org_id,
        ImpactRecord.created_at >= datetime.utcnow().replace(day=1)
    ).all()

    revenue_saved = sum(i.value_amount for i in impacts if i.impact_type == "revenue_saved")
    revenue_created = sum(i.value_amount for i in impacts if i.impact_type == "revenue_created")
    efficiency_gain = sum(i.value_amount for i in impacts if i.impact_type == "efficiency_gain")

    total_impact = revenue_saved + revenue_created + efficiency_gain

    # Assume $500/month ForecastX cost (customize)
    forecastx_cost = 500

    net_value = total_impact - forecastx_cost
    roi_multiplier = total_impact / forecastx_cost if forecastx_cost > 0 else 0

    summary = ROISummary(
        organization_id=org_id,
        period="month",
        period_start=datetime.utcnow().replace(day=1),
        period_end=datetime.utcnow(),
        revenue_saved=revenue_saved,
        revenue_created=revenue_created,
        efficiency_gain=efficiency_gain,
        total_impact=total_impact,
        forecastx_cost=forecastx_cost,
        net_value=net_value,
        roi_multiplier=roi_multiplier,
        roi_percentage=(net_value / forecastx_cost * 100) if forecastx_cost > 0 else 0
    )

    db.add(summary)
    db.commit()

    return summary
