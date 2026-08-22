"""
Playbook Monitor API
Performance tracking and optimization
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta

from app.db.models_saas import User
from app.db.playbook_monitor_models import PlaybookPerformance, PlaybookUsageMetric
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/playbook-monitor", tags=["playbook-monitor"])


@router.get("/performance")
def get_playbook_performance(
    sort_by: str = Query("revenue"),  # revenue, success_rate, executions
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get playbook performance rankings"""

    query = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.organization_id == current_user.organization_id,
        PlaybookPerformance.is_active == True
    )

    if sort_by == "success_rate":
        query = query.order_by(desc(PlaybookPerformance.success_rate))
    elif sort_by == "executions":
        query = query.order_by(desc(PlaybookPerformance.total_executions))
    else:
        query = query.order_by(desc(PlaybookPerformance.total_revenue_generated))

    performances = query.limit(limit).all()

    return {
        "playbooks": [
            {
                "playbook_id": p.playbook_id,
                "playbook_name": p.playbook.name if p.playbook else f"Playbook {p.playbook_id}",
                "executions": p.total_executions,
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "revenue_generated": f"${p.total_revenue_generated:,.0f}",
                "revenue_per_execution": f"${p.average_revenue_per_execution:,.0f}",
                "users_using": p.users_using,
                "roi": f"{p.total_roi:.1f}x",
                "trend": p.trend,
                "status": "active" if p.is_active else "deprecated",
            }
            for p in performances
        ],
        "total": len(performances)
    }


@router.get("/{playbook_id}")
def get_playbook_detail(
    playbook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed performance metrics for a playbook"""

    perf = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.playbook_id == playbook_id,
        PlaybookPerformance.organization_id == current_user.organization_id
    ).first()

    if not perf:
        raise HTTPException(status_code=404, detail="Playbook performance data not found")

    # Get usage history (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    usage_metrics = db.query(PlaybookUsageMetric).filter(
        PlaybookUsageMetric.playbook_id == playbook_id,
        PlaybookUsageMetric.period_date >= thirty_days_ago
    ).order_by(PlaybookUsageMetric.period_date).all()

    return {
        "playbook_id": playbook_id,
        "playbook_name": perf.playbook.name if perf.playbook else f"Playbook {playbook_id}",
        "summary": {
            "total_executions": perf.total_executions,
            "successful_actions": perf.successful_actions,
            "failed_actions": perf.failed_actions,
            "success_rate": f"{perf.success_rate * 100:.1f}%",
            "total_revenue_generated": f"${perf.total_revenue_generated:,.0f}",
            "revenue_per_execution": f"${perf.average_revenue_per_execution:,.0f}",
            "total_customers_affected": perf.total_customers_affected,
            "roi": f"{perf.total_roi:.1f}x",
            "users_using": perf.users_using,
            "trend": perf.trend,
            "month_over_month_change": f"{perf.month_over_month_change:+.1f}%" if perf.month_over_month_change else None,
        },
        "usage_trend": [
            {
                "date": m.period_date.isoformat().split("T")[0],
                "executions": m.executions,
                "success_rate": f"{m.success_rate * 100:.1f}%" if m.success_rate else "0%",
                "unique_users": m.unique_users,
                "new_users": m.new_users,
            }
            for m in usage_metrics
        ],
        "health": "excellent" if perf.success_rate > 0.8 else "good" if perf.success_rate > 0.6 else "needs_improvement"
    }


@router.get("/trending/top-performers")
def get_top_performing_playbooks(
    limit: int = Query(5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top performing playbooks"""

    top = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.organization_id == current_user.organization_id,
        PlaybookPerformance.is_active == True
    ).order_by(
        desc(PlaybookPerformance.total_revenue_generated)
    ).limit(limit).all()

    return {
        "top_performers": [
            {
                "rank": idx + 1,
                "playbook_id": p.playbook_id,
                "playbook_name": p.playbook.name if p.playbook else f"Playbook {p.playbook_id}",
                "revenue": f"${p.total_revenue_generated:,.0f}",
                "executions": p.total_executions,
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "recommendation": "Expand usage" if p.users_using < 10 else "Maintain and optimize",
            }
            for idx, p in enumerate(top)
        ]
    }


@router.get("/trending/underperformers")
def get_underperforming_playbooks(
    limit: int = Query(5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get playbooks that need improvement"""

    underperforming = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.organization_id == current_user.organization_id,
        PlaybookPerformance.is_active == True,
        PlaybookPerformance.success_rate < 0.5  # Less than 50% success rate
    ).order_by(
        PlaybookPerformance.success_rate
    ).limit(limit).all()

    return {
        "underperformers": [
            {
                "playbook_id": p.playbook_id,
                "playbook_name": p.playbook.name if p.playbook else f"Playbook {p.playbook_id}",
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "executions": p.total_executions,
                "trend": p.trend,
                "recommendation": "Review configuration" if p.success_rate < 0.3 else "Consider deprecating",
            }
            for p in underperforming
        ]
    }


@router.get("/comparison")
def compare_playbooks(
    playbook_ids: list = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple playbooks side-by-side"""

    playbooks = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.playbook_id.in_(playbook_ids),
        PlaybookPerformance.organization_id == current_user.organization_id
    ).all()

    return {
        "comparison": [
            {
                "playbook_id": p.playbook_id,
                "playbook_name": p.playbook.name if p.playbook else f"Playbook {p.playbook_id}",
                "executions": p.total_executions,
                "success_rate": f"{p.success_rate * 100:.1f}%",
                "revenue": f"${p.total_revenue_generated:,.0f}",
                "revenue_per_exec": f"${p.average_revenue_per_execution:,.0f}",
                "users": p.users_using,
                "roi": f"{p.total_roi:.1f}x",
            }
            for p in playbooks
        ]
    }


@router.post("/{playbook_id}/deprecate")
def deprecate_playbook(
    playbook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deprecate a playbook"""

    perf = db.query(PlaybookPerformance).filter(
        PlaybookPerformance.playbook_id == playbook_id,
        PlaybookPerformance.organization_id == current_user.organization_id
    ).first()

    if not perf:
        raise HTTPException(status_code=404, detail="Playbook not found")

    perf.is_active = False
    perf.deprecation_date = datetime.utcnow()

    db.commit()

    return {
        "status": "deprecated",
        "playbook_id": playbook_id,
        "message": "Playbook has been marked as deprecated"
    }
