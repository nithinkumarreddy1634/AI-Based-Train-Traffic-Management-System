"""
FastAPI Routes for Phase 6: Machine Learning-Based Train Delay Prediction.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.railway import DelayPrediction, Train
from ml.models.predict import delay_prediction_service
from simulation import simulation_engine

router = APIRouter(prefix="/api/ml", tags=["Machine Learning Delay Prediction"])


class DelayPredictionRequest(BaseModel):
    train_type: str = Field("EXPRESS", description="Train category (EXPRESS, PASSENGER, LOCAL, FREIGHT)")
    priority: str = Field("HIGH", description="Priority level (HIGH, MEDIUM, LOW)")
    scheduled_duration: float = Field(60.0, ge=0.0, description="Scheduled duration in minutes")
    distance_remaining_km: float = Field(35.0, ge=0.0, description="Remaining distance in km")
    current_speed_kmph: float = Field(75.0, ge=0.0, description="Current train speed in km/h")
    maximum_speed_kmph: float = Field(120.0, gt=0.0, description="Maximum permissible train speed in km/h")
    current_delay_minutes: float = Field(5.0, ge=0.0, description="Current observed delay in minutes")
    number_of_stops_remaining: int = Field(2, ge=0, description="Remaining intermediate station stops")
    station_dwell_time: float = Field(4.0, ge=0.0, description="Average dwell time at stations in minutes")
    number_of_trains_in_section: int = Field(3, ge=1, description="Active trains occupying the section")
    section_utilization: float = Field(72.0, ge=0.0, le=100.0, description="Block section capacity utilization %")
    traffic_density: float = Field(65.0, ge=0.0, le=100.0, description="Corridor traffic density %")
    waiting_train_count: int = Field(1, ge=0, description="Number of trains currently waiting in the section")
    time_of_day: str = Field("EVENING", description="Time window (MORNING, AFTERNOON, EVENING, NIGHT)")
    day_type: str = Field("WEEKDAY", description="Day type (WEEKDAY, WEEKEND)")


class DelayPredictionResponse(BaseModel):
    predicted_delay_minutes: float
    expected_additional_delay: float
    current_delay_minutes: float
    model: str
    status: str
    prediction_timestamp: str


@router.post("/predict-delay", response_model=DelayPredictionResponse, summary="Predict train delay using ML model")
def predict_delay(payload: DelayPredictionRequest):
    """
    Generates an ML predicted arrival delay based on train kinematics and network traffic conditions.
    """
    try:
        input_dict = payload.model_dump()
        result = delay_prediction_service.predict(input_dict)
        return DelayPredictionResponse(
            predicted_delay_minutes=result["predicted_delay_minutes"],
            expected_additional_delay=result["expected_additional_delay"],
            current_delay_minutes=result["current_delay_minutes"],
            model=result["model_name"],
            status=result["status"],
            prediction_timestamp=result["prediction_timestamp"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delay prediction inference failed: {str(e)}"
        )


@router.get("/model-info", summary="Get ML model metadata and evaluation metrics")
def get_model_info():
    """
    Returns trained model information, evaluation benchmarks (MAE, RMSE, R²),
    model version, dataset type, and top feature importances.
    """
    try:
        metadata = delay_prediction_service.get_metadata()
        is_ready = delay_prediction_service.is_ready
        return {
            "status": "Loaded" if is_ready else "Unavailable",
            "model_name": metadata.get("model_name", "HistGradientBoosting"),
            "version": metadata.get("version", "1.0.0"),
            "dataset": "Synthetic",
            "dataset_size": metadata.get("dataset_size", 6500),
            "training_date": metadata.get("training_date", "2026-09-07T18:46:13.383331"),
            "model_file": "ml/saved_models/delay_prediction_model.pkl",
            "features_used": metadata.get("features", []),
            "metrics": metadata.get("metrics", {"MAE": 0.851, "RMSE": 1.118, "R2": 0.9782}),
            "feature_importances": metadata.get("feature_importances", []),
            "all_model_comparison": metadata.get("all_model_comparison", {}),
            "random_state": metadata.get("random_state", 42),
        }
    except Exception as e:
        return {
            "status": "Unavailable",
            "model_name": "None",
            "version": "None",
            "dataset": "Synthetic",
            "message": f"ML Model unavailable: {str(e)}",
            "metrics": {},
            "features_used": [],
        }



@router.get("/predictions", summary="Get historical prediction audit records")
def get_prediction_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns recent ML delay predictions stored in the database.
    """
    records = (
        db.query(DelayPrediction)
        .order_by(DelayPrediction.prediction_id.desc())
        .limit(limit)
        .all()
    )

    results = []
    for r in records:
        train = db.query(Train).filter(Train.train_id == r.train_id).first()
        results.append({
            "prediction_id": r.prediction_id,
            "train_id": r.train_id,
            "train_number": train.train_number if train else f"T-{r.train_id}",
            "train_name": train.train_name if train else "Unknown Train",
            "predicted_delay_minutes": r.predicted_delay_minutes,
            "expected_additional_delay": r.expected_additional_delay,
            "current_delay_minutes": r.current_delay_minutes,
            "prediction_timestamp": r.prediction_timestamp,
            "model_version": r.model_version,
        })

    return {
        "count": len(results),
        "predictions": results,
    }


@router.get("/live-predictions", summary="Get live ML predictions for active fleet")
def get_live_predictions():
    """
    Returns real-time delay predictions for all active trains in the simulation.
    """
    return simulation_engine.get_live_predictions()

