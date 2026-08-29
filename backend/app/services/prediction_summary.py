"""
Prediction roll-up.

`prediction_sync` fans predictions out one row per customer, which is the right
shape for the Heatmap and the Action Center because those tabs list customers.
The Insights feed, the Copilot, Quick Wins and the user home dashboard don't
list — they summarize. Writing a row per customer for them would just be the
fan-out again with a different table name, so instead they all read this module
and shape the same roll-up into their own response.

Nothing here invents a number. Every figure traces back to a Prediction row, and
where the uploaded data doesn't say what a customer is worth we return None and
let the caller say "unknown" rather than guessing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.prediction_models import Model, Prediction
from app.services.prediction_sync import (
    ACTIONABLE_BANDS,
    RISK_MODEL_TYPES,
    _customer_attributes,
    _estimate_impact,
)

BANDS = ("critical", "high", "medium", "low")

# What every one of these tabs says when the org hasn't got anything to show yet.
# Deliberately the same sentence everywhere: the fix is always the same two steps.
NO_DATA_MESSAGE = (
    "No predictions yet. Upload your customer data and train a model, "
    "then run scoring to see this."
)
NO_SCORING_MESSAGE = (
    "You have a trained model but haven't scored anyone yet. "
    "Run scoring on a model to see this."
)


@dataclass
class ScoredCustomer:
    """One customer as the latest scoring run left them."""
    customer_id: str
    name: str
    email: Optional[str]
    score: float
    confidence: Optional[float]
    percentile: Optional[float]
    band: str
    recommended_action: Optional[str]
    top_factors: List[Dict[str, Any]] = field(default_factory=list)
    annual_revenue: Optional[float] = None
    revenue_at_stake: Optional[float] = None

    @property
    def is_at_risk(self) -> bool:
        return self.band in ACTIONABLE_BANDS

    @property
    def drivers(self) -> List[str]:
        return [f.get("feature") for f in self.top_factors if f.get("feature")]


@dataclass
class PredictionSummary:
    """The latest scoring run for an organization, rolled up."""
    model_id: int
    model_name: str
    model_type: str
    is_risk_model: bool
    scored_at: Any
    customers: List[ScoredCustomer]          # highest score first
    band_counts: Dict[str, int]
    drivers: List[Dict[str, Any]]
    revenue_at_stake: float
    revenue_known_for: int
    previous: Optional[Dict[str, Any]]       # band counts of the run before this one

    @property
    def total_customers(self) -> int:
        return len(self.customers)

    @property
    def at_risk(self) -> List[ScoredCustomer]:
        return [c for c in self.customers if c.is_at_risk]

    @property
    def subject(self) -> str:
        """The word for what a high score means, for use in prose."""
        return "churn risk" if self.is_risk_model else "opportunity"

    def band_shift(self) -> Optional[Dict[str, int]]:
        """Change in each band vs the previous run, or None if this is the first."""
        if not self.previous:
            return None
        prior = self.previous["band_counts"]
        return {b: self.band_counts[b] - prior.get(b, 0) for b in BANDS}


def _aggregate_drivers(customers: List[ScoredCustomer]) -> List[Dict[str, Any]]:
    """
    Which features drive the most risk across the cohort.

    Each customer's top factors carry the model's importance for that feature, so
    summing them over the at-risk customers shows where the risk actually comes
    from rather than which feature the model likes on average.
    """
    at_risk = [c for c in customers if c.is_at_risk] or customers
    totals: Dict[str, Dict[str, Any]] = {}

    for customer in at_risk:
        for factor in customer.top_factors:
            feature = factor.get("feature")
            if not feature:
                continue
            entry = totals.setdefault(
                feature, {"feature": feature, "weight": 0.0, "customers": 0, "values": []}
            )
            entry["weight"] += float(factor.get("importance") or 0.0)
            entry["customers"] += 1
            value = factor.get("value")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                entry["values"].append(float(value))

    total_weight = sum(e["weight"] for e in totals.values())
    drivers = []
    for entry in sorted(totals.values(), key=lambda e: -e["weight"]):
        values = entry.pop("values")
        drivers.append({
            "feature": entry["feature"],
            "share_of_risk": round(entry["weight"] / total_weight, 4) if total_weight else 0.0,
            "customers_affected": entry["customers"],
            "average_value": round(sum(values) / len(values), 2) if values else None,
        })
    return drivers


def summarize_org_predictions(db: Session, org_id: int) -> Optional[PredictionSummary]:
    """
    Roll up the organization's most recent scoring run, or None if there isn't one.

    Scoring replaces a model's previous predictions, so "the latest run" is the
    newest predicted_at timestamp and everything written under it.
    """
    newest = db.query(Prediction).filter(
        Prediction.organization_id == org_id
    ).order_by(Prediction.predicted_at.desc(), Prediction.id.desc()).first()
    if newest is None:
        return None

    model = db.query(Model).filter(Model.id == newest.model_id).first()
    if model is None:
        return None

    rows = db.query(Prediction).filter(
        Prediction.organization_id == org_id,
        Prediction.model_id == newest.model_id,
        Prediction.predicted_at == newest.predicted_at,
    ).all()

    is_risk_model = model.model_type in RISK_MODEL_TYPES
    attributes = _customer_attributes(db, org_id, [r.customer_id for r in rows])

    customers: List[ScoredCustomer] = []
    for row in rows:
        attrs = attributes.get(row.customer_id, {})
        revenue = attrs.get("annual_revenue")
        customers.append(ScoredCustomer(
            customer_id=row.customer_id,
            name=attrs.get("name") or row.customer_id,
            email=attrs.get("email"),
            score=float(row.score),
            confidence=float(row.confidence) if row.confidence is not None else None,
            percentile=float(row.percentile) if row.percentile is not None else None,
            band=row.risk_level or "low",
            recommended_action=row.recommended_action,
            top_factors=row.top_factors or [],
            annual_revenue=revenue,
            revenue_at_stake=_estimate_impact(float(row.score), revenue, is_risk_model),
        ))
    customers.sort(key=lambda c: -c.score)

    # A run that predates this one, if the org has scored more than once.
    previous = None
    prior = db.query(Prediction).filter(
        Prediction.organization_id == org_id,
        Prediction.model_id == newest.model_id,
        Prediction.predicted_at < newest.predicted_at,
    ).order_by(Prediction.predicted_at.desc()).all()
    if prior:
        prior_at = prior[0].predicted_at
        prior_rows = [p for p in prior if p.predicted_at == prior_at]
        previous = {
            "scored_at": prior_at,
            "total_customers": len(prior_rows),
            "band_counts": {
                b: sum(1 for p in prior_rows if p.risk_level == b) for b in BANDS
            },
        }

    at_risk = [c for c in customers if c.is_at_risk]
    return PredictionSummary(
        model_id=model.id,
        model_name=model.name,
        model_type=model.model_type.value if hasattr(model.model_type, "value") else str(model.model_type),
        is_risk_model=is_risk_model,
        scored_at=newest.predicted_at,
        customers=customers,
        band_counts={b: sum(1 for c in customers if c.band == b) for b in BANDS},
        drivers=_aggregate_drivers(customers),
        revenue_at_stake=round(sum(c.revenue_at_stake or 0.0 for c in at_risk), 2),
        revenue_known_for=sum(1 for c in at_risk if c.annual_revenue is not None),
        previous=previous,
    )


def empty_state_message(db: Session, org_id: int) -> str:
    """Tell the user which of the two missing steps they still owe us."""
    has_model = db.query(Model).filter(Model.organization_id == org_id).first() is not None
    return NO_SCORING_MESSAGE if has_model else NO_DATA_MESSAGE


def money(amount: Optional[float]) -> Optional[str]:
    """Format a dollar figure, or None when we genuinely don't know it."""
    return None if amount is None else f"${amount:,.0f}"
