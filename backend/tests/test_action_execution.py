"""
Executing an action must actually deliver it.

The behaviour these tests exist to prevent: an action that reports success
without anything having been sent. Every case here checks both what the API
says and what the underlying channel was asked to do.
"""

import uuid

import pytest
import requests

from app.database import engine
from app.db.action_models import Action, ActionExecution, ActionStatus
from app.db.database import Base, SessionLocal
from app.services import channels


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def auth(client):
    email = f"exec-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email, "username": email.split("@")[0],
        "password": "Sup3rSecret!", "full_name": "Exec Tester",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}", "_email": email}


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def _make_action(db, client, auth, **overrides):
    """Insert an action belonging to the authenticated user's organization."""
    org_id = client.get("/api/user/home", headers=auth).json().get("organization_id")
    if org_id is None:
        from app.db.models_saas import User
        org_id = db.query(User).filter(User.email == auth["_email"]).first().organization_id

    fields = dict(
        organization_id=org_id,
        title="Call Acme today",
        description="Acme is at 91% churn risk.",
        action_type="email",
        priority="critical",
        status=ActionStatus.PENDING,
        entity_type="customer",
        entity_id="C1",
        entity_name="Acme",
        entity_email="acme@example.com",
        estimated_impact=50000.0,
        action_config={},
    )
    fields.update(overrides)
    action = Action(**fields)
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


# ---------------------------------------------------------------------------
# the core guarantee
# ---------------------------------------------------------------------------

def test_failed_delivery_is_not_reported_as_success(client, auth, db, monkeypatch):
    """An action whose channel fails must not end up completed."""
    action = _make_action(db, client, auth, action_type="slack")  # no Slack configured

    res = client.post("/api/actions/execute", headers=auth, json={"action_id": action.id})
    assert res.status_code == 200
    body = res.json()

    assert body["success"] is False
    assert body["executed"] == []
    assert len(body["failed"]) == 1
    assert body["failed"][0]["needs_setup"] is True
    assert "not connected" in body["failed"][0]["error"].lower()

    db.expire_all()
    assert db.query(Action).get(action.id).status == ActionStatus.FAILED

    execution = db.query(ActionExecution).filter(ActionExecution.action_id == action.id).one()
    assert execution.success is False
    assert execution.error_message


def test_unbuilt_channel_says_so_instead_of_pretending(client, auth, db):
    """We cannot place a phone call, and must not claim we did."""
    action = _make_action(db, client, auth, action_type="phone_call")

    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is False
    assert "isn't built yet" in body["failed"][0]["error"]

    db.expire_all()
    assert db.query(Action).get(action.id).status == ActionStatus.FAILED


# ---------------------------------------------------------------------------
# channels that really deliver
# ---------------------------------------------------------------------------

def test_email_action_sends_and_completes(client, auth, db, monkeypatch):
    sent = {}

    monkeypatch.setattr(channels.settings, "SMTP_USER", "bot@forecastx.test")
    monkeypatch.setattr(channels.settings, "SMTP_PASSWORD", "hunter2")
    monkeypatch.setattr(
        channels.EmailService, "send_email",
        staticmethod(lambda **kw: sent.update(kw) or True),
    )

    action = _make_action(db, client, auth)
    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is True, body
    assert sent["to_email"] == "acme@example.com"
    assert sent["subject"] == "Call Acme today"
    assert "<p>" in sent["html_content"]

    db.expire_all()
    refreshed = db.query(Action).get(action.id)
    assert refreshed.status == ActionStatus.COMPLETED
    assert refreshed.executed_at is not None
    assert refreshed.result["channel"] == "email"


def test_email_action_fails_when_smtp_rejects_it(client, auth, db, monkeypatch):
    """A refused send is a failure, even though SMTP is configured."""
    monkeypatch.setattr(channels.settings, "SMTP_USER", "bot@forecastx.test")
    monkeypatch.setattr(channels.settings, "SMTP_PASSWORD", "hunter2")
    monkeypatch.setattr(channels.EmailService, "send_email", staticmethod(lambda **kw: False))

    action = _make_action(db, client, auth)
    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is False
    assert "refused" in body["failed"][0]["error"]


def test_slack_action_posts_to_the_configured_webhook(client, auth, db, monkeypatch):
    posted = {}

    class FakeResponse:
        status_code = 200
        text = "ok"

    def fake_request(method, url, **kwargs):
        posted.update({"method": method, "url": url, "json": kwargs.get("json")})
        return FakeResponse()

    monkeypatch.setattr(requests, "request", fake_request)

    res = client.put("/api/integrations", headers=auth, json={
        "channel": "slack",
        "config": {"webhook_url": "https://hooks.slack.com/services/T/B/xxx"},
    })
    assert res.status_code == 200, res.text

    action = _make_action(db, client, auth, action_type="slack")
    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is True, body
    assert posted["url"] == "https://hooks.slack.com/services/T/B/xxx"
    assert "Call Acme today" in posted["json"]["text"]
    assert "$50,000 at stake" in posted["json"]["text"]


def test_webhook_action_posts_the_prediction_context(client, auth, db, monkeypatch):
    posted = {}

    class FakeResponse:
        status_code = 202
        text = "accepted"

    monkeypatch.setattr(requests, "request",
                        lambda method, url, **kw: (posted.update(kw.get("json") or {}), FakeResponse())[1])

    action = _make_action(db, client, auth, action_type="webhook",
                          action_config={"url": "https://example.com/hook",
                                         "risk_level": "critical", "score": 0.91})

    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is True, body
    assert posted["event"] == "forecastx.action"
    assert posted["customer"] == "Acme"
    assert posted["risk_level"] == "critical"


def test_task_action_assigns_a_real_owner(client, auth, db):
    action = _make_action(db, client, auth, action_type="task", entity_email=None)

    body = client.post("/api/actions/execute", headers=auth,
                       json={"action_id": action.id}).json()

    assert body["success"] is True, body

    db.expire_all()
    refreshed = db.query(Action).get(action.id)
    assert refreshed.assigned_to_id is not None
    assert refreshed.due_at is not None


# ---------------------------------------------------------------------------
# retries
# ---------------------------------------------------------------------------

def test_transient_failures_are_retried_but_rejections_are_not(monkeypatch):
    """5xx is worth another try; 400 means the request itself is wrong."""
    monkeypatch.setattr(channels.time, "sleep", lambda _s: None)

    attempts = {"n": 0}

    class Resp:
        def __init__(self, code):
            self.status_code = code
            self.text = "boom"

    def flaky(method, url, **kwargs):
        attempts["n"] += 1
        return Resp(200 if attempts["n"] == 3 else 503)

    monkeypatch.setattr(requests, "request", flaky)
    channels._post_with_retries("https://example.com", json_body={}, channel="Test")
    assert attempts["n"] == 3

    attempts["n"] = 0
    monkeypatch.setattr(requests, "request", lambda method, url, **kw: Resp(400))
    with pytest.raises(channels.ChannelError):
        channels._post_with_retries("https://example.com", json_body={}, channel="Test")
    assert attempts["n"] == 0  # not retried


# ---------------------------------------------------------------------------
# integrations API
# ---------------------------------------------------------------------------

def test_integrations_list_reports_what_needs_setup(client, auth):
    body = client.get("/api/integrations", headers=auth).json()
    by_channel = {i["channel"]: i for i in body["integrations"]}

    assert by_channel["slack"]["connected"] is False
    assert by_channel["slack"]["required_fields"] == ["webhook_url"]
    assert "email" in by_channel


def test_integration_rejects_a_non_https_url(client, auth):
    res = client.put("/api/integrations", headers=auth, json={
        "channel": "slack", "config": {"webhook_url": "http://insecure.example.com"},
    })
    assert res.status_code == 400
    assert "https://" in res.json()["detail"]


def test_saved_webhook_url_is_redacted_when_read_back(client, auth):
    client.put("/api/integrations", headers=auth, json={
        "channel": "webhook", "config": {"url": "https://example.com/very/secret/path/abcdef"},
    })
    body = client.get("/api/integrations", headers=auth).json()
    webhook = next(i for i in body["integrations"] if i["channel"] == "webhook")

    assert webhook["connected"] is True
    assert "abcdef" not in str(webhook["config"])


def test_failed_test_send_is_recorded(client, auth, monkeypatch):
    monkeypatch.setattr(channels.time, "sleep", lambda _s: None)
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: (_ for _ in ()).throw(requests.Timeout()))

    client.put("/api/integrations", headers=auth, json={
        "channel": "slack", "config": {"webhook_url": "https://hooks.slack.com/services/T/B/x"},
    })

    res = client.post("/api/integrations/slack/test", headers=auth)
    assert res.status_code == 400
    assert "timed out" in res.json()["detail"]

    body = client.get("/api/integrations", headers=auth).json()
    slack = next(i for i in body["integrations"] if i["channel"] == "slack")
    assert slack["last_test_ok"] is False
    assert slack["last_test_error"]
