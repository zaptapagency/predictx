"""
Team Invitation Management
Send invitations to team members, manage permissions, track adoption
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import uuid

from app.db.models_saas import User, Organization, TeamMember, TeamInvitation
from app.services.email_service import EmailService
from app.db.database import get_db
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/teams", tags=["teams"])
email_service = EmailService()

# ============================================================================
# MODELS
# ============================================================================

class InvitedMember(BaseModel):
    email: EmailStr
    name: str = None
    role: str = "cs_manager"  # cs_manager, ceo, sales, admin, other

class TeamInviteRequest(BaseModel):
    members: list[InvitedMember]

class TeamResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    joined_at: datetime

# ============================================================================
# SEND INVITATIONS
# ============================================================================

@router.post("/invite")
def send_team_invitations(
    payload: TeamInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send invitations to team members

    Each invited person gets:
    - Email with invitation link
    - Personal signup link (auto-joins their organization)
    - Access to all predictions/analytics
    """

    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must be part of an organization")

    organization = current_user.organization
    invitations = []
    invited_count = 0

    for member in payload.members:
        # Check if already a member
        existing_member = db.query(TeamMember).filter(
            TeamMember.email == member.email,
            TeamMember.organization_id == organization.id
        ).first()

        if existing_member:
            continue  # Skip if already invited

        # Check if user already exists in system
        existing_user = db.query(User).filter(User.email == member.email).first()

        if existing_user and existing_user.organization_id == organization.id:
            continue  # Already a member

        # Create invitation
        invitation_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = TeamInvitation(
            organization_id=organization.id,
            invited_by_id=current_user.id,
            email=member.email,
            name=member.name or member.email.split('@')[0],
            role=member.role,
            token=invitation_token,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )

        db.add(invitation)
        invitations.append(invitation)
        invited_count += 1

    db.commit()

    # Send invitation emails
    for invitation in invitations:
        signup_link = f"https://forecastx.io/auth/team-invite?token={invitation.token}"

        email_service.send_email(
            to=invitation.email,
            subject=f"Join {organization.name} on ForecastX",
            template="team_invitation",
            data={
                "invited_by_name": current_user.name,
                "company_name": organization.name,
                "invitee_name": invitation.name,
                "signup_link": signup_link,
                "expires_in_days": 7,
            }
        )

    return {
        "success": True,
        "invited_count": invited_count,
        "message": f"Invitations sent to {invited_count} team members"
    }

# ============================================================================
# ACCEPT INVITATION
# ============================================================================

@router.post("/accept-invitation")
def accept_team_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept team invitation - joins user to organization
    """

    invitation = db.query(TeamInvitation).filter(
        TeamInvitation.token == token,
        TeamInvitation.expires_at > datetime.utcnow(),
        TeamInvitation.accepted_at == None
    ).first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")

    # Check email matches
    if current_user.email != invitation.email:
        raise HTTPException(status_code=403, detail="This invitation is not for this email address")

    # Join organization
    current_user.organization_id = invitation.organization_id

    # Mark invitation as accepted
    invitation.accepted_at = datetime.utcnow()

    # Add as team member
    team_member = TeamMember(
        organization_id=invitation.organization_id,
        user_id=current_user.id,
        name=invitation.name,
        role=invitation.role,
        joined_at=datetime.utcnow(),
    )

    db.add(team_member)
    db.commit()

    return {
        "success": True,
        "organization": {
            "id": invitation.organization.id,
            "name": invitation.organization.name,
        }
    }

# ============================================================================
# LIST TEAM MEMBERS
# ============================================================================

@router.get("/members")
def list_team_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all team members in user's organization
    """

    if not current_user.organization_id:
        return {"members": []}

    members = db.query(TeamMember).filter(
        TeamMember.organization_id == current_user.organization_id
    ).all()

    return {
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.user.email if m.user else "Pending",
                "role": m.role,
                "joined_at": m.joined_at,
                "status": "active" if m.user else "pending"
            }
            for m in members
        ]
    }

# ============================================================================
# LIST PENDING INVITATIONS
# ============================================================================

@router.get("/pending-invitations")
def list_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get pending invitations for user's organization
    """

    if not current_user.organization_id:
        return {"pending": []}

    pending = db.query(TeamInvitation).filter(
        TeamInvitation.organization_id == current_user.organization_id,
        TeamInvitation.accepted_at == None,
        TeamInvitation.expires_at > datetime.utcnow()
    ).all()

    return {
        "pending": [
            {
                "id": p.id,
                "email": p.email,
                "name": p.name,
                "role": p.role,
                "invited_at": p.created_at,
                "expires_at": p.expires_at,
            }
            for p in pending
        ]
    }

# ============================================================================
# REMOVE TEAM MEMBER
# ============================================================================

@router.delete("/members/{member_id}")
def remove_team_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove team member from organization
    """

    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    # Check authorization - only org admins can remove
    if member.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(member)
    db.commit()

    return {"success": True, "message": "Team member removed"}

# ============================================================================
# UPDATE TEAM MEMBER ROLE
# ============================================================================

@router.put("/members/{member_id}")
def update_team_member(
    member_id: int,
    new_role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update team member role/permissions
    """

    member = db.query(TeamMember).filter(TeamMember.id == member_id).first()

    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    # Check authorization
    if member.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    member.role = new_role
    db.commit()

    return {
        "success": True,
        "member": {
            "id": member.id,
            "name": member.name,
            "role": member.role,
        }
    }

# ============================================================================
# TRACK TEAM ADOPTION
# ============================================================================

@router.get("/adoption-metrics")
def get_team_adoption_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get team adoption metrics for organization
    """

    if not current_user.organization_id:
        return {"metrics": None}

    # Calculate metrics
    total_members = db.query(TeamMember).filter(
        TeamMember.organization_id == current_user.organization_id
    ).count()

    active_members = db.query(TeamMember).filter(
        TeamMember.organization_id == current_user.organization_id,
        TeamMember.user != None,  # User exists and accepted invitation
        TeamMember.last_login > datetime.utcnow() - timedelta(days=7)
    ).count()

    pending_invitations = db.query(TeamInvitation).filter(
        TeamInvitation.organization_id == current_user.organization_id,
        TeamInvitation.accepted_at == None,
        TeamInvitation.expires_at > datetime.utcnow()
    ).count()

    return {
        "metrics": {
            "total_members": total_members,
            "active_members": active_members,
            "adoption_rate": f"{(active_members / max(total_members, 1) * 100):.0f}%",
            "pending_invitations": pending_invitations,
        }
    }
