"""
Automated Test Suite for Phase 6: Machine Learning Train Delay Prediction.
Tests:
- Dataset generation and schema consistency
- Preprocessing transformation pipeline
- Model evaluation metrics and model serialization
- DelayPredictionService inference
- Demonstration traffic scenarios (Low vs Medium vs Heavy vs Delayed)
- FastAPI REST endpoints (/api/ml/predict-delay, /api/ml/model-info, /api/ml/predictions, /api/ml/live-predictions)
"""

import os
import json
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from ml.config import DATASET_PATH, MODEL_PATH, PREPROCESSOR_PATH, METADATA_PATH
from ml.features import NUMERICAL_FEATURES, CATEGORICAL_FEATURES, ALL_FEATURES, TARGET
from ml.data.generate_dataset import generate_synthetic_dataset
from ml.data.preprocessing import build_preprocessing_pipeline, load_preprocessor
from ml.models.evaluate_model import evaluate_predictions, select_best_model
from ml.models.predict import delay_prediction_service
from backend.app.main import app

client = TestClient(app)


class TestDatasetAndPreprocessing:
    def test_synthetic_dataset_properties(self):
        assert DATASET_PATH.exists(), "Dataset file must exist on disk"
        df = pd.read_csv(DATASET_PATH)

        # Check minimum dataset size requirement (>= 5,000 samples)
        assert len(df) >= 5000, f"Expected >= 5000 records, got {len(df)}"

        # Check required columns
        for col in ALL_FEATURES + [TARGET]:
            assert col in df.columns, f"Missing required column: {col}"

        # No null values
        assert df[ALL_FEATURES + [TARGET]].isnull().sum().sum() == 0, "Unexpected null values in dataset"

        # Check target sanity: total_delay >= 0
        assert (df[TARGET] >= 0).all(), "Negative delay values found"

    def test_preprocessing_pipeline_transforms_correctly(self):
        assert PREPROCESSOR_PATH.exists(), "Preprocessing pipeline file must exist"
        preprocessor = load_preprocessor()

        sample_data = pd.DataFrame([{
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "scheduled_duration": 60.0,
            "distance_remaining_km": 40.0,
            "current_speed_kmph": 80.0,
            "maximum_speed_kmph": 120.0,
            "current_delay_minutes": 5.0,
            "number_of_stops_remaining": 2,
            "station_dwell_time": 3.0,
            "number_of_trains_in_section": 2,
            "section_utilization": 50.0,
            "traffic_density": 45.0,
            "waiting_train_count": 0,
            "time_of_day": "MORNING",
            "day_type": "WEEKDAY",
        }])

        X_trans = preprocessor.transform(sample_data[ALL_FEATURES])
        assert isinstance(X_trans, np.ndarray)
        assert X_trans.shape[0] == 1
        assert X_trans.shape[1] >= len(NUMERICAL_FEATURES)


class TestModelArtifactsAndEvaluation:
    def test_model_and_metadata_serialization(self):
        assert MODEL_PATH.exists(), "Saved model pickle must exist"
        assert METADATA_PATH.exists(), "Model metadata JSON must exist"

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        assert "model_name" in metadata
        assert "metrics" in metadata
        metrics = metadata["metrics"]
        assert "MAE" in metrics and "RMSE" in metrics and "R2" in metrics

        # Ensure performance meets quality standards
        assert metrics["R2"] > 0.85, f"R² score ({metrics['R2']}) is lower than expected threshold (> 0.85)"
        assert metrics["MAE"] < 3.0, f"MAE ({metrics['MAE']}) is higher than expected threshold (< 3.0 min)"

        # Check feature importances
        assert "feature_importances" in metadata
        assert len(metadata["feature_importances"]) > 0

    def test_evaluate_predictions_function(self):
        y_true = np.array([5.0, 10.0, 15.0, 20.0])
        y_pred = np.array([5.2, 9.8, 14.9, 20.1])
        res = evaluate_predictions(y_true, y_pred)
        assert res["MAE"] < 0.3
        assert res["RMSE"] < 0.3
        assert res["R2"] > 0.99


class TestPredictionServiceAndScenarios:
    def test_service_prediction_output(self):
        payload = {
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "scheduled_duration": 60,
            "distance_remaining_km": 35,
            "current_speed_kmph": 75,
            "maximum_speed_kmph": 120,
            "current_delay_minutes": 5,
            "number_of_stops_remaining": 2,
            "station_dwell_time": 4,
            "number_of_trains_in_section": 3,
            "section_utilization": 72,
            "traffic_density": 65,
            "waiting_train_count": 1,
            "time_of_day": "EVENING",
            "day_type": "WEEKDAY",
        }
        res = delay_prediction_service.predict(payload)
        assert res["status"] == "success"
        assert isinstance(res["predicted_delay_minutes"], float)
        assert res["predicted_delay_minutes"] >= 0.0
        assert res["expected_additional_delay"] >= 0.0

    def test_demonstration_traffic_scenarios(self):
        """
        Demonstrates that predicted delay monotonically increases with traffic congestion:
        Scenario A (Low Traffic) < Scenario B (Medium Traffic) < Scenario C (Heavy Traffic)
        """
        # Scenario A: Low traffic (clear line, free flow)
        scenario_a = {
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "scheduled_duration": 60,
            "distance_remaining_km": 30,
            "current_speed_kmph": 115,
            "maximum_speed_kmph": 120,
            "current_delay_minutes": 0,
            "number_of_stops_remaining": 1,
            "station_dwell_time": 2,
            "number_of_trains_in_section": 1,
            "section_utilization": 15,
            "traffic_density": 10,
            "waiting_train_count": 0,
            "time_of_day": "NIGHT",
            "day_type": "WEEKDAY",
        }

        # Scenario B: Medium traffic (moderate density)
        scenario_b = dict(scenario_a)
        scenario_b.update({
            "current_speed_kmph": 85,
            "number_of_trains_in_section": 2,
            "section_utilization": 50,
            "traffic_density": 45,
            "waiting_train_count": 0,
            "time_of_day": "AFTERNOON",
        })

        # Scenario C: Heavy traffic (congested section, multiple waiting trains)
        scenario_c = dict(scenario_a)
        scenario_c.update({
            "current_speed_kmph": 25,
            "number_of_trains_in_section": 3,
            "section_utilization": 88,
            "traffic_density": 85,
            "waiting_train_count": 2,
            "time_of_day": "MORNING",
        })

        # Scenario D: Existing delayed train
        scenario_d = dict(scenario_c)
        scenario_d.update({
            "current_delay_minutes": 15.0,
        })

        pred_a = delay_prediction_service.predict(scenario_a)["predicted_delay_minutes"]
        pred_b = delay_prediction_service.predict(scenario_b)["predicted_delay_minutes"]
        pred_c = delay_prediction_service.predict(scenario_c)["predicted_delay_minutes"]
        pred_d = delay_prediction_service.predict(scenario_d)["predicted_delay_minutes"]

        print(f"Scenario Predictions -> Low: {pred_a}m | Med: {pred_b}m | Heavy: {pred_c}m | Delayed: {pred_d}m")

        assert pred_a < pred_b, f"Scenario A ({pred_a}) should be less than Scenario B ({pred_b})"
        assert pred_b < pred_c, f"Scenario B ({pred_b}) should be less than Scenario C ({pred_c})"
        assert pred_c < pred_d, f"Scenario C ({pred_c}) should be less than Scenario D with existing delay ({pred_d})"


class TestMLRestAPIs:
    def test_post_predict_delay_valid_payload(self):
        payload = {
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "scheduled_duration": 60,
            "distance_remaining_km": 35,
            "current_speed_kmph": 75,
            "maximum_speed_kmph": 120,
            "current_delay_minutes": 5,
            "number_of_stops_remaining": 2,
            "station_dwell_time": 4,
            "number_of_trains_in_section": 3,
            "section_utilization": 72,
            "traffic_density": 65,
            "waiting_train_count": 1,
            "time_of_day": "EVENING",
            "day_type": "WEEKDAY",
        }
        res = client.post("/api/ml/predict-delay", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "predicted_delay_minutes" in data
        assert "expected_additional_delay" in data
        assert data["status"] == "success"

    def test_post_predict_delay_invalid_payload(self):
        # Invalid payload: negative maximum_speed_kmph
        payload = {
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "maximum_speed_kmph": -50.0,
        }
        res = client.post("/api/ml/predict-delay", json=payload)
        assert res.status_code == 422  # Unprocessable Entity

    def test_get_model_info_endpoint(self):
        res = client.get("/api/ml/model-info")
        assert res.status_code == 200
        data = res.json()
        assert "model_name" in data
        assert "metrics" in data
        assert "feature_importances" in data

    def test_get_predictions_history_endpoint(self):
        res = client.get("/api/ml/predictions")
        assert res.status_code == 200
        data = res.json()
        assert "predictions" in data
        assert "count" in data

    def test_get_live_predictions_endpoint(self):
        res = client.get("/api/ml/live-predictions")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

