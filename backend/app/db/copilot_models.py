"""
AI Copilot Models
Smart recommendations for actions and strategies
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class CopilotRecommendation(Base):
    """
    AI-generated recommendations for user actions
    Smart suggestions based on predictions and historical data
    """
    __tablename__ = "copilot_recommendations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, index=True)

    # Recommendation details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)  # Why this recommendation

    # Suggested action
    suggested_action = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)  # email, call, task, workflow

    # Entity
    entity_type = Column(String(50), nullable=True)  # customer, playbook, team
    entity_id = Column(Integer, nullable=True)

    # Prediction
    estimated_impact = Column(Float, nullable=True)
    success_probability = Column(Float, nullable=True)  # 0-1
    confidence = Column(Float, nullable=True)  # How confident is the AI

    # AI metrics
    model_version = Column(String(50), nullable=True)
    reasoning_factors = Column(JSON, nullable=True)  # What influenced recommendation

    # Engagement
    is_dismissed = Column(Boolean, default=False)
    was_executed = Column(Boolean, default=False)
    execution_date = Column(DateTime, nullable=True)
    execution_outcome = Column(String(50), nullable=True)  # success, failed, pending

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<CopilotRecommendation {self.title}>"


class CopilotFeedback(Base):
    """
    User feedback on AI recommendations
    Used to improve recommendation quality
    """
    __tablename__ = "copilot_feedback"

    id = Column(Integer, primary_key=True)
    recommendation_id = Column(Integer, ForeignKey("copilot_recommendations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)

    # Feedback
    was_helpful = Column(Boolean, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_text = Column(Text, nullable=True)

    # Outcome
    actual_outcome = Column(String(50), nullable=True)  # success, failed, not_applicable
    actual_impact = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    recommendation = relationship("CopilotRecommendation")
    user = relationship("User")

    def __repr__(self):
        return f"<CopilotFeedback rating={self.rating}>"
