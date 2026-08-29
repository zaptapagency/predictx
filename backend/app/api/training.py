"""
Model training on uploaded customer data.

Trains a real supervised classifier on the rows a user uploaded via CSV.
It requires a labelled outcome column: without labels there is nothing to
learn, and inventing them would produce a model with a meaningless
accuracy score. Metrics are computed on a held-out test split.
"""

import base64
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_saas import User
from app.db.connector_models import CustomerData, DataSource
from app.db.prediction_models import (
    Model, ModelArtifact, ModelStatus, ModelType, OutcomeDirection, Prediction, TrainingRun,
)
from app.services.auth_service import get_current_user
from app.services.prediction_sync import sync_from_predictions
from app.utils.time import utcnow

router = APIRouter(prefix="/api/training", tags=["training"])

MIN_ROWS = 20
TEST_SIZE = 0.25

# A single feature that alone separates the outcome this well is almost
# always leakage -- a column derived from the answer, or recorded after it
# was known. Real predictors are rarely this good on their own.
LEAKAGE_AUC = 0.98

# Values accepted as a positive/negative label, so a CSV can say
# "yes"/"true"/1 without the user having to normalise it first.
TRUTHY = {"1", "true", "yes", "y", "churned", "churn", "lost"}
FALSEY = {"0", "false", "no", "n", "active", "retained", "kept"}

# Words in a label column's name that suggest which way a high score points.
# A guess only -- outcome_direction on the request always overrides it. Risk
# is checked first and wins a tie, since assuming risk fires an Action rather
# than staying silent, and a wrongly-silent opportunity is the worse failure.
_RISK_WORDS = ("churn", "cancel", "lost", "complaint", "default", "risk", "fraud")
_OPPORTUNITY_WORDS = ("convert", "purchase", "renew", "upsell", "profit", "success", "win")


def _infer_direction(label_column: str) -> str:
    name = label_column.lower()
    if any(w in name for w in _RISK_WORDS):
        return OutcomeDirection.RISK.value
    if any(w in name for w in _OPPORTUNITY_WORDS):
        return OutcomeDirection.OPPORTUNITY.value
    return OutcomeDirection.RISK.value


class TrainRequest(BaseModel):
    data_source_id: int
    label_column: str
    name: Optional[str] = None
    model_type: str = "churn"
    algorithm: str = "xgboost"
    feature_columns: Optional[List[str]] = None
    # Whether a high score is bad news (risk) or good news (opportunity). See
    # OutcomeDirection. Left unset to infer from label_column, since most
    # callers will not know this vocabulary exists -- but always overridable.
    outcome_direction: Optional[str] = None


class ScoreRequest(BaseModel):
    model_id: int
    data_source_id: Optional[int] = None


def _to_label(value: Any) -> Optional[int]:
    """Normalise a label cell to 1/0, or None if it isn't interpretable."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        if value in (0, 1):
            return int(value)
        return None
    s = str(value).strip().lower()
    if s in TRUTHY:
        return 1
    if s in FALSEY:
        return 0
    return None


def _leakage_suspects(raw, y, features, roc_auc_score):
    """
    Features that predict the outcome almost perfectly on their own.

    A user picks their own label column here, so nothing stops them choosing a
    label and leaving a column that encodes it -- "profitable" alongside the
    revenue it was computed from, "churned" alongside a cancellation date. The
    model then scores near 1.0 in training and is worthless in production,
    which is worse than an obviously bad model because it looks trustworthy.

    Reported, not blocked: a genuinely dominant predictor is possible, and
    that judgement belongs to whoever knows what the columns mean.
    """
    import numpy as np

    suspects = []
    for i, name in enumerate(features):
        column = raw[:, i]
        if np.all(column == column[0]):
            continue  # constant column carries no signal to leak
        try:
            auc = roc_auc_score(y, column)
        except ValueError:
            continue
        # A perfectly inverted predictor leaks just as much as a direct one.
        separation = max(auc, 1.0 - auc)
        if separation >= LEAKAGE_AUC:
            suspects.append({"feature": name, "auc_alone": round(float(separation), 4)})

    return sorted(suspects, key=lambda s: -s["auc_alone"])


def _load_rows(db: Session, org_id: int, source_id: int) -> List[Dict[str, Any]]:
    rows = db.query(CustomerData).filter(
        CustomerData.organization_id == org_id,
        CustomerData.data_source_id == source_id,
    ).all()
    return [{"_customer_id": r.customer_id, **(r.customer_data or {})} for r in rows]


@router.get("/candidates/{data_source_id}")
def training_candidates(
    data_source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze a data source: which columns can be outcome labels, which are features. Returns candidates so the user can pick what to predict."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.organization_id == current_user.organization_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    rows = _load_rows(db, current_user.organization_id, data_source_id)
    if not rows:
        raise HTTPException(status_code=400, detail="This data source has no rows")

    columns = [c for c in rows[0].keys() if c != "_customer_id"]
    label_candidates, numeric_features = [], []
    for col in columns:
        values = [r.get(col) for r in rows]
        labels = [_to_label(v) for v in values]
        if all(l is not None for l in labels) and len(set(labels)) == 2:
            label_candidates.append({
                "column": col,
                "positives": sum(l for l in labels if l),
                "negatives": sum(1 for l in labels if l == 0),
            })
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values if v is not None):
            if any(v is not None for v in values):
                numeric_features.append(col)

    return {
        "data_source": source.name,
        "rows": len(rows),
        "label_candidates": label_candidates,
        "numeric_features": [c for c in numeric_features],
        "ready_to_train": bool(label_candidates) and len(rows) >= MIN_ROWS,
        "note": (
            None if label_candidates else
            "No column looks like a binary outcome. Add a column with true/false "
            "(or yes/no, or 1/0) values for what you want to predict. "
            "Examples: churned, converted, successful, defective. "
            "A model cannot be trained without known outcomes to learn from."
        ),
    }


@router.post("/train")
def train_on_source(
    request: TrainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Train a classifier on an uploaded data source."""
    org_id = current_user.organization_id
    source = db.query(DataSource).filter(
        DataSource.id == request.data_source_id,
        DataSource.organization_id == org_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    try:
        model_type = ModelType[request.model_type.upper()]
    except KeyError:
        valid = ", ".join(t.value for t in ModelType)
        raise HTTPException(status_code=400, detail=f"Invalid model_type. Valid: {valid}")

    direction_value = request.outcome_direction or _infer_direction(request.label_column)
    try:
        outcome_direction = OutcomeDirection(direction_value)
    except ValueError:
        valid = ", ".join(d.value for d in OutcomeDirection)
        raise HTTPException(status_code=400, detail=f"Invalid outcome_direction. Valid: {valid}")
    direction_was_inferred = request.outcome_direction is None

    rows = _load_rows(db, org_id, request.data_source_id)
    if len(rows) < MIN_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {MIN_ROWS} rows to train; this source has {len(rows)}.",
        )

    columns = [c for c in rows[0].keys() if c != "_customer_id"]
    if request.label_column not in columns:
        raise HTTPException(
            status_code=400,
            detail=f"label_column '{request.label_column}' not found. Columns: {', '.join(columns)}",
        )

    # Labels
    labels = [_to_label(r.get(request.label_column)) for r in rows]
    if any(l is None for l in labels):
        bad = next(r.get(request.label_column) for r, l in zip(rows, labels) if l is None)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Column '{request.label_column}' has values that aren't yes/no "
                f"outcomes (e.g. {bad!r}). Use true/false, yes/no, or 1/0."
            ),
        )
    if len(set(labels)) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Every row has the same outcome in '{request.label_column}'. "
                "Training needs both positive and negative examples."
            ),
        )

    # Features: numeric columns only, excluding the label
    if request.feature_columns:
        features = [c for c in request.feature_columns if c != request.label_column]
        missing = [c for c in features if c not in columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Unknown feature columns: {', '.join(missing)}")
    else:
        features = []
        for col in columns:
            if col == request.label_column:
                continue
            vals = [r.get(col) for r in rows]
            if any(v is not None for v in vals) and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals if v is not None
            ):
                features.append(col)

    if not features:
        raise HTTPException(
            status_code=400,
            detail="No numeric feature columns found. A model needs numeric inputs to learn from.",
        )

    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier

    # Build the matrix, filling gaps with each column's mean.
    raw = np.array(
        [[r.get(c) if isinstance(r.get(c), (int, float)) and not isinstance(r.get(c), bool) else np.nan
          for c in features] for r in rows],
        dtype=float,
    )
    col_means = np.nanmean(raw, axis=0)
    col_means = np.where(np.isnan(col_means), 0.0, col_means)
    inds = np.where(np.isnan(raw))
    raw[inds] = np.take(col_means, inds[1])
    y = np.array(labels)

    started = utcnow()
    run = TrainingRun(
        model_id=None, organization_id=org_id, status="running",
        training_start=started, training_records=len(rows),
    )

    stratify = y if min(np.bincount(y)) >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        raw, y, test_size=TEST_SIZE, random_state=42, stratify=stratify,
    )

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    algo = request.algorithm.lower()
    if algo in ("logistic_regression", "logistic"):
        estimator = LogisticRegression(max_iter=1000, random_state=42)
    elif algo == "random_forest":
        estimator = RandomForestClassifier(n_estimators=200, random_state=42)
    else:
        # Reported name must match what actually trained, so callers and the
        # stored artifact do not claim an algorithm that never ran.
        algo = "xgboost"
        estimator = XGBClassifier(n_estimators=100, random_state=42, eval_metric="logloss")

    try:
        estimator.fit(X_train_s, y_train)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Training failed: {e}")

    y_pred = estimator.predict(X_test_s)
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    try:
        proba = estimator.predict_proba(X_test_s)[:, 1]
        auc = float(roc_auc_score(y_test, proba)) if len(set(y_test)) > 1 else None
    except Exception:
        auc = None

    if hasattr(estimator, "feature_importances_"):
        weights = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        weights = np.abs(estimator.coef_[0])
    else:
        weights = np.zeros(len(features))
    total = float(weights.sum()) or 1.0
    importance = {f: round(float(w) / total, 4) for f, w in zip(features, weights)}

    model = Model(
        organization_id=org_id,
        name=request.name or f"{source.name} {model_type.value} model",
        model_type=model_type,
        outcome_direction=outcome_direction,
        description=f"Trained on {len(rows)} rows from '{source.name}', label '{request.label_column}'",
        status=ModelStatus.ACTIVE,
        algorithm=algo,
        features=features,
        feature_importance=importance,
        training_record_count=len(rows),
        training_date=started,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        auc_roc=auc,
        created_by_id=current_user.id,
    )
    db.add(model)
    db.flush()

    db.add(ModelArtifact(
        model_id=model.id,
        organization_id=org_id,
        payload=base64.b64encode(pickle.dumps({
            "estimator": estimator, "scaler": scaler,
            "features": features, "means": col_means.tolist(),
        })).decode("ascii"),
    ))

    completed = utcnow()
    run.model_id = model.id
    run.status = "completed"
    run.completed_at = completed
    run.duration_seconds = int((completed - started).total_seconds())
    run.test_accuracy = accuracy
    run.test_precision = precision
    run.test_recall = recall
    db.add(run)
    db.commit()

    warnings = []
    if direction_was_inferred:
        warnings.append(
            f"Guessed outcome_direction='{outcome_direction.value}' from the column name "
            f"'{request.label_column}' -- if a HIGH score should mean good news (e.g. "
            "conversion, renewal), pass outcome_direction='opportunity' explicitly and retrain, "
            "or the Heatmap and Action Center will treat your best customers as at-risk."
        )
    if len(rows) < 100:
        warnings.append(
            f"Only {len(rows)} rows: metrics come from a {len(y_test)}-row test set "
            "and should be treated as indicative, not reliable."
        )
    if min(int(np.bincount(y)[0]), int(np.bincount(y)[1])) < 5:
        warnings.append("One outcome class has fewer than 5 examples; the model will be biased toward the majority.")

    leakage = _leakage_suspects(raw, y, features, roc_auc_score)
    if leakage:
        names = ", ".join(f"'{s['feature']}'" for s in leakage)
        warnings.append(
            f"Possible label leakage: {names} predict '{request.label_column}' "
            "almost perfectly alone. If any of these is derived from the outcome, "
            "or recorded only after it was known, drop it from feature_columns and "
            "retrain -- otherwise these scores will not hold on new data."
        )

    return {
        "success": True,
        "model_id": model.id,
        "name": model.name,
        "algorithm": algo,
        "trained_on": {
            "rows": len(rows),
            "train_rows": len(y_train),
            "test_rows": len(y_test),
            "positives": int(y.sum()),
            "negatives": int(len(y) - y.sum()),
            "label_column": request.label_column,
            "features": features,
            "outcome_direction": outcome_direction.value,
            "outcome_direction_inferred": direction_was_inferred,
        },
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "auc_roc": round(auc, 4) if auc is not None else None,
            "measured_on": "held-out test split",
        },
        "feature_importance": dict(sorted(importance.items(), key=lambda kv: -kv[1])),
        "leakage_suspects": leakage,
        "warnings": warnings,
    }


@router.post("/score")
def score_with_model(
    request: ScoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Score customers with a trained model, writing Prediction rows."""
    org_id = current_user.organization_id
    model = db.query(Model).filter(
        Model.id == request.model_id, Model.organization_id == org_id,
    ).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    artifact = db.query(ModelArtifact).filter(ModelArtifact.model_id == model.id).first()
    if not artifact:
        raise HTTPException(
            status_code=400,
            detail="This model has no saved artifact and cannot score. Retrain it.",
        )

    bundle = pickle.loads(base64.b64decode(artifact.payload))
    estimator, scaler = bundle["estimator"], bundle["scaler"]
    features, means = bundle["features"], bundle["means"]

    q = db.query(CustomerData).filter(CustomerData.organization_id == org_id)
    if request.data_source_id:
        q = q.filter(CustomerData.data_source_id == request.data_source_id)
    records = q.all()
    if not records:
        raise HTTPException(status_code=400, detail="No customer data to score")

    import numpy as np

    matrix, ids = [], []
    for r in records:
        data = r.customer_data or {}
        row = []
        for i, f in enumerate(features):
            v = data.get(f)
            row.append(float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else means[i])
        matrix.append(row)
        ids.append(r.customer_id)

    scores = estimator.predict_proba(scaler.transform(np.array(matrix, dtype=float)))[:, 1]

    # Refresh this model's predictions rather than accumulating duplicates.
    db.query(Prediction).filter(
        Prediction.organization_id == org_id, Prediction.model_id == model.id,
    ).delete()

    # band/percentile answer "how urgently does this need attention", which is
    # the opposite end of the score for an opportunity model: a customer with
    # a 95% conversion probability is not urgent, one at 5% is. score itself
    # stays the untouched, literal probability of the label -- only urgency
    # ranking inverts. Without this, an opportunity model's best customers
    # were labelled "critical" and handed the same "reach_out_now" action
    # meant for someone about to churn.
    is_risk_model = model.outcome_direction != OutcomeDirection.OPPORTUNITY

    def band(urgency: float) -> str:
        if urgency >= 0.75:
            return "critical"
        if urgency >= 0.5:
            return "high"
        if urgency >= 0.25:
            return "medium"
        return "low"

    ACTIONS = {
        "critical": "reach_out_now", "high": "offer_discount",
        "medium": "schedule_qbr", "low": "monitor",
    }

    top_features = sorted(
        (model.feature_importance or {}).items(), key=lambda kv: -kv[1]
    )[:3]

    now = utcnow()
    urgencies = [float(x) if is_risk_model else 1.0 - float(x) for x in scores]
    ranked = sorted(urgencies, reverse=True)
    written = []
    for cid, score, urgency, row in zip(ids, scores, urgencies, matrix):
        s = float(score)
        level = band(urgency)
        percentile = round(100 * (1 - ranked.index(urgency) / max(len(ranked), 1)), 1)
        prediction = Prediction(
            organization_id=org_id,
            model_id=model.id,
            customer_id=cid,
            score=s,
            confidence=round(abs(s - 0.5) * 2, 4),
            percentile=percentile,
            risk_level=level,
            recommended_action=ACTIONS[level],
            top_factors=[
                {"feature": f, "importance": imp,
                 "value": row[features.index(f)] if f in features else None}
                for f, imp in top_features
            ],
            features_used={f: row[i] for i, f in enumerate(features)},
            predicted_at=now,
        )
        db.add(prediction)
        written.append(prediction)

    db.commit()

    # Predictions on their own only populate the Predictions tab. Fan them out
    # so the Heatmap and Action Center reflect this scoring run too.
    fanout = sync_from_predictions(db, org_id, model, written)

    dist = {b: sum(1 for s in scores if band(float(s)) == b)
            for b in ("critical", "high", "medium", "low")}

    return {
        "success": True,
        "model_id": model.id,
        "model_name": model.name,
        "customers_scored": len(written),
        "risk_distribution": dist,
        "highest_risk": [
            {"customer_id": c, "score": round(float(s), 4)}
            for c, s in sorted(zip(ids, scores), key=lambda t: -t[1])[:5]
        ],
        "fanout": fanout,
    }
