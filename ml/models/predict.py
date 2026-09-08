"""
Delay Prediction Inference Service.
Loads the trained model and preprocessing pipeline once into memory, accepts train operating conditions,
and returns real-time predicted arrival delay.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, Any, Union, Optional
import joblib
import pandas as pd
import numpy as np

from ml.config import MODEL_PATH, PREPROCESSOR_PATH, METADATA_PATH
from ml.features import ALL_FEATURES, NUMERICAL_FEATURES, CATEGORICAL_FEATURES


class DelayPredictionService:
    """Thread-safe prediction service with in-memory model caching."""

    def __init__(self):
        self.model: Optional[Any] = None
        self.preprocessor: Optional[Any] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self._is_loaded: bool = False

    def load_artifacts(self, force_reload: bool = False):
        """Loads model, preprocessing pipeline, and metadata from disk."""
        if self._is_loaded and not force_reload:
            return

        if not MODEL_PATH.exists() or not PREPROCESSOR_PATH.exists():
            raise FileNotFoundError(
                f"Model or preprocessor artifact missing. Expected: {MODEL_PATH} and {PREPROCESSOR_PATH}. "
                "Run `python -m ml.models.train_model` to train and serialize the model."
            )

        self.model = joblib.load(MODEL_PATH)
        self.preprocessor = joblib.load(PREPROCESSOR_PATH)

        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"model_name": type(self.model).__name__, "version": "1.0.0"}

        self._is_loaded = True

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self.model is not None and self.preprocessor is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model performance metrics and feature importances."""
        if not self._is_loaded:
            self.load_artifacts()
        return self.metadata or {}

    def predict(
        self,
        input_data: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Generates delay prediction for a single train or batch:
        Input: feature dictionary or pandas DataFrame
        Returns:
            {
                "predicted_delay_minutes": float,
                "expected_additional_delay": float,
                "current_delay_minutes": float,
                "model_name": str,
                "status": "success",
                "prediction_timestamp": str
            }
        """
        if not self._is_loaded:
            self.load_artifacts()

        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}. Expected dict or DataFrame.")

        # Ensure all required columns exist with sensible defaults
        for col in NUMERICAL_FEATURES:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        for col in CATEGORICAL_FEATURES:
            if col not in df.columns:
                if col == "train_type":
                    df[col] = "EXPRESS"
                elif col == "priority":
                    df[col] = "MEDIUM"
                elif col == "time_of_day":
                    df[col] = "MORNING"
                elif col == "day_type":
                    df[col] = "WEEKDAY"
            else:
                df[col] = df[col].astype(str).str.upper()

        # Extract features in correct order
        X = df[ALL_FEATURES]

        # Apply preprocessing transformation
        X_trans = self.preprocessor.transform(X)

        # Predict
        raw_pred = self.model.predict(X_trans)
        predicted_delay = float(np.clip(raw_pred[0], 0.0, 300.0))
        predicted_delay = round(predicted_delay, 1)

        current_delay = float(df["current_delay_minutes"].iloc[0])
        expected_additional = max(0.0, round(predicted_delay - current_delay, 1))

        now_str = datetime.datetime.now().isoformat()
        model_name = self.metadata.get("model_name", "Trained ML Regressor")

        return {
            "predicted_delay_minutes": predicted_delay,
            "expected_additional_delay": expected_additional,
            "current_delay_minutes": current_delay,
            "model_name": model_name,
            "status": "success",
            "prediction_timestamp": now_str,
        }


delay_prediction_service = DelayPredictionService()

