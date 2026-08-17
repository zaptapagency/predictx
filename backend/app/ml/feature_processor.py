import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import importlib.util
import os
from app.utils import setup_logger

logger = setup_logger(__name__)


class FeatureProcessor:
    """Use preprocessing and feature engineering code from external repo"""

    def __init__(self, repo_path: str = None):
        """
        Initialize with preprocessing/feature engineering modules

        Args:
            repo_path: Path to lightgbm repo
        """
        if repo_path is None:
            repo_path = os.getenv("LIGHTGBM_REPO_PATH", "/app/lightgbm-repo")

        self.repo_path = Path(repo_path)
        self.training_path = self.repo_path / "training"

        # Dynamically import your preprocessing module
        self.preprocess_module = self._load_module("preprocess")
        self.feature_eng_module = self._load_module("feature_engineering")

    def _load_module(self, module_name: str):
        """Dynamically load Python module from external repo"""

        module_path = self.training_path / f"{module_name}.py"

        if not module_path.exists():
            logger.warning(f"Module not found: {module_path}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f"Loaded module: {module_name}")
            return module
        except Exception as e:
            logger.error(f"Error loading module {module_name}: {str(e)}")
            return None

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing logic"""

        if self.preprocess_module and hasattr(self.preprocess_module, "preprocess"):
            try:
                df_processed = self.preprocess_module.preprocess(df)
                logger.info(f"Applied preprocessing: {df.shape} -> {df_processed.shape}")
                return df_processed
            except Exception as e:
                logger.error(f"Error in preprocessing: {str(e)}")
                return df

        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply feature engineering logic"""

        if (
            self.feature_eng_module
            and hasattr(self.feature_eng_module, "engineer_features")
        ):
            try:
                df_engineered = self.feature_eng_module.engineer_features(df)
                logger.info(
                    f"Applied feature engineering: {df.shape} -> {df_engineered.shape}"
                )
                return df_engineered
            except Exception as e:
                logger.error(f"Error in feature engineering: {str(e)}")
                return df

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full preprocessing pipeline"""

        df = self.preprocess(df)
        df = self.engineer_features(df)

        return df

    def validate_features(self, df: pd.DataFrame, required_features: List[str]) -> bool:
        """Validate that all required features are present"""

        missing_features = set(required_features) - set(df.columns)

        if missing_features:
            logger.error(f"Missing features: {missing_features}")
            return False

        return True
