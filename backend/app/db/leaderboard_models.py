"""
Leaderboard & Achievement Models
Gamification to drive engagement and competition
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base
from app.utils.time import utcnow

# ============================================================================
# ACHIEVEMENT TYPES & BADGES
# ============================================================================

class AchievementType(str, enum.Enum):
    CHURN_SAVER = "churn_saver"           # Saved N customers from churning
    EXPANSION_KING = "expansion_king"     # Closed N expansions
    LEAD_CONVERTER = "lead_converter"     # Converted N leads
    SPEED_RACER = "speed_racer"           # Fastest to first action
    ACCURACY_EXPERT = "accuracy_expert"   # Highest prediction accuracy
    TEAM_PLAYER = "team_player"           # Invited N team members
    STREAK_MASTER = "streak_master"       # X-day action streak
    TOP_PERFORMER = "top_performer"       # #1 on leaderboard
    REVENUE_MAKER = "revenue_maker"       # Generated $X revenue
    ACTION_TAKER = "action_taker"         # Took N actions
    EFFICIENCY_MASTER = "efficiency_master"  # Automated N hours

# ============================================================================
# LEADERBOARD ENTRY MODEL
# ============================================================================

class LeaderboardEntry(Base):
    """
    User's position on leaderboard for a time period
    Updated daily/weekly/monthly
    """
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Time period
    period = Column(String(20), nullable=False)  # day, week, month, all_time
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Ranking
    rank = Column(Integer, nullable=False, index=True)  # 1, 2, 3, etc
    rank_previous = Column(Integer, nullable=True)  # Previous rank (for trending)
    rank_change = Column(Integer, nullable=True)  # +2, -1, etc (trending)

    # Primary metric (changes based on period)
    score = Column(Float, default=0.0)
    score_type = Column(String(50), default="points")  # points, revenue, actions, etc

    # Detailed metrics
    customers_saved = Column(Integer, default=0)
    expansions_closed = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    actions_taken = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0.0)
    predictions_made = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)  # 0-1

    # Streaks
    action_streak = Column(Integer, default=0)  # Days in a row with action
    action_streak_start = Column(DateTime, nullable=True)

    # Metadata
    is_top_performer = Column(Boolean, default=False)  # Top 10%
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    organization = relationship("Organization")
    user = relationship("User")

    def __repr__(self):
        return f"<LeaderboardEntry user_id={self.user_id} rank={self.rank}>"


# ============================================================================
# ACHIEVEMENT MODEL
# ============================================================================

class Achievement(Base):
    """
    Badges/achievements earned by users
    Milestone-based (saved 10 customers, 30-day streak, etc)
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Achievement type
    achievement_type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # "Churn Saver Champion"
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon
    badge_color = Column(String(50), nullable=True)  # gold, silver, bronze, etc

    # Threshold/requirement
    threshold = Column(Float, nullable=True)  # Had to save 10 customers
    metric_type = Column(String(50), nullable=True)  # customers_saved, revenue, etc

    # Rarity
    rarity = Column(String(50), nullable=True)  # common, rare, epic, legendary
    unlock_percentage = Column(Float, nullable=True)  # What % of users have this?

    # Earned at
    earned_at = Column(DateTime, default=utcnow, index=True)
    featured = Column(Boolean, default=False)  # Display prominently

    # Leaderboard impact
    points_awarded = Column(Integer, default=50)  # Points for achieving this

    created_at = Column(DateTime, default=utcnow)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<Achievement {self.name}>"


# ============================================================================
# USER STATS MODEL
# ============================================================================

class UserStats(Base):
    """
    Detailed user performance stats
    Used for leaderboard calculations and personalization
    """
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # All-time stats
    total_predictions = Column(Integer, default=0)
    total_actions = Column(Integer, default=0)
    total_customers_saved = Column(Integer, default=0)
    total_expansions_closed = Column(Integer, default=0)
    total_leads_converted = Column(Integer, default=0)
    total_revenue_generated = Column(Float, default=0.0)

    # Current stats
    this_month_actions = Column(Integer, default=0)
    this_week_actions = Column(Integer, default=0)
    today_actions = Column(Integer, default=0)

    # Quality stats
    prediction_accuracy = Column(Float, default=0.0)  # % of predictions correct
    action_success_rate = Column(Float, default=0.0)  # % of actions that succeeded
    avg_revenue_per_action = Column(Float, default=0.0)

    # Engagement
    days_active = Column(Integer, default=0)  # Days user has done something
    current_streak = Column(Integer, default=0)  # Current action streak
    longest_streak = Column(Integer, default=0)  # Best streak ever
    last_action_at = Column(DateTime, nullable=True)
    first_action_at = Column(DateTime, nullable=True)

    # Rank
    current_rank = Column(Integer, nullable=True)  # On leaderboard
    rank_percentile = Column(Float, nullable=True)  # Top X%

    # Badges
    total_achievements = Column(Integer, default=0)
    featured_achievements = Column(Integer, default=0)

    # Updated
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<UserStats user_id={self.user_id} rank={self.current_rank}>"


# ============================================================================
# ACTIVITY STREAM (For celebratory feed)
# ============================================================================

class UserActivity(Base):
    """
    Log of significant user actions (for activity feed)
    Shows what team members are accomplishing
    """
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Activity type
    activity_type = Column(String(50), nullable=False)  # customer_saved, expansion_closed, etc
    activity_title = Column(String(255), nullable=False)  # "Saved Acme Corp"
    activity_description = Column(Text, nullable=True)  # Details

    # Metrics
    revenue_impact = Column(Float, nullable=True)
    customers_affected = Column(Integer, nullable=True)
    entity_name = Column(String(255), nullable=True)  # Customer/company name

    # Visibility
    is_public = Column(Boolean, default=True)  # Show on activity feed
    is_celebratory = Column(Boolean, default=False)  # High-impact action worthy of celebration

    # Reactions
    reaction_count = Column(Integer, default=0)  # Emoji reactions (👏, ❤️, 🔥, etc)

    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    user = relationship("User")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<UserActivity {self.activity_title}>"
