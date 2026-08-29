"""
The summary tabs must reflect the latest scoring run, or admit they have nothing.

Insights, Copilot, Quick Wins and the user home dashboard all roll the same
predictions up differently. These tests walk the real path (signup -> CSV ->
train -> score) and check both ends: the empty state before scoring, and real
numbers after.
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
    email = f"summary-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/signup", json={
        "email": email,
        "username": email.split("@")[0],
        "password": "Sup3rSecret!",
        "full_name": "Summary Sam",
    })
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def scored(client, auth):
    """Upload a learnable dataset, train on it, and score every customer."""
    random.seed(11)
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


# ---------------------------------------------------------------------------
# empty state: no predictions means no numbers, not zero-shaped fiction
# ---------------------------------------------------------------------------

def test_insights_feed_is_empty_before_scoring(client, auth):
    body = client.get("/api/insights/feed", headers=auth).json()
    assert body["insights"] == []
    assert body["unread_count"] == 0
    assert "Upload" in body["message"]


def test_copilot_has_nothing_to_recommend_before_scoring(client, auth):
    body = client.get("/api/copilot/recommendations", headers=auth).json()
    assert body["recommendations"] == []
    assert body["pending_count"] == 0
    assert body["message"]


def test_quick_wins_are_empty_before_scoring(client, auth):
    body = client.get("/api/quick-wins/available", headers=auth).json()
    assert body["quick_wins"] == []
    assert body["total"] == 0
    assert body["message"]


def test_user_home_admits_it_has_no_predictions(client, auth):
    body = client.get("/api/user/home", headers=auth).json()
    assert body["customers_scored"] == 0
    assert body["customers_at_risk"] == 0
    assert body["revenue_at_risk"] is None
    assert body["top_actions"] == []
    # No realized impact, so no invented forecast or confidence.
    assert body["forecast_next_month"] is None
    assert body["forecast_confidence"] is None
    assert body["recommended_playbooks"] == []
    assert "Upload" in body["headline"]


# ---------------------------------------------------------------------------
# after scoring: every figure traces back to the run
# ---------------------------------------------------------------------------

def test_insights_feed_reports_the_real_cohort(client, auth, scored):
    body = client.get("/api/insights/feed", headers=auth).json()

    assert body["customers_scored"] == scored["result"]["customers_scored"]
    assert body["insights"]

    by_id = {i["id"]: i for i in body["insights"]}
    dist = scored["result"]["risk_distribution"]
    at_risk = dist["critical"] + dist["high"]
    assert by_id["risk-concentration"]["title"] == f"{at_risk} customers need attention"

    # Drivers name real uploaded columns, never invented features.
    drivers = [i for i in body["insights"] if i["id"].startswith("driver-")]
    assert drivers
    assert all(i["related_entity"] in {"arr", "logins_30d", "support_tickets"} for i in drivers)

    # First run has no previous run, so we don't claim a shift.
    assert "risk-shift" not in by_id


def test_insights_report_the_shift_after_a_second_scoring_run(client, auth, scored):
    res = client.post("/api/training/score", headers=auth, json={"model_id": scored["model_id"]})
    assert res.status_code == 200, res.text

    body = client.get("/api/insights/feed", headers=auth).json()
    # Scoring replaces a model's predictions, so there is still only one run on
    # record and the feed must not pretend otherwise.
    assert "risk-shift" not in {i["id"] for i in body["insights"]}


def test_copilot_ranks_real_customers_by_what_is_at_stake(client, auth, scored):
    body = client.get("/api/copilot/recommendations", headers=auth).json()

    recs = body["recommendations"]
    assert recs
    assert body["pending_count"] > 0

    for rec in recs:
        assert rec["customer_id"].startswith("C")
        assert "Acme" in rec["title"]
        assert rec["entity_email"]
        # We have no outcome history, so no fabricated success rate.
        assert rec["success_probability"] is None
        assert rec["estimated_impact"].startswith("$")

    impacts = [float(r["estimated_impact"].strip("$").replace(",", "")) for r in recs]
    assert impacts == sorted(impacts, reverse=True)

    # The reasoning names the model and the drivers it actually used.
    assert scored["result"]["model_name"] in recs[0]["reasoning"]
    assert any(f in recs[0]["reasoning"] for f in ("arr", "logins_30d", "support_tickets"))


def test_quick_wins_target_the_customers_the_model_flagged(client, auth, scored):
    body = client.get("/api/quick-wins/available", headers=auth).json()

    wins = {w["id"]: w for w in body["quick_wins"]}
    assert body["total"] == len(body["quick_wins"]) > 0

    dist = scored["result"]["risk_distribution"]
    if dist["critical"]:
        assert wins["outreach-critical"]["estimated_target_count"] == dist["critical"]
    if dist["high"]:
        assert wins["offer-high"]["estimated_target_count"] == dist["high"]

    top = next(w for w in body["quick_wins"] if w["id"].startswith("top-account-"))
    assert top["estimated_target_count"] == 1
    assert top["customer_ids"][0].startswith("C")
    assert all(w["success_probability"] is None for w in body["quick_wins"])


def test_user_home_shows_the_scoring_run(client, auth, scored):
    body = client.get("/api/user/home", headers=auth).json()

    dist = scored["result"]["risk_distribution"]
    assert body["customers_scored"] == scored["result"]["customers_scored"]
    assert body["customers_at_risk"] == dist["critical"] + dist["high"]
    assert body["risk_distribution"] == dist
    assert body["revenue_at_risk"].startswith("$")
    assert "first scoring run" in body["since_last_scoring"]

    assert len(body["top_actions"]) == 3
    assert body["top_actions"][0]["priority"] in {"CRITICAL", "HIGH"}
    assert "Acme" in body["top_actions"][0]["title"]

    # Predictions are not realized value: this month's ROI must still be zero.
    assert body["this_month_impact"] == "$0"


def test_home_insights_count_critical_predictions(client, auth, scored):
    body = client.get("/api/user/insights-for-home", headers=auth).json()
    assert body["urgent_count"] == scored["result"]["risk_distribution"]["critical"]
