"""
AI-Powered Train Traffic Optimization Configuration.

Defines all configurable weights, parameters, priorities, and solver settings
for maximizing railway section throughput while respecting safety constraints.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class OptimizationConfig:
    """Configurable parameters and weights for the AI optimization engine."""

    # 1. Objective Function Weights
    # Higher throughput weight prioritizes maximizing completed train slots per hour
    weight_throughput: float = 40.0

    # Delay cost: penalty per minute of accumulated delay
    weight_delay: float = 1.5

    # Waiting cost: penalty per minute of active holding/dwell time
    weight_waiting: float = 2.0

    # Congestion cost: penalty for pushing section utilization above optimal threshold (e.g. > 75%)
    weight_congestion: float = 15.0

    # Conflict cost: heavy penalty on potential headway or route conflicts
    weight_conflict: float = 50.0

    # 2. Train Priority Multipliers (influences delay and waiting penalties)
    priority_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "HIGH": 2.5,     # Express / Premium Passenger
        "MEDIUM": 1.5,   # Regular Passenger
        "LOW": 1.0       # Freight / Non-scheduled empty runs
    })

    # Train Type Base Speeds (km/h) for transit estimation when stopped
    type_default_speeds: Dict[str, float] = field(default_factory=lambda: {
        "EXPRESS": 100.0,
        "PASSENGER": 80.0,
        "LOCAL": 65.0,
        "FREIGHT": 50.0
    })

    # 3. Operational & Headway Constraints
    # Absolute minimum safe separation time between consecutive trains entering same section (seconds)
    min_headway_seconds: int = 120

    # Buffer added at junctions and switch interlocking points (seconds)
    junction_clearance_seconds: int = 60

    # Station dwell allowance before train can depart (seconds)
    min_station_dwell_seconds: int = 60

    # Planning Horizon for section entry optimization (1 simulation hour)
    planning_horizon_seconds: int = 3600

    # Maximum allowed hold time at signals/loops before dispatch (seconds)
    max_hold_seconds: int = 1800

    # 4. Solver Parameters
    # Time limit for OR-Tools CP-SAT or fallback solver (seconds)
    solver_time_limit_seconds: float = 3.0

    # Max candidate permutations to explore in candidate generator
    max_candidate_sequences: int = 50

    # Number of workers / threads for CP-SAT solver
    solver_num_workers: int = 4

    # 5. Throughput Baseline Reference (trains per hour in an unconstrained corridor)
    baseline_reference_throughput: float = 6.0


# Default global singleton configuration instance
DEFAULT_CONFIG = OptimizationConfig()

