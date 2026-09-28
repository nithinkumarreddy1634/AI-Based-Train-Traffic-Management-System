import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import check_database_connection


@pytest.fixture(scope="module")
def client():
    """Provides a FastAPI test client instance with lifespan events."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test root endpoint returns 200 and valid system status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Train Traffic" in data["project"]
    assert "version" in data
    assert data["phase"] == "Phase 1: Project Foundation & System Setup"
    assert data["docs_url"] == "/docs"


def test_health_endpoint(client):
    """Test health check endpoint probes database connectivity and status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0
    assert "timestamp" in data


def test_api_catalog_endpoint(client):
    """Test API catalog endpoint returns endpoint metadata and module descriptions."""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "endpoints" in data
    assert len(data["endpoints"]) >= 3
    paths = [ep["path"] for ep in data["endpoints"]]
    assert "/" in paths
    assert "/health" in paths
    assert "/api" in paths
    assert "modules" in data
    assert "simulation" in data["modules"]
    assert "ml" in data["modules"]


def test_database_connection_probe():
    """Directly test the SQLite database connection check helper."""
    alive = check_database_connection()
    assert alive is True

