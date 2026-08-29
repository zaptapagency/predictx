"""
Third-party credentials must not sit in the database as plaintext.

These tests read the raw column with plain SQL rather than through the ORM,
because the ORM is exactly the layer under test.
"""

import json
import uuid

import pytest
from sqlalchemy import text

from app.database import engine
from app.db.database import Base, SessionLocal
from app.db.integration_models import Integration
from app.db.models_saas import Organization
from app.services import crypto

WEBHOOK = "https://hooks.slack.com/services/T000/B000/XXXXsupersecretXXXX"


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def org(db):
    org = Organization(name="Crypto Test Org", slug=f"crypto-test-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _raw_config(db, integration_id):
    return db.execute(
        text("SELECT config FROM integrations WHERE id = :i"), {"i": integration_id}
    ).scalar()


def test_stored_config_is_not_readable_plaintext(db, org):
    row = Integration(organization_id=org.id, channel="slack", config={"webhook_url": WEBHOOK})
    db.add(row)
    db.commit()
    db.refresh(row)

    raw = _raw_config(db, row.id)
    assert WEBHOOK not in raw
    assert "hooks.slack.com" not in raw
    assert raw.startswith("fernet:v1:")


def test_round_trip_returns_original_dict(db, org):
    row = Integration(
        organization_id=org.id,
        channel="webhook",
        config={"webhook_url": WEBHOOK, "retries": 3},
    )
    db.add(row)
    db.commit()
    row_id = row.id
    db.expire_all()

    loaded = db.query(Integration).filter(Integration.id == row_id).one()
    assert loaded.config == {"webhook_url": WEBHOOK, "retries": 3}


def test_preexisting_plaintext_row_still_decrypts(db, org):
    """Rows written before encryption existed must keep working."""
    row = Integration(organization_id=org.id, channel="slack", config={"placeholder": True})
    db.add(row)
    db.commit()
    row_id = row.id

    # Simulate the legacy on-disk shape: bare JSON, no ciphertext prefix.
    db.execute(
        text("UPDATE integrations SET config = :c WHERE id = :i"),
        {"c": json.dumps({"webhook_url": WEBHOOK}), "i": row_id},
    )
    db.commit()
    db.expire_all()

    loaded = db.query(Integration).filter(Integration.id == row_id).one()
    assert loaded.config == {"webhook_url": WEBHOOK}

    # ...and the next write upgrades it to ciphertext.
    loaded.config = {"webhook_url": WEBHOOK, "rotated": True}
    db.commit()
    assert _raw_config(db, row_id).startswith("fernet:v1:")


def test_wrong_key_does_not_crash_reads():
    ciphertext = crypto.encrypt_value({"token": "abc"})
    from cryptography.fernet import Fernet

    original = crypto._fernet
    try:
        crypto._fernet = Fernet(Fernet.generate_key())
        assert crypto.decrypt_value(ciphertext) is None
    finally:
        crypto._fernet = original


def test_non_json_legacy_value_passes_through():
    assert crypto.decrypt_value("not json at all") == "not json at all"
    assert crypto.decrypt_value(None) is None
