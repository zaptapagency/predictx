"""
Action Center API
Get actions, execute actions, track outcomes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from app.db.models_saas import User, Organization
from app.db.action_models import Action, ActionExecution, ActionTemplate, QuickAction, ActionStatus, ActionPriority
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/actions", tags=["actions"])
email_service = EmailService()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ActionResponse(BaseModel):
    id: int
    title: str
    description: str
    action_type: str
    priority: str
    status: str
    entity_type: str
    entity_name: str
    entity_email: str
    estimated_impact: float
    impact_type: str
    assigned_to: dict
    due_at: datetime
    created_at: datetime

class ExecuteActionRequest(BaseModel):
    action_ids: list[int] = None  # Bulk action
    action_id: int = None  # Single action
    execution_type: str = "immediate"  # immediate, scheduled, bulk
    scheduled_for: datetime = None

class ActionOutcomeRequest(BaseModel):
    action_id: int
    outcome: str  # success, partial, failed, skipped
    notes: str = None

class QuickActionRequest(BaseModel):
    quick_action_id: int
    confirm: bool = True

# ============================================================================
# GET ACTIONS FOR DASHBOARD
# ============================================================================

@router.get("/dashboard")
def get_action_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get action center dashboard with grouped actions
    """

    if not current_user.organization_id:
        return {"actions_by_priority": {}, "stats": {}}

    # Get all pending actions
    actions = db.query(Action).filter(
        Action.organization_id == current_user.organization_id,
        Action.status.in_([ActionStatus.PENDING, ActionStatus.SCHEDULED])
    ).all()

    # Group by priority
    actions_by_priority = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    total_impact = 0.0

    for action in actions:
        priority = action.priority.lower()
        actions_by_priority[priority].append({
            "id": action.id,
            "title": action.title,
            "description": action.description,
            "action_type": action.action_type,
            "priority": action.priority,
            "status": action.status,
            "entity_type": action.entity_type,
            "entity_name": action.entity_name,
            "entity_email": action.entity_email,
            "estimated_impact": action.estimated_impact,
            "impact_type": action.impact_type,
            "due_at": action.due_at,
        })
        if action.estimated_impact:
            total_impact += action.estimated_impact

    # Count by priority
    stats = {
        "total": len(actions),
        "critical": len(actions_by_priority["critical"]),
        "high": len(actions_by_priority["high"]),
        "medium": len(actions_by_priority["medium"]),
        "low": len(actions_by_priority["low"]),
        "total_estimated_impact": total_impact,
        "impact_unit": "usd"
    }

    # Get quick actions
    quick_actions = db.query(QuickAction).filter(
        QuickAction.organization_id == current_user.organization_id
    ).all()

    return {
        "actions_by_priority": actions_by_priority,
        "stats": stats,
        "quick_actions": [
            {
                "id": qa.id,
                "name": qa.name,
                "description": qa.description,
                "icon": qa.icon,
                "impact_estimate": qa.impact_estimate,
                "times_used": qa.times_used,
                "success_rate": qa.success_rate
            }
            for qa in quick_actions
        ]
    }


# ============================================================================
# EXECUTE ACTION
# ============================================================================

@router.post("/execute")
def execute_action(
    payload: ExecuteActionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute one or more actions
    Handles: email, Slack, create task, schedule call, webhook
    """

    action_ids = payload.action_ids if payload.action_ids else [payload.action_id]

    if not action_ids:
        raise HTTPException(status_code=400, detail="No actions specified")

    executed = []
    failed = []

    for action_id in action_ids:
        action = db.query(Action).filter(Action.id == action_id).first()

        if not action:
            failed.append({"action_id": action_id, "error": "Action not found"})
            continue

        if action.organization_id != current_user.organization_id:
            failed.append({"action_id": action_id, "error": "Unauthorized"})
            continue

        try:
            # Execute based on type
            if action.action_type == "email":
                execute_email_action(action, current_user, db)
            elif action.action_type == "slack":
                execute_slack_action(action, current_user, db)
            elif action.action_type == "salesforce":
                execute_salesforce_action(action, current_user, db)
            elif action.action_type == "task":
                execute_task_action(action, current_user, db)
            elif action.action_type == "meeting":
                execute_meeting_action(action, current_user, db)
            else:
                execute_webhook_action(action, current_user, db)

            # Log execution
            execution = ActionExecution(
                action_id=action.id,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                execution_type=payload.execution_type,
                scheduled_for=payload.scheduled_for,
                success=True
            )
            db.add(execution)

            # Update action status
            action.status = ActionStatus.IN_PROGRESS if payload.execution_type == "scheduled" else ActionStatus.COMPLETED
            action.executed_at = datetime.utcnow()

            executed.append({
                "action_id": action.id,
                "title": action.title,
                "entity_name": action.entity_name,
                "status": action.status
            })

        except Exception as e:
            failed.append({
                "action_id": action.id,
                "title": action.title,
                "error": str(e)
            })

    db.commit()

    return {
        "success": True,
        "executed": executed,
        "failed": failed,
        "total": len(action_ids),
        "message": f"Executed {len(executed)} actions successfully"
    }


def execute_email_action(action: Action, user: User, db: Session):
    """Send email action"""
    config = action.action_config or {}

    email_service.send_email(
        to=action.entity_email,
        subject=config.get("subject", action.title),
        template=config.get("template", "action_email"),
        data={
            "recipient_name": action.entity_name,
            "message": config.get("message"),
            "action_type": "email"
        }
    )


def execute_slack_action(action: Action, user: User, db: Session):
    """Send Slack notification"""
    config = action.action_config or {}

    # TODO: Integrate with Slack API
    # slack_client.send_message(
    #     channel=config.get("channel"),
    #     message=config.get("message")
    # )


def execute_salesforce_action(action: Action, user: User, db: Session):
    """Create task in Salesforce"""
    config = action.action_config or {}

    # TODO: Integrate with Salesforce API
    # sf.Task.create({
    #     'WhoId': config.get('contact_id'),
    #     'WhatId': config.get('account_id'),
    #     'Subject': action.title,
    #     'Description': action.description,
    #     'Priority': 'High',
    #     'Status': 'Open'
    # })


def execute_task_action(action: Action, user: User, db: Session):
    """Create internal task"""
    config = action.action_config or {}

    # TODO: Create task in internal system
    pass


def execute_meeting_action(action: Action, user: User, db: Session):
    """Schedule meeting/call"""
    config = action.action_config or {}

    # TODO: Integrate with Calendly or calendar API
    # calendly.schedule_event(
    #     attendees=[action.entity_email],
    #     title=action.title,
    #     duration=config.get("duration", 30),
    #     when=config.get("when", "asap")
    # )


def execute_webhook_action(action: Action, user: User, db: Session):
    """Send to webhook"""
    config = action.action_config or {}

    # TODO: Send HTTP POST to webhook
    # requests.post(
    #     config.get("url"),
    #     json={"action": action.title, "entity": action.entity_name}
    # )


# ============================================================================
# RECORD OUTCOME
# ============================================================================

@router.post("/outcome")
def record_action_outcome(
    payload: ActionOutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Record what happened after action was taken
    success: customer stayed, lead converted, call scheduled
    failed: customer still left, lead didn't convert
    """

    action = db.query(Action).filter(Action.id == payload.action_id).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Update action outcome
    action.outcome = payload.outcome
    action.result = {
        "outcome": payload.outcome,
        "notes": payload.notes,
        "recorded_at": datetime.utcnow().isoformat(),
        "recorded_by": current_user.name
    }

    # Get execution and update it too
    execution = db.query(ActionExecution).filter(
        ActionExecution.action_id == action.id
    ).order_by(desc(ActionExecution.created_at)).first()

    if execution:
        execution.outcome = payload.outcome
        execution.outcome_at = datetime.utcnow()
        execution.outcome_notes = payload.notes

    db.commit()

    return {
        "success": True,
        "action_id": action.id,
        "outcome": action.outcome,
        "message": f"Action outcome recorded: {payload.outcome}"
    }


# ============================================================================
# QUICK ACTIONS (BULK)
# ============================================================================

@router.post("/quick-action")
def execute_quick_action(
    payload: QuickActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a quick action (pre-configured bulk action)
    Example: "Email all at-risk customers"
    """

    quick_action = db.query(QuickAction).filter(
        QuickAction.id == payload.quick_action_id,
        QuickAction.organization_id == current_user.organization_id
    ).first()

    if not quick_action:
        raise HTTPException(status_code=404, detail="Quick action not found")

    # Get actions matching filter
    filter_config = quick_action.filter_config

    actions = db.query(Action).filter(
        Action.organization_id == current_user.organization_id,
        Action.status == ActionStatus.PENDING
    ).all()

    # Apply filters
    matching_actions = []
    for action in actions:
        if matches_filter(action, filter_config):
            matching_actions.append(action)

    # Execute all matching
    executed = 0
    for action in matching_actions:
        try:
            if action.action_type == "email":
                execute_email_action(action, current_user, db)

            execution = ActionExecution(
                action_id=action.id,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                execution_type="bulk",
                success=True
            )
            db.add(execution)
            action.status = ActionStatus.COMPLETED
            action.executed_at = datetime.utcnow()
            executed += 1

        except Exception as e:
            pass

    # Update quick action stats
    quick_action.times_used += 1
    quick_action.last_used_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "quick_action": quick_action.name,
        "actions_executed": executed,
        "message": f"Executed {executed} actions via quick action"
    }


def matches_filter(action: Action, filter_config: dict) -> bool:
    """Check if action matches filter criteria"""
    # Example filters:
    # - priority: critical, high
    # - action_type: email, task
    # - entity_type: customer, lead
    # - estimated_impact_min: 50000

    if "priority" in filter_config:
        if action.priority not in filter_config["priority"]:
            return False

    if "action_type" in filter_config:
        if action.action_type not in filter_config["action_type"]:
            return False

    if "entity_type" in filter_config:
        if action.entity_type not in filter_config["entity_type"]:
            return False

    if "estimated_impact_min" in filter_config:
        if not action.estimated_impact or action.estimated_impact < filter_config["estimated_impact_min"]:
            return False

    return True


# ============================================================================
# ACTION HISTORY
# ============================================================================

@router.get("/history")
def get_action_history(
    days: int = Query(30),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get history of actions taken"""

    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(ActionExecution).filter(
        ActionExecution.organization_id == current_user.organization_id,
        ActionExecution.executed_at >= since
    )

    if status:
        query = query.filter(ActionExecution.outcome == status)

    executions = query.order_by(desc(ActionExecution.executed_at)).limit(100).all()

    return {
        "history": [
            {
                "id": e.id,
                "action_id": e.action_id,
                "user": e.assigned_to.name if e.assigned_to else "System",
                "execution_type": e.execution_type,
                "executed_at": e.executed_at,
                "outcome": e.outcome,
                "success": e.success
            }
            for e in executions
        ]
    }


# ============================================================================
# ACTION STATS
# ============================================================================

@router.get("/stats")
def get_action_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get action center statistics"""

    org_id = current_user.organization_id

    total_actions = db.query(Action).filter(
        Action.organization_id == org_id
    ).count()

    pending = db.query(Action).filter(
        Action.organization_id == org_id,
        Action.status == ActionStatus.PENDING
    ).count()

    completed = db.query(Action).filter(
        Action.organization_id == org_id,
        Action.status == ActionStatus.COMPLETED
    ).count()

    # Success rate
    executions = db.query(ActionExecution).filter(
        ActionExecution.organization_id == org_id,
        ActionExecution.outcome != None
    ).all()

    successful = len([e for e in executions if e.outcome == "success"])
    success_rate = (successful / len(executions) * 100) if executions else 0

    # Total impact
    total_impact = db.query(Action).filter(
        Action.organization_id == org_id,
        Action.estimated_impact != None
    ).with_entities(
        func.sum(Action.estimated_impact)
    ).scalar() or 0

    return {
        "stats": {
            "total_actions": total_actions,
            "pending": pending,
            "completed": completed,
            "completion_rate": f"{(completed / total_actions * 100):.1f}%" if total_actions > 0 else "0%",
            "success_rate": f"{success_rate:.1f}%",
            "total_impact": total_impact,
            "impact_unit": "usd"
        }
    }
