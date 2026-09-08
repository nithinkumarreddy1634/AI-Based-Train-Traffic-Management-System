"""
Headway and separation distance calculations based on railway physics and braking curves.
"""

from typing import Tuple, Optional


class HeadwayCalculator:
    """Calculates stopping distances, dynamic headways, and separation margins."""

    DEFAULT_DECELERATION_MPS2 = 0.6     # Standard service braking deceleration (m/s^2)
    EMERGENCY_DECELERATION_MPS2 = 0.9   # Emergency braking deceleration (m/s^2)
    DRIVER_REACTION_SECONDS = 2.5       # Signaling & driver reaction time buffer
    SAFETY_MARGIN_KM = 0.5              # Minimum buffer distance beyond stopping distance (km)
    MIN_HEADWAY_TIME_SECONDS = 180.0    # 3-minute minimum time headway between consecutive trains
    MIN_HEADWAY_DISTANCE_KM = 2.0       # Minimum absolute distance headway (km)

    @classmethod
    def calculate_stopping_distance_km(
        cls,
        speed_kmph: float,
        deceleration_mps2: Optional[float] = None,
        reaction_seconds: Optional[float] = None
    ) -> float:
        """
        Calculates safe stopping distance in kilometers using standard kinematics:
        d = (v^2 / (2 * a)) + (v * t_reaction)
        """
        if speed_kmph <= 0:
            return 0.0

        decel = deceleration_mps2 or cls.DEFAULT_DECELERATION_MPS2
        reaction = reaction_seconds or cls.DRIVER_REACTION_SECONDS

        v_mps = speed_kmph / 3.6
        braking_dist_m = (v_mps ** 2) / (2.0 * decel)
        reaction_dist_m = v_mps * reaction
        total_m = braking_dist_m + reaction_dist_m
        return round(total_m / 1000.0, 3)

    @classmethod
    def calculate_required_headway_km(cls, speed_kmph: float) -> float:
        """
        Calculates required safe following headway distance in km:
        Stopping distance + safety margin buffer, with absolute floor.
        """
        stop_dist = cls.calculate_stopping_distance_km(speed_kmph)
        required = stop_dist + cls.SAFETY_MARGIN_KM
        return max(cls.MIN_HEADWAY_DISTANCE_KM, round(required, 3))

    @classmethod
    def calculate_separation_km(
        cls,
        pos1_km: float,
        pos2_km: float
    ) -> float:
        """Calculates longitudinal distance between two trains along the corridor."""
        return round(abs(pos1_km - pos2_km), 3)

    @classmethod
    def calculate_relative_speed_kmph(
        cls,
        speed1_kmph: float,
        dir1: str,
        speed2_kmph: float,
        dir2: str
    ) -> float:
        """
        Calculates the approach/closure speed between two trains in km/h.
        Positive value means distance is closing.
        """
        if dir1 == dir2:
            # Traveling in same direction: relative speed is the difference
            return round(abs(speed1_kmph - speed2_kmph), 1)
        else:
            # Traveling in opposite directions: approach rate is the sum of speeds
            return round(speed1_kmph + speed2_kmph, 1)

    @classmethod
    def is_headway_insufficient(
        cls,
        separation_km: float,
        following_speed_kmph: float
    ) -> Tuple[bool, float]:
        """
        Checks if separation distance is less than required dynamic headway.
        Returns: (is_insufficient, required_headway_km)
        """
        req_headway = cls.calculate_required_headway_km(following_speed_kmph)
        is_violated = separation_km < req_headway
        return is_violated, req_headway

