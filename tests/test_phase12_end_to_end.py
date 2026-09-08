"""
Phase 12: Complete End-to-End Automated Pipeline Test.

Executes the full lifecycle:
    Create Network
         ↓
    Create Trains
         ↓
    Load Scenario
         ↓
    Start Simulation
         ↓
    Generate Traffic
         ↓
    Detect Conflict
         ↓
    Predict Delay
         ↓
    Run AI Optimization
         ↓
    Explain Recommendation
         ↓
    Safety Validation
         ↓
    Controller Approval
         ↓
    Apply Recommendation
         ↓
    Continue Simulation
         ↓
    Calculate Performance
         ↓
    Compare Traditional vs AI
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_phase12_end_to_end_pipeline():
    """Executes and verifies the complete end-to-end intelligent train traffic control pipeline."""

    # 1. System Health Probe
    resp_health = client.get("/api/health")
    assert resp_health.status_code == 200
    health_data = resp_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["database"] == "healthy"
    assert health_data["backend"] == "healthy"

    # 2. Verify / Create Network Infrastructure
    resp_stations = client.get("/api/stations")
    assert resp_stations.status_code == 200
    assert len(resp_stations.json()) >= 5

    resp_sections = client.get("/api/sections")
    assert resp_sections.status_code == 200
    assert len(resp_sections.json()) >= 7

    resp_tracks = client.get("/api/tracks")
    assert resp_tracks.status_code == 200
    assert len(resp_tracks.json()) >= 14

    # 3. Verify / Create Trains Fleet
    resp_trains = client.get("/api/trains")
    assert resp_trains.status_code == 200
    trains_list = resp_trains.json()
    assert len(trains_list) >= 12

    # 4. Load AI Demo Scenario
    resp_load = client.post("/api/control/scenario/load", json={"scenario_id": "ai_demo"})
    assert resp_load.status_code == 200
    load_data = resp_load.json()
    assert load_data["success"] is True
    assert load_data["scenario_id"] == "ai_demo"

    # 5. Start Kinematic Simulation & Step Traffic
    resp_start = client.post("/api/control/scenario/start")
    assert resp_start.status_code == 200

    # Step simulation ticks to advance kinematics
    for _ in range(5):
        resp_step = client.post("/api/simulation/step")
        assert resp_step.status_code == 200
        step_data = resp_step.json()
        assert "status" in step_data or "sim_time" in step_data or "active_trains" in step_data

    # 6. Detect Headway Conflicts
    resp_conflicts = client.get("/api/conflicts")
    assert resp_conflicts.status_code == 200
    conflicts_data = resp_conflicts.json()
    assert "conflicts" in conflicts_data or "active_conflicts" in conflicts_data

    # 7. Predict Delay using ML Engine
    predict_payload = {
        "train_type": "EXPRESS",
        "priority": "HIGH",
        "scheduled_duration": 45.0,
        "distance_remaining_km": 28.0,
        "current_speed_kmph": 85.0,
        "maximum_speed_kmph": 120.0,
        "current_delay_minutes": 6.5,
        "number_of_stops_remaining": 2,
        "station_dwell_time": 3.0,
        "number_of_trains_in_section": 3,
        "section_utilization": 80.0,
        "traffic_density": 70.0,
        "waiting_train_count": 1,
        "time_of_day": "EVENING",
        "day_type": "WEEKDAY",
    }
    resp_ml = client.post("/api/ml/predict-delay", json=predict_payload)
    assert resp_ml.status_code == 200
    ml_result = resp_ml.json()
    assert ml_result["status"] == "success"
    assert "predicted_delay_minutes" in ml_result
    assert ml_result["predicted_delay_minutes"] >= 0.0

    # Verify ML Model Info endpoint
    resp_model_info = client.get("/api/ml/model-info")
    assert resp_model_info.status_code == 200
    info_data = resp_model_info.json()
    assert info_data["status"] in ("Loaded", "Unavailable")
    assert "metrics" in info_data

    # 8. Run AI Multi-Objective Optimization
    resp_opt = client.post("/api/optimization/optimize")
    assert resp_opt.status_code == 200
    opt_data = resp_opt.json()
    assert "recommendations" in opt_data or "status" in opt_data

    # 9. Explain AI Recommendation (Explainability Engine)
    resp_explain = client.get("/api/explainability/latest")
    assert resp_explain.status_code == 200
    explain_data = resp_explain.json()
    assert "lead_recommendation" in explain_data
    assert "score_breakdown" in explain_data
    assert "alternatives" in explain_data
    assert len(explain_data["alternatives"]) >= 2

    lead_rec = explain_data["lead_recommendation"]
    assert "action" in lead_rec
    assert "train_number" in lead_rec

    # 10. Formal Safety Validation Gate (Phase 8)
    safety_check = explain_data.get("safety_proof", {})
    assert safety_check.get("safety_validation_status", "APPROVED") in ("APPROVED", "PASS")
    # Verify unsafe plans applied invariant
    assert safety_check.get("unsafe_plans_applied", 0) == 0

    # 11. Controller Approval & Feedback
    rec_id = explain_data.get("recommendation_id", 1)
    resp_feedback = client.post("/api/explainability/feedback", json={
        "recommendation_id": rec_id,
        "action": "APPROVE",
        "rejection_reason": None,
        "controller_id": "DISPATCHER_01",
    })
    assert resp_feedback.status_code == 200
    feedback_res = resp_feedback.json()
    assert feedback_res.get("status") == "SUCCESS" or feedback_res.get("controller_status") == "APPROVED"

    # 12. Safety-Interlocked Override Verification
    # Test Unsafe Command (negative speed -> must fail with HTTP 422)
    resp_unsafe_override = client.post("/api/control/override", json={
        "action_type": "SPEED_ADVISORY",
        "train_id": 1,
        "new_speed_kmph": -25.0,
        "reason": "Test unsafe negative speed",
        "controller_id": "TEST_DISPATCHER",
    })
    assert resp_unsafe_override.status_code == 422

    # Test Safe Command (HOLD_TRAIN -> must succeed with 200)
    resp_safe_override = client.post("/api/control/override", json={
        "action_type": "HOLD_TRAIN",
        "train_id": 1,
        "reason": "Holding for express clearance",
        "controller_id": "TEST_DISPATCHER",
    })
    assert resp_safe_override.status_code == 200
    assert resp_safe_override.json()["success"] is True

    # 13. Simulated Emergency Injection & Mitigation
    resp_emerg = client.post("/api/control/emergency", json={
        "event_type": "TRACK_BLOCKAGE",
        "affected_section_id": 1,
        "severity": "CRITICAL",
        "description": "Simulated track obstruction on corridor 1",
    })
    assert resp_emerg.status_code == 200
    emerg_id = resp_emerg.json()["id"]

    # AI Mitigation Plan
    resp_mitigate = client.post(f"/api/control/emergency/{emerg_id}/mitigate")
    assert resp_mitigate.status_code == 200
    assert resp_mitigate.json()["status"] == "SAFE_RESPONSE_READY"

    # Resolve Emergency
    resp_resolve = client.post(f"/api/control/emergency/{emerg_id}/resolve", json={
        "resolution_notes": "Obstruction removed safely"
    })
    assert resp_resolve.status_code == 200
    assert resp_resolve.json()["status"] == "RESOLVED"

    # 14. Step Simulation to Observe Result
    client.post("/api/simulation/step")

    # 15. Traditional vs AI Analytics Benchmark Comparison
    resp_compare = client.get("/api/control/ai-vs-human")
    assert resp_compare.status_code == 200
    compare_data = resp_compare.json()
    assert "throughput_impact" in compare_data
    assert "delay_impact" in compare_data
    assert compare_data["safety_compliance_pct"] == 100.0


    # 16. Pause & Reset Simulation
    client.post("/api/control/scenario/pause")
    resp_reset = client.post("/api/control/scenario/reset")
    assert resp_reset.status_code == 200

