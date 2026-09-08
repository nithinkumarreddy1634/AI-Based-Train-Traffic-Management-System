"""
Minimum Safe Headway Validator.

Validates that trains entering and occupying the same corridor maintain
sufficient time and longitudinal separation.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_MINIMUM_HEADWAY
from safety.constraints import SafetyConstraintUtils


class HeadwayValidator:
    """Validates that train dispatch sequences maintain strict safety headway buffers."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG
        self.utils = SafetyConstraintUtils(self.config)

    def validate_headway(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Verify that consecutive trains traveling in the same direction maintain at least
        the required minimum headway.

        Returns (violations, warnings).
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        if len(schedule_entries) < 2:
            return (violations, warnings)

        sec_name = (section_info or {}).get("section_name", "Monitored Section")

        # Group trains by direction
        by_direction: Dict[str, List[Dict[str, Any]]] = {}
        for entry in schedule_entries:
            d = entry.get("direction", "UP").upper()
            by_direction.setdefault(d, []).append(entry)

        for direction, dir_entries in by_direction.items():
            if len(dir_entries) < 2:
                continue

            # Sort chronologically by recommended entry time
            sorted_trains = sorted(dir_entries, key=lambda x: x.get("entry_time_sec", 0))

            for i in range(len(sorted_trains) - 1):
                t_leading = sorted_trains[i]
                t_following = sorted_trains[i + 1]

                t1_num = t_leading.get("train_number", f"T{t_leading.get('train_id')}")
                t2_num = t_following.get("train_number", f"T{t_following.get('train_id')}")

                t1_entry = t_leading.get("entry_time_sec", 0)
                t2_entry = t_following.get("entry_time_sec", 0)
                actual_gap_sec = t2_entry - t1_entry

                # Dynamic required headway based on following train speed
                v_follow = float(t_following.get("current_speed_kmph") or t_following.get("speed_kmph") or 80.0)
                v_lead = float(t_leading.get("current_speed_kmph") or t_leading.get("speed_kmph") or 80.0)
                dynamic_required_headway = self.utils.compute_minimum_time_headway(v_lead, v_follow)

                required_threshold = max(self.config.min_headway_seconds, dynamic_required_headway)

                if actual_gap_sec < self.config.min_headway_seconds:
                    # Critical headway safety breach
                    violations.append(SafetyViolation(
                        rule=RULE_MINIMUM_HEADWAY,
                        severity="CRITICAL",
                        message=(
                            f"Headway safety violation between leading train {t1_num} and following train {t2_num}: "
                            f"time gap {actual_gap_sec}s is below mandatory minimum {self.config.min_headway_seconds}s "
                            f"(deficit of {self.config.min_headway_seconds - actual_gap_sec}s)."
                        ),
                        train_numbers=[t1_num, t2_num],
                        section_name=sec_name,
                        details={
                            "leading_train": t1_num,
                            "following_train": t2_num,
                            "leading_entry_sec": t1_entry,
                            "following_entry_sec": t2_entry,
                            "actual_gap_seconds": actual_gap_sec,
                            "required_min_headway_seconds": self.config.min_headway_seconds,
                            "dynamic_stopping_headway_seconds": dynamic_required_headway,
                            "direction": direction
                        }
                    ))
                elif actual_gap_sec < self.config.warning_headway_seconds:
                    # Warning for marginal separation
                    warnings.append(SafetyWarning(
                        rule=RULE_MINIMUM_HEADWAY,
                        severity="WARNING",
                        message=(
                            f"Tight headway ({actual_gap_sec}s) between {t1_num} and {t2_num} "
                            f"(buffer is within {self.config.warning_headway_seconds}s caution zone)."
                        ),
                        train_numbers=[t1_num, t2_num],
                        section_name=sec_name,
                        recommendation=f"Advise driver of {t2_num} to observe approach aspects."
                    ))

        return (violations, warnings)

