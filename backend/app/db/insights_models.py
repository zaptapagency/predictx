"""
Insights Feed Models
Daily reminders and personalized recommendations
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base
from app.utils.time import utcnow


class Insight(Base):
    """
    Personalized insight for a user
    Daily reminder with actions to take
    """
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Insight type
    insight_type = Column(String(50), nullable=False)  # recommendation, reminder, milestone, etc
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)

    # Action suggestion
    recommended_action = Column(String(255), nullable=True)
    action_type = Column(String(50), nullable=True)  # email, call, task, etc
    estimated_impact = Column(Float, nullable=True)  # $amount or count
    confidence = Column(Float, nullable=True)  # 0-1

    # Metadata
    is_urgent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)

    # Data
    related_entity = Column(String(255), nullable=True)  # customer_name, playbook_id, etc
    meta_data = Column("metadata", JSON, nullable=True)  # Additional context

    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<Insight {self.title}>"


class InsightPreference(Base):
    """
    User preferences for insights (frequency, type, etc)
    """
    __tablename__ = "insight_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Notification frequency
    daily_email_enabled = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    slack_notifications = Column(Boolean, default=False)

    # Preferred time for daily digest
    digest_time = Column(String(5), default="09:00")  # HH:MM format

    # Insight types to include
    include_recommendations = Column(Boolean, default=True)
    include_reminders = Column(Boolean, default=True)
    include_milestones = Column(Boolean, default=True)
    include_team_updates = Column(Boolean, default=True)

    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<InsightPreference user_id={self.user_id}>"
