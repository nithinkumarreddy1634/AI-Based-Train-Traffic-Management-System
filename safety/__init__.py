"""
Safety Validation & Fail-Safe Verification Engine (Phase 8).

Independent formal verification layer ensuring that all AI traffic recommendations
strictly satisfy speed limits, minimum headway, track occupancy, single-track mutual
exclusion, route connectivity, junction interlocking, and emergency interlocks.
"""
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import (
    SafetyViolation,
    SafetyWarning,
    SafetyValidationResult
)
from safety.rules import ALL_SAFETY_RULES
from safety.speed import SpeedValidator
from safety.headway import HeadwayValidator
from safety.occupancy import OccupancyValidator
from safety.route import RouteValidator
from safety.junction import JunctionValidator
from safety.stopping_distance import StoppingDistanceValidator
from safety.emergency import EmergencyManager, DEFAULT_EMERGENCY_MANAGER
from safety.validator import SafetyValidator, DEFAULT_SAFETY_VALIDATOR

__all__ = [
    "SafetyConfig",
    "DEFAULT_SAFETY_CONFIG",
    "SafetyViolation",
    "SafetyWarning",
    "SafetyValidationResult",
    "ALL_SAFETY_RULES",
    "SpeedValidator",
    "HeadwayValidator",
    "OccupancyValidator",
    "RouteValidator",
    "JunctionValidator",
    "StoppingDistanceValidator",
    "EmergencyManager",
    "DEFAULT_EMERGENCY_MANAGER",
    "SafetyValidator",
    "DEFAULT_SAFETY_VALIDATOR",
]

