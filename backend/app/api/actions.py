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
from app.utils.time import utcnow
from app.services.channels import (
    ChannelError, ChannelUnavailable, DeliveryResult, deliver_email, deliver_salesforce_task,
    deliver_slack, deliver_unsupported, deliver_webhook,
)

router = APIRouter(prefix="/api/actions", tags=["actions"])

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
    Execute one or more actions for real.

    An action is only marked completed when its channel confirms delivery.
    Anything else is recorded as a failure with the reason, so the Action
    Center reflects what actually reached the customer.
    """

    action_ids = payload.action_ids if payload.action_ids else [payload.action_id]
    action_ids = [a for a in action_ids if a is not None]

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
            result = _dispatch(action, current_user, db)

        except ChannelError as e:
            # Delivery genuinely failed. Record why, and leave the action
            # recoverable rather than pretending it went out.
            reason = str(e)
            db.add(ActionExecution(
                action_id=action.id,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                execution_type=payload.execution_type,
                scheduled_for=payload.scheduled_for,
                success=False,
                error_message=reason,
            ))
            action.status = ActionStatus.FAILED
            action.outcome = "failed"
            action.updated_at = utcnow()
            failed.append({
                "action_id": action.id,
                "title": action.title,
                "error": reason,
                "needs_setup": isinstance(e, ChannelUnavailable),
            })
            continue

        db.add(ActionExecution(
            action_id=action.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            execution_type=payload.execution_type,
            scheduled_for=payload.scheduled_for,
            success=True,
            response_data=result.response_data,
        ))

        action.status = (
            ActionStatus.IN_PROGRESS if payload.execution_type == "scheduled"
            else ActionStatus.COMPLETED
        )
        action.executed_at = utcnow()
        action.result = {"channel": result.channel, "detail": result.detail,
                         "external_id": result.external_id}

        executed.append({
            "action_id": action.id,
            "title": action.title,
            "entity_name": action.entity_name,
            "status": action.status,
            "detail": result.detail,
        })

    db.commit()

    if executed and failed:
        message = f"Executed {len(executed)} of {len(action_ids)} actions; {len(failed)} failed."
    elif executed:
        message = f"Executed {len(executed)} action{'s' if len(executed) != 1 else ''}."
    elif failed:
        message = f"No actions were executed. {failed[0]['error']}"
    else:
        message = "Nothing to do."

    return {
        "success": bool(executed) and not failed,
        "executed": executed,
        "failed": failed,
        "total": len(action_ids),
        "message": message,
    }


def _dispatch(action: Action, user: User, db: Session):
    """Route an action to its channel. Raises ChannelError if it cannot be delivered."""
    handlers = {
        "email": execute_email_action,
        "slack": execute_slack_action,
        "salesforce": execute_salesforce_action,
        "task": execute_task_action,
        "webhook": execute_webhook_action,
    }
    handler = handlers.get((action.action_type or "").lower())
    if handler is None:
        # phone_call, meeting and friends: we cannot place a call for someone.
        return deliver_unsupported(action.action_type or "unknown")()
    return handler(action, user, db)


def _context(action: Action) -> dict:
    """The facts about this action worth putting in a message."""
    config = action.action_config or {}
    return {
        "customer": action.entity_name or action.entity_id,
        "customer_id": action.entity_id,
        "title": action.title,
        "why": action.description or "",
        "risk_level": config.get("risk_level"),
        "score": config.get("score"),
        "estimated_impact": action.estimated_impact,
        "priority": action.priority,
        "due_at": action.due_at.isoformat() if action.due_at else None,
    }


def execute_email_action(action: Action, user: User, db: Session):
    """Email the customer."""
    config = action.action_config or {}
    subject = config.get("subject") or action.title
    body = config.get("message") or action.recommended_message

    if not body:
        # No hand-written message. Send something truthful and useful rather
        # than forwarding raw model output to a customer.
        body = (
            f"Hi {action.entity_name or 'there'},\n\n"
            "We wanted to check in and make sure you are getting what you need "
            "from us. Is there a good time this week for a quick conversation?"
        )

    paragraphs = "".join(f"<p>{line}</p>" for line in body.split("\n") if line.strip())
    html = (
        '<html><body style="font-family: Arial, sans-serif; line-height:1.6; color:#333;">'
        f'<div style="max-width:600px;margin:0 auto;padding:20px;">{paragraphs}'
        f'<p style="margin-top:24px">-- {user.full_name or user.username}</p>'
        "</div></body></html>"
    )

    return deliver_email(
        db, action.organization_id,
        to=action.entity_email, subject=subject, body_html=html, body_text=body,
    )


def execute_slack_action(action: Action, user: User, db: Session):
    """Post the action to the team's Slack channel."""
    config = action.action_config or {}
    impact = (f" (~${action.estimated_impact:,.0f} at stake)"
              if action.estimated_impact else "")
    text = config.get("message") or (
        f"*{action.title}*{impact}\n{action.description or ''}"
    )
    return deliver_slack(db, action.organization_id, text=text,
                         webhook_url=config.get("webhook_url"))


def execute_salesforce_action(action: Action, user: User, db: Session):
    """Create a follow-up task on the Salesforce record."""
    config = action.action_config or {}
    return deliver_salesforce_task(
        db, action.organization_id,
        subject=action.title,
        description=action.description or "",
        priority="High" if action.priority in ("critical", "high") else "Normal",
        account_id=config.get("account_id"),
        contact_id=config.get("contact_id"),
    )


def execute_task_action(action: Action, user: User, db: Session):
    """
    Assign the action to a teammate.

    The action row is itself the task, so "creating" one means giving it an
    owner and a deadline rather than copying it into another table.
    """
    config = action.action_config or {}
    assignee_id = config.get("assignee_id") or user.id

    assignee = db.query(User).filter(
        User.id == assignee_id,
        User.organization_id == action.organization_id,
    ).first()
    if not assignee:
        raise ChannelError(f"No user {assignee_id} in this organization to assign the task to.")

    action.assigned_to_id = assignee.id
    if not action.due_at:
        action.due_at = utcnow() + timedelta(days=3)

    name = assignee.full_name or assignee.username
    return DeliveryResult(
        channel="task",
        detail=f"Assigned to {name}, due {action.due_at:%b %d}.",
        response_data={"assigned_to_id": assignee.id, "due_at": action.due_at.isoformat()},
    )


def execute_webhook_action(action: Action, user: User, db: Session):
    """POST the action to the customer's own endpoint."""
    config = action.action_config or {}
    return deliver_webhook(
        db, action.organization_id,
        payload={"event": "forecastx.action", "action_id": action.id, **_context(action)},
        url=config.get("url"),
        headers=config.get("headers"),
    )


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
        "recorded_at": utcnow().isoformat(),
        "recorded_by": current_user.name
    }

    # Get execution and update it too
    execution = db.query(ActionExecution).filter(
        ActionExecution.action_id == action.id
    ).order_by(desc(ActionExecution.created_at)).first()

    if execution:
        execution.outcome = payload.outcome
        execution.outcome_at = utcnow()
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

    # Execute all matching. Same rule as single execution: a channel that did
    # not deliver leaves its action open and is counted as a failure, so the
    # bulk result reports what really went out.
    executed = 0
    failures = []

    for action in matching_actions:
        try:
            result = _dispatch(action, current_user, db)
        except ChannelError as e:
            db.add(ActionExecution(
                action_id=action.id,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                execution_type="bulk",
                success=False,
                error_message=str(e),
            ))
            action.status = ActionStatus.FAILED
            action.outcome = "failed"
            failures.append({"action_id": action.id, "title": action.title, "error": str(e)})
            continue

        db.add(ActionExecution(
            action_id=action.id,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            execution_type="bulk",
            success=True,
            response_data=result.response_data,
        ))
        action.status = ActionStatus.COMPLETED
        action.executed_at = utcnow()
        action.result = {"channel": result.channel, "detail": result.detail}
        executed += 1

    # Update quick action stats
    quick_action.times_used += 1
    quick_action.last_used_at = utcnow()

    db.commit()

    if failures:
        message = (f"Executed {executed} of {len(matching_actions)} actions; "
                   f"{len(failures)} failed. First error: {failures[0]['error']}")
    else:
        message = f"Executed {executed} actions via quick action"

    return {
        "success": bool(executed) and not failures,
        "quick_action": quick_action.name,
        "actions_executed": executed,
        "actions_matched": len(matching_actions),
        "failed": failures,
        "message": message,
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

    since = utcnow() - timedelta(days=days)

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
