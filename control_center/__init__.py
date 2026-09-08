"""
Workspace root proxy for control_center module.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path if not present
backend_dir = str(Path(__file__).parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.control_center import (
    event_manager,
    EventManager,
    emergency_manager,
    EmergencyManager,
    override_manager,
    OverrideManager,
    scenario_controller,
    ScenarioController,
    control_state_manager,
    ControlCenterStateManager,
    control_center,
    MasterControlCenter,
)

__all__ = [
    "event_manager",
    "EventManager",
    "emergency_manager",
    "EmergencyManager",
    "override_manager",
    "OverrideManager",
    "scenario_controller",
    "ScenarioController",
    "control_state_manager",
    "ControlCenterStateManager",
    "control_center",
    "MasterControlCenter",
]

