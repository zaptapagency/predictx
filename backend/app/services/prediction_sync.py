"""
Prediction fan-out.

Scoring writes Prediction rows. On its own that only lights up the Predictions
tab. This module turns those predictions into the records the rest of the
platform already reads:

  - CustomerHealthScore / HealthMetric  -> Heatmap tab
  - Action                             -> Action Center tab

ROI is deliberately NOT written here. A prediction is not realized value, so
inventing ImpactRecord rows at score time would overstate ROI. The ROI tab
instead derives an unrealized "pipeline" figure from the open actions this
module creates (see app/api/roi.py).
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.action_models import Action, ActionPriority, ActionStatus, ActionType
from app.db.connector_models import CustomerData
from app.db.heatmap_models import CustomerHealthScore, HealthMetric
from app.db.prediction_models import Model, OutcomeDirection, Prediction
from app.utils.time import utcnow

# Marks the actions/health rows this module owns, so re-scoring can replace its
# own output without touching anything a user created by hand.
AUTO_SOURCE = "prediction_sync"

# Direction now lives on the model itself (Model.outcome_direction), set
# explicitly at training time -- see OutcomeDirection. It used to be inferred
# from a fixed set of model_type values, which broke the moment a model was
# trained on an outcome that did not fit that taxonomy: a "profitable" model
# defaulted to model_type=churn and so was read as risk, inverting health
# scores and firing Actions on the best customers instead of the worst.

# Only these bands are worth interrupting someone for.
ACTIONABLE_BANDS = ("critical", "high")

_PRIORITY = {
    "critical": ActionPriority.CRITICAL,
    "high": ActionPriority.HIGH,
    "medium": ActionPriority.MEDIUM,
    "low": ActionPriority.LOW,
}

# How long the user has to act, by band.
_DUE_IN_DAYS = {"critical": 1, "high": 3, "medium": 7, "low": 14}

# Field names we look for in the uploaded CSV to value a customer.
_REVENUE_KEYS = ("arr", "annual_revenue", "revenue", "mrr", "monthly_revenue", "contract_value")
_NAME_KEYS = ("name", "customer_name", "company", "company_name", "account_name", "account")
_EMAIL_KEYS = ("email", "customer_email", "contact_email", "owner_email")


# ---------------------------------------------------------------------------
# customer attributes from the uploaded data
# ---------------------------------------------------------------------------

def _first_match(record: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[Any]:
    """Find the first key in `record` matching one of `keys`, case-insensitively."""
    lowered = {str(k).lower(): v for k, v in record.items()}
    for key in keys:
        value = lowered.get(key)
        if value not in (None, ""):
            return value
    return None


def _customer_attributes(db: Session, org_id: int, customer_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Pull name / email / annual revenue for each customer from their synced data."""
    if not customer_ids:
        return {}

    rows = db.query(CustomerData).filter(
        CustomerData.organization_id == org_id,
        CustomerData.customer_id.in_(customer_ids),
    ).order_by(CustomerData.synced_at).all()

    attributes: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        record = row.customer_data if isinstance(row.customer_data, dict) else {}

        revenue = _first_match(record, _REVENUE_KEYS)
        try:
            revenue = float(revenue) if revenue is not None else None
        except (TypeError, ValueError):
            revenue = None
        # Monthly figures are annualized so impact estimates are comparable.
        if revenue is not None and _first_match(record, ("mrr", "monthly_revenue")) is not None:
            if _first_match(record, ("arr", "annual_revenue", "revenue", "contract_value")) is None:
                revenue *= 12

        # Later syncs win.
        attributes[row.customer_id] = {
            "name": _first_match(record, _NAME_KEYS) or row.customer_id,
            "email": _first_match(record, _EMAIL_KEYS),
            "annual_revenue": revenue,
        }
    return attributes


# ---------------------------------------------------------------------------
# health scores -> Heatmap
# ---------------------------------------------------------------------------

def _health_from_score(score: float, is_risk_model: bool) -> float:
    """A 0-1 model score becomes a 0-100 health score."""
    return round((1.0 - score) * 100 if is_risk_model else score * 100, 1)


def _flag_counts(prediction: Prediction, is_risk_model: bool) -> Tuple[int, int, int]:
    """
    Count the prediction's top factors as red / yellow / green flags.

    A factor counts against the customer when it pushes the prediction toward
    the bad outcome, which depends on whether high scores are bad.
    """
    red = yellow = green = 0
    factors = prediction.top_factors or []
    bad_direction = prediction.score >= 0.5 if is_risk_model else prediction.score < 0.5

    for factor in factors:
        importance = factor.get("importance") or 0
        if bad_direction and importance >= 0.2:
            red += 1
        elif bad_direction:
            yellow += 1
        else:
            green += 1
    return red, yellow, green


def _sync_health_scores(
    db: Session,
    org_id: int,
    predictions: List[Prediction],
    previous: Dict[str, float],
    is_risk_model: bool,
) -> int:
    """Upsert one CustomerHealthScore per customer, with its contributing metrics."""
    existing = {
        h.customer_id: h
        for h in db.query(CustomerHealthScore).filter(
            CustomerHealthScore.organization_id == org_id,
            CustomerHealthScore.customer_id.in_([p.customer_id for p in predictions]),
        ).all()
    } if predictions else {}

    for prediction in predictions:
        score = float(prediction.score)
        health = _health_from_score(score, is_risk_model)
        red, yellow, green = _flag_counts(prediction, is_risk_model)

        prior = previous.get(prediction.customer_id)
        if prior is None:
            trend, direction = "stable", None
        else:
            direction = round(health - _health_from_score(prior, is_risk_model), 1)
            trend = "improving" if direction > 2 else "declining" if direction < -2 else "stable"

        row = existing.get(prediction.customer_id)
        if row is None:
            row = CustomerHealthScore(
                organization_id=org_id,
                customer_id=prediction.customer_id,
            )
            db.add(row)
            db.flush()

        row.overall_health = health
        row.churn_risk = round(score if is_risk_model else 0.0, 4)
        row.expansion_potential = round(0.0 if is_risk_model else score, 4)
        row.support_urgency = round(score if is_risk_model else 0.0, 4)
        row.health_trend = trend
        row.trend_direction = direction
        row.red_flags = red
        row.yellow_flags = yellow
        row.green_flags = green
        row.updated_at = utcnow()

        # Replace the previous run's metric breakdown for this customer.
        db.query(HealthMetric).filter(HealthMetric.health_score_id == row.id).delete(
            synchronize_session=False
        )
        for factor in (prediction.top_factors or []):
            feature = factor.get("feature")
            if not feature:
                continue
            value = factor.get("value")
            db.add(HealthMetric(
                health_score_id=row.id,
                metric_name=feature,
                metric_value=float(value) if isinstance(value, (int, float)) else 0.0,
                metric_weight=float(factor.get("importance") or 0.0),
                status="critical" if prediction.risk_level == "critical"
                       else "warning" if prediction.risk_level == "high" else "good",
                description=(
                    f"'{feature}' is one of the strongest drivers of this customer's "
                    f"{'risk' if is_risk_model else 'opportunity'} score."
                ),
                recommended_action=prediction.recommended_action,
            ))

    return len(predictions)


# ---------------------------------------------------------------------------
# actions -> Action Center
# ---------------------------------------------------------------------------

# Copy differs by direction: for a risk model "high band" means about to
# churn, so the language is retention-flavoured; for an opportunity model the
# same band means unlikely to convert, so it is not "retention" language at
# all -- there is nothing to retain yet.
_ACTION_COPY_RISK = {
    "reach_out_now": (ActionType.PHONE_CALL, "Call {name} today"),
    "offer_discount": (ActionType.EMAIL, "Email {name} a retention offer"),
    "schedule_qbr": (ActionType.MEETING, "Book a business review with {name}"),
    "monitor": (ActionType.TASK, "Keep an eye on {name}"),
}
_ACTION_COPY_OPPORTUNITY = {
    "reach_out_now": (ActionType.PHONE_CALL, "Call {name} today"),
    "offer_discount": (ActionType.EMAIL, "Email {name} an offer to help them convert"),
    "schedule_qbr": (ActionType.MEETING, "Book a call to move {name} forward"),
    "monitor": (ActionType.TASK, "Keep an eye on {name}"),
}


def _estimate_impact(score: float, annual_revenue: Optional[float], is_risk_model: bool) -> Optional[float]:
    """
    Revenue at stake for this customer, or None when we don't know their value.

    For a risk model this is the revenue we stand to lose (revenue x probability).
    For an upside model it's the expansion we might win, assumed to be 20% of
    the account, weighted by the model's confidence.
    """
    if annual_revenue is None:
        return None
    return round(annual_revenue * score * (1.0 if is_risk_model else 0.2), 2)


def _sync_actions(
    db: Session,
    org_id: int,
    model: Model,
    predictions: List[Prediction],
    attributes: Dict[str, Dict[str, Any]],
    is_risk_model: bool,
) -> int:
    """
    Create one open action per customer that needs attention.

    Actions this module generated on a previous run of the same model and that
    nobody has acted on are skipped first, so the Action Center reflects the
    latest scoring rather than accumulating every run.
    """
    now = utcnow()

    open_actions = db.query(Action).filter(
        Action.organization_id == org_id,
        Action.status.in_([ActionStatus.PENDING, ActionStatus.SCHEDULED]),
    ).all()
    for action in open_actions:
        config = action.action_config or {}
        if config.get("source") == AUTO_SOURCE and str(config.get("model_id")) == str(model.id):
            action.status = ActionStatus.SKIPPED
            action.updated_at = now

    created = 0
    for prediction in predictions:
        band = prediction.risk_level
        if band not in ACTIONABLE_BANDS:
            continue

        attrs = attributes.get(prediction.customer_id, {})
        name = attrs.get("name") or prediction.customer_id
        copy_table = _ACTION_COPY_RISK if is_risk_model else _ACTION_COPY_OPPORTUNITY
        action_type, title_template = copy_table.get(
            prediction.recommended_action, (ActionType.TASK, "Follow up with {name}")
        )
        impact = _estimate_impact(float(prediction.score), attrs.get("annual_revenue"), is_risk_model)

        drivers = ", ".join(
            f.get("feature") for f in (prediction.top_factors or []) if f.get("feature")
        )
        subject = "churn risk" if is_risk_model else "opportunity"
        description = (
            f"{model.name} scored {name} at {prediction.score * 100:.0f}% {subject} "
            f"({band}, {prediction.percentile:.0f}th percentile)."
        )
        if drivers:
            description += f" Biggest drivers: {drivers}."

        db.add(Action(
            organization_id=org_id,
            prediction_id=str(prediction.id),
            title=title_template.format(name=name),
            description=description,
            action_type=action_type,
            priority=_PRIORITY[band],
            status=ActionStatus.PENDING,
            entity_type="customer",
            entity_id=prediction.customer_id,
            entity_name=name,
            entity_email=attrs.get("email"),
            estimated_impact=impact,
            impact_type="revenue_saved" if is_risk_model else "revenue_created",
            impact_unit="usd" if impact is not None else None,
            due_at=now + timedelta(days=_DUE_IN_DAYS[band]),
            action_config={
                "source": AUTO_SOURCE,
                "model_id": str(model.id),
                "score": round(float(prediction.score), 4),
                "risk_level": band,
            },
            created_at=now,
        ))
        created += 1

    return created


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def sync_from_predictions(db: Session, org_id: int, model: Model, predictions: List[Prediction]) -> Dict[str, Any]:
    """
    Fan a batch of fresh predictions out into health scores and actions.

    Called by the scoring endpoint after it commits its Prediction rows.
    Commits its own work and returns a summary for the API response.
    """
    if not predictions:
        return {"health_scores_updated": 0, "actions_created": 0, "revenue_at_risk": 0.0}

    is_risk_model = model.outcome_direction == OutcomeDirection.RISK
    customer_ids = [p.customer_id for p in predictions]

    # Each customer's score from the run before this one, for trend direction.
    previous: Dict[str, float] = {}
    prior_rows = db.query(Prediction).filter(
        Prediction.organization_id == org_id,
        Prediction.model_id == model.id,
        Prediction.customer_id.in_(customer_ids),
        Prediction.id.notin_([p.id for p in predictions]),
    ).order_by(Prediction.predicted_at).all()
    for row in prior_rows:
        previous[row.customer_id] = float(row.score)

    attributes = _customer_attributes(db, org_id, customer_ids)

    health_updated = _sync_health_scores(db, org_id, predictions, previous, is_risk_model)
    actions_created = _sync_actions(db, org_id, model, predictions, attributes, is_risk_model)
    db.commit()

    at_risk = sum(
        _estimate_impact(
            float(p.score), attributes.get(p.customer_id, {}).get("annual_revenue"), is_risk_model
        ) or 0.0
        for p in predictions if p.risk_level in ACTIONABLE_BANDS
    )

    return {
        "health_scores_updated": health_updated,
        "actions_created": actions_created,
        "revenue_at_risk": round(at_risk, 2),
    }
