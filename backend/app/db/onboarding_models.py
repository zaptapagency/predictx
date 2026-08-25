"""
Onboarding tracking models
Track user progress through onboarding flow
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class OnboardingProgress(Base):
    """
    Track onboarding progress for each user
    """
    __tablename__ = "onboarding_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Overall progress
    current_step = Column(Integer, default=0)
    completed_steps = Column(JSON, default=list)  # ["welcome", "goal", "connect", ...]
    completed_at = Column(DateTime, nullable=True)

    # User choices
    selected_goal = Column(String(50))  # "churn", "growth", "onboarding"
    selected_template = Column(String(100))

    # Milestones
    salesforce_connected = Column(Boolean, default=False)
    connected_at = Column(DateTime, nullable=True)

    first_playbook_created = Column(Boolean, default=False)
    first_playbook_created_at = Column(DateTime, nullable=True)

    first_prediction_seen = Column(Boolean, default=False)
    first_prediction_at = Column(DateTime, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Properties
    is_completed = Column(Boolean, default=False)

    user = relationship("User")


class OnboardingEvent(Base):
    """
    Track specific onboarding events for analytics
    """
    __tablename__ = "onboarding_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Event details
    event_type = Column(String(100), nullable=False)  # "step_viewed", "action_completed", "error"
    step_id = Column(String(50))  # "welcome", "goal", "connect", etc

    # Event context
    action = Column(String(255))  # "clicked_connect", "selected_goal", etc
    meta_data = Column("metadata", JSON)  # Additional data

    # Timing
    duration_seconds = Column(Integer)  # Time spent on step
    created_at = Column(DateTime, default=datetime.utcnow)


class OnboardingEmailSequence(Base):
    """
    Track onboarding email sends
    """
    __tablename__ = "onboarding_email_sequence"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Email details
    email_key = Column(String(50), nullable=False)  # "welcome", "day2_playbook", etc
    email_type = Column(String(50))  # "tip", "guide", "celebration"

    # Tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)

    # Personalization
    personalization = Column(JSON)  # Variables used in email
