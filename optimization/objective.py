"""
Optimization Objective Formulation.

Implements the multi-criteria mathematical objective function used by the CP-SAT
and heuristic optimizers to evaluate candidate dispatch schedules.
"""
from typing import List, Dict, Any, Optional
from optimization.config import OptimizationConfig, DEFAULT_CONFIG
from optimization.scoring import ThroughputService, ScoringEngine


class OptimizationObjective:
    """Evaluates the composite objective score of a scheduled train sequence."""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.scoring_engine = ScoringEngine(self.config)

    def evaluate_candidate_schedule(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_length_km: float,
        current_section_utilization: float,
        active_conflict_count: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluate a complete candidate dispatch schedule.

        Each entry in schedule_entries is expected to contain:
          - train_id
          - train_number
          - priority ('HIGH', 'MEDIUM', 'LOW')
          - entry_time_sec
          - transit_duration_sec
          - hold_duration_sec
          - initial_delay_min (current + predicted additional delay)

        Returns a dictionary with:
          - throughput: float
          - total_delay_minutes: float
          - total_waiting_seconds: float
          - optimized_utilization: float
          - objective_score: float
          - explanation_factors: Dict[str, float]
        """
        if not schedule_entries:
            return {
                "throughput": 0.0,
                "total_delay_minutes": 0.0,
                "total_waiting_seconds": 0.0,
                "optimized_utilization": 0.0,
                "objective_score": -999.0,
                "explanation_factors": {}
            }

        num_trains = len(schedule_entries)
        first_entry = min(e["entry_time_sec"] for e in schedule_entries)
        last_exit = max(e["entry_time_sec"] + e["transit_duration_sec"] for e in schedule_entries)

        # 1. Throughput calculation
        throughput = ThroughputService.estimate_schedule_throughput(
            num_trains=num_trains,
            first_entry_sec=first_entry,
            last_exit_sec=last_exit,
            horizon_seconds=self.config.planning_horizon_seconds
        )

        # 2. Delay and Waiting calculations with priority weighting
        total_delay_min = 0.0
        total_waiting_sec = 0.0
        weighted_delay_sum = 0.0
        weighted_waiting_sum = 0.0
        weighted_priority_sum = 0.0

        for entry in schedule_entries:
            priority = entry.get("priority", "MEDIUM").upper()
            prio_mult = self.config.priority_multipliers.get(priority, 1.0)
            weighted_priority_sum += prio_mult

            hold_sec = entry.get("hold_duration_sec", 0)
            total_waiting_sec += hold_sec
            weighted_waiting_sum += (hold_sec / 60.0) * prio_mult

            # Additional delay incurred by holding at entry signal/loop
            hold_delay_min = hold_sec / 60.0
            initial_delay = entry.get("initial_delay_min", 0.0)
            total_delay_min += initial_delay + hold_delay_min
            weighted_delay_sum += (initial_delay + hold_delay_min) * prio_mult

        avg_priority_multiplier = weighted_priority_sum / max(1, num_trains)

        # 3. Post-optimization section utilization
        total_occupied_duration = sum(e["transit_duration_sec"] for e in schedule_entries)
        span = max(1, last_exit - first_entry)
        optimized_utilization = min(95.0, max(15.0, (total_occupied_duration / float(span)) * 100.0))

        # 4. Composite Objective Score
        # Throughput Benefit
        tp_benefit = self.config.weight_throughput * throughput
        delay_cost = self.config.weight_delay * weighted_delay_sum
        waiting_cost = self.config.weight_waiting * weighted_waiting_sum
        excess_util = max(0.0, optimized_utilization - 70.0)
        congestion_cost = self.config.weight_congestion * (excess_util / 10.0)
        conflict_cost = self.config.weight_conflict * active_conflict_count

        score = round(tp_benefit - delay_cost - waiting_cost - congestion_cost - conflict_cost, 2)

        # 5. Factor Contributions for Explainability
        tp_term = self.config.weight_throughput * throughput
        delay_term = self.config.weight_delay * total_delay_min
        wait_term = self.config.weight_waiting * (total_waiting_sec / 60.0)
        conflict_term = self.config.weight_conflict * active_conflict_count
        priority_term = avg_priority_multiplier * 15.0

        factors = self.scoring_engine.calculate_factor_contributions(
            throughput_benefit=tp_term,
            delay_reduction_benefit=delay_term,
            waiting_reduction_benefit=wait_term,
            conflict_avoidance_benefit=conflict_term,
            priority_benefit=priority_term
        )

        return {
            "throughput": throughput,
            "total_delay_minutes": round(total_delay_min, 2),
            "total_waiting_seconds": total_waiting_sec,
            "optimized_utilization": round(optimized_utilization, 1),
            "objective_score": score,
            "explanation_factors": factors
        }
