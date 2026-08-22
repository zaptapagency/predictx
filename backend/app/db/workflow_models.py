"""
Workflow automation models
Define and execute actions in response to predictions
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class WorkflowTrigger(str, enum.Enum):
    """When a workflow should trigger"""
    PREDICTION_CREATED = "prediction_created"
    PREDICTION_THRESHOLD = "prediction_threshold"
    CUSTOMER_SEGMENT = "customer_segment"
    TIME_BASED = "time_based"


class ActionType(str, enum.Enum):
    """Types of actions workflows can execute"""
    EMAIL = "email"
    SLACK = "slack"
    SALESFORCE = "salesforce"
    WEBHOOK = "webhook"
    TASK = "task"


class WorkflowStatus(str, enum.Enum):
    """Workflow status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, enum.Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Workflow(Base):
    """
    Workflow definition
    Defines a sequence of actions triggered by a prediction
    """
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)

    # Trigger configuration
    trigger_type = Column(Enum(WorkflowTrigger), nullable=False)
    trigger_config = Column(JSON)  # {model_type, prediction_field, threshold, segment_id, cron}

    # Scope
    model_type = Column(String(100))  # Which model triggers this? (churn, opportunity, etc)
    segment_filter = Column(JSON)  # Optional: only run for customers matching this segment

    # Actions
    actions = relationship("WorkflowAction", back_populates="workflow", cascade="all, delete-orphan")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    run_count = Column(Integer, default=0)


class WorkflowAction(Base):
    """
    Individual action within a workflow
    Executed in sequence when workflow triggers
    """
    __tablename__ = "workflow_actions"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    sequence = Column(Integer)  # Order to execute
    action_type = Column(Enum(ActionType), nullable=False)

    # Action configuration
    config = Column(JSON)  # Type-specific config

    # For email: {to_field, subject_template, body_template, attachments}
    # For Slack: {channel, message_template, thread_root}
    # For Salesforce: {object, action, field_mapping}
    # For webhook: {url, method, headers, payload_template}
    # For task: {title_template, description_template, owner_id}

    # Conditions (optional)
    condition_expression = Column(Text)  # JS-like expression: data.score > 0.8

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="actions")


class WorkflowExecution(Base):
    """
    Record of a workflow execution
    Tracks when a workflow ran and its results
    """
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    customer_id = Column(String(255))  # Which customer triggered this
    prediction_id = Column(Integer, ForeignKey("predictions.id"))  # What prediction triggered it

    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)  # Total execution time

    # Execution context
    trigger_data = Column(JSON)  # The data that triggered the workflow
    execution_results = Column(JSON)  # Results of each action

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)


class ActionExecution(Base):
    """
    Record of individual action execution
    """
    __tablename__ = "action_executions"

    id = Column(Integer, primary_key=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False)
    action_id = Column(Integer, ForeignKey("workflow_actions.id"), nullable=False)
    sequence = Column(Integer)

    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Result details
    request_payload = Column(JSON)  # What was sent
    response_data = Column(JSON)  # What came back
    error_message = Column(Text)
    external_id = Column(String(255))  # ID from external system (email id, Slack ts, SF record id)

    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowSchedule(Base):
    """
    Scheduled recurring workflows
    """
    __tablename__ = "workflow_schedules"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    cron_expression = Column(String(100))  # "0 9 * * 1" = every Monday at 9am
    timezone = Column(String(50), default="UTC")
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActionTemplate(Base):
    """
    Reusable templates for common actions
    Email templates, Slack message templates, etc.
    """
    __tablename__ = "action_templates"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    description = Column(Text)

    # Template content
    template_content = Column(JSON)  # Type-specific content
    variables = Column(JSON)  # [{name, type, description, default}]

    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
