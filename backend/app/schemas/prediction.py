from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class PredictionRequest(BaseModel):
    """Request model for predictions"""

    vertical: str = Field(..., description="Vertical/industry name")
    prediction_type: str = Field(..., description="Type of prediction")
    features: Dict[str, Any] = Field(..., description="Feature values")

    class Config:
        json_schema_extra = {
            "example": {
                "vertical": "saas",
                "prediction_type": "churn",
                "features": {
                    "feature_1": 1.0,
                    "feature_2": 10,
                    "feature_3": "value",
                },
            }
        }


class PredictionResponse(BaseModel):
    """Response model for predictions"""

    prediction: float = Field(..., description="Prediction value")
    confidence: float = Field(..., description="Prediction confidence")
    explanation: Dict[str, Any] = Field(..., description="SHAP explanation")
    recommendation: str = Field(..., description="Actionable recommendation")
    model_version: str = Field(..., description="Model version used")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""

    vertical: str
    prediction_type: str
    data: List[Dict[str, Any]]


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions"""

    total_records: int
    successful: int
    failed: int
    predictions: List[Dict[str, Any]]
    execution_time_ms: float
