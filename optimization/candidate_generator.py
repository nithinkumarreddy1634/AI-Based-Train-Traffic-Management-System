"""
Candidate Train Sequence Generator.

Employs domain-heuristic sequencing rules (FCFS, Priority-First, Delay-Mitigation,
Earliest-Deadline, Speed-Clustered) and 2-opt neighborhood local perturbations to generate
a focused, practical set of candidate movement sequences without combinatorial explosion.
"""
from typing import List, Dict, Any, Set, Tuple, Optional
from optimization.config import OptimizationConfig, DEFAULT_CONFIG


class CandidateSequenceGenerator:
    """Generates high-potential candidate train dispatch sequences."""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def generate_candidate_sequences(
        self,
        trains: List[Dict[str, Any]],
        max_candidates: Optional[int] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Generate a curated list of candidate train orderings using domain heuristics.
        Each candidate is a list of train dictionaries in proposed dispatch order.
        """
        if not trains:
            return []

        limit = max_candidates or self.config.max_candidate_sequences
        unique_order_keys: Set[Tuple[int, ...]] = set()
        candidates: List[List[Dict[str, Any]]] = []

        def add_candidate(seq: List[Dict[str, Any]]) -> bool:
            key = tuple(t["train_id"] for t in seq)
            if key not in unique_order_keys:
                unique_order_keys.add(key)
                candidates.append(seq)
                return True
            return False

        # 1. Baseline: First-Come, First-Served (FCFS) / Earliest Ready Time
        fcfs_seq = sorted(
            trains,
            key=lambda t: (
                t.get("distance_to_section_km", 0.0),
                t.get("current_delay_minutes", 0.0)
            )
        )
        add_candidate(fcfs_seq)

        # 2. Priority-Dominant Sequence (HIGH > MEDIUM > LOW)
        prio_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        priority_seq = sorted(
            trains,
            key=lambda t: (
                prio_map.get(str(t.get("priority", "MEDIUM")).upper(), 1),
                t.get("distance_to_section_km", 0.0)
            )
        )
        add_candidate(priority_seq)

        # 3. Phase 6 Delay-Mitigation Sequence (Highest predicted delay first to avert propagation)
        delay_mitigation_seq = sorted(
            trains,
            key=lambda t: -(
                t.get("current_delay_minutes", 0.0) +
                t.get("predicted_additional_delay", 0.0)
            )
        )
        add_candidate(delay_mitigation_seq)

        # 4. Speed-Clustered Sequence (Fastest trains dispatched first to prevent train-following deceleration)
        speed_seq = sorted(
            trains,
            key=lambda t: -t.get("current_speed_kmph", 60.0)
        )
        add_candidate(speed_seq)

        # 5. Hybrid: High-Priority + Highest Delay
        hybrid_seq = sorted(
            trains,
            key=lambda t: (
                prio_map.get(str(t.get("priority", "MEDIUM")).upper(), 1),
                -(t.get("current_delay_minutes", 0.0) + t.get("predicted_additional_delay", 0.0))
            )
        )
        add_candidate(hybrid_seq)

        # 6. Neighborhood Perturbations (2-opt adjacent swaps) on promising candidates
        base_pool = list(candidates)
        for base in base_pool:
            if len(candidates) >= limit:
                break
            n = len(base)
            for i in range(n - 1):
                if len(candidates) >= limit:
                    break
                # Swap adjacent pair
                mutated = list(base)
                mutated[i], mutated[i + 1] = mutated[i + 1], mutated[i]
                add_candidate(mutated)

        return candidates

