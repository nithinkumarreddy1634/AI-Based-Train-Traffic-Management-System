import sys
from pathlib import Path

# Ensure root directory is accessible for simulation package
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..models.railway import Station, RailwaySection, Track, Train, TrainSchedule
from simulation import simulation_engine

router = APIRouter(tags=["Simulation Engine & Real-Time Monitoring"])


class SpeedMultiplierRequest(BaseModel):
    multiplier: float = Field(..., ge=1.0, le=10.0, json_schema_extra={"example": 5.0})


def ensure_simulation_initialized(db: Session):
    """Ensures the simulation engine has loaded data from the SQLite database."""
    if not simulation_engine.train_simulators:
        stations = db.query(Station).all()
        sections = db.query(RailwaySection).all()
        tracks = db.query(Track).all()
        trains = db.query(Train).all()
        schedules = db.query(TrainSchedule).all()
        simulation_engine.initialize(stations, sections, tracks, trains, schedules)


# =============================================================================
# SIMULATION CONTROLS
# =============================================================================
@router.post(
    "/api/simulation/start",
    summary="Start Simulation",
    description="Starts the real-time train movement physics loop and clock.",
)
async def start_simulation(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    simulation_engine.start()
    return {"message": "Simulation started successfully.", "status": simulation_engine.get_status()}


@router.post(
    "/api/simulation/pause",
    summary="Pause Simulation",
    description="Freezes train movement and halts simulation clock progression.",
)
async def pause_simulation():
    simulation_engine.pause()
    return {"message": "Simulation paused.", "status": simulation_engine.get_status()}


@router.post(
    "/api/simulation/resume",
    summary="Resume Simulation",
    description="Resumes movement of trains after being paused.",
)
async def resume_simulation():
    simulation_engine.resume()
    return {"message": "Simulation resumed.", "status": simulation_engine.get_status()}


@router.post(
    "/api/simulation/reset",
    summary="Reset Simulation",
    description="Halts simulation and restores trains, tracks, and stations to their baseline scenario state.",
)
async def reset_simulation(db: Session = Depends(get_db)):
    stations = db.query(Station).all()
    sections = db.query(RailwaySection).all()
    tracks = db.query(Track).all()
    trains = db.query(Train).all()
    schedules = db.query(TrainSchedule).all()
    simulation_engine.reset(stations, sections, tracks, trains, schedules)
    return {"message": "Simulation reset to initial state.", "status": simulation_engine.get_status()}


@router.post(
    "/api/simulation/step",
    summary="Step Simulation Tick",
    description="Advances the discrete-time kinematic simulation by one step (default dt=1.0s).",
)
async def step_simulation(dt: float = 1.0, db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    for train_sim in simulation_engine.train_simulators.values():
        train_sim.step(dt, simulation_engine.sim_time_seconds)
    simulation_engine.sim_time_seconds += dt
    simulation_engine.tick_count += 1
    return {
        "success": True,
        "message": "Simulation stepped by 1 tick.",
        "sim_time": simulation_engine.formatted_sim_time,
        "status": simulation_engine.get_status(),
    }




@router.post(
    "/api/simulation/speed",
    summary="Set Simulation Speed Multiplier",
    description="Configures clock time-acceleration (1x, 2x, 5x, 10x).",
)
async def set_speed(payload: SpeedMultiplierRequest):
    success = simulation_engine.set_speed_multiplier(payload.multiplier)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid speed multiplier. Allowed: [1.0, 2.0, 5.0, 10.0]",
        )
    return {"message": f"Speed multiplier set to {payload.multiplier}x", "status": simulation_engine.get_status()}


@router.get(
    "/api/simulation/status",
    summary="Simulation Status",
    description="Returns current running state, clock time, active train counts, and throughput.",
)
async def get_simulation_status(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_status()


@router.get(
    "/api/simulation/state",
    summary="Full Simulation State",
    description="Returns full snapshot containing all train positions, track occupancies, and recent events.",
)
async def get_simulation_state(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_live_state()


@router.get(
    "/api/dashboard/summary",
    summary="Control-Room Dashboard Summary",
    description="Aggregates live control-room statistics: running, waiting, delayed, arrived trains, occupied sections, and throughput.",
)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_dashboard_summary()


@router.get(
    "/api/sections/live",
    summary="Live Railway Section Telemetry",
    description="Real-time block section occupancy, current trains, density levels, and cumulative utilization.",
)
async def get_live_sections(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_sections_live()


@router.get(
    "/api/tracks/live",
    summary="Live Physical Track Status",
    description="Track rack status displaying directional tracks, occupancy, and occupying train details.",
)
async def get_live_tracks(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_tracks_live()


@router.get(
    "/api/alerts",
    summary="Live Dispatcher Alerts",
    description="Returns prioritized alerts filtered by optional severity (INFO, WARNING, CRITICAL).",
)
async def get_alerts(severity: Optional[str] = None, db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_alerts(severity=severity)


@router.delete(
    "/api/alerts",
    summary="Clear Alert Buffer",
    description="Clears all active alerts from the in-memory ring buffer.",
)
async def clear_alerts():
    simulation_engine.clear_alerts()
    return {"message": "Alert buffer cleared successfully."}


@router.get(
    "/api/events",
    summary="Simulation Events",
    description="Recent simulation event log stream.",
)
async def get_events(limit: int = 50):
    events = list(simulation_engine.event_log)
    return events[:limit]


@router.delete(
    "/api/events",
    summary="Clear Event Log",
    description="Clears all recorded simulation events.",
)
async def clear_events():
    simulation_engine.clear_events()
    return {"message": "Event log cleared successfully."}


@router.get(
    "/api/simulation/events",
    summary="Recent Simulation Events (Alias)",
    description="Returns the ring buffer of recent dispatcher events.",
)
async def get_simulation_events():
    return list(simulation_engine.event_log)


@router.get(
    "/api/throughput",
    summary="Real-Time Throughput Counter",
    description="Calculates completed trains and throughput in trains per simulation hour.",
)
async def get_throughput():
    return simulation_engine.get_throughput_metrics()


@router.get(
    "/api/traffic-density",
    summary="Traffic Density Analysis",
    description="Categorizes section and corridor traffic load as LOW, MEDIUM, HIGH, or CRITICAL.",
)
async def get_traffic_density(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_traffic_density()


@router.get(
    "/api/utilization",
    summary="Railway Section Utilization",
    description="Cumulative percentage of time each railway section was occupied during the simulation run.",
)
async def get_utilization(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_utilization()


@router.get(
    "/api/trains/live",
    summary="Live Train Telemetry",
    description="Real-time telemetry for all trains with instantaneous speed, section milepost, route stations, and delay minutes.",
)
async def get_live_trains(db: Session = Depends(get_db)):
    ensure_simulation_initialized(db)
    return simulation_engine.get_live_trains()


# =============================================================================
# WEBSOCKET REAL-TIME STREAMING
# =============================================================================
@router.websocket("/ws/train-updates")
async def websocket_train_updates(websocket: WebSocket):
    """
    WebSocket endpoint streaming instantaneous train positions, speed changes,
    track occupancy transitions, and simulation events to the frontend.
    """
    await websocket.accept()
    simulation_engine.register_websocket(websocket)
    try:
        # Send initial snapshot immediately upon connect
        initial_state = simulation_engine.get_live_state()
        await websocket.send_json(initial_state)

        # Keep socket open and listen for optional ping/commands
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        simulation_engine.unregister_websocket(websocket)
    except Exception:
        simulation_engine.unregister_websocket(websocket)
