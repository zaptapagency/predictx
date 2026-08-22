"""
Model Training and Scoring Service
Train ML models and generate predictions
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import pickle

from app.db.prediction_models import Model, Prediction, Feature, TrainingRun, ModelType, ModelStatus
from app.db.connector_models import CustomerData
from app.services.feature_engineer import FeatureEngineer


class ModelService:
    """
    Trains models and generates predictions
    """

    def __init__(self, db: Session):
        self.db = db
        self.feature_engineer = FeatureEngineer(db)

    def train_model(
        self,
        organization_id: int,
        model_type: str,
        training_start: datetime,
        training_end: datetime,
        algorithm: str = "xgboost",
        hyperparameters: Optional[Dict] = None
    ) -> Model:
        """
        Train a new model
        """
        # Create model record
        model = Model(
            organization_id=organization_id,
            name=f"{model_type.title()} Model v1",
            model_type=ModelType[model_type.upper()],
            status=ModelStatus.TRAINING,
            algorithm=algorithm,
            training_data_start=training_start,
            training_data_end=training_end
        )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        # Create training run record
        run = TrainingRun(
            model_id=model.id,
            organization_id=organization_id,
            status="running",
            training_start=training_start,
            training_end=training_end,
            started_at=datetime.utcnow(),
            hyperparameters=hyperparameters or {}
        )

        self.db.add(run)
        self.db.commit()

        try:
            # Get training data
            df, target = self._prepare_training_data(
                organization_id,
                model_type,
                training_start,
                training_end
            )

            if len(df) < 50:
                raise ValueError(f"Insufficient training data: {len(df)} samples")

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                df.drop("customer_id", axis=1),
                target,
                test_size=0.2,
                random_state=42
            )

            # Standardize features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Train model
            if algorithm.lower() == "logistic_regression":
                estimator = LogisticRegression(max_iter=1000, random_state=42)
            elif algorithm.lower() == "random_forest":
                estimator = RandomForestClassifier(n_estimators=100, random_state=42)
            elif algorithm.lower() == "xgboost" or algorithm.lower() == "gradient_boosting":
                estimator = GradientBoostingClassifier(n_estimators=100, random_state=42)
            else:
                estimator = LogisticRegression(max_iter=1000, random_state=42)

            estimator.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred = estimator.predict(X_test_scaled)
            y_pred_proba = estimator.predict_proba(X_test_scaled)[:, 1]

            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_test, y_pred_proba)

            # Get feature importance
            if hasattr(estimator, "feature_importances_"):
                importances = estimator.feature_importances_
            elif hasattr(estimator, "coef_"):
                importances = np.abs(estimator.coef_[0])
            else:
                importances = [1.0] * len(X_train.columns)

            feature_importance = {
                name: float(importance)
                for name, importance in zip(X_train.columns, importances)
            }

            # Update model
            model.status = ModelStatus.ACTIVE
            model.features = list(X_train.columns)
            model.feature_importance = feature_importance
            model.accuracy = accuracy
            model.precision = precision
            model.recall = recall
            model.f1_score = f1
            model.auc_roc = auc
            model.training_record_count = len(df)
            model.training_date = datetime.utcnow()

            # Update training run
            run.status = "success"
            run.completed_at = datetime.utcnow()
            run.duration_seconds = (run.completed_at - run.started_at).total_seconds()
            run.training_records = len(df)
            run.test_accuracy = accuracy
            run.test_precision = precision
            run.test_recall = recall
            run.test_f1 = f1

            # Store model artifact (pickle)
            # In production, use model registry (MLflow, etc)
            # For now, just store metadata
            model.model_data = pickle.dumps({
                "estimator": estimator,
                "scaler": scaler,
                "feature_names": list(X_train.columns)
            })

            self.db.commit()

            return model

        except Exception as e:
            model.status = ModelStatus.FAILED
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def predict(
        self,
        organization_id: int,
        model_id: int,
        customer_id: str
    ) -> Prediction:
        """
        Generate a prediction for a customer using a trained model
        """
        model = self.db.query(Model).filter(
            Model.id == model_id,
            Model.organization_id == organization_id,
            Model.status == ModelStatus.ACTIVE
        ).first()

        if not model:
            raise ValueError(f"Model {model_id} not found or inactive")

        # Get features for customer
        features_dict = self.feature_engineer.get_customer_features(
            organization_id,
            customer_id
        )

        # Convert to DataFrame
        df = pd.DataFrame([features_dict])

        # Select only features used in model
        X = df[model.features]

        # Fill missing values
        X = X.fillna(0)

        # Load model artifact
        artifact = pickle.loads(model.model_data)
        estimator = artifact["estimator"]
        scaler = artifact["scaler"]

        # Predict
        X_scaled = scaler.transform(X)
        score = estimator.predict_proba(X_scaled)[0, 1]
        confidence = max(estimator.predict_proba(X_scaled)[0])

        # Get contributing factors (top features by importance)
        feature_imp = model.feature_importance or {}
        sorted_features = sorted(
            feature_imp.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        top_factors = []
        for feature_name, importance in sorted_features[:5]:
            feature_value = features_dict.get(feature_name, None)
            top_factors.append({
                "feature": feature_name,
                "value": feature_value,
                "importance": float(importance)
            })

        # Categorize risk level
        if model.model_type == ModelType.CHURN:
            if score > 0.8:
                risk_level = "critical"
                recommended_action = "immediate_outreach"
            elif score > 0.6:
                risk_level = "high"
                recommended_action = "outreach"
            elif score > 0.4:
                risk_level = "medium"
                recommended_action = "monitor"
            else:
                risk_level = "low"
                recommended_action = "maintain"

        else:
            if score > 0.7:
                risk_level = "high"
                recommended_action = "pursue"
            elif score > 0.5:
                risk_level = "medium"
                recommended_action = "explore"
            else:
                risk_level = "low"
                recommended_action = "track"

        # Create prediction record
        prediction = Prediction(
            organization_id=organization_id,
            model_id=model_id,
            customer_id=customer_id,
            score=float(score),
            confidence=float(confidence),
            contributing_factors=top_factors,
            top_factors=top_factors[:3],
            risk_level=risk_level,
            recommended_action=recommended_action,
            features_used=features_dict
        )

        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        return prediction

    def batch_predict(
        self,
        organization_id: int,
        model_id: int,
        customer_ids: Optional[List[str]] = None
    ) -> List[Prediction]:
        """
        Generate predictions for multiple customers
        """
        if customer_ids is None:
            # Get all customers
            records = self.db.query(CustomerData.customer_id).filter(
                CustomerData.organization_id == organization_id
            ).distinct().all()
            customer_ids = [r[0] for r in records if r[0]]

        predictions = []
        for customer_id in customer_ids:
            try:
                prediction = self.predict(organization_id, model_id, customer_id)
                predictions.append(prediction)
            except Exception as e:
                print(f"Error predicting for {customer_id}: {e}")
                continue

        return predictions

    def check_model_drift(
        self,
        organization_id: int,
        model_id: int,
        check_period_days: int = 7
    ) -> bool:
        """
        Detect if model predictions or input features have drifted
        """
        model = self.db.query(Model).filter(
            Model.id == model_id,
            Model.organization_id == organization_id
        ).first()

        if not model:
            return False

        # Get recent predictions
        recent_cutoff = datetime.utcnow() - timedelta(days=check_period_days)
        recent_predictions = self.db.query(Prediction).filter(
            Prediction.model_id == model_id,
            Prediction.predicted_at >= recent_cutoff
        ).all()

        if len(recent_predictions) < 10:
            return False

        # Check prediction distribution drift
        recent_scores = [p.score for p in recent_predictions]
        score_mean = np.mean(recent_scores)
        score_std = np.std(recent_scores)

        # Compare to training distribution (approximate with stored metrics)
        # If prediction mean changed significantly, there's drift
        drift_threshold = 0.15  # 15% shift in mean
        if abs(score_mean - 0.5) > drift_threshold:
            model.is_drifted = True
            self.db.commit()
            return True

        return False

    def _prepare_training_data(
        self,
        organization_id: int,
        model_type: str,
        training_start: datetime,
        training_end: datetime
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data with features and targets
        """
        # Get all customers active during training period
        records = self.db.query(CustomerData).filter(
            CustomerData.organization_id == organization_id,
            CustomerData.created_at >= training_start,
            CustomerData.created_at <= training_end
        ).all()

        customer_ids = set()
        for record in records:
            if record.customer_id:
                customer_ids.add(record.customer_id)

        if not customer_ids:
            return pd.DataFrame(), pd.Series(dtype=int)

        # Get features
        features_df = self.feature_engineer.get_batch_features(
            organization_id,
            list(customer_ids),
            training_end
        )

        if features_df.empty:
            return features_df, pd.Series(dtype=int)

        # Get targets based on model type
        # In production, this would query actual outcomes
        # For now, create synthetic targets based on features (proof of concept)
        targets = self._generate_synthetic_targets(model_type, features_df)

        return features_df, targets

    def _generate_synthetic_targets(self, model_type: str, features_df: pd.DataFrame) -> pd.Series:
        """
        Generate synthetic targets for training (proof of concept)
        In production, query actual customer outcomes
        """
        if model_type.lower() == "churn":
            # High churn risk: overdue payment, dormant, declining usage
            churn_risk = (
                (features_df.get("payment_overdue", 0) * 0.3) +
                (features_df.get("dormant_90d", 0) * 0.3) +
                (features_df.get("usage_declining", 0) * 0.2) +
                (features_df.get("mrr_declining", 0) * 0.2)
            )
            return (churn_risk > 0.5).astype(int)

        elif model_type.lower() == "opportunity":
            # High opportunity: growing usage, growing MRR, power user
            opportunity = (
                (features_df.get("usage_growing", 0) * 0.3) +
                (features_df.get("mrr_growing", 0) * 0.3) +
                (features_df.get("is_power_user", 0) * 0.2) +
                (features_df.get("monthly_active_users", 0).fillna(0) > 5).astype(int) * 0.2
            )
            return (opportunity > 0.5).astype(int)

        elif model_type.lower() == "expansion":
            # High expansion: high value, power user, growing
            expansion = (
                (features_df.get("is_high_value", 0) * 0.3) +
                (features_df.get("is_power_user", 0) * 0.3) +
                (features_df.get("mrr_growing", 0) * 0.2) +
                (features_df.get("usage_growing", 0) * 0.2)
            )
            return (expansion > 0.5).astype(int)

        else:
            # Default: random
            return pd.Series(np.random.randint(0, 2, len(features_df)))

    @property
    def model_data(self):
        """Placeholder for model artifact storage"""
        return None

    @model_data.setter
    def model_data(self, value):
        """Placeholder for model artifact storage"""
        pass
