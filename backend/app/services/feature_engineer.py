"""
Feature Engineering Pipeline
Transform raw customer data into ML features
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import pandas as pd

from app.db.connector_models import CustomerData
from app.db.models_saas import Organization
from app.utils.time import utcnow


class FeatureEngineer:
    """
    Transforms raw customer data into features for ML models
    """

    def __init__(self, db: Session):
        self.db = db

    def get_customer_features(
        self,
        organization_id: int,
        customer_id: str,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get all features for a customer as of a specific date
        """
        if as_of_date is None:
            as_of_date = utcnow()

        features = {}

        # Get raw customer data
        raw_data = self._get_customer_data(organization_id, customer_id, as_of_date)

        # Compute features from raw data
        features.update(self._compute_account_features(raw_data))
        features.update(self._compute_billing_features(raw_data))
        features.update(self._compute_engagement_features(raw_data))
        features.update(self._compute_health_features(raw_data))
        features.update(self._compute_trend_features(organization_id, customer_id, as_of_date))

        return features

    def _get_customer_data(
        self,
        organization_id: int,
        customer_id: str,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """Get all raw data for customer"""

        # Query customer data table
        records = self.db.query(CustomerData).filter(
            CustomerData.organization_id == organization_id,
            CustomerData.customer_id == customer_id,
            CustomerData.created_at <= as_of_date
        ).all()

        # Merge all data sources
        merged = {}
        for record in records:
            if record.customer_data:
                merged.update(record.customer_data)
            if record.raw_fields:
                merged.update(record.raw_fields)

        return merged

    def _compute_account_features(self, raw_data: Dict) -> Dict[str, Any]:
        """Features from account/company data"""

        features = {}

        # Company size
        if "employee_count" in raw_data:
            emp_count = self._safe_int(raw_data.get("employee_count"))
            if emp_count:
                features["company_size_log"] = np.log1p(emp_count)
                features["is_enterprise"] = 1 if emp_count > 1000 else 0
                features["is_mid_market"] = 1 if 50 < emp_count <= 1000 else 0

        # Industry (categorical - will be one-hot encoded)
        if "industry" in raw_data:
            features["industry"] = raw_data.get("industry", "unknown").lower()

        # Region
        if "country" in raw_data:
            features["country"] = raw_data.get("country", "unknown").upper()

        # Company age
        if "created_date" in raw_data or "founded_date" in raw_data:
            date_str = raw_data.get("created_date") or raw_data.get("founded_date")
            if date_str:
                try:
                    date = pd.to_datetime(date_str)
                    days_old = (utcnow() - date).days
                    features["account_age_days"] = max(1, days_old)
                    features["account_age_log"] = np.log1p(days_old)
                except:
                    pass

        return features

    def _compute_billing_features(self, raw_data: Dict) -> Dict[str, Any]:
        """Features from billing and payment data"""

        features = {}

        # MRR (Monthly Recurring Revenue)
        if "mrr" in raw_data:
            mrr = self._safe_float(raw_data.get("mrr"))
            if mrr:
                features["mrr"] = mrr
                features["mrr_log"] = np.log1p(mrr)
                features["is_high_value"] = 1 if mrr > 10000 else 0

        # Contract value
        if "annual_contract_value" in raw_data:
            acv = self._safe_float(raw_data.get("annual_contract_value"))
            if acv:
                features["acv"] = acv
                features["acv_log"] = np.log1p(acv)

        # Payment history
        if "days_since_last_payment" in raw_data:
            days = self._safe_int(raw_data.get("days_since_last_payment"))
            if days is not None:
                features["days_since_last_payment"] = days
                features["payment_overdue"] = 1 if days > 30 else 0

        # Renewal status
        if "renewal_date" in raw_data:
            renewal_str = raw_data.get("renewal_date")
            if renewal_str:
                try:
                    renewal_date = pd.to_datetime(renewal_str)
                    days_to_renewal = (renewal_date - utcnow()).days
                    features["days_to_renewal"] = max(-1000, days_to_renewal)
                    features["renewal_overdue"] = 1 if days_to_renewal < 0 else 0
                    features["renewal_soon"] = 1 if 0 <= days_to_renewal <= 90 else 0
                except:
                    pass

        return features

    def _compute_engagement_features(self, raw_data: Dict) -> Dict[str, Any]:
        """Features from usage and engagement"""

        features = {}

        # Feature usage
        if "features_enabled" in raw_data:
            enabled = self._safe_int(raw_data.get("features_enabled"))
            if enabled:
                features["features_enabled"] = enabled
                features["is_power_user"] = 1 if enabled > 5 else 0

        # Monthly active users
        if "monthly_active_users" in raw_data:
            mau = self._safe_int(raw_data.get("monthly_active_users"))
            if mau:
                features["monthly_active_users"] = mau
                features["mau_log"] = np.log1p(mau)

        # API usage / activity
        if "api_calls_last_30d" in raw_data:
            calls = self._safe_int(raw_data.get("api_calls_last_30d"))
            if calls:
                features["api_calls_last_30d"] = calls
                features["api_active"] = 1 if calls > 100 else 0

        # Support tickets
        if "support_tickets_last_30d" in raw_data:
            tickets = self._safe_int(raw_data.get("support_tickets_last_30d"))
            if tickets is not None:
                features["support_tickets_last_30d"] = tickets
                features["high_support_volume"] = 1 if tickets > 5 else 0

        # Last login / activity
        if "days_since_last_login" in raw_data:
            days = self._safe_int(raw_data.get("days_since_last_login"))
            if days is not None:
                features["days_since_last_login"] = days
                features["dormant_90d"] = 1 if days > 90 else 0
                features["dormant_30d"] = 1 if days > 30 else 0

        return features

    def _compute_health_features(self, raw_data: Dict) -> Dict[str, Any]:
        """Composite health indicators"""

        features = {}

        # Security score (if available)
        if "security_score" in raw_data:
            score = self._safe_float(raw_data.get("security_score"))
            if score is not None:
                features["security_score"] = score / 100.0 if score > 1 else score  # Normalize to 0-1

        # Implementation status
        if "implementation_status" in raw_data:
            status = raw_data.get("implementation_status", "").lower()
            features["implementation_complete"] = 1 if status == "complete" else 0

        # Training completed
        if "training_completed" in raw_data:
            features["training_completed"] = 1 if raw_data.get("training_completed") else 0

        return features

    def _compute_trend_features(
        self,
        organization_id: int,
        customer_id: str,
        as_of_date: datetime
    ) -> Dict[str, Any]:
        """Features computed from trends over time"""

        features = {}

        # Get last 3 snapshots of customer data
        snapshots = []
        for days_back in [0, 30, 90]:
            date = as_of_date - timedelta(days=days_back)
            snapshot = self._get_customer_data(organization_id, customer_id, date)
            if snapshot:
                snapshots.append((days_back, snapshot))

        if len(snapshots) >= 2:
            # MRR trend
            mrr_current = self._safe_float(snapshots[0][1].get("mrr"))
            mrr_30d_ago = self._safe_float(snapshots[1][1].get("mrr")) if len(snapshots) > 1 else None
            if mrr_current and mrr_30d_ago:
                mrr_change = ((mrr_current - mrr_30d_ago) / mrr_30d_ago) * 100
                features["mrr_change_30d_pct"] = mrr_change
                features["mrr_growing"] = 1 if mrr_change > 5 else 0
                features["mrr_declining"] = 1 if mrr_change < -5 else 0

            # Usage trend
            usage_current = self._safe_int(snapshots[0][1].get("monthly_active_users"))
            usage_30d_ago = self._safe_int(snapshots[1][1].get("monthly_active_users")) if len(snapshots) > 1 else None
            if usage_current and usage_30d_ago:
                usage_change = ((usage_current - usage_30d_ago) / max(1, usage_30d_ago)) * 100
                features["usage_change_30d_pct"] = usage_change
                features["usage_growing"] = 1 if usage_change > 10 else 0
                features["usage_declining"] = 1 if usage_change < -10 else 0

            # Activity trend
            activity_current = self._safe_int(snapshots[0][1].get("api_calls_last_30d"))
            activity_30d_ago = self._safe_int(snapshots[1][1].get("api_calls_last_30d")) if len(snapshots) > 1 else None
            if activity_current and activity_30d_ago:
                activity_change = activity_current - activity_30d_ago
                features["activity_change_30d"] = activity_change

        return features

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert to int"""
        if value is None:
            return None
        try:
            return int(float(value))
        except:
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert to float"""
        if value is None:
            return None
        try:
            return float(value)
        except:
            return None

    def get_batch_features(
        self,
        organization_id: int,
        customer_ids: List[str],
        as_of_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get features for multiple customers as DataFrame
        Ready for ML model input
        """
        features_list = []

        for customer_id in customer_ids:
            features = self.get_customer_features(organization_id, customer_id, as_of_date)
            features["customer_id"] = customer_id
            features_list.append(features)

        if not features_list:
            return pd.DataFrame()

        df = pd.DataFrame(features_list)

        # Fill missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

        # One-hot encode categorical columns
        categorical_cols = ["industry", "country"]
        for col in categorical_cols:
            if col in df.columns:
                df = pd.get_dummies(df, columns=[col], prefix=col, drop_first=True)

        return df

    def get_feature_statistics(
        self,
        organization_id: int,
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Compute statistics across all customers
        Useful for normalization
        """
        # Get all customer IDs
        customer_ids = self.db.query(CustomerData.customer_id).filter(
            CustomerData.organization_id == organization_id
        ).distinct().all()

        customer_ids = [c[0] for c in customer_ids if c[0]]

        if not customer_ids:
            return {}

        df = self.get_batch_features(organization_id, customer_ids, as_of_date)

        if df.empty:
            return {}

        stats = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col != "customer_id":
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "p25": float(df[col].quantile(0.25)),
                    "p75": float(df[col].quantile(0.75))
                }

        return stats
