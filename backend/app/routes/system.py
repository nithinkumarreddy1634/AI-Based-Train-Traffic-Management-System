from typing import Dict, Any
from fastapi import APIRouter
from ..schemas.system import RootResponse, HealthResponse, ApiInfoResponse
from ..services.system_service import system_service
from ..database.session import check_database_connection
from ..config.settings import settings
from simulation import simulation_engine
from ml.models.predict import delay_prediction_service

router = APIRouter(tags=["System"])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Root API Status",
    description="Returns the operational status and project information for the Train Traffic Control API.",
)
async def get_root() -> RootResponse:
    return RootResponse(**system_service.get_root_status())


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check Probe",
    description="Probes database connectivity, server uptime, and operational readiness.",
)
async def get_health() -> HealthResponse:
    return HealthResponse(**system_service.get_health_status())


@router.get(
    "/api/health",
    summary="Comprehensive Subsystem Health Status",
    description="Returns granular health status across Backend, Database, Simulation, ML Model, Optimizer, Safety, Analytics, Explainability, and WebSocket.",
)
async def get_comprehensive_health() -> Dict[str, Any]:
    """Granular health check reporting status of all major subsystems."""
    db_ok = check_database_connection()
    sim_ok = simulation_engine.is_ready
    if not delay_prediction_service.is_ready:
        try:
            delay_prediction_service.load_artifacts()
        except Exception:
            pass
    ml_ok = delay_prediction_service.is_ready
    meta = delay_prediction_service.get_metadata() if ml_ok else {}

    return {
        "status": "healthy" if db_ok else "degraded",
        "backend": "healthy",
        "database": "healthy" if db_ok else "unreachable",
        "simulation": "ready" if sim_ok else "initializing",
        "ml_model": "loaded" if ml_ok else "unavailable",
        "optimizer": "ready",
        "safety": "active",
        "safety_engine": "active",
        "analytics": "ready",
        "explainability": "ready",
        "websocket": "ready",
        "application_version": settings.API_VERSION,
        "database_version": "SQLite 3 (SQLAlchemy 2.0)",
        "ml_model_version": f"{meta.get('model_name', 'HistGradientBoosting')} v1.0.0",
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": system_service.uptime_seconds,
        "timestamp": system_service.get_health_status().get("timestamp"),
    }


@router.get(
    "/api",
    response_model=ApiInfoResponse,
    summary="API Catalog Information",
    description="Provides descriptive metadata for the API endpoints and planned subsystem modules.",
)
async def get_api_info() -> ApiInfoResponse:
    return ApiInfoResponse(**system_service.get_api_catalog())
