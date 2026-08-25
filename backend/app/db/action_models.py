"""
Action Center Models
Track prediction-based actions and outcomes
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

# ============================================================================
# ACTION STATUS & PRIORITY
# ============================================================================

class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"

class ActionPriority(str, enum.Enum):
    CRITICAL = "critical"  # Red - immediate action (VIP at risk)
    HIGH = "high"          # Orange - act today
    MEDIUM = "medium"      # Yellow - this week
    LOW = "low"            # Green - when you have time

class ActionType(str, enum.Enum):
    EMAIL = "email"
    SLACK = "slack"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PHONE_CALL = "phone_call"
    MEETING = "meeting"
    TASK = "task"
    WORKFLOW = "workflow"
    WEBHOOK = "webhook"
    CUSTOM = "custom"

# ============================================================================
# ACTION MODEL (What needs to be done)
# ============================================================================

class Action(Base):
    """
    Actionable items generated from predictions
    Each prediction creates N actions to take
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=True)
    prediction_id = Column(String(255), nullable=True, index=True)  # Link to prediction

    # Action details
    title = Column(String(255), nullable=False)  # "Email Acme Corp"
    description = Column(Text, nullable=True)    # Detailed description
    action_type = Column(String(50), nullable=False)  # email, slack, task, etc
    priority = Column(String(50), default=ActionPriority.MEDIUM)
    status = Column(String(50), default=ActionStatus.PENDING, index=True)

    # Target entity
    entity_type = Column(String(50), nullable=False)  # customer, lead, employee, etc
    entity_id = Column(String(255), nullable=False, index=True)  # Salesforce ID, email, etc
    entity_name = Column(String(255), nullable=True)  # Company name, person name
    entity_email = Column(String(255), nullable=True)

    # Business impact
    estimated_impact = Column(Float, nullable=True)  # Revenue saved, revenue created, etc
    impact_type = Column(String(50), nullable=True)  # revenue_saved, revenue_created, efficiency, etc
    impact_unit = Column(String(50), nullable=True)  # usd, customers, hours

    # Action configuration
    action_config = Column(JSON, nullable=True)  # Template, recipient, message, etc
    recommended_message = Column(Text, nullable=True)

    # Execution
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)  # What happened when action was taken
    outcome = Column(String(50), nullable=True)  # success, partial, failed, skipped

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    assigned_to = relationship("User")

    def __repr__(self):
        return f"<Action {self.title} - {self.status}>"


# ============================================================================
# ACTION EXECUTION MODEL (Track when actions were taken)
# ============================================================================

class ActionExecution(Base):
    """
    Log of when/how actions were executed
    One action can have multiple executions (retry, schedule, etc)
    """
    __tablename__ = "action_executions"

    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)

    # Execution details
    execution_type = Column(String(50))  # immediate, scheduled, bulk, auto
    scheduled_for = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    # Result tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=True)  # API response, delivery status, etc

    # Outcome tracking (later)
    outcome = Column(String(50), nullable=True)  # success, partial, failed
    outcome_at = Column(DateTime, nullable=True)  # When we learned the outcome
    outcome_notes = Column(Text, nullable=True)  # User notes, system notes

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ActionExecution action_id={self.action_id} - {self.success}>"


# ============================================================================
# ACTION TEMPLATE MODEL (Re-usable action templates)
# ============================================================================

class ActionTemplate(Base):
    """
    Pre-defined action templates for common scenarios
    Speeds up action creation
    """
    __tablename__ = "action_templates"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Template info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    action_type = Column(String(50), nullable=False)  # email, slack, task, etc

    # Template content
    subject = Column(String(255), nullable=True)  # For emails
    message_template = Column(Text, nullable=True)  # With {{variables}}
    variables = Column(JSON, nullable=True)  # {{company_name}}, {{revenue_saved}}, etc

    # Targeting
    trigger_type = Column(String(50), nullable=True)  # churn, expansion, fraud, etc
    priority_default = Column(String(50), default=ActionPriority.MEDIUM)

    # Metrics
    success_rate = Column(Float, nullable=True)  # % of actions that succeeded
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=False)  # Public template vs org-specific

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ActionTemplate {self.name}>"


# ============================================================================
# ACTION SUMMARY / QUICK ACTIONS
# ============================================================================

class QuickAction(Base):
    """
    Pre-built quick actions for bulk operations
    "Email all at-risk customers", "Schedule calls for expansion-ready"
    """
    __tablename__ = "quick_actions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Quick action definition
    name = Column(String(255), nullable=False)  # "Email at-risk customers"
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji

    # What it does
    action_config = Column(JSON, nullable=False)  # Template, recipients, message
    filter_config = Column(JSON, nullable=False)  # Who to apply this to
    impact_estimate = Column(Float, nullable=True)  # Expected impact

    # Usage
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    success_rate = Column(Float, nullable=True)  # % that succeeded

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QuickAction {self.name}>"
