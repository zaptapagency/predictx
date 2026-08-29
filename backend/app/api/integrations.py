"""
Integrations API.

Where a user tells us how to reach them: a Slack incoming webhook, a default
webhook endpoint. Without this the delivery channels have no destination and
every Slack or webhook action fails as "not connected".
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.integration_models import Integration
from app.db.models_saas import User
from app.services.auth_service import get_current_user
from app.services.channels import ChannelError, test_integration
from app.utils.time import utcnow

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Channels a user can configure here. Email comes from server-side SMTP
# settings instead, and Salesforce reuses the Connectors credentials.
CONFIGURABLE = {
    "slack": {
        "label": "Slack",
        "required": ["webhook_url"],
        "help": "Create an incoming webhook at api.slack.com/messaging/webhooks and paste the URL.",
    },
    "webhook": {
        "label": "Webhook",
        "required": ["url"],
        "help": "We POST a JSON body to this URL when a webhook action runs.",
    },
}


class IntegrationUpsert(BaseModel):
    channel: str
    config: Dict[str, Any]
    is_active: bool = True


def _redact(channel: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """URLs are credentials here — show enough to recognise, not enough to reuse."""
    safe = {}
    for key, value in (config or {}).items():
        if isinstance(value, str) and ("url" in key.lower() or "token" in key.lower()):
            safe[key] = f"{value[:24]}…" if len(value) > 24 else "configured"
        else:
            safe[key] = value
    return safe


@router.get("")
def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Every channel, whether it's set up, and how to set it up if not."""
    org_id = current_user.organization_id
    rows = {
        i.channel: i
        for i in db.query(Integration).filter(Integration.organization_id == org_id).all()
    }

    channels = []
    for channel, meta in CONFIGURABLE.items():
        row = rows.get(channel)
        channels.append({
            "channel": channel,
            "label": meta["label"],
            "help": meta["help"],
            "required_fields": meta["required"],
            "connected": bool(row and row.is_active),
            "config": _redact(channel, row.config) if row else {},
            "last_tested_at": row.last_tested_at if row else None,
            "last_test_ok": row.last_test_ok if row else None,
            "last_test_error": row.last_test_error if row else None,
        })

    # Email is configured by the operator, not the end user, so report its
    # real state rather than offering a form that would not help.
    channels.append({
        "channel": "email",
        "label": "Email",
        "help": "Configured server-side via SMTP_USER / SMTP_PASSWORD.",
        "required_fields": [],
        "connected": bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
        "config": {},
        "last_tested_at": None,
        "last_test_ok": None,
        "last_test_error": None,
    })

    return {"integrations": channels}


@router.put("")
def upsert_integration(
    payload: IntegrationUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect or update a channel."""
    meta = CONFIGURABLE.get(payload.channel)
    if not meta:
        raise HTTPException(
            status_code=400,
            detail=f"'{payload.channel}' is not configurable here. Options: {', '.join(CONFIGURABLE)}",
        )

    missing = [f for f in meta["required"] if not (payload.config or {}).get(f)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required field(s): {', '.join(missing)}")

    for field in meta["required"]:
        value = payload.config[field]
        if "url" in field and not str(value).startswith("https://"):
            raise HTTPException(status_code=400, detail=f"'{field}' must be an https:// URL.")

    org_id = current_user.organization_id
    row = db.query(Integration).filter(
        Integration.organization_id == org_id,
        Integration.channel == payload.channel,
    ).first()

    if row is None:
        row = Integration(organization_id=org_id, channel=payload.channel)
        db.add(row)

    row.config = payload.config
    row.is_active = payload.is_active
    # Settings changed, so any previous test result no longer describes them.
    row.last_tested_at = None
    row.last_test_ok = None
    row.last_test_error = None
    db.commit()

    return {"success": True, "channel": payload.channel,
            "message": f"{meta['label']} saved. Send a test to confirm it works."}


@router.post("/{channel}/test")
def send_test(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a real test message, and remember whether it worked."""
    org_id = current_user.organization_id
    row = db.query(Integration).filter(
        Integration.organization_id == org_id,
        Integration.channel == channel,
    ).first()

    try:
        result = test_integration(db, org_id, channel)
    except ChannelError as e:
        if row:
            row.last_tested_at = utcnow()
            row.last_test_ok = False
            row.last_test_error = str(e)[:500]
            db.commit()
        raise HTTPException(status_code=400, detail=str(e))

    if row:
        row.last_tested_at = utcnow()
        row.last_test_ok = True
        row.last_test_error = None
        db.commit()

    return {"success": True, "message": result.detail}


@router.delete("/{channel}")
def disconnect(
    channel: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect a channel."""
    row = db.query(Integration).filter(
        Integration.organization_id == current_user.organization_id,
        Integration.channel == channel,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"'{channel}' is not connected.")

    db.delete(row)
    db.commit()
    return {"success": True, "message": f"Disconnected {channel}."}
