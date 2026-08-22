"""
Playbook Monitor Models
Performance tracking and optimization
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class PlaybookPerformance(Base):
    """
    Playbook performance metrics
    Tracks how well each playbook is performing
    """
    __tablename__ = "playbook_performance"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)

    # Usage metrics
    total_executions = Column(Integer, default=0)
    total_predictions = Column(Integer, default=0)
    successful_actions = Column(Integer, default=0)
    failed_actions = Column(Integer, default=0)

    # Performance
    success_rate = Column(Float, default=0.0)  # % of predictions that led to positive outcome
    average_execution_time = Column(Float, nullable=True)  # seconds
    average_revenue_per_execution = Column(Float, default=0.0)

    # Total impact
    total_revenue_generated = Column(Float, default=0.0)
    total_customers_affected = Column(Integer, default=0)
    total_roi = Column(Float, default=0.0)  # ROI multiplier

    # Trending
    trend = Column(String(20), default="stable")  # improving, stable, declining
    month_over_month_change = Column(Float, nullable=True)  # % change

    # Adoption
    users_using = Column(Integer, default=0)
    deployment_count = Column(Integer, default=0)

    # Health
    is_active = Column(Boolean, default=True)
    deprecation_date = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    organization = relationship("Organization")
    playbook = relationship("Playbook")

    def __repr__(self):
        return f"<PlaybookPerformance playbook_id={self.playbook_id} success_rate={self.success_rate}%>"


class PlaybookUsageMetric(Base):
    """
    Daily/weekly usage metrics for playbooks
    Used to track trends and identify issues
    """
    __tablename__ = "playbook_usage_metrics"

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, index=True)

    # Time period
    period_date = Column(DateTime, nullable=False, index=True)  # Day this metric is for
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Execution metrics
    executions = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    pending = Column(Integer, default=0)

    # Performance
    success_rate = Column(Float, nullable=True)
    avg_revenue = Column(Float, nullable=True)

    # Users
    unique_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    playbook = relationship("Playbook")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<PlaybookUsageMetric playbook_id={self.playbook_id} date={self.period_date.date()}>"
