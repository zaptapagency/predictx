"""
Predictions API
Train models and generate predictions
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db.models_saas import User
from app.db.prediction_models import (
    Model, Prediction, TrainingRun, ModelStatus, ModelType,
    Outcome, OutcomeType, PredictionFeedback, Feature
)
from app.db.database import get_db
from app.services.auth_service import get_current_user
from app.services.model_service import ModelService
from app.services.feature_engineer import FeatureEngineer

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TrainModelRequest(BaseModel):
    name: str
    model_type: str
    training_start: datetime
    training_end: datetime
    algorithm: str = "xgboost"
    hyperparameters: Optional[Dict[str, Any]] = None


class MakePredictionRequest(BaseModel):
    model_id: int
    customer_id: str


class BatchPredictRequest(BaseModel):
    model_id: int
    customer_ids: Optional[List[str]] = None


class RecordOutcomeRequest(BaseModel):
    prediction_id: int
    outcome_type: str
    outcome_value: Optional[float] = None
    notes: Optional[str] = None


class PredictionFeedbackRequest(BaseModel):
    prediction_id: int
    helpful: bool
    accurate: bool
    comments: Optional[str] = None


# ============================================================================
# MODEL MANAGEMENT
# ============================================================================

@router.post("/models/train")
def train_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Train a new model"""

    try:
        service = ModelService(db)
        model = service.train_model(
            current_user.organization_id,
            request.model_type,
            request.training_start,
            request.training_end,
            request.algorithm,
            request.hyperparameters
        )

        return {
            "id": model.id,
            "name": model.name,
            "status": model.status.value,
            "message": "Model training started"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
def list_models(
    status: Optional[str] = None,
    model_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List models for organization"""

    query = db.query(Model).filter(
        Model.organization_id == current_user.organization_id
    )

    if status:
        query = query.filter(Model.status == ModelStatus[status.upper()])

    if model_type:
        query = query.filter(Model.model_type == ModelType[model_type.upper()])

    models = query.order_by(desc(Model.created_at)).all()

    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "model_type": m.model_type.value,
                "status": m.status.value,
                "algorithm": m.algorithm,
                "accuracy": m.accuracy,
                "f1_score": m.f1_score,
                "auc_roc": m.auc_roc,
                "features_count": len(m.features) if m.features else 0,
                "training_date": m.training_date,
                "is_drifted": m.is_drifted,
                "created_at": m.created_at
            }
            for m in models
        ]
    }


@router.get("/models/{model_id}")
def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get model details"""

    model = db.query(Model).filter(
        Model.id == model_id,
        Model.organization_id == current_user.organization_id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "id": model.id,
        "name": model.name,
        "model_type": model.model_type.value,
        "status": model.status.value,
        "description": model.description,
        "algorithm": model.algorithm,
        "features": model.features,
        "feature_importance": model.feature_importance,
        "performance": {
            "accuracy": model.accuracy,
            "precision": model.precision,
            "recall": model.recall,
            "f1_score": model.f1_score,
            "auc_roc": model.auc_roc
        },
        "training": {
            "start": model.training_data_start,
            "end": model.training_data_end,
            "records": model.training_record_count,
            "date": model.training_date
        },
        "health": {
            "is_drifted": model.is_drifted,
            "last_checked": model.last_checked_drift
        },
        "created_at": model.created_at
    }


@router.get("/models/{model_id}/training-runs")
def get_training_runs(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get training history for model"""

    model = db.query(Model).filter(
        Model.id == model_id,
        Model.organization_id == current_user.organization_id
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    runs = db.query(TrainingRun).filter(
        TrainingRun.model_id == model_id
    ).order_by(desc(TrainingRun.started_at)).all()

    return {
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "started": r.started_at,
                "completed": r.completed_at,
                "duration_seconds": r.duration_seconds,
                "records": r.training_records,
                "metrics": {
                    "accuracy": r.test_accuracy,
                    "precision": r.test_precision,
                    "recall": r.test_recall,
                    "f1": r.test_f1
                },
                "error": r.error_message
            }
            for r in runs
        ]
    }


# ============================================================================
# PREDICTIONS
# ============================================================================

@router.post("/predict")
def make_prediction(
    request: MakePredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate prediction for customer"""

    try:
        service = ModelService(db)
        prediction = service.predict(
            current_user.organization_id,
            request.model_id,
            request.customer_id
        )

        return {
            "id": prediction.id,
            "customer_id": prediction.customer_id,
            "score": prediction.score,
            "confidence": prediction.confidence,
            "risk_level": prediction.risk_level,
            "recommended_action": prediction.recommended_action,
            "top_factors": prediction.top_factors,
            "predicted_at": prediction.predicted_at
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-predict")
def batch_predict(
    request: BatchPredictRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Batch predict for multiple customers"""

    try:
        background_tasks.add_task(
            _batch_predict_task,
            current_user.organization_id,
            request.model_id,
            request.customer_ids,
            db
        )

        return {
            "status": "queued",
            "message": "Batch prediction started in background"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _batch_predict_task(
    organization_id: int,
    model_id: int,
    customer_ids: Optional[List[str]],
    db: Session
):
    """Background task for batch predictions"""
    service = ModelService(db)
    predictions = service.batch_predict(organization_id, model_id, customer_ids)
    print(f"Batch prediction completed: {len(predictions)} predictions")


@router.get("/predictions")
def list_predictions(
    model_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List predictions"""

    query = db.query(Prediction).filter(
        Prediction.organization_id == current_user.organization_id
    )

    if model_id:
        query = query.filter(Prediction.model_id == model_id)

    if risk_level:
        query = query.filter(Prediction.risk_level == risk_level)

    predictions = query.order_by(desc(Prediction.predicted_at)).limit(limit).all()

    return {
        "predictions": [
            {
                "id": p.id,
                "customer_id": p.customer_id,
                "score": p.score,
                "confidence": p.confidence,
                "risk_level": p.risk_level,
                "recommended_action": p.recommended_action,
                "predicted_at": p.predicted_at,
                "has_outcome": p.outcome is not None
            }
            for p in predictions
        ]
    }


@router.get("/predictions/{prediction_id}")
def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prediction details"""

    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.organization_id == current_user.organization_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    model = prediction.model

    return {
        "id": prediction.id,
        "customer_id": prediction.customer_id,
        "model": {
            "id": model.id,
            "name": model.name,
            "type": model.model_type.value
        },
        "score": prediction.score,
        "confidence": prediction.confidence,
        "percentile": prediction.percentile,
        "risk_level": prediction.risk_level,
        "recommended_action": prediction.recommended_action,
        "contributing_factors": prediction.contributing_factors,
        "top_factors": prediction.top_factors,
        "predicted_at": prediction.predicted_at,
        "outcome": {
            "type": prediction.outcome.outcome_type.value if prediction.outcome else None,
            "value": prediction.outcome.outcome_value if prediction.outcome else None,
            "occurred_at": prediction.outcome.occurred_at if prediction.outcome else None,
            "was_correct": prediction.outcome.was_correct if prediction.outcome else None
        } if prediction.outcome else None
    }


# ============================================================================
# OUTCOMES & FEEDBACK
# ============================================================================

@router.post("/predictions/{prediction_id}/outcome")
def record_outcome(
    prediction_id: int,
    request: RecordOutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record actual outcome for prediction"""

    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.organization_id == current_user.organization_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    try:
        outcome = Outcome(
            organization_id=current_user.organization_id,
            prediction_id=prediction_id,
            outcome_type=OutcomeType[request.outcome_type.upper()],
            outcome_value=request.outcome_value,
            occurred_at=datetime.utcnow(),
            notes=request.notes
        )

        db.add(outcome)
        db.commit()
        db.refresh(outcome)

        return {
            "id": outcome.id,
            "prediction_id": prediction_id,
            "outcome_type": outcome.outcome_type.value
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/{prediction_id}/feedback")
def submit_feedback(
    prediction_id: int,
    request: PredictionFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on prediction"""

    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.organization_id == current_user.organization_id
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    try:
        feedback = PredictionFeedback(
            prediction_id=prediction_id,
            organization_id=current_user.organization_id,
            helpful=request.helpful,
            accurate=request.accurate,
            comments=request.comments,
            created_by_id=current_user.id
        )

        db.add(feedback)
        db.commit()

        return {
            "id": feedback.id,
            "prediction_id": prediction_id,
            "status": "recorded"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FEATURES
# ============================================================================

@router.get("/features")
def list_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all features"""

    features = db.query(Feature).filter(
        Feature.organization_id == current_user.organization_id
    ).all()

    return {
        "features": [
            {
                "id": f.id,
                "name": f.name,
                "type": f.feature_type,
                "source": f"{f.source_table}.{f.source_field}",
                "description": f.description,
                "statistics": {
                    "mean": f.mean,
                    "median": f.median,
                    "std": f.stddev,
                    "null_percentage": f.null_percentage
                }
            }
            for f in features
        ]
    }


@router.get("/customer/{customer_id}/features")
def get_customer_features(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all features for a customer"""

    engineer = FeatureEngineer(db)
    features = engineer.get_customer_features(current_user.organization_id, customer_id)

    return {
        "customer_id": customer_id,
        "features": features
    }


@router.get("/feature-statistics")
def get_feature_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feature statistics for normalization"""

    engineer = FeatureEngineer(db)
    stats = engineer.get_feature_statistics(current_user.organization_id)

    return {
        "statistics": stats
    }
