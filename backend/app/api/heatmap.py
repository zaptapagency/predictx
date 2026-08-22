"""
Health Heatmap API
Visual overview of customer health and urgency
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models_saas import User
from app.db.heatmap_models import CustomerHealthScore, HealthMetric
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])


@router.get("/overview")
def get_heatmap_overview(
    sort_by: str = Query("health"),  # health, urgency, churn_risk
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get heatmap overview of all customers"""

    query = db.query(CustomerHealthScore).filter(
        CustomerHealthScore.organization_id == current_user.organization_id
    )

    if sort_by == "urgency":
        query = query.order_by(desc(CustomerHealthScore.support_urgency))
    elif sort_by == "churn_risk":
        query = query.order_by(desc(CustomerHealthScore.churn_risk))
    else:
        query = query.order_by(CustomerHealthScore.overall_health)

    scores = query.all()

    # Categorize by health status
    critical = [s for s in scores if s.overall_health < 30]
    warning = [s for s in scores if 30 <= s.overall_health < 70]
    healthy = [s for s in scores if s.overall_health >= 70]

    return {
        "summary": {
            "critical_count": len(critical),
            "warning_count": len(warning),
            "healthy_count": len(healthy),
            "total_customers": len(scores)
        },
        "customers": [
            {
                "customer_id": s.customer_id,
                "health": s.overall_health,
                "health_status": "critical" if s.overall_health < 30 else "warning" if s.overall_health < 70 else "healthy",
                "churn_risk": f"{s.churn_risk * 100:.0f}%",
                "expansion_potential": f"{s.expansion_potential * 100:.0f}%",
                "support_urgency": f"{s.support_urgency * 100:.0f}%",
                "trend": s.health_trend,
                "red_flags": s.red_flags,
                "yellow_flags": s.yellow_flags,
                "green_flags": s.green_flags,
            }
            for s in scores
        ]
    }


@router.get("/customer/{customer_id}")
def get_customer_health(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed health metrics for a customer"""

    health = db.query(CustomerHealthScore).filter(
        CustomerHealthScore.organization_id == current_user.organization_id,
        CustomerHealthScore.customer_id == customer_id
    ).first()

    if not health:
        raise HTTPException(status_code=404, detail="Customer health data not found")

    metrics = db.query(HealthMetric).filter(
        HealthMetric.health_score_id == health.id
    ).all()

    return {
        "customer_id": customer_id,
        "overall_health": health.overall_health,
        "health_status": "critical" if health.overall_health < 30 else "warning" if health.overall_health < 70 else "healthy",
        "churn_risk": f"{health.churn_risk * 100:.0f}%",
        "expansion_potential": f"{health.expansion_potential * 100:.0f}%",
        "support_urgency": f"{health.support_urgency * 100:.0f}%",
        "trend": health.health_trend,
        "trend_direction": f"{health.trend_direction:+.1f}" if health.trend_direction else None,
        "metrics": [
            {
                "name": m.metric_name,
                "value": m.metric_value,
                "status": m.status,
                "description": m.description,
                "recommended_action": m.recommended_action,
            }
            for m in metrics
        ],
        "flags": {
            "red": health.red_flags,
            "yellow": health.yellow_flags,
            "green": health.green_flags,
        }
    }


@router.get("/critical")
def get_critical_customers(
    limit: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customers in critical health state"""

    critical = db.query(CustomerHealthScore).filter(
        CustomerHealthScore.organization_id == current_user.organization_id,
        CustomerHealthScore.overall_health < 30
    ).order_by(CustomerHealthScore.overall_health).limit(limit).all()

    return {
        "critical_customers": [
            {
                "customer_id": c.customer_id,
                "health": c.overall_health,
                "churn_risk": f"{c.churn_risk * 100:.0f}%",
                "red_flags": c.red_flags,
                "recommended_actions": ["Take immediate action", "Schedule call", "Review contract"],
            }
            for c in critical
        ],
        "total": len(critical)
    }


@router.get("/expansion-opportunities")
def get_expansion_opportunities(
    limit: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customers with highest expansion potential"""

    opportunities = db.query(CustomerHealthScore).filter(
        CustomerHealthScore.organization_id == current_user.organization_id,
        CustomerHealthScore.overall_health >= 70
    ).order_by(desc(CustomerHealthScore.expansion_potential)).limit(limit).all()

    return {
        "expansion_opportunities": [
            {
                "customer_id": c.customer_id,
                "health": c.overall_health,
                "expansion_potential": f"{c.expansion_potential * 100:.0f}%",
                "recommended_actions": ["Suggest premium tier", "Propose add-ons", "Schedule expansion call"],
            }
            for c in opportunities
        ],
        "total": len(opportunities)
    }


@router.get("/heatmap-data")
def get_heatmap_visualization_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data formatted for heatmap visualization"""

    scores = db.query(CustomerHealthScore).filter(
        CustomerHealthScore.organization_id == current_user.organization_id
    ).all()

    # Create heatmap cells (customer_id vs metrics)
    heatmap_data = []
    for score in scores:
        heatmap_data.append({
            "x": score.customer_id,
            "y": "Health",
            "value": score.overall_health,
            "intensity": "critical" if score.overall_health < 30 else "warning" if score.overall_health < 70 else "healthy"
        })

    return {
        "heatmap": heatmap_data,
        "scale": {
            "critical": {"min": 0, "max": 30, "color": "#ef4444"},
            "warning": {"min": 30, "max": 70, "color": "#fbbf24"},
            "healthy": {"min": 70, "max": 100, "color": "#10b981"}
        }
    }
