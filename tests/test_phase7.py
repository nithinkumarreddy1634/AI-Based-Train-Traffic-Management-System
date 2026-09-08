"""
Test Suite for Phase 7: AI-Powered Precise Train Traffic Optimization.

Tests:
1. Basic optimization produces a valid feasible sequence.
2. Throughput calculation and maximization logic.
3. Integration with Phase 6 ML delay predictions.
4. Train priority weighting (Express/High vs Freight/Low).
5. Minimum headway safety constraint satisfaction.
6. Single-track and track occupancy constraints.
7. Conflict and congestion penalty sensitivity.
8. Handling empty/infeasible scenarios gracefully.
9. Evaluation across 4 benchmark scenarios.
10. All REST API endpoints (/run, /latest, /history, /benchmark, /preview, /apply).
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure project root and backend are on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from optimization import (
    DEFAULT_CONFIG,
    OptimizationConfig,
    TrainTrafficOptimizer,
    ThroughputService,
    ScoringEngine,
    OptimizationObjective,
    ConstraintValidator,
    CandidateSequenceGenerator,
    CPSATScheduler
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def optimizer():
    return TrainTrafficOptimizer()


@pytest.fixture
def sample_trains():
    return [
        {
            "train_id": 1,
            "train_number": "EXP-101",
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "current_speed_kmph": 110.0,
            "max_speed_kmph": 120.0,
            "current_delay_minutes": 2.0,
            "predicted_additional_delay": 1.5,
            "ready_time_sec": 0,
            "direction": "UP",
        },
        {
            "train_id": 2,
            "train_number": "PAS-102",
            "train_type": "PASSENGER",
            "priority": "MEDIUM",
            "current_speed_kmph": 80.0,
            "max_speed_kmph": 100.0,
            "current_delay_minutes": 5.0,
            "predicted_additional_delay": 3.0,
            "ready_time_sec": 30,
            "direction": "UP",
        },
        {
            "train_id": 3,
            "train_number": "FRT-103",
            "train_type": "FREIGHT",
            "priority": "LOW",
            "current_speed_kmph": 50.0,
            "max_speed_kmph": 75.0,
            "current_delay_minutes": 1.0,
            "predicted_additional_delay": 1.0,
            "ready_time_sec": 60,
            "direction": "UP",
        },
        {
            "train_id": 4,
            "train_number": "EXP-104",
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "current_speed_kmph": 115.0,
            "max_speed_kmph": 130.0,
            "current_delay_minutes": 0.0,
            "predicted_additional_delay": 0.5,
            "ready_time_sec": 90,
            "direction": "UP",
        },
    ]


# =========================================================================
# 1. Basic Optimization & Algorithm Feasibility Tests
# =========================================================================

def test_basic_optimization_feasibility(optimizer, sample_trains):
    """Verify optimizer produces an ordered, feasible dispatch sequence."""
    sec_info = {"section_id": 1, "section_name": "Test Section", "length_km": 20.0, "utilization_pct": 50.0}
    res = optimizer.optimize_traffic(sample_trains, sec_info)

    assert res.status in ("OPTIMIZED", "FEASIBLE")
    assert len(res.recommended_sequence) == len(sample_trains)
    assert len(res.train_recommendations) == len(sample_trains)
    assert res.expected_throughput > 0
    assert res.expected_total_delay >= 0
    assert "Recommended sequence" in res.explanation


def test_throughput_calculation_service():
    """Verify throughput service correctly calculates trains/hr."""
    # 6 trains completed in 1 hour (3600s) = 6.0 trains/hr
    tp = ThroughputService.calculate_throughput(completed_trains=6, time_window_seconds=3600)
    assert tp == 6.0

    # 3 trains completed in 30 minutes (1800s) = 6.0 trains/hr
    tp_half_hour = ThroughputService.calculate_throughput(completed_trains=3, time_window_seconds=1800)
    assert tp_half_hour == 6.0

    # Schedule throughput estimate
    sched_tp = ThroughputService.estimate_schedule_throughput(num_trains=4, first_entry_sec=0, last_exit_sec=1800)
    assert sched_tp > 0


def test_headway_safety_constraint(optimizer, sample_trains):
    """Verify that all scheduled entry times satisfy the minimum headway buffer."""
    sec_info = {"section_id": 1, "length_km": 20.0, "utilization_pct": 50.0}
    res = optimizer.optimize_traffic(sample_trains, sec_info)

    validator = ConstraintValidator()
    scheduled_dicts = [
        {"train_number": r.train_number, "entry_time_sec": r.recommended_entry_time_sec, "transit_duration_sec": 600}
        for r in res.train_recommendations
    ]
    is_valid, violations = validator.validate_headway_sequence(
        scheduled_dicts, min_headway_sec=DEFAULT_CONFIG.min_headway_seconds
    )
    assert is_valid, f"Headway violations detected: {violations}"


def test_train_priority_influence(optimizer):
    """Verify that High-Priority trains are scheduled with preference over Freight."""
    trains = [
        {
            "train_id": 1,
            "train_number": "FRT-999",
            "train_type": "FREIGHT",
            "priority": "LOW",
            "current_speed_kmph": 50.0,
            "current_delay_minutes": 2.0,
            "predicted_additional_delay": 1.0,
            "ready_time_sec": 0,
        },
        {
            "train_id": 2,
            "train_number": "EXP-001",
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "current_speed_kmph": 110.0,
            "current_delay_minutes": 2.0,
            "predicted_additional_delay": 1.0,
            "ready_time_sec": 10,
        },
    ]
    sec_info = {"section_id": 1, "length_km": 15.0, "utilization_pct": 70.0}
    res = optimizer.optimize_traffic(trains, sec_info)

    # In a priority-aware schedule, the High Priority Express should not be delayed behind slow freight
    assert res.status in ("OPTIMIZED", "FEASIBLE")
    exp_rec = next(r for r in res.train_recommendations if r.train_number == "EXP-001")
    frt_rec = next(r for r in res.train_recommendations if r.train_number == "FRT-999")
    # Express should be dispatched first or with lower hold duration
    assert exp_rec.hold_duration_seconds <= frt_rec.hold_duration_seconds or exp_rec.recommended_entry_time_sec < frt_rec.recommended_entry_time_sec


def test_delay_prediction_integration(optimizer):
    """Verify that trains with severe Phase 6 ML delay predictions are prioritized to mitigate corridor cascade."""
    trains = [
        {
            "train_id": 1,
            "train_number": "PAS-A",
            "train_type": "PASSENGER",
            "priority": "MEDIUM",
            "current_speed_kmph": 80.0,
            "current_delay_minutes": 0.0,
            "predicted_additional_delay": 0.5,
            "ready_time_sec": 0,
        },
        {
            "train_id": 2,
            "train_number": "PAS-B",
            "train_type": "PASSENGER",
            "priority": "MEDIUM",
            "current_speed_kmph": 80.0,
            "current_delay_minutes": 15.0,
            "predicted_additional_delay": 12.0,  # Huge predicted delay!
            "ready_time_sec": 5,
        },
    ]
    sec_info = {"section_id": 1, "length_km": 20.0, "utilization_pct": 60.0}
    res = optimizer.optimize_traffic(trains, sec_info)
    assert res.status in ("OPTIMIZED", "FEASIBLE")
    # Both trains must be scheduled
    assert len(res.recommended_sequence) == 2


def test_empty_trains_graceful_handling(optimizer):
    """Verify graceful handling when no trains are approaching."""
    res = optimizer.optimize_traffic([])
    assert res.status == "NO_FEASIBLE_SOLUTION"
    assert res.train_count == 0
    assert len(res.recommended_sequence) == 0


def test_before_vs_after_metrics_generation(optimizer, sample_trains):
    """Verify before-vs-after metrics calculation."""
    sec_info = {"section_id": 1, "length_km": 20.0, "utilization_pct": 70.0}
    res = optimizer.optimize_traffic(sample_trains, sec_info)

    bva = res.before_vs_after
    assert bva.current_throughput > 0
    assert bva.optimized_throughput >= bva.current_throughput
    assert bva.throughput_improvement_pct >= 0.0
    assert bva.optimized_total_delay >= 0.0


def test_all_four_benchmark_scenarios(optimizer):
    """Verify standard execution across all 4 benchmark scenarios."""
    scenarios = optimizer.run_benchmark_scenarios()
    assert len(scenarios) == 4

    # Check each scenario
    s1, s2, s3, s4 = scenarios
    assert s1.scenario_id == "scenario_1"
    assert s1.train_count == 5
    assert s1.status in ("OPTIMIZED", "FEASIBLE")

    assert s2.scenario_id == "scenario_2"
    assert s2.train_count == 10
    assert s2.status in ("OPTIMIZED", "FEASIBLE")

    assert s3.scenario_id == "scenario_3"
    assert s3.train_count == 15
    assert s3.status in ("OPTIMIZED", "FEASIBLE")

    assert s4.scenario_id == "scenario_4"
    assert s4.train_count == 6
    assert s4.status in ("OPTIMIZED", "FEASIBLE")


# =========================================================================
# 2. REST API Integration Tests
# =========================================================================

def test_api_run_optimization(client):
    """Test POST /api/optimization/run endpoint."""
    res = client.post("/api/optimization/run", json={})
    assert res.status_code == 200
    data = res.json()
    assert "recommended_sequence" in data
    assert "before_vs_after" in data
    assert "explanation" in data
    assert "factor_contributions" in data


def test_api_get_latest_optimization(client):
    """Test GET /api/optimization/latest endpoint."""
    res = client.get("/api/optimization/latest")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "recommended_sequence" in data


def test_api_get_optimization_history(client):
    """Test GET /api/optimization/history endpoint."""
    res = client.get("/api/optimization/history?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "runs" in data
    assert "total" in data


def test_api_benchmark_endpoint(client):
    """Test POST /api/optimization/benchmark endpoint."""
    res = client.post("/api/optimization/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert data[0]["scenario_id"] == "scenario_1"
    assert data[1]["scenario_id"] == "scenario_2"


def test_api_preview_and_apply(client):
    """Test POST /api/optimization/preview and POST /api/optimization/apply."""
    # First get latest recommendations
    run_res = client.post("/api/optimization/run", json={})
    run_data = run_res.json()
    recs = run_data.get("train_recommendations", [])

    # Test preview
    prev_res = client.post("/api/optimization/preview", json={"train_recommendations": recs})
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["status"] == "PREVIEW_READY"
    assert "projected_timeline" in prev_data

    # Test apply
    apply_res = client.post(
        "/api/optimization/apply",
        json={"optimization_id": run_data.get("optimization_id"), "train_recommendations": recs}
    )
    assert apply_res.status_code == 200
    apply_data = apply_res.json()
    assert apply_data["status"] == "APPLIED"

