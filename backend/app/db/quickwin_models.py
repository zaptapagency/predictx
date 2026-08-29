"""
Quick Wins Models
Pre-configured 1-click actions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base
from app.utils.time import utcnow


class QuickWin(Base):
    """
    Pre-configured 1-click actions
    Execute common workflows instantly
    """
    __tablename__ = "quick_wins"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Quick win details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)

    # Action configuration
    action_type = Column(String(50), nullable=False)  # bulk_email, bulk_call, bulk_task
    action_config = Column(JSON, nullable=False)  # What to execute

    # Targeting
    target_criteria = Column(JSON, nullable=False)  # Who to target (at-risk customers, high-value, etc)
    estimated_target_count = Column(Integer, nullable=True)

    # Impact
    estimated_impact = Column(Float, nullable=True)
    success_probability = Column(Float, nullable=True)

    # Playbook association
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # Display order

    created_at = Column(DateTime, default=utcnow)

    # Relationships
    organization = relationship("Organization")

    def __repr__(self):
        return f"<QuickWin {self.title}>"


class QuickWinExecution(Base):
    """
    Track when quick wins are executed
    """
    __tablename__ = "quick_win_executions"

    id = Column(Integer, primary_key=True)
    quick_win_id = Column(Integer, ForeignKey("quick_wins.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Execution details
    target_count = Column(Integer, nullable=False)  # How many entities targeted
    success_count = Column(Integer, nullable=False)  # How many succeeded
    failed_count = Column(Integer, nullable=False)

    # Results
    actual_impact = Column(Float, nullable=True)
    execution_duration = Column(Float, nullable=True)  # seconds

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed

    created_at = Column(DateTime, default=utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    quick_win = relationship("QuickWin")
    user = relationship("User")

    def __repr__(self):
        return f"<QuickWinExecution status={self.status}>"
