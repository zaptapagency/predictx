"""
Team Activity Feed Models
Social proof and celebration tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base
from app.utils.time import utcnow


class TeamActivity(Base):
    """
    Team-wide activities (wins, achievements, milestones)
    Feeds social proof and team motivation
    """
    __tablename__ = "team_activities"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Activity details
    activity_type = Column(String(50), nullable=False)  # customer_saved, expansion_closed, achievement_unlocked
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Entity details
    entity_type = Column(String(50), nullable=True)  # customer, playbook, achievement
    entity_id = Column(Integer, nullable=True)
    entity_name = Column(String(255), nullable=True)

    # Impact
    revenue_impact = Column(Float, nullable=True)
    customers_affected = Column(Integer, nullable=True)
    metric_value = Column(Float, nullable=True)

    # Visibility
    is_public = Column(Boolean, default=True)
    is_celebratory = Column(Boolean, default=False)  # High-impact, worthy of celebration

    # Engagement
    reaction_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<TeamActivity {self.title}>"


class ActivityReaction(Base):
    """
    User reactions to team activities (👏, ❤️, 🔥, etc)
    """
    __tablename__ = "activity_reactions"

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("team_activities.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Reaction emoji
    emoji = Column(String(10), nullable=False)  # 👏, ❤️, 🔥, etc

    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    activity = relationship("TeamActivity")
    user = relationship("User")

    def __repr__(self):
        return f"<ActivityReaction {self.emoji} on activity {self.activity_id}>"
