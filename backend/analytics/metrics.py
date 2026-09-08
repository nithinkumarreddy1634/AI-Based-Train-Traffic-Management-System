"""
Performance Metrics Module for Train Traffic Analytics.

Defines data models and computation routines for evaluating railway section
performance, delays, waiting times, throughput, and safety invariants.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import statistics


@dataclass
class TrainMetrics:
    """Detailed performance records for an individual train."""
    train_id: int
    train_number: str
    train_name: str
    priority: str
    train_type: str
    initial_delay_minutes: float = 0.0
    final_delay_minutes: float = 0.0
    delay_change_minutes: float = 0.0
    waiting_time_seconds: float = 0.0
    journey_time_minutes: float = 0.0
    completed: bool = False
    average_speed_kmph: float = 0.0
    distance_covered_km: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationMetrics:
    """Comprehensive performance metrics produced by a simulation run."""
    throughput_tph: float = 0.0
    completed_trains: int = 0
    total_trains: int = 0
    avg_delay_minutes: float = 0.0
    max_delay_minutes: float = 0.0
    min_delay_minutes: float = 0.0
    total_delay_minutes: float = 0.0
    median_delay_minutes: float = 0.0
    total_waiting_time: float = 0.0
    avg_waiting_time: float = 0.0
    max_waiting_time: float = 0.0
    section_utilization_pct: float = 0.0
    peak_traffic_density: float = 0.0
    bottleneck_duration_sec: float = 0.0
    total_conflicts: int = 0
    critical_conflicts: int = 0
    resolved_conflicts: int = 0
    safety_violations: int = 0
    unsafe_plans_applied: int = 0
    avg_journey_time_min: float = 0.0
    time_series: List[Dict[str, Any]] = field(default_factory=list)
    train_metrics: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_throughput(completed_trains: int, duration_seconds: float) -> float:
    """Calculates section throughput in trains per hour (TPH)."""
    if duration_seconds <= 0:
        return 0.0
    hours = duration_seconds / 3600.0
    return round(completed_trains / hours, 2)


def calculate_delay_metrics(delays: List[float]) -> Dict[str, float]:
    """Computes summary statistics (avg, max, min, total, median) for delays."""
    if not delays:
        return {
            "avg_delay_minutes": 0.0,
            "max_delay_minutes": 0.0,
            "min_delay_minutes": 0.0,
            "total_delay_minutes": 0.0,
            "median_delay_minutes": 0.0,
        }
    clean = [max(0.0, float(d)) for d in delays]
    return {
        "avg_delay_minutes": round(statistics.mean(clean), 2),
        "max_delay_minutes": round(max(clean), 2),
        "min_delay_minutes": round(min(clean), 2),
        "total_delay_minutes": round(sum(clean), 2),
        "median_delay_minutes": round(statistics.median(clean), 2),
    }


def calculate_waiting_metrics(waiting_times: List[float]) -> Dict[str, float]:
    """Computes summary statistics (total, avg, max) for waiting durations in seconds."""
    if not waiting_times:
        return {
            "total_waiting_time": 0.0,
            "avg_waiting_time": 0.0,
            "max_waiting_time": 0.0,
        }
    clean = [max(0.0, float(w)) for w in waiting_times]
    return {
        "total_waiting_time": round(sum(clean), 2),
        "avg_waiting_time": round(statistics.mean(clean), 2),
        "max_waiting_time": round(max(clean), 2),
    }


def calculate_improvement(baseline_val: float, ai_val: float, higher_is_better: bool = True) -> float:
    """
    Computes percentage improvement of AI over baseline.
    Avoids division by zero using max(0.001, baseline_val).
    """
    denom = max(0.001, abs(baseline_val))
    if higher_is_better:
        # e.g., Throughput: AI 12 vs Baseline 10 -> (12 - 10) / 10 = +20%
        imp = ((ai_val - baseline_val) / denom) * 100.0
    else:
        # e.g., Delay / Waiting / Conflicts: AI 6 vs Baseline 10 -> (10 - 6) / 10 = +40%
        imp = ((baseline_val - ai_val) / denom) * 100.0
    return round(imp, 2)

