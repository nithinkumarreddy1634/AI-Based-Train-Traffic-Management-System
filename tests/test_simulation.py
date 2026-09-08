import pytest
from fastapi.testclient import TestClient
from app.main import app
from simulation.movement import calculate_motion
from simulation.state_manager import StateManager
from simulation.config import config
from simulation.engine import simulation_engine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# KINEMATICS & MOVEMENT TESTS
# =============================================================================
def test_motion_acceleration():
    # Train accelerating from 0 km/h towards 100 km/h limit on 20 km section
    speed, pos, reached_end = calculate_motion(
        current_speed_kmph=0.0,
        current_pos_km=0.0,
        section_length_km=20.0,
        train_type="EXPRESS",
        max_section_speed_kmph=120.0,
        dt_seconds=5.0,
        is_approaching_stop=False,
    )
    assert speed > 0.0
    assert pos > 0.0
    assert not reached_end


def test_motion_speed_capping():
    # Train speed capped by section limit (e.g. section max 60 km/h, train max 130 km/h)
    speed, pos, _ = calculate_motion(
        current_speed_kmph=55.0,
        current_pos_km=5.0,
        section_length_km=20.0,
        train_type="EXPRESS",
        max_section_speed_kmph=60.0,
        dt_seconds=10.0,
        is_approaching_stop=False,
    )
    assert speed <= 60.0


def test_motion_deceleration_approaching_stop():
    # Near end of section, deceleration kicks in
    speed, pos, reached_end = calculate_motion(
        current_speed_kmph=80.0,
        current_pos_km=19.5,
        section_length_km=20.0,
        train_type="PASSENGER",
        max_section_speed_kmph=100.0,
        dt_seconds=2.0,
        is_approaching_stop=True,
    )
    # Speed should be significantly reduced when approaching stop
    assert speed < 80.0


def test_motion_boundary_clamping():
    # Overshoot should clamp to section length
    speed, pos, reached_end = calculate_motion(
        current_speed_kmph=120.0,
        current_pos_km=19.9,
        section_length_km=20.0,
        train_type="EXPRESS",
        max_section_speed_kmph=130.0,
        dt_seconds=10.0,
        is_approaching_stop=True,
    )
    assert pos == 20.0
    assert reached_end is True


# =============================================================================
# TRACK OCCUPANCY & SAFETY RULES
# =============================================================================
def test_track_reservation_and_release():
    sm = StateManager()
    tracks_mock = [
        {"track_id": 101, "section_id": 1, "track_number": 1, "direction": "UP", "status": "AVAILABLE", "occupied_by_train": None}
    ]
    sm.initialize_tracks(tracks_mock)

    # Reserve track
    ok = sm.reserve_track(101, train_id=1)
    assert ok is True
    assert sm.tracks[101]["status"] == "OCCUPIED"
    assert sm.tracks[101]["occupied_by_train"] == 1
    assert sm.is_section_occupied(1) is True

    # Safety: second train cannot enter occupied track
    ok2 = sm.reserve_track(101, train_id=2)
    assert ok2 is False

    # Release track
    sm.release_track(train_id=1)
    assert sm.tracks[101]["status"] == "AVAILABLE"
    assert sm.tracks[101]["occupied_by_train"] is None
    assert sm.is_section_occupied(1) is False


# =============================================================================
# SIMULATION ENGINE CONTROLS & API TESTS
# =============================================================================
def test_simulation_status_api(client):
    res = client.get("/api/simulation/status")
    assert res.status_code == 200
    data = res.json()
    assert "running" in data
    assert "simulation_time" in data
    assert "speed_multiplier" in data
    assert "active_trains" in data
    assert "throughput_trains_per_hour" in data


def test_simulation_start_pause_resume_reset_apis(client):
    # Start
    res_start = client.post("/api/simulation/start")
    assert res_start.status_code == 200
    assert res_start.json()["status"]["running"] is True

    # Pause
    res_pause = client.post("/api/simulation/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["status"]["paused"] is True

    # Resume
    res_resume = client.post("/api/simulation/resume")
    assert res_resume.status_code == 200
    assert res_resume.json()["status"]["paused"] is False

    # Change Speed Multiplier
    res_speed = client.post("/api/simulation/speed", json={"multiplier": 5.0})
    assert res_speed.status_code == 200
    assert res_speed.json()["status"]["speed_multiplier"] == 5.0

    # Invalid speed multiplier rejected
    res_bad_speed = client.post("/api/simulation/speed", json={"multiplier": 99.0})
    assert res_bad_speed.status_code in (400, 422)

    # Reset
    res_reset = client.post("/api/simulation/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"]["running"] is False


def test_simulation_live_trains_api(client):
    res = client.get("/api/trains/live")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    first = data[0]
    assert "train_id" in first
    assert "train_number" in first
    assert "speed_kmph" in first
    assert "current_position_km" in first
    assert "status" in first


def test_simulation_events_api(client):
    res = client.get("/api/simulation/events")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "event_type" in data[0]
    assert "timestamp" in data[0]


def test_websocket_train_updates(client):
    with client.websocket_connect("/ws/train-updates") as websocket:
        initial_frame = websocket.receive_json()
        assert "status" in initial_frame
        assert "trains" in initial_frame
        assert "tracks" in initial_frame
        assert "events" in initial_frame
        assert len(initial_frame["trains"]) >= 10

        # Send ping
        websocket.send_text("ping")
        resp = websocket.receive_text()
        assert resp == "pong"
