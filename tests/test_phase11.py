"""
Unit and Integration Tests for Phase 11: Real-Time Intelligent Control Center,
Scenario Management & Emergency Handling.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from control_center import (
    scenario_controller,
    emergency_manager,
    override_manager,
    event_manager,
    control_state_manager,
    control_center
)
from simulation import simulation_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_control_center():
    """Ensures simulation has an active corridor scenario loaded for tests."""
    scenario_controller.load_scenario("medium_traffic")
    event_manager.clear()
    yield
    if simulation_engine.is_running:
        simulation_engine.stop()


def test_scenario_controller_lifecycle():
    """Verifies loading, starting, pausing, resuming, and resetting scenarios."""
    scenarios = scenario_controller.list_available_scenarios()
    assert len(scenarios) >= 6
    assert any(s["id"] == "heavy_traffic" for s in scenarios)

    # 1. Load heavy traffic
    load_res = scenario_controller.load_scenario("heavy_traffic")
    assert load_res["success"] is True
    assert load_res["train_count"] == 24
    assert len(simulation_engine.train_simulators) == 24

    # 2. Start simulation
    start_res = scenario_controller.start_scenario()
    assert start_res["success"] is True
    assert start_res["status"] == "RUNNING"
    assert simulation_engine.is_running is True

    # 3. Pause simulation
    pause_res = scenario_controller.pause_scenario()
    assert pause_res["success"] is True
    assert pause_res["status"] == "PAUSED"
    assert simulation_engine.is_paused is True

    # 4. Resume simulation
    resume_res = scenario_controller.resume_scenario()
    assert resume_res["success"] is True
    assert resume_res["status"] == "RUNNING"

    # 5. Reset scenario
    reset_res = scenario_controller.reset_scenario()
    assert reset_res["success"] is True
    assert reset_res["status"] == "INITIALIZED"
    assert simulation_engine.is_running is False


def test_custom_scenario_validation_and_creation():
    """Verifies custom scenario input bounds and successful generation."""
    # Valid custom scenario
    res = scenario_controller.create_custom_scenario(
        name="Express Rush Hour",
        num_trains=18,
        traffic_level="heavy",
        delayed_trains=4,
        priority_trains=6,
        duration_minutes=45.0
    )
    assert res["success"] is True
    assert "scenario_id" in res
    assert res["config"]["num_trains"] == 18

    # Invalid cases
    inv1 = scenario_controller.create_custom_scenario(name="", num_trains=10)
    assert inv1["success"] is False

    inv2 = scenario_controller.create_custom_scenario(name="Too many", num_trains=999)
    assert inv2["success"] is False

    inv3 = scenario_controller.create_custom_scenario(name="Negative delay", num_trains=10, delayed_trains=-2)
    assert inv3["success"] is False


def test_emergency_manager_workflow():
    """Verifies emergency event creation, impact assessment, safe response, and resolution."""
    # 1. Create emergency event
    evt = emergency_manager.create_event(
        event_type="TRACK_BLOCKAGE",
        affected_section_id=2,
        severity="HIGH",
        description="Fallen tree obstructing Section 2 tracks."
    )
    assert evt["status"] == "ACTIVE"
    assert evt["severity"] == "HIGH"
    assert evt["impact_summary"]["section_closed"] is True
    assert "affected_trains_count" in evt["impact_summary"]

    evt_id = evt["id"]
    active = emergency_manager.get_active_emergencies()
    assert any(e["id"] == evt_id for e in active)

    # 2. Generate safe mitigation response via AI & Safety Validator
    safe_plan = emergency_manager.generate_safe_response(evt_id)
    assert safe_plan["status"] == "SAFE_RESPONSE_READY"
    assert safe_plan["safety_status"] == "APPROVED"
    assert len(safe_plan["recommendations"]) > 0

    # 3. Resolve emergency
    resolve_res = emergency_manager.resolve_event(evt_id, "Track cleared by maintenance crew.")
    assert resolve_res["success"] is True
    assert resolve_res["status"] == "RESOLVED"

    # Verify no longer active
    active_post = emergency_manager.get_active_emergencies()
    assert not any(e["id"] == evt_id for e in active_post)


def test_manual_controller_override_and_safety_interlock():
    """Verifies manual controller overrides and guarantees safety interlock blocks unsafe commands."""
    agent_id = list(simulation_engine.train_simulators.keys())[0]
    agent = simulation_engine.train_simulators[agent_id]

    # 1. Safe override: Hold train
    res_hold = override_manager.execute_override(
        action_type="HOLD_TRAIN",
        train_id=agent_id,
        hold_duration_seconds=180.0,
        reason="Holding for platform congestion clearing."
    )
    assert res_hold["success"] is True
    assert res_hold["safety_status"] == "APPROVED"
    assert agent.status == "WAITING"

    # 2. Safe override: Release train
    res_release = override_manager.execute_override(
        action_type="RELEASE_TRAIN",
        train_id=agent_id,
        reason="Platform cleared, train authorized to proceed."
    )
    assert res_release["success"] is True
    assert res_release["safety_status"] == "APPROVED"
    assert agent.status == "RUNNING"

    # 3. Unsafe override: Negative speed advisory (MUST BE REJECTED BY SAFETY ENGINE)
    res_unsafe = override_manager.execute_override(
        action_type="SPEED_ADVISORY",
        train_id=agent_id,
        new_speed_kmph=-20.0,
        reason="Testing negative speed violation."
    )
    assert res_unsafe["success"] is False
    assert res_unsafe["safety_status"] == "REJECTED"
    assert len(res_unsafe["violations"]) > 0
    assert "RULE_BRAKING_CURVE" in res_unsafe["violations"][0]

    # 4. Verify audit history
    history = override_manager.get_action_history(limit=10)
    assert len(history) >= 2
    assert any(h["train_id"] == agent_id for h in history)


def test_event_manager_stream_and_filtering():
    """Verifies event publication, ring-buffer storage, and filtering."""
    event_manager.clear()

    e1 = event_manager.publish("TRAIN_STARTED", "Train 101 started", category="SIMULATION", severity="INFO")
    e2 = event_manager.publish("CONFLICT_DETECTED", "Headway conflict on Section 1", category="TRAFFIC", severity="WARNING")
    e3 = event_manager.publish("EMERGENCY_CREATED", "Signal failure", category="EMERGENCY", severity="CRITICAL")

    events_all = event_manager.get_events(limit=20)
    assert len(events_all) == 3

    # Filter by category
    traffic_events = event_manager.get_events(category="TRAFFIC")
    assert len(traffic_events) == 1
    assert traffic_events[0]["event_type"] == "CONFLICT_DETECTED"

    # Filter by severity
    critical_events = event_manager.get_events(severity="CRITICAL")
    assert len(critical_events) == 1
    assert critical_events[0]["event_type"] == "EMERGENCY_CREATED"


def test_control_center_apis_via_testclient():
    """Verifies all Phase 11 REST endpoints via FastAPI TestClient."""
    # 1. State endpoint
    r_state = client.get("/api/control/state")
    assert r_state.status_code == 200
    state_data = r_state.json()
    assert "fleet_summary" in state_data
    assert "corridor_summary" in state_data
    assert "sections" in state_data
    assert "system_health" in state_data

    # 2. Health endpoint
    r_health = client.get("/api/control/health")
    assert r_health.status_code == 200
    health_data = r_health.json()
    assert "components" in health_data
    assert health_data["components"]["backend"]["status"] == "ONLINE"

    # 3. AI vs Human analytics endpoint
    r_comp = client.get("/api/control/ai-vs-human")
    assert r_comp.status_code == 200
    comp_data = r_comp.json()
    assert "throughput_impact" in comp_data
    assert "safety_compliance_pct" in comp_data

    # 4. Scenario list & load
    r_scenarios = client.get("/api/control/scenarios")
    assert r_scenarios.status_code == 200
    assert len(r_scenarios.json()) >= 6

    r_load = client.post("/api/control/scenario/load", json={"scenario_id": "low_traffic"})
    assert r_load.status_code == 200
    assert r_load.json()["train_count"] == 6

    # 5. Events endpoint
    r_events = client.get("/api/control/events?limit=10")
    assert r_events.status_code == 200
    assert isinstance(r_events.json(), list)

    # 6. Manual override via API (valid)
    r_override = client.post("/api/control/override", json={
        "action_type": "HOLD_TRAIN",
        "train_id": 1,
        "reason": "Test hold via API"
    })
    assert r_override.status_code == 200
    assert r_override.json()["safety_status"] == "APPROVED"

    # 7. Unsafe manual override via API (expect 422 with safety details)
    r_unsafe_override = client.post("/api/control/override", json={
        "action_type": "SPEED_ADVISORY",
        "train_id": 1,
        "new_speed_kmph": -50.0,
        "reason": "Dangerous negative speed"
    })
    assert r_unsafe_override.status_code == 422


def test_demo_mode_workflow():
    """Verifies demonstration mode status querying and step definitions."""
    demo_status = client.get("/api/control/demo/status")
    assert demo_status.status_code == 200
    d_data = demo_status.json()
    assert d_data["total_steps"] == 12
    assert len(d_data["steps"]) == 12
