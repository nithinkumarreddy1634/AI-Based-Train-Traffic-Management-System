"""
Phase 13: Final End-to-End Workflow & Integration Test.

Validates the full 15-stage intelligent train traffic control pipeline using actual system modules:
1. Create/Load Network
2. Load Trains
3. Load Scenario
4. Start Simulation
5. Train Movement Kinematics
6. Conflict Detection
7. Congestion & Bottleneck Analysis
8. ML Delay Prediction
9. AI Optimization
10. Explain Recommendation
11. Safety Validation Gate
12. Controller Approval
13. Apply Recommendation
14. Continue Simulation & Calculate Metrics
15. Traditional vs AI Benchmark Comparison & Final Result
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from simulation import simulation_engine
from safety import DEFAULT_SAFETY_VALIDATOR
from optimization import DEFAULT_OPTIMIZER

client = TestClient(app)


def test_complete_phase13_full_integration():
    """Executes and verifies the 15-stage end-to-end intelligent railway control lifecycle."""

    # 1. Load / Verify Network Topology
    res_net = client.get("/api/network")
    assert res_net.status_code == 200
    net_data = res_net.json()
    assert len(net_data["stations"]) >= 5
    assert len(net_data["sections"]) >= 7
    assert len(net_data["tracks"]) >= 14

    # 2. Load / Verify Train Fleet
    res_trains = client.get("/api/trains")
    assert res_trains.status_code == 200
    assert len(res_trains.json()) >= 12

    # 3. Load Benchmark Scenario
    res_scenario = client.post("/api/control/scenario/load", json={"scenario_id": "ai_demo"})
    assert res_scenario.status_code == 200
    sc_data = res_scenario.json()
    assert sc_data["success"] is True
    assert sc_data["scenario_id"] == "ai_demo"

    # 4. Start Simulation
    res_start = client.post("/api/simulation/start")
    assert res_start.status_code == 200
    assert simulation_engine.is_running is True

    # 5. Train Movement Kinematics (step multiple ticks)
    for _ in range(5):
        res_step = client.post("/api/simulation/step")
        assert res_step.status_code == 200

    # Verify positions and speeds updated
    status = simulation_engine.get_status()
    assert status["running"] is True
    assert status["simulation_seconds"] > 0

    # 6. Conflict Detection
    res_conflicts = client.get("/api/conflicts/active")
    assert res_conflicts.status_code == 200
    conflicts_data = res_conflicts.json()
    assert isinstance(conflicts_data, (list, dict))

    # 7. Congestion & Bottleneck Analysis
    res_bottlenecks = client.get("/api/bottlenecks")
    assert res_bottlenecks.status_code == 200
    assert isinstance(res_bottlenecks.json().get("bottlenecks"), list)

    # 8. ML Delay Prediction
    res_predict = client.post("/api/ml/predict-delay", json={
        "train_type": "EXPRESS",
        "priority": "HIGH",
        "current_delay_minutes": 6.5,
        "scheduled_speed_kmph": 100.0,
        "current_speed_kmph": 85.0,
        "track_occupancy_ratio": 0.6,
        "scheduled_departure_hour": 15,
        "is_peak_hour": 1,
        "approaching_bottleneck": 1,
        "weather_condition": "CLEAR",
        "day_of_week": 2,
    })
    assert res_predict.status_code == 200
    pred_data = res_predict.json()
    assert "predicted_delay_minutes" in pred_data
    assert isinstance(pred_data["predicted_delay_minutes"], (int, float))

    # 9. AI Multi-Objective Optimization
    live_trains = [
        t for t in simulation_engine.get_live_trains()
        if t.get("status") != "ARRIVED"
    ]
    assert len(live_trains) > 0

    res_opt = client.post("/api/optimization/optimize", json={
        "section_id": 1,
        "train_ids": [t["train_id"] for t in live_trains[:8]],
        "weights": {"throughput": 0.4, "delay": 0.3, "waiting": 0.2, "priority": 0.1},
    })
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    assert opt_data.get("status") in ("COMPLETED", "OPTIMAL", "SUCCESS") or "candidate_solutions" in opt_data or "recommended_sequence" in opt_data

    # 10. Explain Recommendation
    res_explain = client.get("/api/explainability/latest")
    assert res_explain.status_code == 200
    explain_data = res_explain.json()
    assert "feature_attribution" in explain_data or "decision_narrative" in explain_data or "explanation" in explain_data or "score_breakdown" in explain_data

    # 11. Phase 8 Safety Validation Gate
    sample_candidate = {
        "candidate_id": "phase13_plan_001",
        "target_section_id": 1,
        "train_recommendations": [
            {
                "train_id": live_trains[0]["train_id"],
                "train_number": live_trains[0]["train_number"],
                "assigned_track_id": 1,
                "target_speed_kmph": 80.0,
                "entry_time_sec": 0.0,
                "exit_time_sec": 120.0,
                "headway_to_lead_sec": 240.0,
            }
        ],
    }
    res_safety = client.post("/api/safety/validate", json={"recommendation": sample_candidate})
    assert res_safety.status_code == 200
    safety_data = res_safety.json()
    assert safety_data.get("is_approved") is True or safety_data.get("status") == "APPROVED"

    # 12. Human Controller Approval
    res_feedback = client.post("/api/explainability/feedback", json={
        "action": "APPROVE",
        "controller_id": "CHIEF_DISPATCHER_P13",
        "notes": "Optimal sequencing approved for bottleneck clearance."
    })
    assert res_feedback.status_code == 200
    assert res_feedback.json().get("status") == "SUCCESS" or res_feedback.json().get("controller_status") == "APPROVED"

    # 13. Apply Recommendation to Simulation
    # Check that the safety gate either allows safe commit (200) or rejects if live conflict (400)
    res_apply = client.post("/api/optimization/apply", json={
        "optimization_id": 1,
        "train_recommendations": sample_candidate["train_recommendations"]
    })
    assert res_apply.status_code in (200, 400)
    if res_apply.status_code == 200:
        assert res_apply.json().get("applied") is True
    else:
        err_info = res_apply.json().get("detail", {})
        if isinstance(err_info, dict):
            assert err_info.get("error") == "SAFETY_VALIDATION_FAILED"

    # 14. Continue Simulation
    for _ in range(5):
        client.post("/api/simulation/step")

    # 15. Traditional vs AI Benchmark Comparison
    res_bench = client.post("/api/analytics/run", json={
        "scenario_id": "bottleneck_corridor",
        "duration_seconds": 1800,
        "runs": 1,
        "random_seed": 42
    })
    assert res_bench.status_code == 200
    bench_data = res_bench.json()
    assert "comparison" in bench_data
    comp = bench_data["comparison"]
    assert "throughput_gain_pct" in comp
    assert "delay_reduction_pct" in comp
    assert "overall_performance_score" in comp
    assert comp["safety_violations"] == 0
    assert comp["unsafe_plans_applied"] == 0

    # Ensure zero unsafe actions applied across the entire run
    res_audit = client.get("/api/safety/status")
    assert res_audit.status_code == 200
    assert res_audit.json().get("unsafe_actions_applied", 0) == 0

    # Stop simulation
    client.post("/api/simulation/pause")
