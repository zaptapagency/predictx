"""
Quick Wins API

The available plays are derived from the latest scoring run rather than
pre-configured: a quick win is only a quick win if it points at customers who
are actually flagged right now. See app/services/prediction_summary.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.db.models_saas import User
from app.db.quickwin_models import QuickWin, QuickWinExecution
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.prediction_summary import (
    empty_state_message, money, summarize_org_predictions,
)

router = APIRouter(prefix="/api/quick-wins", tags=["quick-wins"])


def _stake(customers):
    """Total revenue at stake across a group, and how many of them we can value."""
    known = [c for c in customers if c.revenue_at_stake is not None]
    return round(sum(c.revenue_at_stake for c in known), 2), len(known)


@router.get("/available")
def get_available_quick_wins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the high-impact, low-effort plays the latest scoring run supports"""

    summary = summarize_org_predictions(db, current_user.organization_id)
    if summary is None:
        return {
            "quick_wins": [],
            "total": 0,
            "message": empty_state_message(db, current_user.organization_id),
        }

    subject = summary.subject
    critical = [c for c in summary.customers if c.band == "critical"]
    high = [c for c in summary.customers if c.band == "high"]
    quick_wins = []

    # The single biggest account, first: one phone call, most money on the line.
    valued = [c for c in summary.at_risk if c.revenue_at_stake is not None]
    if valued:
        top = max(valued, key=lambda c: c.revenue_at_stake)
        quick_wins.append({
            "id": f"top-account-{top.customer_id}",
            "title": f"Call {top.name}",
            "description": (
                f"One call. {top.name} scores {top.score * 100:.0f}% {subject} on "
                f"{money(top.annual_revenue)} of annual revenue"
                + (f", driven by {', '.join(top.drivers)}." if top.drivers else ".")
            ),
            "icon": "📞",
            "action_type": "call",
            "estimated_target_count": 1,
            "estimated_impact": money(top.revenue_at_stake),
            "success_probability": None,  # No outcome history yet, so we don't guess.
            "customer_ids": [top.customer_id],
        })

    if critical:
        amount, known = _stake(critical)
        quick_wins.append({
            "id": "outreach-critical",
            "title": f"Reach out to {len(critical)} critical accounts",
            "description": (
                f"{len(critical)} customers scored above the critical {subject} threshold in "
                f"{summary.model_name}'s latest run."
                + (f" Revenue at stake is known for {known} of them." if known < len(critical) else "")
            ),
            "icon": "🚨",
            "action_type": "bulk_call",
            "estimated_target_count": len(critical),
            "estimated_impact": money(amount) if known else None,
            "success_probability": None,
            "customer_ids": [c.customer_id for c in critical[:50]],
        })

    if high:
        amount, known = _stake(high)
        quick_wins.append({
            "id": "offer-high",
            "title": f"Email {len(high)} high-risk accounts",
            "description": (
                f"{len(high)} customers sit in the high {subject} band — close enough to matter, "
                f"far enough that an email is usually the right first touch."
            ),
            "icon": "✉️",
            "action_type": "bulk_email",
            "estimated_target_count": len(high),
            "estimated_impact": money(amount) if known else None,
            "success_probability": None,
            "customer_ids": [c.customer_id for c in high[:50]],
        })

    # A play aimed at the one thing driving most of the cohort's risk.
    if summary.drivers and summary.at_risk:
        driver = summary.drivers[0]
        quick_wins.append({
            "id": f"driver-{driver['feature']}",
            "title": f"Review {driver['feature']} across flagged accounts",
            "description": (
                f"'{driver['feature']}' accounts for {driver['share_of_risk'] * 100:.0f}% of the "
                f"modelled {subject} across {driver['customers_affected']} flagged customers"
                + (f", averaging {driver['average_value']:,.2f}." if driver["average_value"] is not None else ".")
            ),
            "icon": "🔎",
            "action_type": "task",
            "estimated_target_count": driver["customers_affected"],
            "estimated_impact": None,
            "success_probability": None,
            "customer_ids": [c.customer_id for c in summary.at_risk[:50]],
        })

    return {
        "quick_wins": quick_wins,
        "total": len(quick_wins),
        "model": summary.model_name,
        "scored_at": summary.scored_at.isoformat() if summary.scored_at else None,
    }


@router.get("/{quick_win_id}")
def get_quick_win_detail(
    quick_win_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific quick win"""

    quick_win = db.query(QuickWin).filter(
        QuickWin.id == quick_win_id,
        QuickWin.organization_id == current_user.organization_id
    ).first()

    if not quick_win:
        raise HTTPException(status_code=404, detail="Quick win not found")

    # Get execution history
    executions = db.query(QuickWinExecution).filter(
        QuickWinExecution.quick_win_id == quick_win_id
    ).order_by(desc(QuickWinExecution.created_at)).limit(5).all()

    return {
        "id": quick_win.id,
        "title": quick_win.title,
        "description": quick_win.description,
        "icon": quick_win.icon,
        "action_type": quick_win.action_type,
        "estimated_target_count": quick_win.estimated_target_count,
        "estimated_impact": f"${quick_win.estimated_impact:,.0f}" if quick_win.estimated_impact else None,
        "success_probability": f"{quick_win.success_probability * 100:.0f}%" if quick_win.success_probability else None,
        "recent_executions": [
            {
                "executed_by": e.user.name,
                "target_count": e.target_count,
                "success_count": e.success_count,
                "success_rate": f"{(e.success_count / e.target_count * 100):.0f}%" if e.target_count > 0 else "0%",
                "actual_impact": f"${e.actual_impact:,.0f}" if e.actual_impact else None,
                "executed_at": e.created_at.isoformat(),
            }
            for e in executions
        ]
    }


@router.post("/{quick_win_id}/execute")
def execute_quick_win(
    quick_win_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a quick win (1-click action)"""

    quick_win = db.query(QuickWin).filter(
        QuickWin.id == quick_win_id,
        QuickWin.organization_id == current_user.organization_id
    ).first()

    if not quick_win:
        raise HTTPException(status_code=404, detail="Quick win not found")

    # Create execution record
    execution = QuickWinExecution(
        quick_win_id=quick_win_id,
        user_id=current_user.id,
        target_count=quick_win.estimated_target_count or 0,
        success_count=int((quick_win.estimated_target_count or 0) * (quick_win.success_probability or 0.5)),
        failed_count=int((quick_win.estimated_target_count or 0) * (1 - (quick_win.success_probability or 0.5))),
        status="pending"
    )

    db.add(execution)
    db.commit()

    return {
        "status": "executing",
        "execution_id": execution.id,
        "title": quick_win.title,
        "message": f"Executing {quick_win.title}... This will affect {quick_win.estimated_target_count} targets."
    }


@router.get("/execution/{execution_id}/status")
def get_execution_status(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of a quick win execution"""

    execution = db.query(QuickWinExecution).filter(
        QuickWinExecution.id == execution_id,
        QuickWinExecution.user_id == current_user.id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    success_rate = (execution.success_count / execution.target_count * 100) if execution.target_count > 0 else 0

    return {
        "execution_id": execution.id,
        "status": execution.status,
        "target_count": execution.target_count,
        "success_count": execution.success_count,
        "failed_count": execution.failed_count,
        "success_rate": f"{success_rate:.0f}%",
        "actual_impact": f"${execution.actual_impact:,.0f}" if execution.actual_impact else None,
        "created_at": execution.created_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }


@router.get("/history")
def get_quick_win_history(
    limit: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's quick win execution history"""

    executions = db.query(QuickWinExecution).filter(
        QuickWinExecution.user_id == current_user.id
    ).order_by(desc(QuickWinExecution.created_at)).limit(limit).all()

    return {
        "history": [
            {
                "quick_win": e.quick_win.title,
                "target_count": e.target_count,
                "success_count": e.success_count,
                "success_rate": f"{(e.success_count / e.target_count * 100):.0f}%" if e.target_count > 0 else "0%",
                "actual_impact": f"${e.actual_impact:,.0f}" if e.actual_impact else None,
                "status": e.status,
                "executed_at": e.created_at.isoformat(),
            }
            for e in executions
        ],
        "total_executions": len(executions),
        "total_impact": f"${sum(e.actual_impact or 0 for e in executions):,.0f}"
    }
