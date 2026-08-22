"""
Onboarding API endpoints
Track and manage user onboarding flow
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

from app.db.models_saas import User
from app.db.onboarding_models import OnboardingProgress, OnboardingEvent, OnboardingEmailSequence
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OnboardingStepUpdate(BaseModel):
    step_id: str
    action: Optional[str] = None
    metadata: Optional[dict] = None


class GoalSelection(BaseModel):
    goal: str  # "churn", "growth", "onboarding"


class TemplateSelection(BaseModel):
    template: str  # template ID


class OnboardingProgressResponse(BaseModel):
    current_step: int
    completed_steps: List[str]
    selected_goal: Optional[str]
    selected_template: Optional[str]
    salesforce_connected: bool
    first_playbook_created: bool
    first_prediction_seen: bool
    is_completed: bool


# ============================================================================
# ONBOARDING FLOW ENDPOINTS
# ============================================================================

@router.get("/progress")
def get_onboarding_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OnboardingProgressResponse:
    """Get user's onboarding progress"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        # Create initial progress record
        progress = OnboardingProgress(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            current_step=0,
            completed_steps=[]
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return OnboardingProgressResponse(
        current_step=progress.current_step,
        completed_steps=progress.completed_steps or [],
        selected_goal=progress.selected_goal,
        selected_template=progress.selected_template,
        salesforce_connected=progress.salesforce_connected,
        first_playbook_created=progress.first_playbook_created,
        first_prediction_seen=progress.first_prediction_seen,
        is_completed=progress.is_completed
    )


@router.post("/steps/{step_id}/complete")
def complete_onboarding_step(
    step_id: str,
    request: OnboardingStepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark onboarding step as complete"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    # Add to completed steps
    if step_id not in (progress.completed_steps or []):
        progress.completed_steps = (progress.completed_steps or []) + [step_id]
        progress.current_step += 1
        progress.updated_at = datetime.utcnow()

        # Check if fully completed
        if len(progress.completed_steps) == 5:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()

    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="step_completed",
        step_id=step_id,
        action=request.action,
        metadata=request.metadata
    )
    db.add(event)
    db.commit()

    return {
        "step_id": step_id,
        "completed": True,
        "progress": len(progress.completed_steps or []),
        "total_steps": 5
    }


@router.post("/goal")
def select_goal(
    request: GoalSelection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """User selects their goal"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    progress.selected_goal = request.goal
    progress.updated_at = datetime.utcnow()
    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="goal_selected",
        action=f"selected_{request.goal}",
        metadata={"goal": request.goal}
    )
    db.add(event)
    db.commit()

    return {
        "goal": request.goal,
        "selected": True
    }


@router.post("/template")
def select_template(
    request: TemplateSelection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """User selects playbook template"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    progress.selected_template = request.template
    progress.updated_at = datetime.utcnow()
    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="template_selected",
        action=f"selected_{request.template}",
        metadata={"template": request.template}
    )
    db.add(event)
    db.commit()

    return {
        "template": request.template,
        "selected": True
    }


@router.post("/salesforce/connected")
def mark_salesforce_connected(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark Salesforce as connected"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    progress.salesforce_connected = True
    progress.connected_at = datetime.utcnow()
    progress.updated_at = datetime.utcnow()
    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="salesforce_connected",
        action="connected_salesforce"
    )
    db.add(event)
    db.commit()

    return {
        "salesforce_connected": True,
        "connected_at": progress.connected_at
    }


@router.post("/first-playbook-created")
def mark_first_playbook_created(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark first playbook as created"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    progress.first_playbook_created = True
    progress.first_playbook_created_at = datetime.utcnow()
    progress.updated_at = datetime.utcnow()
    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="first_playbook_created"
    )
    db.add(event)
    db.commit()

    return {
        "playbook_created": True,
        "created_at": progress.first_playbook_created_at
    }


@router.post("/first-prediction-seen")
def mark_first_prediction_seen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Mark first prediction as seen"""

    progress = db.query(OnboardingProgress).filter(
        OnboardingProgress.user_id == current_user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding progress not found")

    progress.first_prediction_seen = True
    progress.first_prediction_at = datetime.utcnow()
    progress.updated_at = datetime.utcnow()

    # Check if all steps complete
    if len(progress.completed_steps or []) == 5:
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

    db.commit()

    # Track event
    event = OnboardingEvent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        event_type="first_prediction_seen"
    )
    db.add(event)
    db.commit()

    return {
        "prediction_seen": True,
        "seen_at": progress.first_prediction_at,
        "onboarding_complete": progress.is_completed
    }


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/events")
def get_onboarding_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get all onboarding events for user"""

    events = db.query(OnboardingEvent).filter(
        OnboardingEvent.user_id == current_user.id
    ).all()

    return {
        "events": [
            {
                "event_type": e.event_type,
                "step_id": e.step_id,
                "action": e.action,
                "created_at": e.created_at
            }
            for e in events
        ]
    }


@router.get("/stats")
def get_onboarding_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get onboarding completion stats for organization"""

    total_users = db.query(OnboardingProgress).filter(
        OnboardingProgress.organization_id == current_user.organization_id
    ).count()

    completed_users = db.query(OnboardingProgress).filter(
        OnboardingProgress.organization_id == current_user.organization_id,
        OnboardingProgress.is_completed == True
    ).count()

    salesforce_connected = db.query(OnboardingProgress).filter(
        OnboardingProgress.organization_id == current_user.organization_id,
        OnboardingProgress.salesforce_connected == True
    ).count()

    playbook_created = db.query(OnboardingProgress).filter(
        OnboardingProgress.organization_id == current_user.organization_id,
        OnboardingProgress.first_playbook_created == True
    ).count()

    return {
        "total_users": total_users,
        "completed_users": completed_users,
        "completion_rate": (completed_users / total_users * 100) if total_users > 0 else 0,
        "salesforce_connected": salesforce_connected,
        "first_playbook_created": playbook_created
    }
