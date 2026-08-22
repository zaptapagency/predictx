"""
Quick Wins API
Pre-configured 1-click actions
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.db.models_saas import User
from app.db.quickwin_models import QuickWin, QuickWinExecution
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/quick-wins", tags=["quick-wins"])


@router.get("/available")
def get_available_quick_wins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available quick wins for user"""

    quick_wins = db.query(QuickWin).filter(
        QuickWin.organization_id == current_user.organization_id,
        QuickWin.is_active == True
    ).order_by(QuickWin.order).all()

    return {
        "quick_wins": [
            {
                "id": w.id,
                "title": w.title,
                "description": w.description,
                "icon": w.icon,
                "action_type": w.action_type,
                "estimated_target_count": w.estimated_target_count,
                "estimated_impact": f"${w.estimated_impact:,.0f}" if w.estimated_impact else None,
                "success_probability": f"{w.success_probability * 100:.0f}%" if w.success_probability else None,
            }
            for w in quick_wins
        ],
        "total": len(quick_wins)
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
