import time
import datetime
from typing import Dict, Any
from ..config.settings import settings
from ..database.session import check_database_connection


class SystemService:
    """Service handling system-level status, health checks, and API cataloging."""

    def __init__(self) -> None:
        self._start_time = time.time()

    @property
    def uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 2)

    def get_root_status(self) -> Dict[str, Any]:
        """Provides status for the root `/` endpoint."""
        return {
            "status": "online",
            "message": "AI-Powered Train Traffic Control API is running",
            "project": settings.PROJECT_NAME,
            "version": settings.API_VERSION,
            "phase": "Phase 1: Project Foundation & System Setup",
            "current_phase": settings.PROJECT_PHASE,
            "docs_url": "/docs",
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Performs system diagnostic check including SQLite database connectivity."""
        db_alive = check_database_connection()
        return {
            "status": "healthy" if db_alive else "degraded",
            "database": "connected" if db_alive else "disconnected",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "version": settings.API_VERSION,
            "environment": "development" if settings.API_DEBUG else "production",
        }

    def get_api_catalog(self) -> Dict[str, Any]:
        """Returns API overview, module listing, and available endpoints."""
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.API_VERSION,
            "phase": settings.PROJECT_PHASE,
            "description": (
                "Simulation and decision-support API for precise train traffic control, "
                "section throughput maximization, and conflict prediction."
            ),
            "endpoints": [
                {
                    "path": "/",
                    "method": "GET",
                    "description": "Root endpoint indicating API service status and project metadata.",
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "System health probe verifying database connectivity, uptime, and state.",
                },
                {
                    "path": "/api",
                    "method": "GET",
                    "description": "API metadata catalog with details on registered routes and subsystems.",
                },
                {
                    "path": "/docs",
                    "method": "GET",
                    "description": "Interactive OpenAPI Swagger documentation.",
                },
                {
                    "path": "/redoc",
                    "method": "GET",
                    "description": "ReDoc alternative API documentation interface.",
                },
            ],
            "modules": {
                "backend": "FastAPI REST API & SQLite persistence foundation",
                "frontend": "React + Vite train controller dashboard",
                "simulation": "Phase 2: Railway block and kinematic simulation engine",
                "ml": "Phase 3: Train delay prediction and dwell time regression models",
                "optimization": "Phase 4: AI & mathematical dispatching throughput optimizer",
                "safety": "Phase 4: Block headway constraints and safety interlocking",
            },
        }


system_service = SystemService()
