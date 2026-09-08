import pytest
from fastapi.testclient import TestClient
from app.main import app
from simulation.engine import simulation_engine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_dashboard_summary_endpoint(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_trains" in data
    assert "running_trains" in data
    assert "waiting_trains" in data
    assert "delayed_trains" in data
    assert "arrived_trains" in data
    assert "occupied_sections" in data
    assert "total_sections" in data
    assert "throughput_trains_per_hour" in data
    assert "simulation_time" in data
    assert data["total_trains"] >= 10
    assert data["total_sections"] >= 5


def test_sections_live_endpoint(client):
    response = client.get("/api/sections/live")
    assert response.status_code == 200
    sections = response.json()
    assert isinstance(sections, list)
    assert len(sections) >= 5
    first_sec = sections[0]
    assert "section_id" in first_sec
    assert "section_name" in first_sec
    assert "status" in first_sec
    assert first_sec["status"] in ("AVAILABLE", "OCCUPIED", "BLOCKED", "MAINTENANCE")
    assert "utilization_percent" in first_sec
    assert "density_level" in first_sec
    assert first_sec["density_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "current_trains" in first_sec


def test_tracks_live_endpoint(client):
    response = client.get("/api/tracks/live")
    assert response.status_code == 200
    tracks = response.json()
    assert isinstance(tracks, list)
    assert len(tracks) >= 10
    first_track = tracks[0]
    assert "track_id" in first_track
    assert "section_id" in first_track
    assert "direction" in first_track
    assert "status" in first_track
    assert first_track["status"] in ("AVAILABLE", "OCCUPIED", "BLOCKED")


def test_traffic_density_endpoint(client):
    response = client.get("/api/traffic-density")
    assert response.status_code == 200
    data = response.json()
    assert "network_density" in data
    assert data["network_density"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "average_trains_per_section" in data
    assert "sections" in data
    assert len(data["sections"]) >= 5


def test_utilization_endpoint(client):
    response = client.get("/api/utilization")
    assert response.status_code == 200
    util_list = response.json()
    assert isinstance(util_list, list)
    assert len(util_list) >= 5
    first_util = util_list[0]
    assert "section_id" in first_util
    assert "section_name" in first_util
    assert "utilization_percent" in first_util
    assert 0.0 <= first_util["utilization_percent"] <= 100.0


def test_throughput_endpoint(client):
    response = client.get("/api/throughput")
    assert response.status_code == 200
    data = response.json()
    assert "completed_trains" in data
    assert "throughput_trains_per_hour" in data
    assert "simulation_seconds" in data


def test_alerts_endpoint_and_clear(client):
    # Retrieve alerts
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)

    # Filter by severity
    filtered_response = client.get("/api/alerts?severity=INFO")
    assert filtered_response.status_code == 200
    filtered_alerts = filtered_response.json()
    for a in filtered_alerts:
        assert a["severity"] == "INFO"

    # Clear alerts
    del_response = client.delete("/api/alerts")
    assert del_response.status_code == 200
    after_clear = client.get("/api/alerts").json()
    assert len(after_clear) == 0


def test_events_endpoint_and_clear(client):
    # Retrieve events
    response = client.get("/api/events?limit=10")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)

    # Clear events
    del_response = client.delete("/api/events")
    assert del_response.status_code == 200
    after_clear = client.get("/api/events").json()
    assert len(after_clear) == 0


def test_live_trains_enriched_fields(client):
    response = client.get("/api/trains/live")
    assert response.status_code == 200
    trains = response.json()
    assert len(trains) >= 10
    first_train = trains[0]
    assert "remaining_distance_km" in first_train
    assert "section_progress_pct" in first_train
    assert "max_speed_kmph" in first_train
    assert "route_stations" in first_train
    assert isinstance(first_train["route_stations"], list)
    if first_train["route_stations"]:
        st0 = first_train["route_stations"][0]
        assert "station_code" in st0
        assert "station_name" in st0
        assert "is_visited" in st0
        assert "is_current" in st0
