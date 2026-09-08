"""
Mathematical and Operational Constraint Utilities for Safety Verification.
"""
from typing import Dict, Any, List, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG


class SafetyConstraintUtils:
    """Helper utilities for physical safety validation."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG

    def compute_service_stopping_distance(self, speed_kmph: float) -> float:
        """
        Compute standard service stopping distance:
        d = (v^2 / 2a) + v * t_reaction
        """
        v_ms = max(0.0, speed_kmph / 3.6)
        a = self.config.service_deceleration_mps2
        t_react = self.config.reaction_time_seconds
        d_brake = (v_ms ** 2) / (2.0 * a) if a > 0 else 0.0
        d_react = v_ms * t_react
        return round(d_brake + d_react + self.config.min_stopping_margin_meters, 2)

    def compute_emergency_stopping_distance(self, speed_kmph: float) -> float:
        """Compute maximum emergency stopping distance under full deceleration."""
        v_ms = max(0.0, speed_kmph / 3.6)
        a = self.config.emergency_deceleration_mps2
        t_react = 1.0  # emergency reaction buffer
        d_brake = (v_ms ** 2) / (2.0 * a) if a > 0 else 0.0
        d_react = v_ms * t_react
        return round(d_brake + d_react, 2)

    def compute_minimum_time_headway(
        self,
        speed_leading_kmph: float,
        speed_following_kmph: float
    ) -> int:
        """
        Compute dynamic time headway between two consecutive trains.
        Ensures following train can decelerate safely if leading train slows down.
        """
        d_stop_meters = self.compute_service_stopping_distance(speed_following_kmph)
        v_follow_ms = max(5.0, speed_following_kmph / 3.6)
        dynamic_headway_sec = int(d_stop_meters / v_follow_ms)
        return max(self.config.min_headway_seconds, dynamic_headway_sec)

