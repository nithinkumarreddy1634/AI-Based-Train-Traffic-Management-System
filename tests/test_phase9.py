"""
Comprehensive Phase 9 AI vs Traditional Scheduling Evaluation Test Suite.

Verifies:
1. Baseline Scheduler (FCFS and Priority-aware headway dispatching)
2. Scenario Manager (6 repeatable benchmarks with deep-copy isolation)
3. Metrics & Scoring calculations (Throughput, Delay, Waiting, Composite score)
4. Scenario Evaluator under identical conditions & Safety Invariant (0 violations)
5. Comparison Engine with statistical multi-run aggregation
6. Report Generator (CSV, JSON, Markdown)
7. REST APIs (/api/analytics/scenarios, /run, /experiments, /compare, /metrics, /export)
"""

import sys
from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.database.session import SessionLocal
from app.models.railway import Experiment, ExperimentResult, ComparisonResult
from analytics import (
    BaselineScheduler,
    ScenarioManager,
    ScenarioEvaluator,
    ComparisonEngine,
    ReportGenerator,
    calculate_throughput,
    calculate_delay_metrics,
    calculate_waiting_metrics,
    calculate_improvement,
    DEFAULT_SCENARIO_MANAGER,
    DEFAULT_COMPARISON_ENGINE,
)

client = TestClient(app)


# =====================================================================
# 1. Baseline Scheduler Tests
# =====================================================================

def test_baseline_scheduler_fcfs():
    scheduler = BaselineScheduler(dispatch_mode="FCFS", min_headway_seconds=120.0)
    trains = [
        {"train_id": 1, "train_number": "T1", "priority": "LOW", "current_delay_minutes": 10.0, "current_position_km": 5.0},
        {"train_id": 2, "train_number": "T2", "priority": "HIGH", "current_delay_minutes": 2.0, "current_position_km": 15.0},
    ]
    seq = scheduler.compute_dispatch_sequence(trains)
    assert len(seq) == 2
    # In FCFS with lower delay first
    assert seq[0]["train_id"] == 2


def test_baseline_scheduler_priority_and_headway():
    scheduler = BaselineScheduler(dispatch_mode="SCHEDULED_PRIORITY", min_headway_seconds=180.0)
    trains = [
        {"train_id": 1, "train_number": "FRT-1", "priority": "LOW", "current_delay_minutes": 0.0},
        {"train_id": 2, "train_number": "EXP-1", "priority": "HIGH", "current_delay_minutes": 0.0},
        {"train_id": 3, "train_number": "PAS-1", "priority": "MEDIUM", "current_delay_minutes": 0.0},
    ]
    seq = scheduler.compute_dispatch_sequence(trains)
    assert len(seq) == 3
    assert seq[0]["priority"] == "HIGH"
    assert seq[1]["priority"] == "MEDIUM"
    assert seq[2]["priority"] == "LOW"

    # Headway spacing verification
    assert scheduler.can_dispatch_train(trains[1], current_sim_time=0.0) is True
    assert scheduler.can_dispatch_train(trains[0], current_sim_time=50.0) is False  # < 180s
    assert scheduler.can_dispatch_train(trains[0], current_sim_time=200.0) is True  # > 180s


# =====================================================================
# 2. Scenario Manager Tests
# =====================================================================

def test_scenario_manager_catalog():
    sm = ScenarioManager()
    scenarios = sm.list_scenarios()
    assert len(scenarios) == 6
    ids = [s["id"] for s in scenarios]
    assert "low_traffic" in ids
    assert "medium_traffic" in ids
    assert "heavy_traffic" in ids
    assert "high_delay" in ids
    assert "bottleneck_corridor" in ids
    assert "mixed_priority" in ids


def test_scenario_manager_deep_copy_isolation():
    sm = ScenarioManager()
    state1 = sm.create_initial_state("low_traffic")
    state2 = sm.create_initial_state("low_traffic")

    assert len(state1["trains"]) == 6
    assert len(state2["trains"]) == 6

    # Mutate state1 and verify state2 is unchanged
    state1["trains"][0]["speed_kmph"] = 999.0
    assert state2["trains"][0]["speed_kmph"] != 999.0


# =====================================================================
# 3. Metrics Calculation & Scoring Tests
# =====================================================================

def test_metrics_calculations():
    # Throughput
    assert calculate_throughput(10, 3600.0) == 10.0
    assert calculate_throughput(5, 1800.0) == 10.0
    assert calculate_throughput(0, 3600.0) == 0.0

    # Delay metrics
    d_stats = calculate_delay_metrics([5.0, 10.0, 15.0])
    assert d_stats["avg_delay_minutes"] == 10.0
    assert d_stats["max_delay_minutes"] == 15.0
    assert d_stats["min_delay_minutes"] == 5.0
    assert d_stats["total_delay_minutes"] == 30.0
    assert d_stats["median_delay_minutes"] == 10.0

    # Waiting metrics
    w_stats = calculate_waiting_metrics([100.0, 200.0, 300.0])
    assert w_stats["total_waiting_time"] == 600.0
    assert w_stats["avg_waiting_time"] == 200.0
    assert w_stats["max_waiting_time"] == 300.0

    # Improvement percentages
    # Higher is better: 12 vs 10 = +20%
    assert calculate_improvement(10.0, 12.0, higher_is_better=True) == 20.0
    # Lower is better: 6 vs 10 = +40%
    assert calculate_improvement(10.0, 6.0, higher_is_better=False) == 40.0
    # Zero baseline safety
    assert calculate_improvement(0.0, 5.0, higher_is_better=True) > 0.0


# =====================================================================
# 4. Scenario Evaluator & Safety Invariant Tests
# =====================================================================

def test_scenario_evaluator_traditional_and_ai():
    sm = ScenarioManager()
    evaluator = ScenarioEvaluator(dt=30.0)
    initial_state = sm.create_initial_state("low_traffic")

    # Short simulation duration for fast unit test execution
    trad_res = evaluator.run_simulation(initial_state, scheduler_type="TRADITIONAL", duration_seconds=600.0)
    ai_res = evaluator.run_simulation(initial_state, scheduler_type="AI", duration_seconds=600.0)

    # Both must complete with non-negative metrics
    assert trad_res.total_trains == 6
    assert ai_res.total_trains == 6
    assert trad_res.throughput_tph >= 0.0
    assert ai_res.throughput_tph >= 0.0

    # STRICT SAFETY INVARIANT: Violations & unsafe plans must be 0
    assert ai_res.safety_violations == 0
    assert ai_res.unsafe_plans_applied == 0
    assert trad_res.safety_violations == 0
    assert trad_res.unsafe_plans_applied == 0


# =====================================================================
# 5. Comparison Engine & Multi-Run Statistical Tests
# =====================================================================

def test_comparison_engine_multi_run():
    sm = ScenarioManager()
    evaluator = ScenarioEvaluator(dt=30.0)
    engine = ComparisonEngine(scenario_manager=sm, evaluator=evaluator)

    result = engine.run_experiment(scenario_id="low_traffic", runs_count=2)

    assert result["status"] == "COMPLETED"
    assert result["runs_count"] == 2
    assert len(result["traditional_runs"]) == 2
    assert len(result["ai_runs"]) == 2

    # Verify statistical aggregations exist
    trad_sum = result["traditional_summary"]
    ai_sum = result["ai_summary"]
    assert "mean" in trad_sum["throughput_tph"]
    assert "stddev" in trad_sum["throughput_tph"]
    assert "mean" in ai_sum["throughput_tph"]

    # Verify comparison payload
    comp = result["comparison"]
    assert "throughput_gain_pct" in comp
    assert "delay_reduction_pct" in comp
    assert "overall_performance_score" in comp
    assert comp["safety_compliant"] is True
    assert comp["safety_violations"] == 0
    assert comp["unsafe_plans_applied"] == 0


# =====================================================================
# 6. Report Generator Tests
# =====================================================================

def test_report_generator_formats():
    sm = ScenarioManager()
    evaluator = ScenarioEvaluator(dt=30.0)
    engine = ComparisonEngine(scenario_manager=sm, evaluator=evaluator)
    exp_data = engine.run_experiment(scenario_id="low_traffic", runs_count=1)

    # CSV Generation
    csv_out = ReportGenerator.generate_csv(exp_data)
    assert "# EXPERIMENT OVERVIEW" in csv_out
    assert "# COMPARATIVE PERFORMANCE METRICS" in csv_out
    assert "Section Throughput" in csv_out
    assert "Traditional Baseline" in csv_out

    # JSON Generation
    json_out = ReportGenerator.generate_json(exp_data)
    parsed = json.loads(json_out)
    assert parsed["scenario_id"] == "low_traffic"
    assert "comparison" in parsed

    # Markdown Summary
    md_out = ReportGenerator.generate_summary_markdown(exp_data)
    assert "# Benchmark Report" in md_out
    assert "Safety Violations" in md_out


# =====================================================================
# 7. REST API Endpoints Tests
# =====================================================================

def test_api_scenarios():
    res = client.get("/api/analytics/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 6
    assert any(s["id"] == "medium_traffic" for s in data)


def test_api_run_experiment_and_retrieval():
    # Run a quick low_traffic experiment via REST
    payload = {
        "scenario_id": "low_traffic",
        "runs_count": 1,
        "name": "Automated Unit Test Experiment",
        "description": "Validating Phase 9 REST integration"
    }
    run_res = client.post("/api/analytics/run", json=payload)
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert "comparison" in run_data
    exp_id = run_data.get("experiment_id")

    if exp_id:
        # 1. GET /experiments
        list_res = client.get("/api/analytics/experiments")
        assert list_res.status_code == 200
        exps = list_res.json()
        assert any(e["experiment_id"] == exp_id for e in exps)

        # 2. GET /experiments/{id}
        det_res = client.get(f"/api/analytics/experiments/{exp_id}")
        assert det_res.status_code == 200
        assert det_res.json()["experiment_id"] == exp_id

        # 3. GET /compare/{id}
        comp_res = client.get(f"/api/analytics/compare/{exp_id}")
        assert comp_res.status_code == 200
        assert "overall_performance_score" in comp_res.json()

        # 4. GET /metrics/{id}
        met_res = client.get(f"/api/analytics/metrics/{exp_id}")
        assert met_res.status_code == 200
        assert len(met_res.json()["runs"]) >= 1

        # 5. GET /export/{id}?format=csv
        csv_res = client.get(f"/api/analytics/export/{exp_id}?format=csv")
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers.get("content-type", "")
        assert "Section Throughput" in csv_res.text

        # 6. GET /export/{id}?format=json
        json_res = client.get(f"/api/analytics/export/{exp_id}?format=json")
        assert json_res.status_code == 200
        assert json_res.json()["experiment_id"] == exp_id

