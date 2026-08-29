"""
Per-organization delivery settings.

Sending a Slack message or posting to a webhook needs somewhere to keep the
destination. This is that place: one row per organization per channel.

Nothing here is a secret-management system, but `config` does hold credentials
-- a Slack incoming-webhook URL is enough to post into a customer's channel --
so it is encrypted at rest by EncryptedJSON, the same type connector
credentials use. Rows written before that change are still readable as
plaintext and get re-encrypted the next time they are saved.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.services.crypto import EncryptedJSON
from app.utils.time import utcnow


class Integration(Base):
    """Where a given channel should deliver for a given organization."""

    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("organization_id", "channel", name="uq_integration_org_channel"),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # "slack", "webhook", "salesforce", ...
    channel = Column(String(50), nullable=False, index=True)

    # Channel-specific settings, e.g. {"webhook_url": "https://hooks.slack.com/..."}
    config = Column(EncryptedJSON, nullable=False, default=dict)

    is_active = Column(Boolean, default=True)

    # Result of the last test send, so the settings page can show whether it works.
    last_tested_at = Column(DateTime, nullable=True)
    last_test_ok = Column(Boolean, nullable=True)
    last_test_error = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    organization = relationship("Organization")

    def __repr__(self):
        return f"<Integration org={self.organization_id} channel={self.channel}>"
