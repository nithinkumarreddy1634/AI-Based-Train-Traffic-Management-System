"""
FastAPI Route Handlers for AI-Powered Train Traffic Optimization (Phase 7).

Endpoints:
- POST /api/optimization/run        : Execute optimizer on current live state or target section.
- GET  /api/optimization/latest     : Retrieve latest optimization run result.
- GET  /api/optimization/history    : Retrieve historical optimization runs.
- POST /api/optimization/benchmark  : Run evaluation across standard benchmark scenarios.
- POST /api/optimization/preview    : Preview forward-projected dispatch timeline.
- POST /api/optimization/apply      : Apply dispatch holds/priorities to live simulation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.railway import OptimizationRun, Track, SafetyAuditLog
from simulation.engine import simulation_engine
from optimization import DEFAULT_OPTIMIZER, OptimizationResult
from safety import DEFAULT_SAFETY_VALIDATOR

router = APIRouter(prefix="/api/optimization", tags=["optimization"])

# In-memory cache for latest optimization result
_latest_optimization_result: Optional[Dict[str, Any]] = None


class RunOptimizationRequest(BaseModel):
    section_id: Optional[int] = None
    target_section_name: Optional[str] = None
    override_trains: Optional[List[Dict[str, Any]]] = None


class ApplyOptimizationRequest(BaseModel):
    optimization_id: Optional[int] = None
    train_recommendations: List[Dict[str, Any]]


class PreviewOptimizationRequest(BaseModel):
    train_recommendations: List[Dict[str, Any]]


@router.post("/run", response_model=Dict[str, Any])
@router.post("/optimize", response_model=Dict[str, Any])
def run_optimization(
    payload: Optional[RunOptimizationRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Executes AI optimization using live simulation state, Phase 5 conflicts,
    and Phase 6 ML delay forecasts.
    """
    global _latest_optimization_result

    # 1. Gather active trains
    if payload and payload.override_trains:
        candidate_trains = payload.override_trains
    else:
        live_trains = simulation_engine.get_live_trains()
        # Filter for active moving/waiting trains (exclude ARRIVED)
        candidate_trains = [
            t for t in live_trains
            if t.get("status") in ("RUNNING", "WAITING", "STOPPED", "SCHEDULED", "DELAYED")
        ]

    # 2. Gather section information
    sections_live = simulation_engine.get_sections_live()
    target_sec = None
    if payload and payload.section_id:
        target_sec = next((s for s in sections_live if s["section_id"] == payload.section_id), None)

    if not target_sec and sections_live:
        # Default to the most congested section or section 1
        sorted_by_util = sorted(sections_live, key=lambda s: -s.get("utilization_percentage", 0.0))
        target_sec = sorted_by_util[0]

    sec_info = {
        "section_id": target_sec["section_id"] if target_sec else 1,
        "section_name": target_sec["section_name"] if target_sec else "Central Corridor",
        "length_km": target_sec.get("length_km", 20.0) if target_sec else 20.0,
        "max_speed_kmph": target_sec.get("max_speed_kmph", 110.0) if target_sec else 110.0,
        "is_single_track": False,
        "utilization_pct": target_sec.get("utilization_percentage", 60.0) if target_sec else 60.0,
    }

    # 3. Gather active Phase 5 conflicts
    scan_res = getattr(simulation_engine, "last_conflict_scan_result", {}) or {}
    active_confs = scan_res.get("active_conflicts", [])

    # Format conflict dictionaries
    conf_dicts = []
    for c in active_confs:
        conf_dicts.append({
            "conflict_id": getattr(c, "conflict_id", ""),
            "severity": getattr(c, "severity", "MEDIUM"),
            "section_name": getattr(c, "section_name", ""),
            "conflict_type": getattr(c, "conflict_type", "")
        })

    # 4. Ingest ML Delay Predictions
    # Each train from simulation_engine already has predicted_delay_minutes and expected_additional_delay
    formatted_trains = []
    for t in candidate_trains:
        formatted_trains.append({
            "train_id": t["train_id"],
            "train_number": t.get("train_number", f"T{t['train_id']}"),
            "train_name": t.get("train_name", ""),
            "train_type": t.get("train_type", "PASSENGER"),
            "priority": t.get("priority", "MEDIUM"),
            "current_speed_kmph": float(t.get("speed_kmph") or t.get("current_speed_kmph") or 60.0),
            "max_speed_kmph": float(t.get("max_speed_kmph", 110.0)),
            "current_position_km": float(t.get("current_position_km", 0.0)),
            "distance_to_section_km": max(0.0, float(t.get("distance_remaining_km", 10.0))),
            "direction": t.get("direction", "UP"),
            "status": t.get("status", "SCHEDULED"),
            "current_delay_minutes": float(t.get("current_delay_minutes", 0.0)),
            "predicted_additional_delay": float(t.get("expected_additional_delay", 0.0)),
            "ready_time_sec": 0,
        })

    # 5. Run Optimizer
    opt_result: OptimizationResult = DEFAULT_OPTIMIZER.optimize_traffic(
        trains=formatted_trains,
        section_info=sec_info,
        traffic_state={"utilization_pct": sec_info["utilization_pct"]},
        active_conflicts=conf_dicts
    )

    result_dict = opt_result.to_dict()
    _latest_optimization_result = result_dict

    # 6. Persist to SQLite Database
    try:
        run_record = OptimizationRun(
            timestamp=opt_result.timestamp,
            target_section_id=opt_result.target_section_id,
            target_section_name=opt_result.monitored_section_name,
            status=opt_result.status,
            train_count=opt_result.train_count,
            expected_throughput=opt_result.expected_throughput,
            expected_total_delay=opt_result.expected_total_delay,
            expected_waiting_time=opt_result.expected_waiting_time,
            optimization_score=opt_result.optimization_score,
            recommended_sequence_json=json.dumps(opt_result.recommended_sequence),
            train_recommendations_json=json.dumps([r.to_dict() for r in opt_result.train_recommendations]),
            before_metrics_json=json.dumps(opt_result.before_vs_after.to_dict()),
            after_metrics_json=json.dumps(result_dict["before_vs_after"]),
            explanation=opt_result.explanation,
            applied=False
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)
        result_dict["optimization_id"] = run_record.optimization_id
    except Exception as db_err:
        print(f"[!] Warning: Could not persist optimization run to DB: {db_err}")

    return result_dict


@router.get("/latest", response_model=Dict[str, Any])
def get_latest_optimization(db: Session = Depends(get_db)):
    """Returns the most recent optimization result from memory or database."""
    global _latest_optimization_result

    if _latest_optimization_result is not None:
        return _latest_optimization_result

    # Check database
    latest_run = db.query(OptimizationRun).order_by(OptimizationRun.optimization_id.desc()).first()
    if latest_run:
        try:
            recs = json.loads(latest_run.train_recommendations_json or "[]")
            seq = json.loads(latest_run.recommended_sequence_json or "[]")
            before_after = json.loads(latest_run.before_metrics_json or "{}")
            return {
                "optimization_id": latest_run.optimization_id,
                "timestamp": latest_run.timestamp,
                "status": latest_run.status,
                "target_section_id": latest_run.target_section_id,
                "monitored_section_name": latest_run.target_section_name,
                "train_count": latest_run.train_count,
                "recommended_sequence": seq,
                "train_recommendations": recs,
                "expected_throughput": latest_run.expected_throughput,
                "expected_total_delay": latest_run.expected_total_delay,
                "expected_waiting_time": latest_run.expected_waiting_time,
                "optimization_score": latest_run.optimization_score,
                "before_vs_after": before_after,
                "explanation": latest_run.explanation,
                "factor_contributions": {
                    "throughput_maximization": 35.0,
                    "delay_mitigation": 30.0,
                    "waiting_time_minimization": 15.0,
                    "conflict_safety_headway": 12.0,
                    "priority_adherence": 8.0
                },
                "applied": latest_run.applied,
            }
        except Exception:
            pass

    # If no run exists yet, execute on current state
    return run_optimization(db=db)


@router.get("/history", response_model=Dict[str, Any])
def get_optimization_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns previous optimization runs stored in SQLite."""
    runs = db.query(OptimizationRun).order_by(OptimizationRun.optimization_id.desc()).limit(limit).all()
    history = []
    for r in runs:
        try:
            seq = json.loads(r.recommended_sequence_json or "[]")
            before_after = json.loads(r.before_metrics_json or "{}")
        except Exception:
            seq = []
            before_after = {}

        history.append({
            "optimization_id": r.optimization_id,
            "timestamp": r.timestamp,
            "status": r.status,
            "monitored_section_name": r.target_section_name,
            "train_count": r.train_count,
            "expected_throughput": r.expected_throughput,
            "expected_total_delay": r.expected_total_delay,
            "expected_waiting_time": r.expected_waiting_time,
            "optimization_score": r.optimization_score,
            "recommended_sequence": seq,
            "before_vs_after": before_after,
            "applied": r.applied,
        })
    return {"total": len(history), "runs": history}


@router.post("/benchmark", response_model=List[Dict[str, Any]])
def run_benchmark():
    """
    Executes all 4 required benchmark scenarios:
    1. Low Traffic (5 trains)
    2. Medium Traffic (10 trains)
    3. Heavy Bottleneck Traffic (15 trains)
    4. High Delay Mitigation (6 trains)
    """
    results = DEFAULT_OPTIMIZER.run_benchmark_scenarios()
    return [r.to_dict() for r in results]


@router.post("/preview", response_model=Dict[str, Any])
def preview_optimization(payload: PreviewOptimizationRequest):
    """
    Forward-projects the recommended sequence into a simulation timeline
    without mutating live simulation state.
    """
    return simulation_engine.preview_optimization_plan(payload.train_recommendations)


@router.post("/apply", response_model=Dict[str, Any])
def apply_optimization(
    payload: ApplyOptimizationRequest,
    db: Session = Depends(get_db)
):
    """
    Applies the recommended dispatch order (holding trains at signals/loops and
    releasing them at designated headway intervals) to the simulation engine.
    Guarded by the fail-safe Safety Validation Engine.
    """
    # 1. Fail-Safe Gate: Inspect through formal safety validation pipeline
    val_payload = {
        "optimization_id": payload.optimization_id,
        "train_recommendations": payload.train_recommendations
    }
    tracks_db = db.query(Track).all()
    curr_tracks = {
        t.track_id: {
            "track_id": t.track_id,
            "track_number": t.track_number,
            "is_occupied": (t.status == "OCCUPIED" or t.occupied_by_train is not None),
            "status": t.status,
            "occupied_by_train": t.occupied_by_train
        }
        for t in tracks_db
    }
    curr_conflicts = (getattr(simulation_engine, "last_conflict_scan_result", {}) or {}).get("active_conflicts", [])
    val_state = {
        "tracks": curr_tracks,
        "conflicts": curr_conflicts
    }
    val_result = DEFAULT_SAFETY_VALIDATOR.validate(val_payload, val_state)

    if not val_result.is_approved:
        # Audit log the rejected application attempt
        try:
            audit = SafetyAuditLog(
                recommendation_id=payload.optimization_id,
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="REJECTED",
                safety_score_status="UNSAFE",
                rules_checked_json=json.dumps(val_result.rules_checked),
                violations_json=json.dumps([v.to_dict() for v in val_result.violations]),
                warnings_json=json.dumps([w.to_dict() for w in val_result.warnings]),
                violations_count=len(val_result.violations),
                warnings_count=len(val_result.warnings),
                applied_to_simulation=False,
                summary_notes="Apply operation blocked by fail-safe gatekeeper due to safety violations."
            )
            db.add(audit)
            db.commit()
        except Exception:
            pass

        raise HTTPException(
            status_code=400,
            detail={
                "error": "SAFETY_VALIDATION_FAILED",
                "message": "Optimization plan rejected by safety validator. Cannot apply to simulation.",
                "violations": [v.to_dict() for v in val_result.violations],
                "warnings": [w.to_dict() for w in val_result.warnings]
            }
        )

    # 2. Approved: apply to simulation engine
    result = simulation_engine.apply_optimization_plan(payload.train_recommendations)

    if payload.optimization_id:
        run_record = db.query(OptimizationRun).filter(OptimizationRun.optimization_id == payload.optimization_id).first()
        if run_record:
            run_record.applied = True
            db.commit()

    global _latest_optimization_result
    if _latest_optimization_result:
        _latest_optimization_result["applied"] = True

    # Audit log the approved application
    try:
        audit = SafetyAuditLog(
            recommendation_id=payload.optimization_id,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="APPROVED",
            safety_score_status=val_result.safety_score_status,
            rules_checked_json=json.dumps(val_result.rules_checked),
            violations_json="[]",
            warnings_json=json.dumps([w.to_dict() for w in val_result.warnings]),
            violations_count=0,
            warnings_count=len(val_result.warnings),
            applied_to_simulation=True,
            summary_notes="Applied approved optimization schedule to simulation engine."
        )
        db.add(audit)
        db.commit()
    except Exception:
        pass

    return result

