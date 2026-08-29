"""
A user picks their own outcome column, so nothing stops them leaving a feature
that encodes the answer. The model then looks perfect and is worthless.

These tests pin that the platform says so, and that it does not cry wolf on an
ordinary strong predictor.
"""

import uuid

import pytest

from app.database import engine
from app.db.connector_models import CustomerData, DataConnection, DataSource
from app.db.database import Base, SessionLocal
from app.db.models_saas import Organization, User
from app.api.training import TrainRequest, train_on_source


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
    organization = Organization(name=f"Leak {uuid.uuid4().hex[:6]}", slug=uuid.uuid4().hex[:10])
    db.add(organization)
    db.flush()
    owner = User(
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        username=uuid.uuid4().hex[:8],
        hashed_password="x",
        full_name="Owner",
        organization_id=organization.id,
    )
    db.add(owner)
    db.commit()
    organization._owner = owner
    return organization


def _source_with(db, org, records):
    connection = DataConnection(organization_id=org.id, name="csv", connector_type="csv",
                                config={}, credentials={}, created_by_id=org._owner.id)
    db.add(connection)
    db.flush()
    source = DataSource(organization_id=org.id, connection_id=connection.id, name="rows",
                        source_path="rows", schema={}, primary_key="id")
    db.add(source)
    db.flush()
    for i, record in enumerate(records):
        db.add(CustomerData(organization_id=org.id, data_source_id=source.id,
                            customer_id=f"r{i:03d}", customer_data=record, raw_fields={}))
    db.commit()
    return source


def test_a_feature_derived_from_the_label_is_reported(db, org):
    """`refund_issued` only ever happens to churned accounts -- that is leakage."""
    records = []
    for i in range(60):
        churned = i % 2 == 0
        records.append({
            "logins": 3 if churned else 40,
            "tickets": i % 7,
            # Recorded only after the outcome was known.
            "refund_issued": 1 if churned else 0,
            "churned": "yes" if churned else "no",
        })
    source = _source_with(db, org, records)

    result = train_on_source(
        TrainRequest(data_source_id=source.id, label_column="churned", name="Leaky"),
        org._owner, db,
    )

    flagged = [s["feature"] for s in result["leakage_suspects"]]
    assert "refund_issued" in flagged
    assert any("leakage" in w.lower() for w in result["warnings"])
    assert any("refund_issued" in w for w in result["warnings"])


def test_an_ordinary_predictor_is_not_flagged(db, org):
    """A useful but imperfect feature must not be called leakage."""
    records = []
    for i in range(60):
        churned = i % 3 == 0
        # Correlated with the outcome, but the two classes overlap heavily,
        # which is what an ordinary real-world predictor looks like.
        logins = (i % 11) if churned else (5 + (i % 11))
        records.append({
            "logins": logins,
            "tickets": i % 5,
            "churned": "yes" if churned else "no",
        })
    source = _source_with(db, org, records)

    result = train_on_source(
        TrainRequest(data_source_id=source.id, label_column="churned", name="Clean"),
        org._owner, db,
    )

    assert result["leakage_suspects"] == []
    assert not any("leakage" in w.lower() for w in result["warnings"])


def test_an_inverted_leak_is_caught_too(db, org):
    """Perfect negative separation leaks exactly as much as positive."""
    records = []
    for i in range(60):
        churned = i % 2 == 0
        records.append({
            "logins": i % 11,
            # 1 for everyone who did NOT churn.
            "still_subscribed": 0 if churned else 1,
            "churned": "yes" if churned else "no",
        })
    source = _source_with(db, org, records)

    result = train_on_source(
        TrainRequest(data_source_id=source.id, label_column="churned", name="Inverted"),
        org._owner, db,
    )

    assert "still_subscribed" in [s["feature"] for s in result["leakage_suspects"]]
