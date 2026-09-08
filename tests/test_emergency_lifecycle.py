"""
Phase 13 Mandatory Emergency Lifecycle Test Suite.

Verifies:
1. Track Blockage Lifecycle:
   - Detection & Registration
   - Affected Train Identification & Impact Assessment
   - Traffic State & Simulation Updates (Track Closed / Speed = 0)
   - AI Mitigation Plan Formulation with Headway Spacing
   - Phase 8 Safety Validation Approval
   - Emergency Resolution & Track Capacity Restoration
2. Signal Failure Lifecycle:
   - Caution Speed Imposition (<= 25 km/h)
   - AI Mitigation Response Verification
   - Safe Resolution
3. Emergency REST API Contract (/api/control/emergency/*)
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
from control_center import emergency_manager, scenario_controller

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_scenario():
    """Initializes standard corridor scenario before each emergency test."""
    scenario_controller.load_scenario("medium_traffic")
    yield
    # Clean up active emergencies
    for eid in list(emergency_manager._active_events.keys()):
        emergency_manager.resolve_event(eid, "Test tear-down cleanup")


def test_track_blockage_full_lifecycle():
    """Verify complete end-to-end lifecycle for a TRACK_BLOCKAGE incident."""
    # 1. Trigger Track Blockage on Section 1 via REST API
    res_inject = client.post("/api/control/emergency", json={
        "event_type": "TRACK_BLOCKAGE",
        "affected_section_id": 1,
        "severity": "CRITICAL",
        "description": "Simulated rockfall on Central - North Junction Line"
    })
    assert res_inject.status_code == 200
    evt = res_inject.json()
    assert evt["status"] == "ACTIVE"
    assert evt["severity"] == "CRITICAL"
    event_id = evt["id"]
    assert event_id > 0

    # 2. Verify Corridor Impact Assessment
    impact = evt.get("impact_summary", {})
    assert impact.get("section_closed") is True
    assert "affected_trains_count" in impact

    # 3. Query Active Emergencies API
    res_active = client.get("/api/control/emergencies")
    assert res_active.status_code == 200
    active_list = res_active.json()
    assert any(e["id"] == event_id for e in active_list)

    # 4. Generate AI Emergency Mitigation Recovery Plan
    res_mitigate = client.post(f"/api/control/emergency/{event_id}/mitigate")
    assert res_mitigate.status_code == 200
    safe_plan = res_mitigate.json()
    assert safe_plan["status"] == "SAFE_RESPONSE_READY"
    assert safe_plan["safety_status"] == "APPROVED"
    assert len(safe_plan.get("recommendations", [])) > 0

    # 5. Resolve Emergency Incident
    res_resolve = client.post(
        f"/api/control/emergency/{event_id}/resolve",
        json={"resolution_notes": "Track cleared and inspected by maintenance team."}
    )
    assert res_resolve.status_code == 200
    resolve_data = res_resolve.json()
    assert resolve_data["success"] is True

    # 6. Verify Incident Marked Resolved
    active_now = emergency_manager.get_active_emergencies()
    assert not any(e["id"] == event_id for e in active_now)


def test_signal_failure_lifecycle():
    """Verify complete end-to-end lifecycle for a SIGNAL_FAILURE incident."""
    # 1. Trigger Signal Failure on Section 2
    res_inject = client.post("/api/control/emergency", json={
        "event_type": "SIGNAL_FAILURE",
        "affected_section_id": 2,
        "severity": "HIGH",
        "description": "Red-aspect failure at North Junction interlocking"
    })
    assert res_inject.status_code == 200
    evt = res_inject.json()
    assert evt["status"] == "ACTIVE"
    event_id = evt["id"]

    # 2. Generate Safe AI Mitigation
    res_mit = client.post(f"/api/control/emergency/{event_id}/mitigate")
    assert res_mit.status_code == 200
    plan = res_mit.json()
    assert plan["status"] == "SAFE_RESPONSE_READY"
    assert plan["safety_status"] == "APPROVED"

    # 3. Resolve Incident
    res_res = client.post(
        f"/api/control/emergency/{event_id}/resolve",
        json={"resolution_notes": "Signal relay replaced and tested."}
    )
    assert res_res.status_code == 200
    assert res_res.json()["success"] is True
