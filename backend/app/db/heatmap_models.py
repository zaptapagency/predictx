"""
Health Heatmap Models
Visual overview of customer health and urgency
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class CustomerHealthScore(Base):
    """
    Overall health score for each customer
    Composite metric: churn risk, expansion potential, support needs
    """
    __tablename__ = "customer_health_scores"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=False, index=True)
    customer_id = Column(String(255), nullable=False, index=True)

    # Health metrics (0-100)
    overall_health = Column(Float, default=50.0)  # Composite score
    churn_risk = Column(Float, default=0.0)  # 0-1 probability
    expansion_potential = Column(Float, default=0.0)  # 0-1 likelihood
    support_urgency = Column(Float, default=0.0)  # 0-1 urgency

    # Trending
    health_trend = Column(String(20), default="stable")  # improving, stable, declining
    trend_direction = Column(Float, nullable=True)  # +/- change

    # Risk factors
    red_flags = Column(Integer, default=0)  # Number of risk indicators
    yellow_flags = Column(Integer, default=0)
    green_flags = Column(Integer, default=0)

    # Last update
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    organization = relationship("Organization")

    def __repr__(self):
        return f"<CustomerHealthScore customer_id={self.customer_id} health={self.overall_health}>"


class HealthMetric(Base):
    """
    Individual health metrics contributing to overall score
    """
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True)
    health_score_id = Column(Integer, ForeignKey("customer_health_scores.id"), nullable=False)

    # Metric
    metric_name = Column(String(100), nullable=False)  # login_frequency, support_tickets, nps, etc
    metric_value = Column(Float, nullable=False)
    metric_weight = Column(Float, default=1.0)  # Importance in calculation

    # Classification
    status = Column(String(20), nullable=False)  # good, warning, critical

    # Details
    description = Column(Text, nullable=True)
    recommended_action = Column(String(255), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_score = relationship("CustomerHealthScore")

    def __repr__(self):
        return f"<HealthMetric {self.metric_name}>"
