"""
A high score is bad news for churn but good news for conversion. Which one
applies used to be inferred from model_type, and that inference broke the
moment a user trained on an outcome that was not churn-shaped: a "converted"
model defaulted to model_type=churn, so a HIGH conversion score -- a great
customer -- was read as risk, given a low Heatmap health score, and handed an
urgent Action meant for someone about to leave.

These tests train on an opportunity-shaped outcome through the real HTTP
endpoints and pin that the best customers end up reading as healthy, not
at-risk.
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
    email = f"direction-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email, "username": email.split("@")[0],
        "password": "Sup3rSecret!", "full_name": "Direction Test",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _upload_conversion_data(client, auth):
    """
    Ad-campaign-shaped rows (not customer rows) with a "converted" outcome --
    high engagement means converted, unlike churn where high engagement means
    safe. If direction were still guessed from model_type=churn, a converted
    campaign would be scored as if it were at risk.
    """
    random.seed(3)
    rows = ["campaign_id,name,email,arr,clicks,checkouts,converted"]
    for i in range(120):
        converted = 1 if i % 3 == 0 else 0
        clicks = random.randint(30, 60) if converted else random.randint(0, 10)
        checkouts = random.randint(3, 8) if converted else random.randint(0, 1)
        rows.append(f"CMP{i},Campaign {i},c{i}@ex.com,{(i + 1) * 500},{clicks},{checkouts},{converted}")

    res = client.post(
        "/api/connectors/csv/upload", headers=auth,
        files={"file": ("campaigns.csv", io.BytesIO("\n".join(rows).encode()), "text/csv")},
        data={"name": "Campaigns", "id_column": "campaign_id"},
    )
    assert res.status_code == 200, res.text
    return res.json()["data_source_id"]


def test_direction_is_inferred_from_the_label_name(client, auth):
    source_id = _upload_conversion_data(client, auth)

    res = client.post("/api/training/train", headers=auth, json={
        "data_source_id": source_id, "label_column": "converted",
    })
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["trained_on"]["outcome_direction"] == "opportunity"
    assert body["trained_on"]["outcome_direction_inferred"] is True
    assert any("Guessed outcome_direction" in w for w in body["warnings"])


def test_opportunity_direction_can_be_stated_explicitly(client, auth):
    source_id = _upload_conversion_data(client, auth)

    # A label name the inference heuristic would not recognise at all.
    res = client.post("/api/training/train", headers=auth, json={
        "data_source_id": source_id, "label_column": "converted",
        "name": "explicit", "outcome_direction": "opportunity",
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["trained_on"]["outcome_direction"] == "opportunity"
    assert body["trained_on"]["outcome_direction_inferred"] is False
    assert not any("Guessed outcome_direction" in w for w in body["warnings"])


def test_the_best_customer_reads_as_healthy_not_at_risk(client, auth):
    """
    The actual regression: a high score on an opportunity model must produce
    a HIGH health score and must not fire a red-flagged Action, the way a
    high churn score correctly does.
    """
    source_id = _upload_conversion_data(client, auth)

    train = client.post("/api/training/train", headers=auth, json={
        "data_source_id": source_id, "label_column": "converted",
    })
    assert train.status_code == 200, train.text
    model_id = train.json()["model_id"]

    score = client.post("/api/training/score", headers=auth, json={"model_id": model_id})
    assert score.status_code == 200, score.text

    overview = client.get("/api/heatmap/overview", headers=auth).json()
    assert overview["summary"]["total_customers"] > 0

    # Sorted ascending by health, so [0] is worst and [-1] is best -- for an
    # opportunity model, best means highest-converting. If direction were
    # still guessed from model_type=churn, this would show up as "critical".
    healthiest = overview["customers"][-1]
    assert healthiest["health_status"] == "healthy"
    assert healthiest["red_flags"] == 0

    worst = overview["customers"][0]
    assert worst["health_status"] == "critical"

    dashboard = client.get("/api/actions/dashboard", headers=auth).json()
    critical_names = {a["entity_name"] for a in dashboard["actions_by_priority"]["critical"]}
    # customer_id is the row's uploaded id ("CMP42"); the uploaded name column
    # for that same row is "Campaign 42" -- derive it and confirm no critical
    # Action targets the best-converting campaign.
    best_number = healthiest["customer_id"].replace("CMP", "")
    assert f"Campaign {best_number}" not in critical_names, (
        "an opportunity model fired a critical Action on its best customer"
    )
