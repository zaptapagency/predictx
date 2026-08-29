"""
Real delivery for actions and workflow steps.

Everything that claims to contact the outside world goes through here, so
there is exactly one place that knows how to send a message and exactly one
definition of what "it worked" means.

The rule this module exists to enforce: a channel that did not deliver must
raise. Callers mark work complete based on that, so silently returning
success — the previous behaviour — made every action and playbook report a
delivery that never happened.

Channels that genuinely cannot run in this deployment (no credentials, no
integration configured) raise ChannelUnavailable, which is a distinct, clearly
worded failure rather than a fake success.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.db.integration_models import Integration
from app.services.email_service import EmailService
from app.utils import setup_logger
from app.utils.time import utcnow

logger = setup_logger(__name__)

HTTP_TIMEOUT = 15  # seconds
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 3)  # waits between attempt 1->2 and 2->3

# Status codes worth trying again: the request was fine, the far end wasn't.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ChannelError(Exception):
    """Delivery was attempted and failed."""


class ChannelUnavailable(ChannelError):
    """
    The channel cannot run at all — not configured, or not implemented here.

    Separate from ChannelError so the UI can tell "set this up" apart from
    "we tried and it broke".
    """


@dataclass
class DeliveryResult:
    """What actually happened, for the audit log."""

    channel: str
    detail: str                                    # human-readable, shown to the user
    external_id: Optional[str] = None              # id from the far end, when there is one
    response_data: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def get_integration(db: Session, org_id: int, channel: str) -> Optional[Integration]:
    return db.query(Integration).filter(
        Integration.organization_id == org_id,
        Integration.channel == channel,
        Integration.is_active.is_(True),
    ).first()


def _post_with_retries(url: str, *, json_body: Any = None, headers: Dict[str, str] = None,
                       method: str = "POST", channel: str = "webhook") -> requests.Response:
    """
    Send an HTTP request, retrying only failures that might succeed next time.

    A 4xx (other than 429) means the request itself is wrong; retrying it just
    wastes time and, for anything that reaches a customer, risks duplicates.
    """
    last_error = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.request(
                method, url, json=json_body, headers=headers or {}, timeout=HTTP_TIMEOUT
            )
        except requests.Timeout:
            last_error = f"timed out after {HTTP_TIMEOUT}s"
        except requests.RequestException as e:
            last_error = f"could not reach {url}: {e}"
        else:
            if response.status_code < 400:
                return response
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
            if response.status_code not in RETRYABLE_STATUS:
                raise ChannelError(f"{channel} rejected the request — {last_error}")

        if attempt < MAX_ATTEMPTS - 1:
            time.sleep(BACKOFF_SECONDS[attempt])

    raise ChannelError(f"{channel} delivery failed after {MAX_ATTEMPTS} attempts — {last_error}")


# ---------------------------------------------------------------------------
# channels
# ---------------------------------------------------------------------------

def deliver_email(db: Session, org_id: int, *, to: str, subject: str,
                  body_html: str, body_text: str = "") -> DeliveryResult:
    """Send a real email over SMTP."""
    if not to:
        raise ChannelError("No recipient email address on this record.")
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise ChannelUnavailable(
            "Email is not configured. Set SMTP_USER and SMTP_PASSWORD to send mail."
        )

    sent = EmailService.send_email(
        to_email=to, subject=subject, html_content=body_html, text_content=body_text
    )
    if not sent:
        raise ChannelError(f"SMTP server refused the message to {to}.")

    return DeliveryResult(channel="email", detail=f"Email sent to {to}.",
                          response_data={"to": to, "subject": subject})


def deliver_slack(db: Session, org_id: int, *, text: str,
                  blocks: Any = None, webhook_url: str = None) -> DeliveryResult:
    """
    Post to Slack via an incoming webhook.

    Incoming webhooks are used rather than a bot token because they need no
    OAuth flow and no extra dependency: the user pastes one URL and it works.
    """
    if not webhook_url:
        integration = get_integration(db, org_id, "slack")
        webhook_url = (integration.config or {}).get("webhook_url") if integration else None

    if not webhook_url:
        raise ChannelUnavailable(
            "Slack is not connected. Add a Slack incoming webhook URL in Integrations."
        )

    payload: Dict[str, Any] = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    _post_with_retries(webhook_url, json_body=payload, channel="Slack")
    return DeliveryResult(channel="slack", detail="Posted to Slack.",
                          response_data={"text": text})


def deliver_webhook(db: Session, org_id: int, *, payload: Dict[str, Any],
                    url: str = None, method: str = "POST",
                    headers: Dict[str, str] = None) -> DeliveryResult:
    """POST a JSON payload to a customer-supplied endpoint."""
    if not url:
        integration = get_integration(db, org_id, "webhook")
        config = (integration.config or {}) if integration else {}
        url = config.get("url")
        headers = headers or config.get("headers")

    if not url:
        raise ChannelUnavailable(
            "No webhook URL. Set one on the action, or add a default in Integrations."
        )

    response = _post_with_retries(url, json_body=payload, headers=headers,
                                  method=method, channel="Webhook")
    return DeliveryResult(
        channel="webhook",
        detail=f"Webhook returned {response.status_code}.",
        external_id=str(response.status_code),
        response_data={"status_code": response.status_code, "body": response.text[:500]},
    )


def deliver_salesforce_task(db: Session, org_id: int, *, subject: str, description: str,
                            priority: str = "High", account_id: str = None,
                            contact_id: str = None) -> DeliveryResult:
    """
    Create a Task in Salesforce using the org's existing Salesforce connection.

    Reuses the credentials already stored for data sync rather than asking for
    a second set. NOTE: this path has not been exercised against a live
    Salesforce org — it fails loudly rather than silently, but treat the first
    real send as a test.
    """
    from app.connectors.salesforce_connector import SalesforceConnector
    from app.db.connector_models import DataConnection

    connection = db.query(DataConnection).filter(
        DataConnection.organization_id == org_id,
        DataConnection.connector_type == "salesforce",
    ).first()

    if not connection:
        raise ChannelUnavailable(
            "No Salesforce connection. Connect Salesforce under Connectors first."
        )

    connector = SalesforceConnector(connection.config or {}, connection.credentials or {})
    instance_url = (connection.config or {}).get("instance_url", "").rstrip("/")
    if not instance_url:
        raise ChannelUnavailable("The Salesforce connection has no instance_url configured.")

    body = {"Subject": subject, "Description": description,
            "Priority": priority, "Status": "Open"}
    if contact_id:
        body["WhoId"] = contact_id
    if account_id:
        body["WhatId"] = account_id

    response = _post_with_retries(
        f"{instance_url}/services/data/v58.0/sobjects/Task",
        json_body=body, headers=connector._get_headers(), channel="Salesforce",
    )
    record_id = (response.json() or {}).get("id")
    return DeliveryResult(channel="salesforce", detail=f"Created Salesforce task {record_id}.",
                          external_id=record_id, response_data={"id": record_id})


def deliver_unsupported(channel: str) -> Callable[..., DeliveryResult]:
    """
    A channel we advertise but have not built.

    It raises rather than no-ops on purpose: a user who schedules a meeting
    should be told we cannot schedule it, not shown a green checkmark.
    """
    def _raise(*_args, **_kwargs) -> DeliveryResult:
        raise ChannelUnavailable(
            f"{channel.replace('_', ' ').title()} delivery isn't built yet. "
            f"Use email, Slack, a webhook, or an internal task instead."
        )
    return _raise


def test_integration(db: Session, org_id: int, channel: str) -> DeliveryResult:
    """Send a harmless message so the user can confirm a channel really works."""
    stamp = utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if channel == "slack":
        return deliver_slack(db, org_id, text=f"✅ ForecastX test message ({stamp}).")
    if channel == "webhook":
        return deliver_webhook(db, org_id, payload={"event": "forecastx.test", "sent_at": stamp})
    if channel == "email":
        raise ChannelUnavailable(
            "Email has no default recipient to test against. Execute an action to send one."
        )
    raise ChannelUnavailable(f"No test available for '{channel}'.")
