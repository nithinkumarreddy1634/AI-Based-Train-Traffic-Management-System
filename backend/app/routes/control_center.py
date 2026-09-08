"""
REST API Router for Phase 11: Real-Time Intelligent Control Center,
Scenario Management & Emergency Handling.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from control_center import (
    control_center,
    scenario_controller,
    emergency_manager,
    override_manager,
    control_state_manager,
    event_manager
)

router = APIRouter(prefix="/api/control", tags=["Intelligent Control Center"])


# Request Models
class LoadScenarioRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of scenario to load (e.g. 'heavy_traffic', 'high_delay')")


class CustomScenarioRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    num_trains: int = Field(15, ge=2, le=50)
    traffic_level: str = Field("medium", description="Traffic density (low, medium, heavy, critical)")
    delayed_trains: int = Field(3, ge=0)
    priority_trains: int = Field(4, ge=0)
    bottleneck_section_id: Optional[int] = Field(None)
    duration_minutes: float = Field(60.0, ge=1.0, le=720.0)


class CreateEmergencyRequest(BaseModel):
    event_type: str = Field(..., description="TRACK_BLOCKAGE, SIGNAL_UNAVAILABLE, TRAIN_STOPPED, UNEXPECTED_DELAY, SECTION_UNAVAILABLE, EMERGENCY_STOP")
    affected_section_id: Optional[int] = Field(None)
    affected_train_id: Optional[int] = Field(None)
    severity: str = Field("HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    description: Optional[str] = Field(None)


class ResolveEmergencyRequest(BaseModel):
    resolution_notes: Optional[str] = Field(None, description="Clearance notes and operational instructions")


class ManualOverrideRequest(BaseModel):
    action_type: str = Field(..., description="HOLD_TRAIN, RELEASE_TRAIN, CHANGE_PRIORITY, PAUSE_TRAIN, RESUME_TRAIN, SELECT_ALTERNATIVE_TRACK, SPEED_ADVISORY, CANCEL_RECOMMENDATION")
    train_id: int = Field(..., description="Target train ID")
    section_id: Optional[int] = Field(None)
    new_speed_kmph: Optional[float] = Field(None, description="Advisory or operating speed")
    new_priority: Optional[str] = Field(None, description="HIGH, MEDIUM, LOW")
    track_id: Optional[int] = Field(None, description="Target track ID for diversion")
    hold_duration_seconds: Optional[float] = Field(None)
    reason: Optional[str] = Field(None, description="Operational justification for override")
    controller_id: str = Field("CONTROLLER_DESK_1")


# 1. State & Health Endpoints
@router.get("/state", response_model=Dict[str, Any])
def get_control_center_state():
    """Returns the unified real-time operational status of all corridor assets and subsystems."""
    return control_state_manager.get_unified_state()


@router.get("/health", response_model=Dict[str, Any])
def get_system_health():
    """Returns granular component health for all 7 subsystems."""
    return control_state_manager.get_system_health()


@router.get("/ai-vs-human", response_model=Dict[str, Any])
def get_ai_vs_human_analytics():
    """Returns comparative metrics between AI recommendations and manual controller overrides."""
    return control_center.get_ai_vs_human_metrics()


# 2. Scenario Management Endpoints
@router.get("/scenarios", response_model=List[Dict[str, Any]])
def list_scenarios():
    """Lists standard and custom available scenarios."""
    return scenario_controller.list_available_scenarios()


@router.post("/scenario/load", response_model=Dict[str, Any])
def load_scenario(req: LoadScenarioRequest):
    """Loads a standard or custom scenario into the simulation engine."""
    res = scenario_controller.load_scenario(req.scenario_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to load scenario."))
    return res


@router.post("/scenario/start", response_model=Dict[str, Any])
def start_scenario():
    """Starts the real-time simulation engine."""
    return scenario_controller.start_scenario()


@router.post("/scenario/pause", response_model=Dict[str, Any])
def pause_scenario():
    """Pauses the simulation engine."""
    return scenario_controller.pause_scenario()


@router.post("/scenario/resume", response_model=Dict[str, Any])
def resume_scenario():
    """Resumes paused simulation."""
    return scenario_controller.resume_scenario()


@router.post("/scenario/reset", response_model=Dict[str, Any])
def reset_scenario():
    """Resets the active simulation back to time zero."""
    return scenario_controller.reset_scenario()


@router.post("/scenario/custom", response_model=Dict[str, Any])
def create_custom_scenario(req: CustomScenarioRequest):
    """Builds and stores a custom traffic scenario."""
    res = scenario_controller.create_custom_scenario(
        name=req.name,
        num_trains=req.num_trains,
        traffic_level=req.traffic_level,
        delayed_trains=req.delayed_trains,
        priority_trains=req.priority_trains,
        bottleneck_section_id=req.bottleneck_section_id,
        duration_minutes=req.duration_minutes
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to create custom scenario."))
    return res


# 3. Emergency Management Endpoints
@router.post("/emergency", response_model=Dict[str, Any])
def create_simulated_emergency(req: CreateEmergencyRequest):
    """Injects a simulated emergency event and assesses corridor impact."""
    return emergency_manager.create_event(
        event_type=req.event_type,
        affected_section_id=req.affected_section_id,
        affected_train_id=req.affected_train_id,
        severity=req.severity,
        description=req.description
    )


@router.get("/emergencies", response_model=List[Dict[str, Any]])
def get_emergencies(limit: int = Query(50, ge=1, le=100)):
    """Returns active and historical emergency events."""
    return emergency_manager.get_all_emergencies(limit=limit)


@router.post("/emergency/{emergency_id}/mitigate", response_model=Dict[str, Any])
def generate_safe_emergency_response(emergency_id: int):
    """Runs AI re-optimization and Phase 8 safety validation to generate a safe mitigation plan."""
    res = emergency_manager.generate_safe_response(emergency_id)
    if not res.get("status") == "SAFE_RESPONSE_READY":
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to generate emergency response."))
    return res


@router.post("/emergency/{emergency_id}/resolve", response_model=Dict[str, Any])
def resolve_emergency(emergency_id: int, req: ResolveEmergencyRequest):
    """Resolves an active emergency and restores corridor operation."""
    res = emergency_manager.resolve_event(emergency_id, req.resolution_notes)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Emergency not found."))
    return res


# 4. Manual Controller Override Endpoints
@router.post("/override", response_model=Dict[str, Any])
def execute_manual_override(req: ManualOverrideRequest):
    """
    Executes a manual controller override with strict safety interlock validation.
    Rejects unsafe commands with explicit safety violations.
    """
    res = override_manager.execute_override(
        action_type=req.action_type,
        train_id=req.train_id,
        section_id=req.section_id,
        new_speed_kmph=req.new_speed_kmph,
        new_priority=req.new_priority,
        track_id=req.track_id,
        hold_duration_seconds=req.hold_duration_seconds,
        reason=req.reason,
        controller_id=req.controller_id
    )
    if not res.get("success"):
        # We return 422 if safety rejected or 400 if invalid train
        if res.get("safety_status") == "REJECTED":
            raise HTTPException(status_code=422, detail={
                "message": res.get("message"),
                "violations": res.get("violations", []),
                "safety_status": "REJECTED"
            })
        raise HTTPException(status_code=400, detail=res.get("error", "Manual action failed."))
    return res


@router.get("/actions", response_model=List[Dict[str, Any]])
def get_controller_action_history(limit: int = Query(50, ge=1, le=100)):
    """Returns historical controller actions and safety validation outcomes."""
    return override_manager.get_action_history(limit=limit)


# 5. Live Unified Event Stream
@router.get("/events", response_model=List[Dict[str, Any]])
def get_event_stream(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    train_id: Optional[int] = Query(None),
    section_id: Optional[int] = Query(None),
    since_id: Optional[int] = Query(None)
):
    """Retrieves filtered chronological events from the unified event stream."""
    return event_manager.get_events(
        limit=limit,
        category=category,
        severity=severity,
        train_id=train_id,
        section_id=section_id,
        since_id=since_id
    )


# 6. Demonstration Mode Endpoints
@router.post("/demo/start", response_model=Dict[str, Any])
def start_demonstration_mode():
    """Starts the 12-step end-to-end automated demonstration workflow."""
    return control_center.start_demo_session()


@router.get("/demo/status", response_model=Dict[str, Any])
def get_demonstration_status():
    """Returns live progression status of the demonstration session."""
    return control_center.get_demo_status()

