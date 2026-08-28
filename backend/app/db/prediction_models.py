"""
Prediction models and tracking
Stores model definitions, predictions, outcomes, and feedback
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class ModelType(str, enum.Enum):
    """Types of prediction models"""
    CHURN = "churn"
    OPPORTUNITY = "opportunity"
    EXPANSION = "expansion"
    HEALTH = "health"
    NPS = "nps"


class ModelStatus(str, enum.Enum):
    """Model status"""
    DRAFT = "draft"
    TRAINING = "training"
    ACTIVE = "active"
    ARCHIVED = "archived"
    FAILED = "failed"


class OutcomeType(str, enum.Enum):
    """Types of outcomes models predict"""
    CHURN = "churn"
    EXPANSION = "expansion"
    RENEWAL = "renewal"
    UPGRADE = "upgrade"
    NPS = "nps"


class Model(Base):
    """
    ML model definition and metadata
    """
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    model_type = Column(Enum(ModelType), nullable=False)
    description = Column(Text)

    # Model configuration
    status = Column(Enum(ModelStatus), default=ModelStatus.DRAFT)
    version = Column(Integer, default=1)
    algorithm = Column(String(100))  # "logistic_regression", "xgboost", "random_forest"

    # Features used
    features = Column(JSON)  # List of feature names
    feature_importance = Column(JSON)  # {feature_name: importance_score}

    # Training metadata
    training_data_start = Column(DateTime)
    training_data_end = Column(DateTime)
    training_record_count = Column(Integer)
    training_date = Column(DateTime)

    # Performance metrics on holdout test set
    accuracy = Column(Float)  # For classification
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)

    rmse = Column(Float)  # For regression
    r2_score = Column(Float)

    # Drift detection
    is_drifted = Column(Boolean, default=False)
    last_checked_drift = Column(DateTime)

    # Predictions using this model
    predictions = relationship("Prediction", back_populates="model")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))


class Prediction(Base):
    """
    Individual prediction for a customer
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)

    customer_id = Column(String(255), nullable=False)

    # Prediction value
    score = Column(Float, nullable=False)  # 0-1 for classification, any for regression
    confidence = Column(Float)  # 0-1 confidence in prediction
    percentile = Column(Float)  # Customer's percentile vs other customers (0-100)

    # Contributing factors
    contributing_factors = Column(JSON)  # [{feature, value, contribution}]
    top_factors = Column(JSON)  # Top 3-5 factors driving this prediction

    # Risk/opportunity categorization
    risk_level = Column(String(50))  # "low", "medium", "high", "critical"
    recommended_action = Column(String(255))  # "reach_out", "cross_sell", "renew", etc

    # Metadata
    predicted_at = Column(DateTime, default=datetime.utcnow)
    features_used = Column(JSON)  # Snapshot of features that went into prediction

    # Link to workflow
    triggered_workflows = Column(JSON)  # List of workflow IDs triggered by this prediction

    # Relationships
    model = relationship("Model", back_populates="predictions")
    outcome = relationship("Outcome", back_populates="prediction", uselist=False)


class Outcome(Base):
    """
    Actual outcome that occurred after prediction
    Used for model evaluation and feedback
    """
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False, unique=True)

    # What actually happened
    outcome_type = Column(Enum(OutcomeType), nullable=False)  # churn, expansion, renewal, etc
    outcome_value = Column(Float)  # e.g., MRR at time of outcome

    # Timing
    predicted_at = Column(DateTime)  # When prediction was made
    occurred_at = Column(DateTime)  # When outcome actually happened

    # Was prediction correct?
    was_correct = Column(Boolean)  # Did prediction match reality?

    # Additional context
    contributing_factors = Column(JSON)  # What actually drove the outcome?
    notes = Column(Text)  # Manual notes about why prediction was/wasn't accurate

    created_at = Column(DateTime, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="outcome")


class Feature(Base):
    """
    Definition of a feature used in models
    """
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    name = Column(String(255), nullable=False)  # "customer_mrr", "account_age_days"
    description = Column(Text)
    feature_type = Column(String(50))  # "numeric", "categorical", "date", "boolean"

    # Source
    source_table = Column(String(100))  # "customer_data", "accounts", "billing"
    source_field = Column(String(255))  # "mrr", "created_at"

    # Computation
    computation = Column(Text)  # "MRR from last 30 days", "Days since created"

    # Statistics
    mean = Column(Float)
    median = Column(Float)
    stddev = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    null_percentage = Column(Float)  # % of values that are null

    # Used in models
    models_using = Column(JSON)  # List of model IDs using this feature

    created_at = Column(DateTime, default=datetime.utcnow)


class ModelPerformance(Base):
    """
    Track model performance over time for drift detection
    """
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    period_start = Column(DateTime)  # e.g., start of week
    period_end = Column(DateTime)

    predictions_made = Column(Integer)  # How many predictions in this period

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)

    # Drift indicators
    prediction_drift = Column(Float)  # How much did prediction distribution change?
    feature_drift = Column(Float)  # How much did feature values change?

    is_drifted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class PredictionFeedback(Base):
    """
    User feedback on predictions
    "This prediction was helpful/not helpful"
    """
    __tablename__ = "prediction_feedback"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # User evaluation
    helpful = Column(Boolean)  # Was the prediction useful?
    accurate = Column(Boolean)  # Was the prediction accurate?

    # User annotations
    comments = Column(Text)
    tagged_factors = Column(JSON)  # Which factors actually mattered?

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingRun(Base):
    """
    Record of a model training execution
    """
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    status = Column(String(50))  # "running", "success", "failed"

    # Data used
    training_start = Column(DateTime)
    training_end = Column(DateTime)
    training_records = Column(Integer)

    # Training process
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Results
    test_accuracy = Column(Float)
    test_precision = Column(Float)
    test_recall = Column(Float)
    test_f1 = Column(Float)

    # Config
    hyperparameters = Column(JSON)  # {learning_rate, max_depth, etc}
    training_config = Column(JSON)  # {epochs, batch_size, etc}

    error_message = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class ModelArtifact(Base):
    """
    Serialized trained model, kept out of the Model row so the metadata
    table stays queryable. One artifact per model.
    """
    __tablename__ = "model_artifacts"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # base64-encoded pickle of {"estimator": ..., "scaler": ..., "features": [...]}
    payload = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
