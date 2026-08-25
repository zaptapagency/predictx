"""
Team Management Models
- TeamMember: Organization members
- TeamInvitation: Pending invitations
- TeamRole: Role-based permissions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

# ============================================================================
# TEAM MEMBER ROLES
# ============================================================================

class TeamRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CS_MANAGER = "cs_manager"
    CS_AGENT = "cs_agent"
    SALES = "sales"
    VIEWER = "viewer"

# ============================================================================
# TEAM MEMBER MODEL
# ============================================================================

class TeamMember(Base):
    """
    Organization team members
    Links users to organizations with roles
    """
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=True, index=True)
    role = Column(String(50), default=TeamRole.VIEWER)

    # Access permissions
    can_view_all_customers = Column(Boolean, default=False)  # Admins/managers only
    can_edit_predictions = Column(Boolean, default=False)    # Admin only
    can_manage_team = Column(Boolean, default=False)         # Admin only

    # Activity tracking
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")

    def __repr__(self):
        return f"<TeamMember {self.name} - {self.role}>"

# ============================================================================
# TEAM INVITATION MODEL
# ============================================================================

class TeamInvitation(Base):
    """
    Pending team member invitations
    Tracks invitations and acceptance
    """
    __tablename__ = "team_invitations"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    role = Column(String(50), default=TeamRole.CS_MANAGER)

    # Invitation token & expiration
    token = Column(String(36), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Acceptance tracking
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization")
    invited_by = relationship("User")

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_accepted(self) -> bool:
        return self.accepted_at is not None

    def __repr__(self):
        return f"<TeamInvitation {self.email} - {self.role}>"

# ============================================================================
# AUDIT LOG MODEL (for team activity tracking)
# ============================================================================

class TeamActivityLog(Base):
    """
    Log all team activities for audit trail
    - Predictions viewed
    - Team members invited
    - Settings changed
    - Integrations connected
    """
    __tablename__ = "team_activity_logs"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    action = Column(String(100), index=True)  # invited_member, viewed_prediction, etc
    resource_type = Column(String(50))         # user, prediction, integration, etc
    resource_id = Column(String(255), nullable=True)

    details = Column(Text, nullable=True)  # JSON with additional context

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<TeamActivityLog {self.action} by user {self.user_id}>"

# ============================================================================
# UPDATE ORGANIZATION MODEL
# ============================================================================

"""
Add these fields to Organization model:

class Organization(Base):
    # ... existing fields ...

    # Team management
    team_members = relationship("TeamMember", back_populates="organization")
    invitations = relationship("TeamInvitation", foreign_keys="TeamInvitation.organization_id")

    # Team settings
    allow_team_members = Column(Boolean, default=True)
    max_team_members = Column(Integer, default=50)
    team_member_count = Column(Integer, default=1)

    # Activity
    last_team_activity = Column(DateTime, nullable=True)
"""

# ============================================================================
# UPDATE USER MODEL
# ============================================================================

"""
Add these fields to User model:

class User(Base):
    # ... existing fields ...

    # Team relationships
    team_members = relationship("TeamMember", back_populates="user")

    # Activity tracking
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
"""
