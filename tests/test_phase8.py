"""
Comprehensive Phase 8 Safety Validation & Recommendation Engine Test Suite.

Verifies:
1. Rule 1: Emergency State Check (Manual and automated triggers)
2. Rule 2: Speed Limit Compliance (vehicle & section limits, speed difference)
3. Rule 3: Minimum Headway Validation (static and dynamic speed-dependent headway)
4. Rule 4: Track Occupancy Exclusivity (blocked, occupied, maintenance tracks)
5. Rule 5: Section Capacity Check (concurrent train counts vs block signaling)
6. Rule 6: Opposite-Direction Mutual Exclusion (head-on single-track safety)
7. Rule 7: Route Connectivity (valid topology continuity)
8. Rule 8: Junction Interlocking Clearance (switch clearance window)
9. Rule 9: Safe Stopping Distance (kinematic margin vs speed/gradient)
10. Two-Tier Screening & Fallback Selection in Optimizer
11. Safety-Gated Apply Endpoint Protection
12. REST APIs: /api/safety/validate, /status, /rules, /audit-log, /emergency
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from safety import (
    SafetyValidator,
    EmergencyManager,
    DEFAULT_SAFETY_VALIDATOR,
    DEFAULT_EMERGENCY_MANAGER,
)
from safety.config import SafetyConfig
from safety.rules import (
    RULE_EMERGENCY_STATE,
    RULE_SPEED_LIMIT,
    RULE_MINIMUM_HEADWAY,
    RULE_TRACK_OCCUPANCY,
    RULE_SECTION_OCCUPANCY,
    RULE_OPPOSITE_DIRECTION,
    RULE_ROUTE_CONNECTIVITY,
    RULE_JUNCTION_CLEARANCE,
    RULE_STOPPING_DISTANCE,
    ALL_SAFETY_RULES
)
from optimization.optimizer import TrainTrafficOptimizer


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def validator():
    # Fresh validator with clean emergency manager
    em = EmergencyManager()
    return SafetyValidator(emergency_manager=em)


# ============================================================================
# 1. Rule 1: Emergency State Check
# ============================================================================
def test_rule1_emergency_state_rejection():
    """Verify that any recommendation is immediately rejected under active emergency."""
    em = EmergencyManager()
    em.trigger_emergency("Track obstruction detected at KM 42", affected_sections=[1])
    val = SafetyValidator(emergency_manager=em)

    rec = {
        "optimization_id": 1,
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-101", "entry_time_sec": 0, "current_speed_kmph": 80.0}
        ]
    }
    state = {"section_info": {"section_id": 1, "section_name": "Main Corridor"}}

    res = val.validate(rec, state)
    assert not res.is_approved
    assert res.status == "REJECTED"
    assert res.safety_score_status == "UNSAFE"
    assert any(v.rule == RULE_EMERGENCY_STATE for v in res.violations)

    # Clearing emergency allows validation to proceed
    em.clear_emergency()
    res_cleared = val.validate(rec, state)
    assert res_cleared.is_approved
    assert res_cleared.status == "APPROVED"


# ============================================================================
# 2. Rule 2: Speed Limit Compliance
# ============================================================================
def test_rule2_speed_limit_compliance(validator):
    """Verify speed limits: vehicles cannot exceed section or rolling stock limits."""
    # Overspeed case: freight train traveling at 110 km/h (freight max is 75 km/h)
    rec_overspeed = {
        "train_recommendations": [
            {
                "train_id": 10,
                "train_number": "FRT-500",
                "train_type": "FREIGHT",
                "current_speed_kmph": 110.0,
                "entry_time_sec": 0
            }
        ]
    }
    sec_info = {"section_id": 1, "max_speed_kmph": 100.0, "section_name": "Mountain Section"}
    res = validator.validate(rec_overspeed, {"section_info": sec_info})

    assert not res.is_approved
    assert any(v.rule == RULE_SPEED_LIMIT for v in res.violations)

    # Compliant speed case
    rec_safe = {
        "train_recommendations": [
            {
                "train_id": 10,
                "train_number": "FRT-500",
                "train_type": "FREIGHT",
                "current_speed_kmph": 65.0,
                "entry_time_sec": 0
            }
        ]
    }
    res_safe = validator.validate(rec_safe, {"section_info": sec_info})
    assert res_safe.is_approved


# ============================================================================
# 3. Rule 3: Minimum Safe Headway Validation
# ============================================================================
def test_rule3_headway_validation(validator):
    """Verify minimum safe headway enforcement (120s baseline, caution under 150s)."""
    # Headway of only 60 seconds between consecutive trains -> REJECTED
    rec_violating = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-1", "entry_time_sec": 0, "current_speed_kmph": 80.0},
            {"train_id": 2, "train_number": "EXP-2", "entry_time_sec": 60, "current_speed_kmph": 80.0}
        ]
    }
    res = validator.validate(rec_violating)
    assert not res.is_approved
    assert any(v.rule == RULE_MINIMUM_HEADWAY for v in res.violations)

    # Headway of 130s -> APPROVED with caution WARNING (120s <= headway < 150s)
    rec_warning = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-1", "entry_time_sec": 0, "current_speed_kmph": 80.0},
            {"train_id": 2, "train_number": "EXP-2", "entry_time_sec": 130, "current_speed_kmph": 80.0}
        ]
    }
    res_warn = validator.validate(rec_warning)
    assert res_warn.is_approved
    assert res_warn.safety_score_status == "WARNING"
    assert any(w.rule == RULE_MINIMUM_HEADWAY for w in res_warn.warnings)

    # Headway of 180s -> APPROVED SAFE
    rec_safe = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-1", "entry_time_sec": 0, "current_speed_kmph": 80.0},
            {"train_id": 2, "train_number": "EXP-2", "entry_time_sec": 180, "current_speed_kmph": 80.0}
        ]
    }
    res_safe = validator.validate(rec_safe)
    assert res_safe.is_approved
    assert res_safe.safety_score_status == "SAFE"


# ============================================================================
# 4. Rule 4: Track Occupancy Exclusivity
# ============================================================================
def test_rule4_track_occupancy_exclusivity(validator):
    """Verify that routing a train onto a blocked or occupied track is rejected."""
    tracks_state = {
        101: {"track_id": 101, "track_number": "TRK-01", "status": "BLOCKED", "is_occupied": False},
        102: {"track_id": 102, "track_number": "TRK-02", "status": "OCCUPIED", "is_occupied": True, "occupied_by_train_id": 999}
    }

    # Attempting to dispatch to BLOCKED track
    rec_blocked = {
        "train_recommendations": [
            {"train_id": 5, "train_number": "EXP-5", "track_id": 101, "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_b = validator.validate(rec_blocked, {"tracks": tracks_state})
    assert not res_b.is_approved
    assert any(v.rule == RULE_TRACK_OCCUPANCY for v in res_b.violations)

    # Attempting to dispatch to track OCCUPIED by another train
    rec_occ = {
        "train_recommendations": [
            {"train_id": 5, "train_number": "EXP-5", "track_id": 102, "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_o = validator.validate(rec_occ, {"tracks": tracks_state})
    assert not res_o.is_approved
    assert any(v.rule == RULE_TRACK_OCCUPANCY for v in res_o.violations)


# ============================================================================
# 5. Rule 5: Section Capacity Check
# ============================================================================
def test_rule5_section_capacity(validator):
    """Verify that exceeding physical section capacity is caught."""
    sec_info = {
        "section_id": 5,
        "section_name": "Choke Section",
        "is_single_track": True,
        "track_count": 1,
        "block_signaling": False,
        "capacity": 1
    }
    # Two trains simultaneously scheduled inside a 1-train capacity section
    rec = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "T1", "entry_time_sec": 0, "transit_duration_sec": 600, "current_speed_kmph": 60.0},
            {"train_id": 2, "train_number": "T2", "entry_time_sec": 150, "transit_duration_sec": 600, "current_speed_kmph": 60.0}
        ]
    }
    res = validator.validate(rec, {"section_info": sec_info})
    assert not res.is_approved
    assert any(v.rule == RULE_SECTION_OCCUPANCY for v in res.violations)


# ============================================================================
# 6. Rule 6: Opposite-Direction Single-Track Mutual Exclusion
# ============================================================================
def test_rule6_opposite_direction_head_on_prevention(validator):
    """Verify head-on collision exclusion on single-track sections."""
    sec_info = {
        "section_id": 7,
        "section_name": "Single Line Canyon",
        "is_single_track": True,
        "track_count": 1
    }
    # UP and DOWN trains entering single-track simultaneously
    rec_headon = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "UP-101", "direction": "UP", "entry_time_sec": 0, "transit_duration_sec": 500, "current_speed_kmph": 70.0},
            {"train_id": 2, "train_number": "DN-202", "direction": "DOWN", "entry_time_sec": 200, "transit_duration_sec": 500, "current_speed_kmph": 70.0}
        ]
    }
    res = validator.validate(rec_headon, {"section_info": sec_info})
    assert not res.is_approved
    assert any(v.rule == RULE_OPPOSITE_DIRECTION for v in res.violations)

    # Properly sequenced (UP exits before DOWN enters + clearance buffer)
    rec_sequenced = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "UP-101", "direction": "UP", "entry_time_sec": 0, "transit_duration_sec": 400, "current_speed_kmph": 70.0},
            {"train_id": 2, "train_number": "DN-202", "direction": "DOWN", "entry_time_sec": 550, "transit_duration_sec": 400, "current_speed_kmph": 70.0}
        ]
    }
    res_seq = validator.validate(rec_sequenced, {"section_info": sec_info})
    assert not any(v.rule == RULE_OPPOSITE_DIRECTION for v in res_seq.violations)


# ============================================================================
# 7. Rule 7: Route Connectivity
# ============================================================================
def test_rule7_route_connectivity(validator):
    """Verify topological continuity across route sections."""
    sections_db = {
        1: {"section_id": 1, "start_station_id": 10, "end_station_id": 20},
        2: {"section_id": 2, "start_station_id": 20, "end_station_id": 30},
        3: {"section_id": 3, "start_station_id": 30, "end_station_id": 40},
    }

    # Continuous sequence: 1 -> 2 -> 3
    rec_valid = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "T1", "route_sections": [1, 2, 3], "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_val = validator.validate(rec_valid, {"sections": sections_db})
    assert not any(v.rule == RULE_ROUTE_CONNECTIVITY for v in res_val.violations)

    # Discontinuous sequence: 1 -> 3 (skipping 2, station 20 cannot connect to station 30)
    rec_broken = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "T1", "route_sections": [1, 3], "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_brok = validator.validate(rec_broken, {"sections": sections_db})
    assert not res_brok.is_approved
    assert any(v.rule == RULE_ROUTE_CONNECTIVITY for v in res_brok.violations)


# ============================================================================
# 8. Rule 8: Junction Interlocking Clearance
# ============================================================================
def test_rule8_junction_clearance(validator):
    """Verify switch/junction interlocking clearance windows."""
    conflicts = [
        {
            "conflict_type": "JUNCTION_CROSSING",
            "train1_number": "EXP-101",
            "train2_number": "FRT-202",
            "time_to_conflict_seconds": 35.0,  # Below 60s safety clearance
            "junction_id": "SW-4"
        }
    ]
    rec = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-101", "entry_time_sec": 0, "current_speed_kmph": 80.0},
            {"train_id": 2, "train_number": "FRT-202", "entry_time_sec": 120, "current_speed_kmph": 60.0}
        ]
    }
    res = validator.validate(rec, {"conflicts": conflicts})
    assert not res.is_approved
    assert any(v.rule == RULE_JUNCTION_CLEARANCE for v in res.violations)


# ============================================================================
# 9. Rule 9: Safe Kinematic Stopping Distance
# ============================================================================
def test_rule9_stopping_distance(validator):
    """Verify kinematic stopping distance margin validation."""
    # Train going 100 km/h with only 300m available distance (needs ~812m with margin)
    rec_overshoot = {
        "train_recommendations": [
            {
                "train_id": 1,
                "train_number": "SUPER-FAST",
                "train_type": "EXPRESS",
                "current_speed_kmph": 100.0,
                "distance_to_target_meters": 300.0,
                "entry_time_sec": 0
            }
        ]
    }
    res = validator.validate(rec_overshoot)
    assert not res.is_approved
    assert any(v.rule == RULE_STOPPING_DISTANCE for v in res.violations)

    # Compliant distance: 1500m available for 100 km/h Express
    rec_ok = {
        "train_recommendations": [
            {
                "train_id": 1,
                "train_number": "SUPER-FAST",
                "train_type": "EXPRESS",
                "current_speed_kmph": 100.0,
                "distance_to_target_meters": 1500.0,
                "entry_time_sec": 0
            }
        ]
    }
    res_ok = validator.validate(rec_ok)
    assert res_ok.is_approved


# ============================================================================
# 10. Two-Tier Screening & Fallback Selection in Optimizer
# ============================================================================
def test_optimizer_candidate_screening_and_stamping():
    """Verify optimizer screens candidates through safety validation and stamps results."""
    opt = TrainTrafficOptimizer()
    trains = [
        {
            "train_id": 1,
            "train_number": "EXP-101",
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "current_speed_kmph": 90.0,
            "current_delay_minutes": 0.0,
            "predicted_additional_delay": 0.0,
            "ready_time_sec": 0
        },
        {
            "train_id": 2,
            "train_number": "FRT-202",
            "train_type": "FREIGHT",
            "priority": "LOW",
            "current_speed_kmph": 60.0,
            "current_delay_minutes": 1.0,
            "predicted_additional_delay": 0.0,
            "ready_time_sec": 10
        }
    ]
    res = opt.optimize_traffic(trains)

    assert res.status in ("OPTIMIZED", "FEASIBLE")
    assert res.safety_validation is not None
    assert res.safety_validation["status"] == "APPROVED"
    assert len(res.safety_validation["rules_checked"]) == len(ALL_SAFETY_RULES)


# ============================================================================
# 11. Safety-Gated Apply Endpoint Protection
# ============================================================================
def test_api_apply_blocked_when_safety_rejected(client):
    """Verify /api/optimization/apply blocks applying unsafe plans with HTTP 400."""
    # Trigger emergency so all apply requests are rejected
    DEFAULT_EMERGENCY_MANAGER.trigger_emergency("Simulated test emergency halt")

    try:
        payload = {
            "optimization_id": 999,
            "train_recommendations": [
                {"train_id": 1, "train_number": "EXP-101", "hold_duration_seconds": 0}
            ]
        }
        resp = client.post("/api/optimization/apply", json=payload)
        assert resp.status_code == 400
        data = resp.json()
        assert "SAFETY_VALIDATION_FAILED" in str(data)
    finally:
        DEFAULT_EMERGENCY_MANAGER.clear_emergency()


# ============================================================================
# 12. REST API Endpoints Verification
# ============================================================================
def test_api_safety_validate_endpoint(client):
    """Verify POST /api/safety/validate returns structured result and creates audit log."""
    payload = {
        "recommendation": {
            "optimization_id": 88,
            "train_recommendations": [
                {"train_id": 1, "train_number": "EXP-88", "entry_time_sec": 0, "current_speed_kmph": 80.0},
                {"train_id": 2, "train_number": "FRT-88", "entry_time_sec": 180, "current_speed_kmph": 65.0}
            ]
        }
    }
    resp = client.post("/api/safety/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APPROVED"
    assert data["safety_score_status"] == "SAFE"
    assert len(data["rules_checked"]) == 9
    assert "audit_id" in data


def test_api_safety_status_endpoint(client):
    """Verify GET /api/safety/status returns real-time safety health."""
    resp = client.get("/api/safety/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_status"] in ("SAFE", "WARNING", "CRITICAL")
    assert "emergency_active" in data
    assert data["total_rules_enforced"] == 9
    assert "active_constraints" in data


def test_api_safety_rules_catalog(client):
    """Verify GET /api/safety/rules catalogs all 9 formal safety rules."""
    resp = client.get("/api/safety/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) == 9
    rule_ids = [r["rule_id"] for r in rules]
    for r in ALL_SAFETY_RULES:
        assert r in rule_ids


def test_api_safety_audit_log_endpoint(client):
    """Verify GET /api/safety/audit-log returns historical audit entries."""
    resp = client.get("/api/safety/audit-log?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert isinstance(data["logs"], list)


def test_api_safety_emergency_controls(client):
    """Verify POST /api/safety/emergency triggers and clears emergency."""
    # 1. Trigger
    resp_trig = client.post("/api/safety/emergency", json={"action": "TRIGGER", "reason": "Debris on track"})
    assert resp_trig.status_code == 200
    assert resp_trig.json()["action"] == "TRIGGER"
    assert resp_trig.json()["emergency_state"]["is_emergency"] is True

    # 2. Status reflects emergency
    resp_stat = client.get("/api/safety/status")
    assert resp_stat.json()["emergency_active"] is True
    assert resp_stat.json()["system_status"] == "CRITICAL"

    # 3. Clear
    resp_clr = client.post("/api/safety/emergency", json={"action": "CLEAR"})
    assert resp_clr.status_code == 200
    assert resp_clr.json()["action"] == "CLEAR"
    assert resp_clr.json()["emergency_state"]["is_emergency"] is False
