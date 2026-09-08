"""
Traditional Baseline Railway Scheduler.

Implements conventional railway dispatching heuristics:
- First-Come First-Served (FCFS) dispatching
- Priority-aware scheduled timetable order (HIGH > MEDIUM > LOW)
- Fixed headway spacing enforcement
- Reactive signal holds without dynamic speed adjustments or proactive rerouting
"""

from typing import List, Dict, Any, Optional
import copy


class BaselineScheduler:
    """
    Simulates traditional rule-based dispatching.
    Provides comparison baseline against AI-driven dynamic optimization.
    """

    def __init__(self, dispatch_mode: str = "SCHEDULED_PRIORITY", min_headway_seconds: float = 180.0):
        """
        Args:
            dispatch_mode: 'FCFS' or 'SCHEDULED_PRIORITY'
            min_headway_seconds: Minimum clearance interval between consecutive departures (default 180s = 3 min)
        """
        self.dispatch_mode = dispatch_mode
        self.min_headway_seconds = min_headway_seconds
        self.last_dispatch_time: Dict[str, float] = {}  # key: section_id or track_id -> sim_time

    def compute_dispatch_sequence(self, trains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sorts candidate trains according to baseline rule.
        Returns ordered list of train records with scheduled release windows.
        """
        trains_copy = copy.deepcopy(trains)

        if self.dispatch_mode == "FCFS":
            # Sort strictly by current position / ready time / arrival time
            trains_copy.sort(
                key=lambda t: (
                    t.get("current_delay_minutes", 0.0),
                    -float(t.get("current_position_km", 0.0)),
                    t.get("train_id", 0)
                )
            )
        else:
            # Traditional Priority-aware timetable order
            priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            trains_copy.sort(
                key=lambda t: (
                    priority_rank.get(str(t.get("priority", "MEDIUM")).upper(), 1),
                    t.get("current_delay_minutes", 0.0),
                    t.get("train_id", 0)
                )
            )

        sequence = []
        for idx, tr in enumerate(trains_copy):
            sequence.append({
                "sequence_order": idx + 1,
                "train_id": tr["train_id"],
                "train_number": tr.get("train_number", ""),
                "priority": tr.get("priority", "MEDIUM"),
                "assigned_action": "PROCEED",
                "recommended_speed": min(tr.get("speed_kmph", 80.0), 100.0),
                "hold_seconds": 0.0,
                "scheduled_slot_sec": idx * self.min_headway_seconds
            })
        return sequence

    def can_dispatch_train(self, train: Dict[str, Any], current_sim_time: float, track_key: str = "main") -> bool:
        """Enforces statutory fixed headway spacing for traditional dispatching."""
        last_time = self.last_dispatch_time.get(track_key, -9999.0)
        if (current_sim_time - last_time) >= self.min_headway_seconds:
            self.last_dispatch_time[track_key] = current_sim_time
            return True
        return False

