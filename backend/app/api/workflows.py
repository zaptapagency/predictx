"""
Workflow Management API
Create, manage, and monitor workflows
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.models_saas import User
from app.db.workflow_models import (
    Workflow, WorkflowAction, WorkflowExecution, WorkflowActionExecution,
    WorkflowStatus, ActionType, WorkflowTrigger, WorkflowActionTemplate
)
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.workflow_engine import WorkflowEngine
from app.utils.time import utcnow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CreateWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any]
    model_type: Optional[str] = None
    segment_filter: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]]


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None


class TestWorkflowRequest(BaseModel):
    customer_id: str
    trigger_data: Dict[str, Any]


# ============================================================================
# WORKFLOW MANAGEMENT
# ============================================================================

@router.post("/")
def create_workflow(
    request: CreateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new workflow"""

    try:
        workflow = Workflow(
            organization_id=current_user.organization_id,
            name=request.name,
            description=request.description,
            trigger_type=WorkflowTrigger[request.trigger_type.upper()],
            trigger_config=request.trigger_config,
            model_type=request.model_type,
            segment_filter=request.segment_filter,
            created_by_id=current_user.id,
            status=WorkflowStatus.DRAFT
        )

        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        # Create actions
        for i, action_config in enumerate(request.actions):
            action = WorkflowAction(
                workflow_id=workflow.id,
                sequence=i,
                action_type=ActionType[action_config.get("type").upper()],
                config=action_config.get("config"),
                condition_expression=action_config.get("condition")
            )
            db.add(action)

        db.commit()

        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "actions_count": len(request.actions)
        }

    except KeyError as e:
        triggers = ", ".join(t.value for t in WorkflowTrigger)
        action_types = ", ".join(a.value for a in ActionType)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid value {e}. Valid trigger_type: {triggers}. "
                f"Valid action type: {action_types}."
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def list_workflows(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List workflows"""

    query = db.query(Workflow).filter(
        Workflow.organization_id == current_user.organization_id
    )

    if status:
        query = query.filter(Workflow.status == WorkflowStatus[status.upper()])

    workflows = query.all()

    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "status": w.status.value,
                "trigger_type": w.trigger_type.value,
                "model_type": w.model_type,
                "actions_count": len(w.actions),
                "run_count": w.run_count,
                "created_at": w.created_at
            }
            for w in workflows
        ]
    }


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workflow details"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status.value,
        "trigger_type": workflow.trigger_type.value,
        "trigger_config": workflow.trigger_config,
        "model_type": workflow.model_type,
        "segment_filter": workflow.segment_filter,
        "actions": [
            {
                "id": a.id,
                "sequence": a.sequence,
                "type": a.action_type.value,
                "config": a.config,
                "condition": a.condition_expression
            }
            for a in sorted(workflow.actions, key=lambda x: x.sequence)
        ],
        "run_count": workflow.run_count,
        "created_at": workflow.created_at
    }


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: int,
    request: UpdateWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update workflow"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        if request.name:
            workflow.name = request.name
        if request.description:
            workflow.description = request.description
        if request.status:
            workflow.status = WorkflowStatus[request.status.upper()]
        if request.trigger_config:
            workflow.trigger_config = request.trigger_config

        if request.actions:
            # Delete existing actions
            db.query(WorkflowAction).filter(
                WorkflowAction.workflow_id == workflow_id
            ).delete()

            # Create new actions
            for i, action_config in enumerate(request.actions):
                action = WorkflowAction(
                    workflow_id=workflow_id,
                    sequence=i,
                    action_type=ActionType[action_config.get("type").upper()],
                    config=action_config.get("config"),
                    condition_expression=action_config.get("condition")
                )
                db.add(action)

        workflow.updated_at = utcnow()
        db.commit()

        return {"id": workflow.id, "status": "updated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete workflow"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Soft delete by archiving
    workflow.status = WorkflowStatus.ARCHIVED
    db.commit()

    return {"status": "deleted"}


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

@router.post("/{workflow_id}/test")
def test_workflow(
    workflow_id: int,
    request: TestWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test workflow with sample data"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        engine = WorkflowEngine(db)
        execution = engine.execute_workflow(
            workflow_id,
            request.customer_id,
            request.trigger_data
        )

        return {
            "execution_id": execution.id,
            "status": execution.status.value,
            "results": execution.execution_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: int,
    request: TestWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute workflow for customer"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        engine = WorkflowEngine(db)
        execution = engine.execute_workflow(
            workflow_id,
            request.customer_id,
            request.trigger_data
        )

        return {
            "execution_id": execution.id,
            "status": execution.status.value
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions")
def get_workflow_executions(
    workflow_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get execution history"""

    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.organization_id == current_user.organization_id
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id
    ).order_by(desc(WorkflowExecution.created_at)).limit(limit).all()

    return {
        "executions": [
            {
                "id": e.id,
                "customer_id": e.customer_id,
                "status": e.status.value,
                "started_at": e.started_at,
                "completed_at": e.completed_at,
                "duration_seconds": e.duration_seconds,
                "actions_count": len(db.query(WorkflowActionExecution).filter(
                    WorkflowActionExecution.workflow_execution_id == e.id
                ).all())
            }
            for e in executions
        ]
    }


@router.get("/executions/{execution_id}")
def get_execution_details(
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed execution info"""

    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == execution_id,
        WorkflowExecution.organization_id == current_user.organization_id
    ).first()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    action_executions = db.query(WorkflowActionExecution).filter(
        WorkflowActionExecution.workflow_execution_id == execution_id
    ).order_by(WorkflowActionExecution.sequence).all()

    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "customer_id": execution.customer_id,
        "status": execution.status.value,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "duration_seconds": execution.duration_seconds,
        "trigger_data": execution.trigger_data,
        "actions": [
            {
                "sequence": a.sequence,
                "status": a.status.value,
                "duration_seconds": a.duration_seconds,
                "external_id": a.external_id,
                "error": a.error_message
            }
            for a in action_executions
        ],
        "error": execution.error_message
    }


# ============================================================================
# ACTION TEMPLATES
# ============================================================================

@router.get("/templates")
def list_templates(
    action_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List action templates"""

    query = db.query(WorkflowActionTemplate).filter(
        (WorkflowActionTemplate.organization_id == current_user.organization_id) |
        (WorkflowActionTemplate.is_public == True)
    )

    if action_type:
        query = query.filter(WorkflowActionTemplate.action_type == ActionType[action_type.upper()])

    templates = query.all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "action_type": t.action_type.value,
                "description": t.description,
                "variables": t.variables
            }
            for t in templates
        ]
    }


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get template details"""

    template = db.query(WorkflowActionTemplate).filter(
        WorkflowActionTemplate.id == template_id,
        (WorkflowActionTemplate.organization_id == current_user.organization_id) |
        (WorkflowActionTemplate.is_public == True)
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template.id,
        "name": template.name,
        "action_type": template.action_type.value,
        "template_content": template.template_content,
        "variables": template.variables
    }
