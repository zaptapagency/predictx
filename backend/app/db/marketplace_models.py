"""
ForecastX Marketplace Models
- Playbook: Shareable playbooks created by users
- PlaybookReview: Ratings & reviews from users
- PlaybookPurchase: Purchase history & licensing
- CreatorEarnings: Revenue tracking for creators
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

# ============================================================================
# PLAYBOOK STATUS
# ============================================================================

class PlaybookStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"

# ============================================================================
# PLAYBOOK MODEL (Shareable playbooks for marketplace)
# ============================================================================

class Playbook(Base):
    """
    User-created playbooks for marketplace
    Can be shared, purchased, and used by other organizations
    """
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Playbook info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)  # URL-friendly name
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # churn, expansion, fraud, etc
    use_case = Column(String(100), nullable=False)  # lead-scoring, churn-prediction, etc
    industry = Column(String(100), nullable=True)  # saas, ecommerce, fintech, etc

    # Pricing
    price_monthly = Column(Float, default=49.0)  # Monthly subscription price
    price_yearly = Column(Float, nullable=True)  # Yearly discount
    free = Column(Boolean, default=False)  # Free playbooks

    # Content
    configuration = Column(JSON, nullable=False)  # Playbook logic (trigger, actions, rules)
    icon = Column(String(255), nullable=True)  # Emoji or icon
    thumbnail_url = Column(String(500), nullable=True)  # Screenshot/preview image
    tags = Column(JSON, nullable=True)  # ['high-value', 'automated', 'proven']

    # Metrics
    downloads = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)

    # Status & publishing
    status = Column(String(50), default=PlaybookStatus.DRAFT)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    success_rate = Column(Float, nullable=True)  # e.g., 0.78 = 78% success
    typical_roi = Column(Float, nullable=True)  # e.g., 5.6 = 560% ROI
    setup_time_minutes = Column(Integer, nullable=True)  # How long to setup

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")
    reviews = relationship("PlaybookReview", back_populates="playbook", cascade="all, delete-orphan")
    purchases = relationship("PlaybookPurchase", back_populates="playbook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Playbook {self.name} by {self.creator.email}>"


# ============================================================================
# PLAYBOOK REVIEW MODEL (Ratings & reviews)
# ============================================================================

class PlaybookReview(Base):
    """
    User reviews and ratings for playbooks
    Helps other users decide if playbook is worth purchasing
    """
    __tablename__ = "playbook_reviews"

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    review_text = Column(Text, nullable=True)

    # Review insights
    ease_of_setup = Column(Integer, nullable=True)  # 1-5
    roi_achieved = Column(String(50), nullable=True)  # "exceeded", "met", "lower"
    would_recommend = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    helpful_count = Column(Integer, default=0)  # How many found this review helpful

    # Relationships
    playbook = relationship("Playbook", back_populates="reviews")
    user = relationship("User")

    def __repr__(self):
        return f"<PlaybookReview {self.rating}★ for {self.playbook.name}>"


# ============================================================================
# PLAYBOOK PURCHASE MODEL (Licensing & usage tracking)
# ============================================================================

class PlaybookPurchase(Base):
    """
    Track playbook purchases and active licenses
    Handles subscription management and access control
    """
    __tablename__ = "playbook_purchases"

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    purchased_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Purchase details
    stripe_subscription_id = Column(String(255), nullable=True)  # Stripe sub ID
    license_type = Column(String(50), default="monthly")  # monthly, yearly, lifetime
    price_paid = Column(Float, nullable=False)  # What they paid

    # Subscription status
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For yearly/lifetime
    cancelled_at = Column(DateTime, nullable=True)

    # Usage tracking
    times_run = Column(Integer, default=0)  # How many times playbook executed
    last_used_at = Column(DateTime, nullable=True)
    churn_saved = Column(Float, default=0.0)  # Revenue saved by using this playbook
    customers_affected = Column(Integer, default=0)  # How many customers impacted

    # Relationships
    playbook = relationship("Playbook", back_populates="purchases")
    organization = relationship("Organization")
    purchased_by = relationship("User")

    def __repr__(self):
        return f"<PlaybookPurchase {self.organization.name} → {self.playbook.name}>"


# ============================================================================
# CREATOR EARNINGS MODEL (Revenue tracking)
# ============================================================================

class CreatorEarnings(Base):
    """
    Track earnings for playbook creators
    ForecastX takes 30%, creator gets 70% of revenue
    """
    __tablename__ = "creator_earnings"

    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Revenue
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM format
    total_revenue = Column(Float, default=0.0)  # Total from all purchases
    creator_share = Column(Float, default=0.0)  # Creator's 70%
    forecastx_share = Column(Float, default=0.0)  # ForecastX's 30%

    # Breakdown
    purchases_count = Column(Integer, default=0)
    active_subscriptions = Column(Integer, default=0)
    churn_of_purchases = Column(Float, default=0.0)  # % of customers who cancelled

    # Payout
    payout_status = Column(String(50), default="pending")  # pending, processing, paid
    payout_date = Column(DateTime, nullable=True)
    stripe_transfer_id = Column(String(255), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CreatorEarnings {self.creator.email} - {self.month}: ${self.creator_share}>"


# ============================================================================
# MARKETPLACE ANALYTICS MODEL
# ============================================================================

class MarketplaceAnalytics(Base):
    """
    Platform-level marketplace metrics (updated daily)
    """
    __tablename__ = "marketplace_analytics"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow, index=True, unique=True)

    # Platform metrics
    total_playbooks = Column(Integer, default=0)
    active_playbooks = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    total_creators = Column(Integer, default=0)

    # Top performers
    top_playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=True)
    top_creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Trends
    new_playbooks_today = Column(Integer, default=0)
    new_purchases_today = Column(Integer, default=0)

    def __repr__(self):
        return f"<MarketplaceAnalytics {self.date.date()} - ${self.total_revenue}>"
