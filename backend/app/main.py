import sys
from pathlib import Path

# Add project root and backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .config.settings import settings
from .config.logging import logger
from .database.session import init_db, SessionLocal
from .models.railway import Station, RailwaySection, Track, Train, TrainSchedule
from .routes.system import router as system_router
from .routes.railway import router as railway_router
from .routes.simulation import router as simulation_router
from .routes.conflicts import router as conflicts_router
from .routes.ml import router as ml_router
from .routes.optimization import router as optimization_router
from .routes.safety import router as safety_router
from .routes.analytics import router as analytics_router
from .routes.explainability import router as explainability_router
from .routes.control_center import router as control_center_router
from simulation import simulation_engine


openapi_tags = [
    {"name": "System", "description": "Core system status, health probes, and API catalog."},
    {"name": "Railway Infrastructure", "description": "Stations, corridor sections, physical tracks, and timetable schedules."},
    {"name": "Train Simulation & Telemetry", "description": "Discrete kinematic train simulation, clock stepping, and real-time WebSocket stream."},
    {"name": "Conflict Detection & Headway", "description": "Continuous safety headway monitoring, route conflict analysis, and bottleneck detection."},
    {"name": "Machine Learning Delay Prediction", "description": "HistGradientBoosting regression for arrival delay forecasting and feature importance."},
    {"name": "AI Traffic Optimization", "description": "Multi-objective mathematical and heuristic train dispatching optimizer."},
    {"name": "Safety Validation Engine", "description": "9-rule formal safety verification gate for collision prevention and emergency halt."},
    {"name": "Performance Analytics", "description": "Empirical scientific benchmark comparing AI against Traditional FCFS heuristics."},
    {"name": "Explainable AI", "description": "Deterministic decision explanations, feature attributions, and candidate alternative comparisons."},
    {"name": "Control Center & Emergency", "description": "Real-time unified dispatch center, scenario management, safety-interlocked overrides, and demo mode."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info("Initializing %s (%s)...", settings.PROJECT_NAME, settings.PROJECT_PHASE)
    # Initialize database tables on startup
    init_db()
    logger.info("Database initialized successfully.")

    # Pre-initialize simulation engine with database records
    db = SessionLocal()
    try:
        stations = db.query(Station).all()
        sections = db.query(RailwaySection).all()
        tracks = db.query(Track).all()
        trains = db.query(Train).all()
        schedules = db.query(TrainSchedule).all()
        if stations and trains:
            simulation_engine.initialize(stations, sections, tracks, trains, schedules)
            logger.info("Simulation engine pre-initialized with %d stations, %d trains.", len(stations), len(trains))
    except Exception as exc:
        logger.warning("Simulation pre-initialization notice: %s", exc)
    finally:
        db.close()

    yield

    # Shutdown: Stop any active simulation loop
    logger.info("Shutting down application...")
    if simulation_engine.is_running:
        simulation_engine.is_running = False
        if simulation_engine._loop_task and not simulation_engine._loop_task.done():
            simulation_engine._loop_task.cancel()
        logger.info("Simulation loop cleanly halted.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description=(
        "API for AI-Powered Precise Train Traffic Control.\n\n"
        "**Academic Simulation & Decision-Support Prototype Notice**:\n"
        "This system does NOT directly control physical railway infrastructure, signals, switches, or locomotives. "
        "It serves as a high-fidelity simulation and decision-support tool to evaluate section throughput optimization."
    ),
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend cross-origin requests
origins = settings.ALLOWED_ORIGINS
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global Centralized Error Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTP exceptions consistently while preserving backward compatibility."""
    logger.warning("HTTP %d error on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly."""
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    err_list = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "detail": err_list,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request payload failed schema validation.",
                "details": err_list,
            },
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Catches database exceptions without leaking database credentials or raw SQL."""
    logger.error("Database error on %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "A database error occurred while processing the request.",
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A transactional database error occurred. Consult server logs.",
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catches unexpected exceptions, logs traceback, and returns safe 500 JSON."""
    logger.exception("Unhandled server error on %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "An internal server error occurred.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact the administrator or consult logs.",
            },
        },
    )


# Register routes
app.include_router(system_router)
app.include_router(simulation_router)
app.include_router(railway_router)
app.include_router(conflicts_router)
app.include_router(ml_router)
app.include_router(optimization_router)
app.include_router(safety_router)
app.include_router(analytics_router)
app.include_router(explainability_router)
app.include_router(control_center_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
    )
