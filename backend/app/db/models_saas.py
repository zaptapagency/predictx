from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text, Enum, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    """User accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    avatar_url = Column(String, nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Organization
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    subscriptions = relationship("Subscription", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")


class Organization(Base):
    """Organizations/Teams for multi-tenant"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Settings
    stripe_customer_id = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization", foreign_keys="[User.organization_id]")
    subscriptions = relationship("Subscription", back_populates="organization")


class SubscriptionTier(enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Subscription(Base):
    """Subscription management"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)

    # User/Organization
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)

    # Subscription details
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    stripe_price_id = Column(String, nullable=True)

    # Status
    status = Column(String, default="active")  # active, past_due, canceled, expired

    # Dates
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Usage limits
    monthly_predictions_limit = Column(Integer, default=0)  # 0 = unlimited
    api_calls_limit = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    organization = relationship("Organization", back_populates="subscriptions")


class Invoice(Base):
    """Billing invoices"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Invoice details
    stripe_invoice_id = Column(String, unique=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    # Amount
    amount = Column(Numeric(precision=10, scale=2))
    currency = Column(String, default="usd")

    # Status
    status = Column(String)  # draft, sent, paid, open, void, uncollectible

    # Dates
    invoice_date = Column(DateTime)
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)

    # PDF
    invoice_pdf_url = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="invoices")


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Key details
    name = Column(String)
    key_hash = Column(String, unique=True, index=True)  # Hashed for security
    prefix = Column(String)  # First 8 chars for display

    # Permissions
    permissions = Column(JSON, default={})

    # Usage
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")


class UsageLog(Base):
    """Track API usage and predictions"""
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Action
    action = Column(String)  # prediction, api_call, file_upload, etc.
    endpoint = Column(String, nullable=True)

    # Details
    vertical = Column(String, nullable=True)
    prediction_type = Column(String, nullable=True)

    # Cost/Usage
    tokens_used = Column(Integer, default=0)
    cost = Column(Numeric(precision=10, scale=4), default=0)

    # Response
    status_code = Column(Integer)
    response_time_ms = Column(Integer)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_logs")


class PasswordResetToken(Base):
    """Password reset tokens"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Token
    token_hash = Column(String, unique=True, index=True)

    # Status
    is_used = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class PredictionLog(Base):
    """Store individual predictions"""
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Prediction details
    vertical = Column(String)
    prediction_type = Column(String)
    features = Column(JSON)

    # Results
    prediction = Column(Float)
    confidence = Column(Float)
    explanation = Column(JSON, nullable=True)
    recommendation = Column(String, nullable=True)

    # Model
    model_version = Column(String)
    inference_time_ms = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="prediction_logs")


User.prediction_logs = relationship("PredictionLog", back_populates="user")
