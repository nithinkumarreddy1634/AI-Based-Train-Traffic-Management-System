"""
Feature definitions and schema for Machine Learning Train Delay Prediction.
"""

from typing import List

NUMERICAL_FEATURES: List[str] = [
    "scheduled_duration",
    "distance_remaining_km",
    "current_speed_kmph",
    "maximum_speed_kmph",
    "current_delay_minutes",
    "number_of_stops_remaining",
    "station_dwell_time",
    "number_of_trains_in_section",
    "section_utilization",
    "traffic_density",
    "waiting_train_count",
]

CATEGORICAL_FEATURES: List[str] = [
    "train_type",
    "priority",
    "time_of_day",
    "day_type",
]

ALL_FEATURES: List[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

TARGET: str = "total_delay_minutes"

# Valid Categories for Validation and One-Hot Encoding
TRAIN_TYPES: List[str] = ["EXPRESS", "PASSENGER", "LOCAL", "FREIGHT"]
PRIORITIES: List[str] = ["HIGH", "MEDIUM", "LOW"]
TIMES_OF_DAY: List[str] = ["MORNING", "AFTERNOON", "EVENING", "NIGHT"]
DAY_TYPES: List[str] = ["WEEKDAY", "WEEKEND"]

