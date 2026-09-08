"""
Simulation Configuration for AI-Powered Train Traffic Control.
Defines kinematics, dwell times, clock stepping, and speed multipliers.
"""

from typing import Dict


class SimulationConfig:
    # Clock and step settings
    TICK_INTERVAL_SECONDS: float = 1.0  # Base real-time seconds per simulation tick
    DEFAULT_SPEED_MULTIPLIER: float = 1.0
    ALLOWED_SPEED_MULTIPLIERS = [1.0, 2.0, 5.0, 10.0]

    # Kinematics parameters (acceleration / braking in km/h per second)
    DEFAULT_ACCELERATION_KMPH_S: float = 3.6  # ~1.0 m/s^2 acceleration
    DEFAULT_DECELERATION_KMPH_S: float = 4.5  # ~1.25 m/s^2 normal braking
    APPROACH_DECEL_DISTANCE_KM: float = 1.2  # Distance from station to start slowing down

    # Default station dwell times (in simulation seconds) by train type
    DWELL_TIMES_BY_TYPE: Dict[str, float] = {
        "EXPRESS": 25.0,
        "PASSENGER": 45.0,
        "LOCAL": 60.0,
        "FREIGHT": 30.0,
    }

    # Database synchronization interval (every N simulation seconds)
    DB_SYNC_INTERVAL_TICKS: int = 5

    # Maximum event log history in memory
    MAX_EVENT_LOG_SIZE: int = 100

    # Train maximum physical speeds (km/h) by train type
    TRAIN_MAX_SPEED_BY_TYPE: Dict[str, float] = {
        "EXPRESS": 130.0,
        "PASSENGER": 100.0,
        "LOCAL": 75.0,
        "FREIGHT": 65.0,
    }


config = SimulationConfig()

