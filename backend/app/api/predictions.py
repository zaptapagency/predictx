from fastapi import APIRouter, HTTPException
import pandas as pd
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.ml.model_loader import LightGBMModelLoader
from app.ml.feature_processor import FeatureProcessor
from app.utils import setup_logger

router = APIRouter(prefix="/api/predictions", tags=["predictions"])
logger = setup_logger(__name__)


@router.post("/", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Make a single prediction"""

    try:
        # Initialize model loader; the pre-trained LightGBM repo is an
        # optional install — respond 503 rather than a raw 500 without it.
        try:
            model_loader = LightGBMModelLoader()
            model_loader.load_all_models()
        except (ValueError, FileNotFoundError) as e:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Pre-trained models are not installed on this deployment. "
                    "Use POST /api/predictions/models/train to train a model instead."
                ),
            )

        # Initialize feature processor
        feature_processor = FeatureProcessor()

        # Convert features to DataFrame
        feature_df = pd.DataFrame([request.features])

        # Apply preprocessing
        feature_df = feature_processor.transform(feature_df)

        # Get predictions
        predictions = model_loader.predict(
            feature_df, vertical=request.vertical, use_adapter=True
        )

        pred_value = predictions["final"].iloc[0]

        # Generate recommendation
        recommendation = _generate_recommendation(
            pred_value, request.vertical, request.prediction_type
        )

        return PredictionResponse(
            prediction=float(pred_value),
            confidence=float(min(max(pred_value, 0), 1)),
            explanation={},  # Would include SHAP values
            recommendation=recommendation,
            model_version=model_loader.get_model_info()["version"],
            inference_time_ms=15.0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendation(
    prediction: float, vertical: str, prediction_type: str
) -> str:
    """Generate actionable recommendation"""

    if vertical == "saas" and "churn" in prediction_type:
        if prediction > 0.75:
            return "URGENT: Send retention offer and schedule customer success call"
        elif prediction > 0.5:
            return "Send personalized re-engagement email campaign"
        else:
            return "Continue normal customer engagement"

    else:
        if prediction > 0.75:
            return "High priority: Take action"
        elif prediction > 0.5:
            return "Medium priority: Monitor and engage"
        else:
            return "Low priority: Standard process"
