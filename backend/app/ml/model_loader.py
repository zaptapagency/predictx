import os
import pickle
import json
from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd
from app.utils import setup_logger

logger = setup_logger(__name__)


class LightGBMModelLoader:
    """Load LightGBM models from external repository"""

    def __init__(self, repo_path: str = None):
        """
        Initialize loader

        Args:
            repo_path: Path to lightgbm repo (e.g., /app/lightgbm-repo)
        """
        if repo_path is None:
            repo_path = os.getenv("LIGHTGBM_REPO_PATH", "/app/lightgbm-repo")

        self.repo_path = Path(repo_path)
        self.models_path = self.repo_path / "models"

        if not self.models_path.exists():
            raise ValueError(f"Models directory not found at {self.models_path}")

        self.universal_model = None
        self.adapters = {}
        self.metadata = {}

        logger.info(f"Initialized LightGBMModelLoader with repo at {repo_path}")

    def load_all_models(self, version: str = "latest") -> bool:
        """Load all models (universal + adapters)"""

        try:
            # Find model version directory
            if version == "latest":
                version_dir = self._find_latest_version()
            else:
                version_dir = self.models_path / version

            if not version_dir.exists():
                raise ValueError(f"Model version directory not found: {version_dir}")

            logger.info(f"Loading models from {version_dir}")

            # Load universal model
            self.universal_model = self._load_model(version_dir / "universal_model.pkl")

            # Load metadata
            self.metadata = self._load_metadata(
                version_dir / "universal_model_metadata.json"
            )

            # Load adapters
            adapters_dir = version_dir / "adapters"
            if adapters_dir.exists():
                self._load_adapters(adapters_dir)

            # Load adapters from parent directory (backward compatibility)
            if (self.models_path / "adapters").exists():
                self._load_adapters(self.models_path / "adapters")

            logger.info(f"Successfully loaded {len(self.adapters)} adapters")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False

    def _find_latest_version(self) -> Path:
        """Find the latest model version directory"""

        version_dirs = [
            d
            for d in self.models_path.iterdir()
            if d.is_dir() and d.name != "adapters"
        ]

        if not version_dirs:
            raise ValueError("No model version directories found")

        # Sort by version number (assumes v1.0, v1.1, v2.0, etc.)
        version_dirs.sort(key=lambda x: self._parse_version(x.name), reverse=True)

        return version_dirs[0]

    @staticmethod
    def _parse_version(version_str: str) -> tuple:
        """Parse version string to tuple for sorting"""
        try:
            version_str = version_str.lstrip("v")
            parts = version_str.split(".")
            return tuple(int(p) for p in parts)
        except:
            return (0, 0)

    def _load_model(self, model_path: Path):
        """Load a single pickle model"""

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            logger.info(f"Loaded model from {model_path.name}")
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {str(e)}")
            raise

    def _load_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        """Load model metadata"""

        if not metadata_path.exists():
            logger.warning(f"Metadata file not found: {metadata_path}")
            return {}

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata from {metadata_path.name}")
            return metadata
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {}

    def _load_adapters(self, adapters_dir: Path):
        """Load all adapter models from directory"""

        for adapter_file in adapters_dir.glob("*.pkl"):
            vertical_name = adapter_file.stem

            try:
                model = self._load_model(adapter_file)
                self.adapters[vertical_name] = model
                logger.info(f"Loaded adapter: {vertical_name}")
            except Exception as e:
                logger.error(f"Error loading adapter {vertical_name}: {str(e)}")

    def predict(
        self,
        features: pd.DataFrame,
        vertical: str = None,
        use_adapter: bool = True,
    ) -> pd.DataFrame:
        """
        Make predictions using universal model + adapter

        Args:
            features: DataFrame with feature values
            vertical: Vertical name for adapter selection
            use_adapter: Whether to use vertical adapter

        Returns:
            Predictions DataFrame
        """

        if self.universal_model is None:
            raise ValueError("Models not loaded. Call load_all_models() first.")

        predictions = []

        # Get universal predictions
        universal_preds = self.universal_model.predict_proba(features)

        for idx, _ in features.iterrows():
            pred_dict = {
                "universal": universal_preds[idx][1]
                if len(universal_preds[idx]) > 1
                else universal_preds[idx][0]
            }

            # Get adapter predictions if vertical specified
            if use_adapter and vertical and vertical in self.adapters:
                adapter_model = self.adapters[vertical]
                adapter_pred = adapter_model.predict_proba(features.iloc[[idx]])
                pred_dict["adapter"] = (
                    adapter_pred[0][1]
                    if len(adapter_pred[0]) > 1
                    else adapter_pred[0][0]
                )

            # Ensemble: 40% universal, 60% adapter
            if "adapter" in pred_dict:
                final_pred = 0.4 * pred_dict["universal"] + 0.6 * pred_dict["adapter"]
            else:
                final_pred = pred_dict["universal"]

            pred_dict["final"] = final_pred
            predictions.append(pred_dict)

        return pd.DataFrame(predictions)

    def get_feature_names(self) -> Optional[list]:
        """Get feature names from metadata"""

        if self.metadata and "feature_names" in self.metadata:
            return self.metadata["feature_names"]

        # Try to get from model if available
        if hasattr(self.universal_model, "feature_names_"):
            return list(self.universal_model.feature_names_)

        if hasattr(self.universal_model, "feature_name"):
            return list(self.universal_model.feature_name)

        return None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""

        return {
            "version": self.metadata.get("version", "unknown"),
            "training_date": self.metadata.get("training_date"),
            "accuracy": self.metadata.get("accuracy"),
            "feature_count": self.metadata.get("feature_count"),
            "adapters_loaded": len(self.adapters),
            "adapter_names": list(self.adapters.keys()),
            "universal_model_type": type(self.universal_model).__name__,
        }
