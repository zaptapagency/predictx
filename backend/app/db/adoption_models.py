"""
Adoption Tracker Models
Team adoption metrics and management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class TeamAdoption(Base):
    """
    Team adoption metrics and progress
    Tracks who's using ForecastX and how
    """
    __tablename__ = "team_adoption"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, unique=True)

    # Team metrics
    total_team_size = Column(Integer, default=0)
    active_users = Column(Integer, default=0)  # Users who took action this month
    inactive_users = Column(Integer, default=0)
    adoption_rate = Column(Float, default=0.0)  # % of team using platform

    # Usage patterns
    avg_actions_per_user = Column(Float, default=0.0)
    total_actions = Column(Integer, default=0)
    total_predictions_run = Column(Integer, default=0)

    # Engagement
    daily_active_users = Column(Integer, default=0)
    weekly_active_users = Column(Integer, default=0)
    monthly_active_users = Column(Integer, default=0)

    # Playbook adoption
    playbooks_deployed = Column(Integer, default=0)
    avg_playbooks_per_user = Column(Float, default=0.0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")

    def __repr__(self):
        return f"<TeamAdoption org_id={self.organization_id} adoption={self.adoption_rate}%>"


class UserAdoption(Base):
    """
    Individual user adoption progress
    Tracks each user's journey from signup to power user
    """
    __tablename__ = "user_adoption"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, unique=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, index=True)

    # Adoption stage (funnel)
    stage = Column(String(50), default="onboarded")  # onboarded, activated, habit_forming, power_user, churned

    # Milestones
    first_action_at = Column(DateTime, nullable=True)
    first_value_at = Column(DateTime, nullable=True)  # First customer saved/prediction made
    habit_formed_at = Column(DateTime, nullable=True)  # 10+ actions in month

    # Activity
    last_active_at = Column(DateTime, nullable=True)
    days_active = Column(Integer, default=0)
    total_actions = Column(Integer, default=0)
    total_predictions = Column(Integer, default=0)

    # Engagement health
    engagement_score = Column(Float, default=0.0)  # 0-100
    churn_risk = Column(Float, default=0.0)  # 0-1 probability of churning

    # Features used
    features_used = Column(Integer, default=0)  # How many different features
    playbooks_deployed = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<UserAdoption user_id={self.user_id} stage={self.stage}>"
