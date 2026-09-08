import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# STATIONS API TESTS
# =============================================================================
def test_get_stations(client):
    response = client.get("/api/stations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    codes = [s["station_code"] for s in data]
    assert "SEC01" in codes
    assert "SEC02" in codes


def test_get_station_by_id(client):
    response = client.get("/api/stations/1")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 1
    assert "station_code" in data
    assert "station_name" in data


def test_get_station_not_found(client):
    response = client.get("/api/stations/99999")
    assert response.status_code == 404


def test_create_and_delete_station(client):
    new_station = {
        "station_code": "SEC99",
        "station_name": "Test Orbital Station",
        "latitude": 28.9,
        "longitude": 77.4,
        "number_of_platforms": 2,
        "status": "ACTIVE",
    }
    create_res = client.post("/api/stations", json=new_station)
    assert create_res.status_code == 201
    created_id = create_res.json()["station_id"]
    assert create_res.json()["station_code"] == "SEC99"

    # Update station
    upd_res = client.put(f"/api/stations/{created_id}", json={"station_name": "Updated Orbital Station"})
    assert upd_res.status_code == 200
    assert upd_res.json()["station_name"] == "Updated Orbital Station"

    # Delete station
    del_res = client.delete(f"/api/stations/{created_id}")
    assert del_res.status_code == 204

    # Confirm 404
    get_res = client.get(f"/api/stations/{created_id}")
    assert get_res.status_code == 404


# =============================================================================
# SECTIONS API TESTS
# =============================================================================
def test_get_sections(client):
    response = client.get("/api/sections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 7
    first_sec = data[0]
    assert "section_id" in first_sec
    assert "length_km" in first_sec
    assert len(first_sec["tracks"]) >= 1


def test_create_section_invalid_station(client):
    bad_section = {
        "section_name": "Ghost Line",
        "start_station_id": 9999,
        "end_station_id": 1,
        "length_km": 15.0,
        "maximum_speed_kmph": 100.0,
        "number_of_tracks": 2,
        "status": "AVAILABLE",
    }
    response = client.post("/api/sections", json=bad_section)
    assert response.status_code == 404


def test_create_section_same_station_rejected(client):
    bad_section = {
        "section_name": "Loopback Loop",
        "start_station_id": 1,
        "end_station_id": 1,
        "length_km": 5.0,
        "maximum_speed_kmph": 80.0,
        "number_of_tracks": 1,
        "status": "AVAILABLE",
    }
    response = client.post("/api/sections", json=bad_section)
    assert response.status_code in (400, 422)


# =============================================================================
# TRACKS API TESTS
# =============================================================================
def test_get_tracks(client):
    response = client.get("/api/tracks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 14
    t = data[0]
    assert "direction" in t
    assert "status" in t


def test_update_track(client):
    response = client.put("/api/tracks/1", json={"status": "MAINTENANCE"})
    assert response.status_code == 200
    assert response.json()["status"] == "MAINTENANCE"

    # Reset
    client.put("/api/tracks/1", json={"status": "OCCUPIED"})


# =============================================================================
# TRAINS API TESTS
# =============================================================================
def test_get_trains(client):
    response = client.get("/api/trains")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 12


def test_get_trains_filtered(client):
    # Filter by type
    res_exp = client.get("/api/trains?train_type=EXPRESS")
    assert res_exp.status_code == 200
    assert all(t["train_type"] == "EXPRESS" for t in res_exp.json())

    # Filter by priority
    res_prio = client.get("/api/trains?priority=HIGH")
    assert res_prio.status_code == 200
    assert all(t["priority"] == "HIGH" for t in res_prio.json())

    # Search query
    res_search = client.get("/api/trains?search=Rajdhani")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1


def test_create_train_invalid_same_source_dest(client):
    bad_train = {
        "train_number": "BAD-999",
        "train_name": "Non-moving Train",
        "train_type": "LOCAL",
        "priority": "LOW",
        "source_station_id": 1,
        "destination_station_id": 1,
        "scheduled_departure": "09:00",
        "scheduled_arrival": "09:30",
    }
    response = client.post("/api/trains", json=bad_train)
    assert response.status_code in (400, 422)


def test_create_train_invalid_negative_speed(client):
    bad_train = {
        "train_number": "NEG-999",
        "train_name": "Reverse Train",
        "train_type": "LOCAL",
        "priority": "LOW",
        "source_station_id": 1,
        "destination_station_id": 2,
        "speed_kmph": -50.0,
        "scheduled_departure": "09:00",
        "scheduled_arrival": "09:30",
    }
    response = client.post("/api/trains", json=bad_train)
    assert response.status_code == 422


def test_create_and_delete_train(client):
    new_train = {
        "train_number": "TMP-777",
        "train_name": "Temporary Test Express",
        "train_type": "EXPRESS",
        "priority": "HIGH",
        "source_station_id": 1,
        "destination_station_id": 4,
        "current_position_km": 0.0,
        "speed_kmph": 80.0,
        "direction": "UP",
        "status": "RUNNING",
        "scheduled_departure": "12:00",
        "scheduled_arrival": "13:30",
        "current_delay_minutes": 0.0,
    }
    create_res = client.post("/api/trains", json=new_train)
    assert create_res.status_code == 201
    created_id = create_res.json()["train_id"]

    # Update train delay
    upd_res = client.put(f"/api/trains/{created_id}", json={"current_delay_minutes": 10.0, "status": "DELAYED"})
    assert upd_res.status_code == 200
    assert upd_res.json()["current_delay_minutes"] == 10.0
    assert upd_res.json()["status"] == "DELAYED"

    # Delete train
    del_res = client.delete(f"/api/trains/{created_id}")
    assert del_res.status_code == 204


# =============================================================================
# NETWORK & DASHBOARD TESTS
# =============================================================================
def test_get_network(client):
    response = client.get("/api/network")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert "sections" in data
    assert "tracks" in data
    assert "trains" in data
    assert "connections" in data
    assert len(data["stations"]) >= 5
    assert len(data["sections"]) >= 7
    assert len(data["connections"]) >= 7


def test_get_schedules(client):
    response = client.get("/api/schedules")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    s = data[0]
    assert "train_number" in s
    assert "station_name" in s
    assert "stop_sequence" in s


def test_get_dashboard_stats(client):
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_trains"] >= 12
    assert data["active_trains"] >= 1
    assert data["total_sections"] >= 7
    assert data["total_tracks"] >= 14
    assert 0 <= data["track_utilization_percent"] <= 100
    assert "system_status" in data
