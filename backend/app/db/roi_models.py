"""
ROI & Impact Tracking Models
Track financial value from ForecastX usage
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

# ============================================================================
# IMPACT TYPE & CATEGORY
# ============================================================================

class ImpactType(str, enum.Enum):
    REVENUE_SAVED = "revenue_saved"      # Customer didn't churn
    REVENUE_CREATED = "revenue_created"  # Customer expanded/upsold
    EFFICIENCY_GAIN = "efficiency_gain"  # Time saved, cost avoided

class ImpactCategory(str, enum.Enum):
    CHURN_PREVENTION = "churn_prevention"
    EXPANSION = "expansion"
    LEAD_CONVERSION = "lead_conversion"
    FRAUD_PREVENTION = "fraud_prevention"
    DEMAND_OPTIMIZATION = "demand_optimization"
    PRICING_OPTIMIZATION = "pricing_optimization"
    SUPPORT_EFFICIENCY = "support_efficiency"
    HR_RETENTION = "hr_retention"
    READMISSION_PREVENTION = "readmission_prevention"
    OTHER = "other"

# ============================================================================
# IMPACT RECORD MODEL (Each saved/created revenue tracked)
# ============================================================================

class ImpactRecord(Base):
    """
    Individual impact records
    One per prediction action that created value
    """
    __tablename__ = "impact_records"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)

    # What happened
    impact_type = Column(String(50), nullable=False)  # revenue_saved, revenue_created, efficiency_gain
    impact_category = Column(String(50), nullable=False)  # churn_prevention, expansion, etc

    # Target entity
    entity_type = Column(String(50), nullable=False)  # customer, lead, employee, etc
    entity_id = Column(String(255), nullable=False)
    entity_name = Column(String(255), nullable=False)

    # Value
    value_amount = Column(Float, nullable=False)  # How much $ saved/created
    value_unit = Column(String(50), default="usd")  # usd, customers, hours, etc

    # Confidence/certainty
    confidence_level = Column(Float, nullable=True)  # 0-1, how confident are we?
    is_confirmed = Column(Boolean, default=False)  # User confirmed it actually happened
    confirmation_note = Column(Text, nullable=True)  # User's note on confirmation

    # Timeline
    predicted_at = Column(DateTime, default=datetime.utcnow, index=True)  # When prediction was made
    action_taken_at = Column(DateTime, nullable=True)  # When action was taken
    value_realized_at = Column(DateTime, nullable=True, index=True)  # When value was actually realized

    # Metadata
    is_annual = Column(Boolean, default=False)  # Annual value (recurring) vs. one-time
    is_recurring = Column(Boolean, default=False)  # Will this repeat? (e.g., monthly expansion)
    annual_value = Column(Float, nullable=True)  # If recurring, annual impact

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ImpactRecord {self.entity_name} - ${self.value_amount}>"


# ============================================================================
# ROI SUMMARY (Monthly/Weekly/Daily rollup)
# ============================================================================

class ROISummary(Base):
    """
    Aggregated ROI metrics by time period
    Updated daily/weekly/monthly
    """
    __tablename__ = "roi_summaries"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Time period
    period = Column(String(20), nullable=False)  # day, week, month, all_time
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Revenue saved (churn prevention)
    revenue_saved = Column(Float, default=0.0)
    customers_saved = Column(Integer, default=0)
    churn_prevention_actions = Column(Integer, default=0)

    # Revenue created (expansion, leads)
    revenue_created = Column(Float, default=0.0)
    expansions_closed = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    expansion_actions = Column(Integer, default=0)

    # Efficiency gains
    efficiency_gain = Column(Float, default=0.0)  # Value of time saved
    hours_saved = Column(Float, default=0.0)
    tasks_automated = Column(Integer, default=0)

    # Total
    total_impact = Column(Float, default=0.0)  # revenue_saved + revenue_created + efficiency_gain

    # Cost of ForecastX
    forecastx_cost = Column(Float, default=0.0)  # How much user paid for ForecastX this period

    # ROI calculation
    net_value = Column(Float, default=0.0)  # total_impact - forecastx_cost
    roi_multiplier = Column(Float, default=0.0)  # total_impact / forecastx_cost
    roi_percentage = Column(Float, default=0.0)  # (net_value / forecastx_cost) * 100

    # Breakdown by impact type
    breakdown = Column(JSON, nullable=True)  # {"churn": 500K, "expansion": 150K, "efficiency": 50K}

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ROISummary {self.period} - ${self.net_value}>"


# ============================================================================
# PLAYBOOK PERFORMANCE (ROI per playbook)
# ============================================================================

class PlaybookROI(Base):
    """
    ROI metrics per playbook
    Which playbooks are generating most value?
    """
    __tablename__ = "playbook_roi"

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Time period
    period = Column(String(20), nullable=False)  # day, week, month
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Usage
    executions = Column(Integer, default=0)  # How many times playbook ran
    successful_outcomes = Column(Integer, default=0)  # How many succeeded
    success_rate = Column(Float, default=0.0)  # % success

    # Value generated
    total_value = Column(Float, default=0.0)
    value_per_execution = Column(Float, default=0.0)  # Average $ per run
    value_per_success = Column(Float, default=0.0)  # Average $ per successful outcome

    # Comparison
    rank_by_value = Column(Integer, nullable=True)  # #1, #2, #3 playbook by value
    rank_by_roi = Column(Integer, nullable=True)  # #1, #2, #3 playbook by ROI

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PlaybookROI playbook_id={self.playbook_id} - ${self.total_value}>"


# ============================================================================
# TOP CUSTOMERS BY IMPACT (Who saved/created most value)
# ============================================================================

class CustomerImpact(Base):
    """
    Per-customer impact summary
    Who's generating most value?
    """
    __tablename__ = "customer_impact"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    customer_id = Column(String(255), nullable=False)  # Salesforce account ID or internal ID
    customer_name = Column(String(255), nullable=False)
    customer_revenue = Column(Float, nullable=True)  # Annual revenue (ARR, etc.)

    # Impact
    revenue_saved = Column(Float, default=0.0)
    revenue_created = Column(Float, default=0.0)
    total_impact = Column(Float, default=0.0)

    # Timeline
    impact_start_date = Column(DateTime, nullable=True)
    last_impact_date = Column(DateTime, nullable=True)

    # Engagement
    playbooks_used = Column(Integer, default=0)
    actions_taken = Column(Integer, default=0)
    outcomes_confirmed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CustomerImpact {self.customer_name} - ${self.total_impact}>"


# ============================================================================
# ROI FORECAST (Predicted future impact)
# ============================================================================

class ROIForecast(Base):
    """
    Forecast future ROI based on current trends
    Help users plan ahead
    """
    __tablename__ = "roi_forecasts"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Forecast period
    forecast_month = Column(String(7), nullable=False)  # YYYY-MM
    forecast_start = Column(DateTime, nullable=False)
    forecast_end = Column(DateTime, nullable=False)

    # Predicted values
    forecasted_impact = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)  # 0-1, how confident?

    # Components
    churn_prevention_forecast = Column(Float, default=0.0)
    expansion_forecast = Column(Float, default=0.0)
    efficiency_forecast = Column(Float, default=0.0)

    # Comparison to historical
    historical_average = Column(Float, nullable=True)
    trend = Column(String(50), nullable=True)  # up, down, flat
    growth_rate = Column(Float, nullable=True)  # % month-over-month growth

    # Assumptions
    assumptions = Column(JSON, nullable=True)  # What did we assume to get this forecast?

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ROIForecast {self.forecast_month} - ${self.forecasted_impact}>"
