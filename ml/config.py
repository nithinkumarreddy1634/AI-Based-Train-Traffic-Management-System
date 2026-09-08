"""
Machine Learning Configuration for Phase 6 Train Delay Prediction.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAVED_MODELS_DIR = Path(__file__).resolve().parent / "saved_models"

DATASET_PATH = DATA_DIR / "train_delay_dataset.csv"
MODEL_PATH = SAVED_MODELS_DIR / "delay_prediction_model.pkl"
PREPROCESSOR_PATH = SAVED_MODELS_DIR / "preprocessing_pipeline.pkl"
METADATA_PATH = SAVED_MODELS_DIR / "model_metadata.json"

# Random seed for strict reproducibility
RANDOM_STATE = 42

# Synthetic Dataset Parameters
SYNTHETIC_DATASET_SIZE = 6500
TEST_SPLIT_RATIO = 0.20

# Live Simulation Inference Settings
DELAY_PREDICTION_INTERVAL_SECONDS = 10.0
DELAY_PREDICTION_TICK_INTERVAL = 20  # Every 20 simulation ticks (~10s)

