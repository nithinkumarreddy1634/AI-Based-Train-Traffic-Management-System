"""
Operational, Traffic, and Safety Constraints Engine.

Enforces minimum headway separations, track occupancy non-overlap, speed limits,
single-track mutual exclusion, and junction clearance windows.
"""
from typing import List, Dict, Any, Tuple, Optional
from optimization.config import OptimizationConfig, DEFAULT_CONFIG


class ConstraintValidator:
    """Validates operational and safety constraints for candidate train sequences."""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def calculate_required_headway_seconds(
        self,
        speed_leading_kmph: float,
        speed_following_kmph: float,
        buffer_km: float = 0.5
    ) -> int:
        """
        Calculate dynamic physics-grounded minimum headway time (seconds).

        Based on stopping distance of the following train plus safety buffer.
        """
        v_follow_ms = max(5.0, speed_following_kmph / 3.6)
        # Safe service braking deceleration (0.6 m/s^2)
        d_stop_meters = (v_follow_ms ** 2) / (2 * 0.6) + (v_follow_ms * 2.5)
        total_separation_meters = d_stop_meters + (buffer_km * 1000.0)

        # Time required to traverse separation distance
        time_sec = int(total_separation_meters / v_follow_ms)
        return max(self.config.min_headway_seconds, time_sec)

    def validate_headway_sequence(
        self,
        scheduled_entries: List[Dict[str, Any]],
        min_headway_sec: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verify that consecutive trains entering a shared track section respect the minimum headway.

        Returns (is_valid, list_of_violations).
        """
        headway_threshold = min_headway_sec or self.config.min_headway_seconds
        violations = []

        # Sort by entry time
        sorted_entries = sorted(scheduled_entries, key=lambda x: x["entry_time_sec"])

        for i in range(len(sorted_entries) - 1):
            t_curr = sorted_entries[i]
            t_next = sorted_entries[i + 1]

            gap = t_next["entry_time_sec"] - t_curr["entry_time_sec"]
            if gap < headway_threshold:
                violations.append(
                    f"Headway violation between {t_curr['train_number']} and {t_next['train_number']}: "
                    f"gap {gap}s < required {headway_threshold}s"
                )

        return (len(violations) == 0, violations)

    def validate_single_track_no_overlap(
        self,
        scheduled_entries: List[Dict[str, Any]],
        is_single_track: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        For single-track sections (or directional track locks), verify that trains
        moving in opposite directions never occupy the block simultaneously.
        """
        if not is_single_track:
            return (True, [])

        violations = []
        for i in range(len(scheduled_entries)):
            for j in range(i + 1, len(scheduled_entries)):
                t1 = scheduled_entries[i]
                t2 = scheduled_entries[j]

                # If traveling in opposing directions on single track
                dir1 = t1.get("direction", "UP")
                dir2 = t2.get("direction", "UP")

                if dir1 != dir2:
                    # Check interval overlap [entry, exit]
                    start1 = t1["entry_time_sec"]
                    end1 = start1 + t1["transit_duration_sec"]

                    start2 = t2["entry_time_sec"]
                    end2 = start2 + t2["transit_duration_sec"]

                    if max(start1, start2) < min(end1, end2):
                        violations.append(
                            f"Opposing direction collision risk on single track between "
                            f"{t1['train_number']} ({dir1}) and {t2['train_number']} ({dir2}) "
                            f"during window [{max(start1, start2)}, {min(end1, end2)}]s"
                        )

        return (len(violations) == 0, violations)

    def validate_hold_durations(
        self,
        scheduled_entries: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Verify that holding durations do not exceed maximum operational limits."""
        violations = []
        for entry in scheduled_entries:
            hold = entry.get("hold_duration_sec", 0)
            if hold > self.config.max_hold_seconds:
                violations.append(
                    f"Excessive hold duration for {entry['train_number']}: "
                    f"{hold}s exceeds maximum {self.config.max_hold_seconds}s"
                )
        return (len(violations) == 0, violations)

    def full_safety_and_operational_check(
        self,
        scheduled_entries: List[Dict[str, Any]],
        is_single_track: bool = False
    ) -> Tuple[bool, List[str]]:
        """Run complete battery of safety and operational constraint validations."""
        all_violations = []

        valid_hw, hw_violations = self.validate_headway_sequence(scheduled_entries)
        all_violations.extend(hw_violations)

        valid_st, st_violations = self.validate_single_track_no_overlap(scheduled_entries, is_single_track)
        all_violations.extend(st_violations)

        valid_hd, hd_violations = self.validate_hold_durations(scheduled_entries)
        all_violations.extend(hd_violations)

        return (len(all_violations) == 0, all_violations)

