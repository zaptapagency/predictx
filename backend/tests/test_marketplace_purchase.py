"""
Buying a playbook must actually take money.

The behaviour these tests exist to prevent: access granted, and the creator
credited, for a payment that was never collected.
"""

import uuid

import pytest
import stripe

from app.database import engine
from app.api import marketplace
from app.config import settings
from app.db.database import Base, SessionLocal
from app.db.marketplace_models import (
    Playbook, PlaybookPurchase, CreatorEarnings, PlaybookStatus
)
from app.db.models_saas import User


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def auth(client):
    email = f"buyer-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email, "username": email.split("@")[0],
        "password": "Sup3rSecret!", "full_name": "Playbook Buyer",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}", "_email": email}


def _org_id(db, auth):
    return db.query(User).filter(User.email == auth["_email"]).first().organization_id


def _make_playbook(db, auth, price=99.0, free=False):
    """A published playbook owned by a separate creator organization."""
    creator = db.query(User).filter(User.email == auth["_email"]).first()
    slug = f"pb-{uuid.uuid4().hex[:10]}"
    playbook = Playbook(
        organization_id=creator.organization_id,
        creator_id=creator.id,
        name="Churn Rescue",
        slug=slug,
        description="Rescue at-risk accounts",
        category="churn",
        use_case="churn-prediction",
        price_monthly=price,
        free=free,
        configuration={"steps": []},
        status=PlaybookStatus.PUBLISHED,
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    return playbook


def _purchase(db, playbook_id, org_id):
    return db.query(PlaybookPurchase).filter(
        PlaybookPurchase.playbook_id == playbook_id,
        PlaybookPurchase.organization_id == org_id,
    ).first()


@pytest.fixture
def stripe_key(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_API_KEY", "sk_test_fake")


class _FakeSession(dict):
    """Stripe objects support attribute access as well as mapping access."""
    def __getattr__(self, item):
        return self[item]


def test_paid_purchase_is_pending_until_webhook_confirms(client, db, auth, monkeypatch, stripe_key):
    playbook = _make_playbook(db, auth)
    org_id = _org_id(db, auth)

    created = {}

    def fake_create(**kwargs):
        created.update(kwargs)
        return _FakeSession(id="cs_test_1", url="https://checkout.stripe.test/cs_test_1")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    res = client.post(f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "pending"
    assert body["checkout_url"] == "https://checkout.stripe.test/cs_test_1"
    # Stripe was asked for the real amount, in cents.
    assert created["line_items"][0]["price_data"]["unit_amount"] == 9900

    purchase = _purchase(db, playbook.id, org_id)
    assert purchase.payment_status == "pending"
    assert purchase.is_active is False

    # No access, no revenue yet.
    detail = client.get(f"/api/marketplace/playbooks/{playbook.slug}", headers=auth)
    assert detail.json()["has_purchased"] is False
    db.refresh(playbook)
    assert playbook.total_revenue == 0.0

    # Stripe confirms payment.
    marketplace.confirm_marketplace_checkout(db, {
        "payment_status": "paid",
        "payment_intent": "pi_test_1",
        "metadata": {"purchase_id": str(purchase.id)},
    })

    db.refresh(purchase)
    db.refresh(playbook)
    assert purchase.payment_status == "paid"
    assert purchase.is_active is True
    assert purchase.stripe_payment_intent_id == "pi_test_1"
    assert playbook.total_revenue == 99.0
    assert playbook.downloads == 1

    earnings = db.query(CreatorEarnings).filter(
        CreatorEarnings.playbook_id == playbook.id
    ).first()
    assert earnings is not None
    assert earnings.creator_share == pytest.approx(69.3)

    detail = client.get(f"/api/marketplace/playbooks/{playbook.slug}", headers=auth)
    assert detail.json()["has_purchased"] is True


def test_declined_card_does_not_grant_access(client, db, auth, monkeypatch, stripe_key):
    playbook = _make_playbook(db, auth)
    org_id = _org_id(db, auth)

    def fake_create(**kwargs):
        raise stripe.error.CardError("Your card was declined.", param=None, code="card_declined")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    res = client.post(f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth)
    assert res.status_code == 402
    assert "declined" in res.json()["detail"].lower()

    purchase = _purchase(db, playbook.id, org_id)
    assert purchase.payment_status == "failed"
    assert purchase.is_active is False

    db.refresh(playbook)
    assert playbook.total_revenue == 0.0
    assert client.get(
        f"/api/marketplace/playbooks/{playbook.slug}", headers=auth
    ).json()["has_purchased"] is False


def test_stripe_api_error_does_not_grant_access(client, db, auth, monkeypatch, stripe_key):
    playbook = _make_playbook(db, auth)
    org_id = _org_id(db, auth)

    def fake_create(**kwargs):
        raise stripe.error.APIConnectionError("stripe is down")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(fake_create))

    res = client.post(f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth)
    assert res.status_code == 502

    purchase = _purchase(db, playbook.id, org_id)
    assert purchase.payment_status == "failed"
    assert purchase.is_active is False
    db.refresh(playbook)
    assert playbook.total_revenue == 0.0


def test_unconfigured_stripe_never_grants_playbook_for_free(client, db, auth, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_API_KEY", "")
    playbook = _make_playbook(db, auth)
    org_id = _org_id(db, auth)

    res = client.post(f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth)
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"].lower()

    assert _purchase(db, playbook.id, org_id) is None
    db.refresh(playbook)
    assert playbook.total_revenue == 0.0
    assert client.get(
        f"/api/marketplace/playbooks/{playbook.slug}", headers=auth
    ).json()["has_purchased"] is False


def test_unpaid_checkout_session_does_not_grant_access(client, db, auth, monkeypatch, stripe_key):
    playbook = _make_playbook(db, auth)
    org_id = _org_id(db, auth)

    monkeypatch.setattr(
        stripe.checkout.Session, "create",
        staticmethod(lambda **kw: _FakeSession(id="cs_test_2", url="https://checkout.stripe.test/2")),
    )
    assert client.post(
        f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth
    ).status_code == 200

    purchase = _purchase(db, playbook.id, org_id)
    granted = marketplace.confirm_marketplace_checkout(db, {
        "payment_status": "unpaid",
        "metadata": {"purchase_id": str(purchase.id)},
    })

    assert granted is False
    db.refresh(purchase)
    db.refresh(playbook)
    assert purchase.payment_status == "failed"
    assert purchase.is_active is False
    assert playbook.total_revenue == 0.0


def test_free_playbook_works_without_stripe(client, db, auth, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_API_KEY", "")

    def explode(**kwargs):
        raise AssertionError("Stripe must not be called for a free playbook")

    monkeypatch.setattr(stripe.checkout.Session, "create", staticmethod(explode))

    playbook = _make_playbook(db, auth, price=0.0, free=True)
    org_id = _org_id(db, auth)

    res = client.post(f"/api/marketplace/playbooks/{playbook.id}/purchase", headers=auth)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "active"
    assert res.json()["price_paid"] == 0.0

    purchase = _purchase(db, playbook.id, org_id)
    assert purchase.payment_status == "free"
    assert purchase.is_active is True

    db.refresh(playbook)
    assert playbook.total_revenue == 0.0
    assert client.get(
        f"/api/marketplace/playbooks/{playbook.slug}", headers=auth
    ).json()["has_purchased"] is True
