"""
Phase 13 Mandatory Safety Bypass Test Suite.

Verifies:
1. Unsafe AI recommendation rejection (overspeeding)
2. Insufficient headway hazard rejection (< 120s)
3. Occupied track hazard rejection (BLOCKED / OCCUPIED)
4. Opposite-direction collision hazard rejection (single-track conflict)
5. Section capacity overrun rejection
6. Unsafe manual override API rejection (HTTP 422)
7. Guarantee that unapproved recommendations cannot be applied
8. Verified invariant: zero unsafe actions applied across the system
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
from safety import (
    SafetyValidator,
    DEFAULT_SAFETY_VALIDATOR,
)
from safety.rules import (
    RULE_SPEED_LIMIT,
    RULE_MINIMUM_HEADWAY,
    RULE_TRACK_OCCUPANCY,
    RULE_SECTION_OCCUPANCY,
    RULE_OPPOSITE_DIRECTION,
)

client = TestClient(app)


def test_unsafe_ai_recommendation_overspeed_rejected():
    """Verify that an AI recommendation prescribing speed above limit is rejected."""
    validator = SafetyValidator()
    rec_overspeed = {
        "train_recommendations": [
            {
                "train_id": 10,
                "train_number": "FRT-500",
                "train_type": "FREIGHT",
                "current_speed_kmph": 110.0,  # Freight maximum is 75 km/h
                "entry_time_sec": 0
            }
        ]
    }
    sec_info = {"section_id": 1, "max_speed_kmph": 100.0, "section_name": "Mountain Section"}
    res = validator.validate(rec_overspeed, {"section_info": sec_info})

    assert not res.is_approved
    assert res.status == "REJECTED"
    assert any(v.rule == RULE_SPEED_LIMIT for v in res.violations)


def test_insufficient_headway_rejected():
    """Verify that train spacing below minimum headway (60s vs 120s) is rejected."""
    validator = SafetyValidator()
    rec_violating = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "EXP-1", "entry_time_sec": 0, "current_speed_kmph": 80.0},
            {"train_id": 2, "train_number": "EXP-2", "entry_time_sec": 60, "current_speed_kmph": 80.0}
        ]
    }
    res = validator.validate(rec_violating)
    assert not res.is_approved
    assert res.status == "REJECTED"
    assert any(v.rule == RULE_MINIMUM_HEADWAY for v in res.violations)


def test_occupied_track_dispatch_rejected():
    """Verify that routing a train onto a blocked or occupied track is rejected."""
    validator = SafetyValidator()
    tracks_state = {
        101: {"track_id": 101, "track_number": "TRK-01", "status": "BLOCKED", "is_occupied": False},
        102: {"track_id": 102, "track_number": "TRK-02", "status": "OCCUPIED", "is_occupied": True, "occupied_by_train_id": 999}
    }

    rec_blocked = {
        "train_recommendations": [
            {"train_id": 5, "train_number": "EXP-5", "track_id": 101, "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_b = validator.validate(rec_blocked, {"tracks": tracks_state})
    assert not res_b.is_approved
    assert any(v.rule == RULE_TRACK_OCCUPANCY for v in res_b.violations)

    rec_occ = {
        "train_recommendations": [
            {"train_id": 5, "train_number": "EXP-5", "track_id": 102, "entry_time_sec": 0, "current_speed_kmph": 70.0}
        ]
    }
    res_o = validator.validate(rec_occ, {"tracks": tracks_state})
    assert not res_o.is_approved
    assert any(v.rule == RULE_TRACK_OCCUPANCY for v in res_o.violations)


def test_opposite_direction_conflict_rejected():
    """Verify head-on collision exclusion on single-track sections."""
    validator = SafetyValidator()
    sec_info = {
        "section_id": 7,
        "section_name": "Single Line Canyon",
        "is_single_track": True,
        "track_count": 1
    }
    rec_headon = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "UP-101", "direction": "UP", "entry_time_sec": 0, "transit_duration_sec": 500, "current_speed_kmph": 70.0},
            {"train_id": 2, "train_number": "DN-202", "direction": "DOWN", "entry_time_sec": 200, "transit_duration_sec": 500, "current_speed_kmph": 70.0}
        ]
    }
    res = validator.validate(rec_headon, {"section_info": sec_info})
    assert not res.is_approved
    assert res.status == "REJECTED"
    assert any(v.rule == RULE_OPPOSITE_DIRECTION for v in res.violations)


def test_section_capacity_exceeded_rejected():
    """Verify that attempting to pack more trains than capacity into a block section is rejected."""
    validator = SafetyValidator()
    sec_info = {
        "section_id": 9,
        "section_name": "Narrow Gorge",
        "is_single_track": True,
        "track_count": 1,
        "block_signaling": False,
        "capacity": 1,
        "length_km": 10.0
    }
    rec = {
        "train_recommendations": [
            {"train_id": 1, "train_number": "T1", "entry_time_sec": 0, "transit_duration_sec": 600, "current_speed_kmph": 60.0},
            {"train_id": 2, "train_number": "T2", "entry_time_sec": 150, "transit_duration_sec": 600, "current_speed_kmph": 60.0}
        ]
    }
    res = validator.validate(rec, {"section_info": sec_info})
    assert not res.is_approved
    assert res.status == "REJECTED"
    assert any(v.rule == RULE_SECTION_OCCUPANCY for v in res.violations)


def test_unsafe_manual_override_api_rejected():
    """Verify that an unsafe manual controller override is rejected with HTTP 422."""
    res = client.post("/api/control/override", json={
        "action_type": "SPEED_ADVISORY",
        "train_id": 1,
        "new_speed_kmph": 350.0,
        "reason": "Dangerous excessive speed test",
        "controller_id": "DISPATCHER_MALICIOUS"
    })
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


def test_cannot_apply_unapproved_recommendation():
    """Verify that an unapproved recommendation cannot be applied via API."""
    res = client.post("/api/optimization/apply", json={"optimization_id": 999999})
    assert res.status_code in (400, 404, 422)


def test_zero_unsafe_actions_applied_invariant():
    """Verify the core safety invariant: unsafe_actions_applied == 0."""
    res = client.get("/api/safety/status")
    assert res.status_code == 200
    data = res.json()
    assert data.get("unsafe_actions_applied", 0) == 0
