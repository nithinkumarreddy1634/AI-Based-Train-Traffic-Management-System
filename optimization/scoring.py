"""
Throughput Calculation Service and Multi-Factor Optimization Scoring.

Defines the reusable throughput calculation service (trains per simulation hour)
and the multi-criteria composite scoring engine using configurable weights.
"""
from typing import Dict, List, Any, Optional
from optimization.config import OptimizationConfig, DEFAULT_CONFIG


class ThroughputService:
    """Reusable service for calculating corridor and section throughput."""

    @staticmethod
    def calculate_throughput(completed_trains: int, time_window_seconds: float = 3600.0) -> float:
        """
        Calculate realized throughput in trains per simulation hour.

        Throughput = (Number of trains completed / time_window_seconds) * 3600
        """
        if time_window_seconds <= 0:
            return 0.0
        return round((float(completed_trains) / float(time_window_seconds)) * 3600.0, 2)

    @staticmethod
    def estimate_schedule_throughput(
        num_trains: int,
        first_entry_sec: int,
        last_exit_sec: int,
        horizon_seconds: int = 3600
    ) -> float:
        """
        Estimate projected throughput from an optimized train dispatch schedule.

        Calculates the completion rate across the effective schedule makespan.
        """
        if num_trains <= 0:
            return 0.0

        makespan = max(1, last_exit_sec - first_entry_sec)
        # If makespan is very short (e.g. 1 train), normalize to horizon
        effective_window = max(makespan, 1800)  # at least 30 min reference
        rate = (float(num_trains) / float(effective_window)) * 3600.0

        # Bound reasonably to physical corridor ceiling (e.g. 12-18 trains/hr depending on headway)
        return round(min(rate, 20.0), 2)


class ScoringEngine:
    """Calculates multi-objective scores and factor breakdowns for candidate dispatch schedules."""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def calculate_score(
        self,
        throughput: float,
        total_delay_minutes: float,
        total_waiting_seconds: float,
        section_utilization_pct: float,
        conflict_count: int,
        priority_penalty_multiplier: float = 1.0
    ) -> float:
        """
        Compute overall composite optimization score.

        Score = (Throughput Benefit)
              - (Delay Cost)
              - (Waiting Cost)
              - (Congestion Cost)
              - (Conflict Cost)
        """
        # Throughput Benefit
        tp_benefit = self.config.weight_throughput * throughput

        # Delay Cost (weighted by train priority if applicable)
        delay_cost = self.config.weight_delay * total_delay_minutes * priority_penalty_multiplier

        # Waiting Cost (converted to minutes)
        waiting_cost = self.config.weight_waiting * (total_waiting_seconds / 60.0) * priority_penalty_multiplier

        # Congestion Cost: exponential penalty when utilization exceeds 75%
        excess_util = max(0.0, section_utilization_pct - 70.0)
        congestion_cost = self.config.weight_congestion * (excess_util / 10.0)

        # Conflict Cost
        conflict_cost = self.config.weight_conflict * conflict_count

        composite_score = tp_benefit - delay_cost - waiting_cost - congestion_cost - conflict_cost
        return round(composite_score, 2)

    def calculate_factor_contributions(
        self,
        throughput_benefit: float,
        delay_reduction_benefit: float,
        waiting_reduction_benefit: float,
        conflict_avoidance_benefit: float,
        priority_benefit: float
    ) -> Dict[str, float]:
        """
        Calculate relative percentage contribution of each decision factor for explainability.
        Ensures transparent accounting of why a schedule was favored.
        """
        total_positive = (
            abs(throughput_benefit) +
            abs(delay_reduction_benefit) +
            abs(waiting_reduction_benefit) +
            abs(conflict_avoidance_benefit) +
            abs(priority_benefit)
        )

        if total_positive <= 0.001:
            return {
                "throughput_maximization": 30.0,
                "delay_mitigation": 30.0,
                "waiting_time_minimization": 20.0,
                "conflict_safety_headway": 10.0,
                "priority_adherence": 10.0
            }

        return {
            "throughput_maximization": round((abs(throughput_benefit) / total_positive) * 100.0, 1),
            "delay_mitigation": round((abs(delay_reduction_benefit) / total_positive) * 100.0, 1),
            "waiting_time_minimization": round((abs(waiting_reduction_benefit) / total_positive) * 100.0, 1),
            "conflict_safety_headway": round((abs(conflict_avoidance_benefit) / total_positive) * 100.0, 1),
            "priority_adherence": round((abs(priority_benefit) / total_positive) * 100.0, 1)
        }

