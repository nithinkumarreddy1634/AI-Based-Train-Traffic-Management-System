"""
Safety Validation Engine Configuration.

Defines all configurable safety thresholds, headway limits, braking parameters,
interlocking clearances, and emergency triggers.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SafetyConfig:
    """Configurable safety thresholds for formal validation."""

    # 1. Headway Constraints
    # Absolute minimum time separation between trains moving in the same direction (seconds)
    min_headway_seconds: int = 120

    # Warning threshold for tight headway (seconds)
    warning_headway_seconds: int = 150

    # 2. Speed Limits
    # Absolute maximum section velocity ceiling across any corridor (km/h)
    max_network_speed_kmph: float = 130.0

    # Maximum allowable overspeed tolerance before hard rejection (km/h)
    overspeed_tolerance_kmph: float = 0.0

    # Speed limit reductions for specific train types (km/h)
    train_max_speeds: Dict[str, float] = field(default_factory=lambda: {
        "EXPRESS": 120.0,
        "PASSENGER": 100.0,
        "LOCAL": 80.0,
        "FREIGHT": 65.0
    })

    # 3. Kinematic Braking & Safe Stopping Distance
    # Driver / signaling reaction time buffer (seconds)
    reaction_time_seconds: float = 2.5

    # Nominal service deceleration rate (m/s^2)
    service_deceleration_mps2: float = 0.6

    # Emergency deceleration rate (m/s^2)
    emergency_deceleration_mps2: float = 1.2

    # Minimum physical safety clearance margin before red aspect or obstruction (meters)
    min_stopping_margin_meters: float = 100.0

    # Emergency proximity threshold (meters)
    emergency_stop_threshold_meters: float = 200.0

    # 4. Junction & Interlocking Clearance
    # Clearance time required before conflicting route switch movement (seconds)
    junction_clearance_seconds: int = 60

    # 5. Occupancy Limits
    # Maximum trains allowed on a single track simultaneously
    max_trains_per_track: int = 1

    # Single-track mutual exclusion enforcement (True = zero opposing overlap allowed)
    enforce_single_track_mutex: bool = True

    # 6. Holding Limits
    # Maximum permissible holding duration before rejecting as an operational stall (seconds)
    max_safe_hold_seconds: int = 1800


# Global singleton safety configuration instance
DEFAULT_SAFETY_CONFIG = SafetyConfig()

