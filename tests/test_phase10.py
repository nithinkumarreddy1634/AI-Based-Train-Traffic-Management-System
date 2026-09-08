"""
Comprehensive Phase 10 Explainable AI Decision Engine Test Suite.

Verifies:
1. Feature Analyzer (Priority, Delay, Utilization, Queue depth, and Conflict factors)
2. Decision Confidence Calculator (HIGH/MEDIUM/LOW, score margin, disclaimer)
3. Explanation Formatter (Deterministic narrative, key points, safety checklist)
4. Recommendation Explainer (Per-train trade-offs and decision scores)
5. Decision Explainer (Master orchestrator, alternatives ranking, Before->Decision->After flow)
6. Safety Validation integration (Rejection explanation and fail-safe application block)
7. Controller approval/rejection feedback workflow with operational reasons
8. REST APIs (/api/explainability/latest, /recommendation/{id}, /history, /feedback, /summary-stats)
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
from app.models.railway import DecisionExplanation
from explainability import (
    FeatureAnalyzer,
    ConfidenceCalculator,
    ExplanationFormatter,
    RecommendationExplainer,
    DecisionExplainer,
    DEFAULT_DECISION_EXPLAINER,
    DISCLAIMER_TEXT,
)
from optimization.optimizer import TrainTrafficOptimizer

client = TestClient(app)


# =====================================================================
# 1. Feature Analyzer Tests
# =====================================================================

def test_feature_analyzer_ranks_factors():
    analyzer = FeatureAnalyzer()
    train = {
        "train_id": 1,
        "train_number": "EXP-12001",
        "priority": "HIGH",
        "current_delay_minutes": 12.5,
        "predicted_additional_delay": 3.0,
        "speed_kmph": 85.0,
        "current_position_km": 14.0,
    }
    rec = {"action": "PRIORITIZE", "recommended_speed": 95.0, "hold_duration_seconds": 0}
    sec = {"section_id": 1, "section_name": "Main Line", "utilization_pct": 80.0, "max_speed_kmph": 110.0}

    factors = analyzer.analyze_factors(
        train_data=train,
        recommendation=rec,
        section_info=sec,
        traffic_state={"section_utilization": 80.0, "waiting_train_count": 3},
        active_conflicts=[]
    )

    assert len(factors) >= 4
    factor_names = [f["factor"] for f in factors]
    assert "Train Priority" in factor_names
    assert "Predicted Delay" in factor_names
    assert "Section Utilization" in factor_names

    # Factors must be sorted descending by importance_score
    scores = [f["importance_score"] for f in factors]
    assert scores == sorted(scores, reverse=True)


# =====================================================================
# 2. Confidence Calculator Tests
# =====================================================================

def test_confidence_calculator_clean_and_rejected():
    calc = ConfidenceCalculator()

    # Clean approved optimization -> HIGH confidence
    high_conf = calc.calculate_confidence(
        optimization_status="OPTIMIZED",
        safety_validation_status="APPROVED",
        safety_violations_count=0,
        score_margin=25.0,
        candidates_count=4,
        data_completeness_pct=100.0,
        ml_prediction_available=True
    )
    assert high_conf.level == "HIGH"
    assert high_conf.score >= 80.0
    assert high_conf.disclaimer == DISCLAIMER_TEXT

    # Safety-rejected optimization -> strictly LOW confidence
    low_conf = calc.calculate_confidence(
        optimization_status="FEASIBLE",
        safety_validation_status="REJECTED",
        safety_violations_count=2,
        score_margin=5.0,
        candidates_count=1,
    )
    assert low_conf.level == "LOW"
    assert "safety validation" in low_conf.rationale.lower()


# =====================================================================
# 3. Explanation Formatter Tests
# =====================================================================

def test_explanation_formatter_narrative_and_checklist():
    formatter = ExplanationFormatter()
    factors = [
        {"factor": "Predicted Delay", "value": 14.5, "unit": "min", "reason": "high delay risk"},
        {"factor": "Train Priority", "value": "HIGH", "unit": "class", "reason": "priority service"}
    ]

    narrative = formatter.format_narrative(
        train_number="EXP-101",
        train_type="EXPRESS",
        priority="HIGH",
        action="PRIORITIZE",
        section_name="Corridor Section 1",
        factors=factors,
        safety_status="APPROVED",
        throughput_gain_pct=15.0,
        delay_reduction_pct=25.0
    )
    assert "EXP-101" in narrative
    assert "Corridor Section 1" in narrative
    assert "15.0%" in narrative

    key_points = formatter.format_key_points(
        train_data={"priority": "HIGH"},
        action="PRIORITIZE",
        factors=factors,
        safety_status="APPROVED"
    )
    assert len(key_points) >= 3
    assert any("priority" in p.lower() for p in key_points)

    checklist = formatter.format_safety_checklist({
        "status": "APPROVED",
        "violations": []
    })
    assert checklist["overall_status"] == "APPROVED"
    assert len(checklist["rules"]) == 9
    assert all(r["passed"] for r in checklist["rules"])


# =====================================================================
# 4. Recommendation & Decision Explainer Tests
# =====================================================================

def test_decision_explainer_full_package():
    explainer = DecisionExplainer()
    optimizer = TrainTrafficOptimizer()

    trains = [
        {"train_id": 1, "train_number": "EXP-101", "train_type": "EXPRESS", "priority": "HIGH", "speed_kmph": 90.0, "current_delay_minutes": 8.0, "current_position_km": 10.0},
        {"train_id": 2, "train_number": "FRT-202", "train_type": "FREIGHT", "priority": "LOW", "speed_kmph": 60.0, "current_delay_minutes": 2.0, "current_position_km": 5.0},
    ]
    sec = {"section_id": 1, "section_name": "Main Corridor", "length_km": 20.0, "max_speed_kmph": 110.0, "utilization_pct": 65.0}

    opt_result = optimizer.optimize_traffic(trains=trains, section_info=sec, active_conflicts=[])

    package = explainer.explain_optimization_result(
        optimization_result=opt_result,
        trains=trains,
        section_info=sec,
        traffic_state={"section_utilization": 65.0, "waiting_train_count": 1},
        active_conflicts=[]
    )

    assert "recommendation_id" in package
    assert "lead_recommendation" in package
    lead = package["lead_recommendation"]
    assert lead["train_number"] in ("EXP-101", "FRT-202")
    assert "score_breakdown" in package
    sb = package["score_breakdown"]
    assert "throughput_contribution" in sb
    assert "delay_reduction_contribution" in sb
    assert "total_score" in sb

    # Verify candidate alternatives
    alternatives = package["alternatives"]
    assert len(alternatives) >= 2
    assert any(a["is_selected"] for a in alternatives)

    # Verify decision flow
    assert "decision_flow" in package
    df = package["decision_flow"]
    assert "current_state" in df
    assert "projected_outcome" in df


# =====================================================================
# 5. REST API Endpoints Tests
# =====================================================================

def test_api_explainability_latest():
    res = client.get("/api/explainability/latest")
    assert res.status_code == 200
    data = res.json()
    assert "lead_recommendation" in data
    assert "score_breakdown" in data
    assert "alternatives" in data
    assert "decision_flow" in data


def test_api_explainability_recommendation_and_history():
    # 1. First ensure an explanation is generated and persisted
    latest_res = client.get("/api/explainability/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    rec_id = latest_data.get("recommendation_id", 1)

    # 2. Query recommendation explanation by ID
    rec_res = client.get(f"/api/explainability/recommendation/{rec_id}")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "action" in rec_data
    assert "factors" in rec_data
    assert "score_breakdown" in rec_data
    assert "confidence" in rec_data

    # 3. Query history
    hist_res = client.get("/api/explainability/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert isinstance(history, list)

    if history:
        item_id = history[0]["id"]
        item_res = client.get(f"/api/explainability/history/{item_id}")
        assert item_res.status_code == 200
        assert item_res.json()["id"] == item_id


def test_api_controller_feedback_and_summary_stats():
    # Submit controller rejection feedback
    feedback_payload = {
        "action": "REJECT",
        "rejection_reason": "Operational constraint: scheduled track inspection"
    }
    fb_res = client.post("/api/explainability/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["status"] == "SUCCESS"
    assert fb_data["controller_status"] == "REJECTED"
    assert "track inspection" in fb_data["rejection_reason"]

    # Submit approval feedback
    fb_approve = {"action": "APPROVE"}
    app_res = client.post("/api/explainability/feedback", json=fb_approve)
    assert app_res.status_code == 200
    assert app_res.json()["controller_status"] == "APPROVED"

    # Verify summary stats
    stats_res = client.get("/api/explainability/summary-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_recommendations" in stats
    assert "approved_count" in stats
    assert "controller_rejected_count" in stats
    assert stats["total_recommendations"] >= 1

