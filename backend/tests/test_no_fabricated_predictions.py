"""
The predictions API must never invent training labels or scores.

The old ModelService trained on synthetic targets (and on random labels for
unknown model types), so its "accuracy" was meaningless. These tests pin the
replacement: training is refused here, and scoring only works off the pickled
artifact that /api/training/train persists.
"""

import io
import random
import uuid

import pytest

from app.database import engine
from app.db.database import Base


@pytest.fixture(scope="module", autouse=True)
def _tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def auth(client):
    email = f"nofab-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email,
        "username": email.split("@")[0],
        "password": "Sup3rSecret!",
        "full_name": "No Fab",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def trained(client, auth):
    """A genuinely trained model over an uploaded, labelled data source."""
    random.seed(11)
    rows = ["customer_id,arr,logins_30d,support_tickets,churned"]
    for i in range(120):
        churned = 1 if i % 3 == 0 else 0
        logins = random.randint(0, 5) if churned else random.randint(20, 60)
        tickets = random.randint(5, 12) if churned else random.randint(0, 2)
        rows.append(f"C{i},{(i + 1) * 1000},{logins},{tickets},{churned}")

    res = client.post(
        "/api/connectors/csv/upload",
        headers=auth,
        files={"file": ("customers.csv", io.BytesIO("\n".join(rows).encode()), "text/csv")},
        data={"name": "Customers", "id_column": "customer_id"},
    )
    assert res.status_code == 200, res.text
    source_id = res.json()["data_source_id"]

    res = client.post("/api/training/train", headers=auth, json={
        "data_source_id": source_id,
        "label_column": "churned",
        "model_type": "churn",
    })
    assert res.status_code == 200, res.text
    return res.json()["model_id"]


def test_model_service_module_is_gone():
    with pytest.raises(ImportError):
        __import__("app.services.model_service")


def test_no_synthetic_target_generation_in_source():
    import pathlib
    app_dir = pathlib.Path(__file__).resolve().parents[1] / "app"
    offenders = [
        str(path)
        for path in app_dir.rglob("*.py")
        if "_generate_synthetic_targets" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_legacy_train_endpoint_refuses_and_points_at_real_trainer(client, auth):
    res = client.post("/api/predictions/models/train", headers=auth, json={
        "name": "Churn",
        "model_type": "churn",
        "training_start": "2024-01-01T00:00:00",
        "training_end": "2024-06-01T00:00:00",
    })
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "/api/training/train" in detail
    assert "label_column" in detail


def test_predict_refuses_when_model_has_no_artifact(client, auth):
    res = client.post("/api/predictions/predict", headers=auth, json={
        "model_id": 999999,
        "customer_id": "C0",
    })
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_predict_uses_the_trained_artifact(client, auth, trained):
    res = client.post("/api/predictions/predict", headers=auth, json={
        "model_id": trained,
        "customer_id": "C0",
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert 0.0 <= body["score"] <= 1.0
    assert body["risk_level"] in ("critical", "high", "medium", "low")
    assert body["top_factors"]

    # Deterministic: the same artifact and inputs give the same score, which a
    # fabricating implementation would not.
    again = client.post("/api/predictions/predict", headers=auth, json={
        "model_id": trained,
        "customer_id": "C0",
    })
    assert again.json()["score"] == body["score"]


def test_batch_predict_scores_real_customers(client, auth, trained):
    res = client.post("/api/predictions/batch-predict", headers=auth, json={
        "model_id": trained,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "completed"
    assert body["customers_scored"] == 120
    assert sum(body["risk_distribution"].values()) == 120

    listed = client.get(f"/api/predictions/predictions?model_id={trained}", headers=auth)
    assert listed.status_code == 200
    assert len(listed.json()["predictions"]) > 0


def test_batch_predict_refuses_unknown_model(client, auth):
    res = client.post("/api/predictions/batch-predict", headers=auth, json={
        "model_id": 999999,
    })
    assert res.status_code == 404
