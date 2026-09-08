"""
Synthetic Training Dataset Generator for Train Delay Prediction.
Generates logically consistent, domain-grounded railway operations data.
"""

import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from ml.config import DATASET_PATH, SYNTHETIC_DATASET_SIZE, RANDOM_STATE
from ml.features import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURES,
    TARGET,
    TRAIN_TYPES,
    PRIORITIES,
    TIMES_OF_DAY,
    DAY_TYPES,
)


def generate_synthetic_dataset(
    num_samples: int = SYNTHETIC_DATASET_SIZE,
    random_seed: int = RANDOM_STATE,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Generates a synthetic but logically consistent dataset of railway operating conditions.
    Realistic relationships are mathematically encoded:
    - Base delay propagates into future delay.
    - Higher section utilization and traffic density increase delay.
    - Waiting trains in section create non-linear queuing delays.
    - Speed deficit over remaining distance compounds schedule loss.
    - High priority trains get preferential clearance (lower delay multiplier).
    - Station stops and extended dwell times add cumulative delay.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)

    records = []

    for _ in range(num_samples):
        # 1. Categorical sampling
        train_type = np.random.choice(
            TRAIN_TYPES, p=[0.40, 0.30, 0.18, 0.12]
        )

        if train_type == "EXPRESS":
            priority = np.random.choice(PRIORITIES, p=[0.85, 0.15, 0.0])
            max_speed = float(np.random.choice([110, 120, 130, 140]))
        elif train_type == "PASSENGER":
            priority = np.random.choice(PRIORITIES, p=[0.20, 0.75, 0.05])
            max_speed = float(np.random.choice([100, 110]))
        elif train_type == "LOCAL":
            priority = np.random.choice(PRIORITIES, p=[0.05, 0.65, 0.30])
            max_speed = float(np.random.choice([80, 90]))
        else:  # FREIGHT
            priority = np.random.choice(PRIORITIES, p=[0.0, 0.20, 0.80])
            max_speed = float(np.random.choice([65, 75]))

        time_of_day = np.random.choice(
            TIMES_OF_DAY, p=[0.32, 0.22, 0.34, 0.12]
        )
        day_type = np.random.choice(DAY_TYPES, p=[0.72, 0.28])

        is_peak = time_of_day in ("MORNING", "EVENING") and day_type == "WEEKDAY"

        # 2. Operating & Track Conditions
        distance_remaining_km = round(float(np.random.uniform(5.0, 95.0)), 1)
        scheduled_duration = round(float(np.random.uniform(30.0, 180.0)), 1)

        # Traffic density and section utilization (higher during peak)
        if is_peak:
            traffic_density = round(float(np.random.beta(4, 2) * 100.0), 1)
            section_utilization = round(float(np.clip(traffic_density + np.random.normal(5, 4), 20.0, 98.0)), 1)
            num_trains_in_sec = int(np.random.choice([1, 2, 3, 4], p=[0.15, 0.45, 0.30, 0.10]))
        else:
            traffic_density = round(float(np.random.beta(2, 3) * 100.0), 1)
            section_utilization = round(float(np.clip(traffic_density + np.random.normal(0, 5), 10.0, 90.0)), 1)
            num_trains_in_sec = int(np.random.choice([1, 2, 3], p=[0.60, 0.32, 0.08]))

        # Waiting train count is influenced by utilization and number of trains
        if section_utilization > 75.0 or num_trains_in_sec >= 2:
            waiting_train_count = int(np.random.choice([0, 1, 2, 3], p=[0.25, 0.45, 0.22, 0.08]))
        else:
            waiting_train_count = int(np.random.choice([0, 1], p=[0.88, 0.12]))

        # Current speed vs maximum speed
        if waiting_train_count > 0:
            current_speed_kmph = round(float(np.random.uniform(0.0, max_speed * 0.45)), 1)
        elif section_utilization > 70.0:
            current_speed_kmph = round(float(np.random.uniform(max_speed * 0.4, max_speed * 0.85)), 1)
        else:
            current_speed_kmph = round(float(np.random.uniform(max_speed * 0.75, max_speed)), 1)

        # Current initial delay (right-skewed distribution)
        current_delay_minutes = round(float(np.random.exponential(scale=3.5)), 1)
        if np.random.rand() < 0.35:
            current_delay_minutes = 0.0  # 35% on-time baseline

        # Stops and dwell time
        max_possible_stops = max(1, int(distance_remaining_km // 15))
        stops_remaining = int(np.random.randint(0, min(6, max_possible_stops + 1)))
        dwell_time = round(float(np.random.uniform(1.5, 5.0)), 1) if stops_remaining > 0 else 0.0

        # 3. Ground Truth Target Calculation (Domain Logic)
        # Baseline is current delay
        base_delay = current_delay_minutes

        # Priority factor: High priority trains are granted clear signals and held less
        if priority == "HIGH":
            prio_mult = 0.65
        elif priority == "MEDIUM":
            prio_mult = 1.00
        else:  # LOW (e.g. freight)
            prio_mult = 1.45

        # Congestion additional delay
        util_delay = (section_utilization / 100.0) * 4.2 * prio_mult
        density_delay = (traffic_density / 100.0) * 2.8 * prio_mult

        # Queuing bottleneck delay
        wait_delay = waiting_train_count * 3.6 * prio_mult
        multi_train_delay = max(0, num_trains_in_sec - 1) * 1.5

        # Speed restriction penalty over remaining distance
        speed_deficit = max(0.0, max_speed - current_speed_kmph)
        speed_delay = (speed_deficit / max_speed) * (distance_remaining_km / 12.0)

        # Dwell extra delay
        dwell_delay = stops_remaining * max(0.0, dwell_time - 2.5) * 0.8

        # Peak period baseline friction
        peak_delay = 1.8 if is_peak else 0.0

        # Recoverable margin: if running at top speed with clear track, train can make up slight time
        makeup_potential = 0.0
        if current_speed_kmph >= max_speed * 0.95 and section_utilization < 35.0 and distance_remaining_km > 30.0:
            makeup_potential = min(2.5, distance_remaining_km * 0.03)

        # Composite total delay with realistic Gaussian noise
        noise = float(np.random.normal(0.0, 0.65))
        additional_delay = (
            util_delay +
            density_delay +
            wait_delay +
            multi_train_delay +
            speed_delay +
            dwell_delay +
            peak_delay -
            makeup_potential +
            noise
        )

        total_delay = max(0.0, round(base_delay + additional_delay, 1))

        records.append({
            "train_type": train_type,
            "priority": priority,
            "scheduled_duration": scheduled_duration,
            "distance_remaining_km": distance_remaining_km,
            "current_speed_kmph": current_speed_kmph,
            "maximum_speed_kmph": max_speed,
            "current_delay_minutes": current_delay_minutes,
            "number_of_stops_remaining": stops_remaining,
            "station_dwell_time": dwell_time,
            "number_of_trains_in_section": num_trains_in_sec,
            "section_utilization": section_utilization,
            "traffic_density": traffic_density,
            "waiting_train_count": waiting_train_count,
            "time_of_day": time_of_day,
            "day_type": day_type,
            TARGET: total_delay,
        })

    df = pd.DataFrame(records)

    # Save to disk
    save_path = output_path or DATASET_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"[*] Synthetic dataset generated: {len(df)} samples saved to {save_path}")

    return df


if __name__ == "__main__":
    generate_synthetic_dataset()

