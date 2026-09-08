"""
Machine Learning Train Delay Prediction Package.
Phase 6: Synthetic dataset generation, multi-model evaluation, feature importance,
and low-latency inference for train arrival delay forecasting.
"""

from .config import (
    DATASET_PATH,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    METADATA_PATH,
    RANDOM_STATE,
    SYNTHETIC_DATASET_SIZE,
    DELAY_PREDICTION_INTERVAL_SECONDS,
)
from .features import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURES,
    TARGET,
    TRAIN_TYPES,
    PRIORITIES,
    TIMES_OF_DAY,
    DAY_TYPES,
)
from .models.predict import DelayPredictionService, delay_prediction_service

__all__ = [
    "DATASET_PATH",
    "MODEL_PATH",
    "PREPROCESSOR_PATH",
    "METADATA_PATH",
    "RANDOM_STATE",
    "SYNTHETIC_DATASET_SIZE",
    "DELAY_PREDICTION_INTERVAL_SECONDS",
    "NUMERICAL_FEATURES",
    "CATEGORICAL_FEATURES",
    "ALL_FEATURES",
    "TARGET",
    "TRAIN_TYPES",
    "PRIORITIES",
    "TIMES_OF_DAY",
    "DAY_TYPES",
    "DelayPredictionService",
    "delay_prediction_service",
]

