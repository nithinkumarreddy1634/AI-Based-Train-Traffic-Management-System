"""
Train Movement & Kinematics Engine.
Calculates acceleration, cruising, deceleration, and distance progression.
"""

from typing import Tuple
from .config import config


def calculate_motion(
    current_speed_kmph: float,
    current_pos_km: float,
    section_length_km: float,
    train_type: str,
    max_section_speed_kmph: float,
    dt_seconds: float,
    is_approaching_stop: bool = False,
) -> Tuple[float, float, bool]:
    """
    Computes the next speed and position for a train over a time delta `dt_seconds`.

    Returns:
        (new_speed_kmph, new_position_km, has_reached_section_end)
    """
    # 1. Determine permitted maximum speed
    train_max_speed = config.TRAIN_MAX_SPEED_BY_TYPE.get(train_type.upper(), 90.0)
    permitted_speed = min(train_max_speed, max_section_speed_kmph)

    # 2. Check deceleration when approaching a stop (station or occupied boundary)
    remaining_distance_km = max(0.0, section_length_km - current_pos_km)

    if is_approaching_stop and remaining_distance_km <= config.APPROACH_DECEL_DISTANCE_KM:
        # Calculate target speed scaled down to remaining distance
        target_speed = max(15.0, permitted_speed * (remaining_distance_km / config.APPROACH_DECEL_DISTANCE_KM))
        if current_speed_kmph > target_speed:
            new_speed = max(target_speed, current_speed_kmph - config.DEFAULT_DECELERATION_KMPH_S * dt_seconds)
        else:
            new_speed = current_speed_kmph
    else:
        # Cruising or accelerating towards permitted speed
        if current_speed_kmph < permitted_speed:
            new_speed = min(permitted_speed, current_speed_kmph + config.DEFAULT_ACCELERATION_KMPH_S * dt_seconds)
        elif current_speed_kmph > permitted_speed:
            new_speed = max(permitted_speed, current_speed_kmph - config.DEFAULT_DECELERATION_KMPH_S * dt_seconds)
        else:
            new_speed = permitted_speed

    # 3. Calculate distance traveled in kilometers during dt
    # Average speed between current and new speed for smoother integration
    avg_speed = (current_speed_kmph + new_speed) / 2.0
    distance_traveled_km = (avg_speed / 3600.0) * dt_seconds

    # 4. Advance position
    new_position_km = current_pos_km + distance_traveled_km

    # 5. Boundary check
    has_reached_section_end = False
    if new_position_km >= section_length_km:
        new_position_km = section_length_km
        has_reached_section_end = True
        if is_approaching_stop:
            new_speed = 0.0

    return round(new_speed, 1), round(new_position_km, 3), has_reached_section_end

