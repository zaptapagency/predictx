"""
Scoring must light up the rest of the platform, not just the Predictions tab.

Covers the path a user actually walks: upload a CSV, train, score, then look
at the Heatmap, Action Center and ROI tabs.
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
    """A signed-up user with their own organization, as auth headers."""
    email = f"fanout-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email,
        "username": email.split("@")[0],
        "password": "Sup3rSecret!",
        "full_name": "Fan Out",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def scored(client, auth):
    """Upload a learnable dataset, train on it, and score every customer."""
    random.seed(7)
    rows = ["customer_id,name,email,arr,logins_30d,support_tickets,churned"]
    for i in range(120):
        churned = 1 if i % 3 == 0 else 0
        logins = random.randint(0, 5) if churned else random.randint(20, 60)
        tickets = random.randint(5, 12) if churned else random.randint(0, 2)
        rows.append(f"C{i},Acme {i},c{i}@ex.com,{(i + 1) * 1000},{logins},{tickets},{churned}")

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
        "algorithm": "gradient_boosting",
    })
    assert res.status_code == 200, res.text
    model_id = res.json()["model_id"]

    res = client.post("/api/training/score", headers=auth, json={"model_id": model_id})
    assert res.status_code == 200, res.text
    return {"model_id": model_id, "result": res.json()}


def test_downstream_tabs_are_empty_before_scoring(client, auth):
    assert client.get("/api/heatmap/overview", headers=auth).json()["summary"]["total_customers"] == 0
    assert client.get("/api/actions/dashboard", headers=auth).json()["stats"]["total"] == 0


def test_scoring_reports_what_it_fanned_out(scored):
    fanout = scored["result"]["fanout"]
    assert fanout["health_scores_updated"] == scored["result"]["customers_scored"]
    assert fanout["actions_created"] > 0
    assert fanout["revenue_at_risk"] > 0


def test_heatmap_reflects_the_scoring_run(client, auth, scored):
    overview = client.get("/api/heatmap/overview", headers=auth).json()

    assert overview["summary"]["total_customers"] == scored["result"]["customers_scored"]
    assert overview["summary"]["critical_count"] > 0

    riskiest = overview["customers"][0]
    assert riskiest["health_status"] == "critical"
    assert riskiest["red_flags"] > 0

    detail = client.get(f"/api/heatmap/customer/{riskiest['customer_id']}", headers=auth)
    assert detail.status_code == 200
    # Metrics come from the prediction's top factors, so they name real columns.
    assert {m["name"] for m in detail.json()["metrics"]} <= {"arr", "logins_30d", "support_tickets"}
    assert detail.json()["metrics"]


def test_action_center_gets_one_action_per_at_risk_customer(client, auth, scored):
    dashboard = client.get("/api/actions/dashboard", headers=auth).json()

    assert dashboard["stats"]["total"] == scored["result"]["fanout"]["actions_created"]
    assert dashboard["stats"]["total_estimated_impact"] > 0

    action = (dashboard["actions_by_priority"]["critical"]
              or dashboard["actions_by_priority"]["high"])[0]
    assert action["entity_name"].startswith("Acme")
    assert action["entity_email"]
    assert action["impact_type"] == "revenue_saved"
    # The description explains itself without the user opening the model.
    assert "churn risk" in action["description"]


def test_rescoring_replaces_actions_instead_of_duplicating(client, auth, scored):
    before = client.get("/api/actions/dashboard", headers=auth).json()["stats"]["total"]

    res = client.post("/api/training/score", headers=auth, json={"model_id": scored["model_id"]})
    assert res.status_code == 200, res.text

    after = client.get("/api/actions/dashboard", headers=auth).json()["stats"]["total"]
    assert after == before


def test_roi_shows_pipeline_without_claiming_realized_value(client, auth, scored):
    roi = client.get("/api/roi/dashboard", headers=auth).json()
    pipeline = roi["pipeline"]

    assert pipeline["is_realized"] is False
    assert pipeline["open_actions"] == scored["result"]["fanout"]["actions_created"]
    assert pipeline["revenue_at_risk"] > 0
    assert pipeline["top_opportunities"]
    # Nobody has acted on anything yet, so realized impact must still be zero.
    assert roi["summary"]["total_impact"] == 0
