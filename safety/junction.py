"""
Junction Interlocking and Switch Clearance Validator.

Validates that trains crossing station throats, converging lines, and diamond switches
respect interlocking mutual exclusion and clearance time windows.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_JUNCTION_CLEARANCE


class JunctionValidator:
    """Validates junction route allocations and switch interlocking windows."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG

    def validate_junctions(
        self,
        schedule_entries: List[Dict[str, Any]],
        active_conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Validates that converging or crossing train routes maintain junction clearance times.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        # Check known Phase 5 active conflicts involving junctions
        if active_conflicts:
            for conf in active_conflicts:
                ctype = str(conf.get("conflict_type", "")).upper()
                if "JUNCTION" in ctype or "CROSSING" in ctype:
                    t1 = conf.get("train_number_1") or conf.get("train1_number") or conf.get("train_number") or "T1"
                    t2 = conf.get("train_number_2") or conf.get("train2_number") or "T2"
                    sec = conf.get("section_name", "Junction Interlocking")

                    # Check time to conflict if specified on the active conflict
                    time_to_conf = conf.get("time_to_conflict_seconds")
                    if time_to_conf is not None and float(time_to_conf) < self.config.junction_clearance_seconds:
                        violations.append(SafetyViolation(
                            rule=RULE_JUNCTION_CLEARANCE,
                            severity="CRITICAL",
                            message=(
                                f"Simultaneous conflicting junction crossing: Conflict between {t1} and {t2} "
                                f"at junction in {time_to_conf}s (minimum clearance required: {self.config.junction_clearance_seconds}s)."
                            ),
                            train_numbers=[t1, t2],
                            section_name=sec,
                            details=conf
                        ))
                        continue

                    # Check if recommended schedule addresses the junction conflict with enough separation
                    # If both trains are scheduled to cross within the junction clearance time window:
                    t1_entry = next((e.get("entry_time_sec", 0) for e in schedule_entries if e.get("train_number") == t1), None)
                    t2_entry = next((e.get("entry_time_sec", 0) for e in schedule_entries if e.get("train_number") == t2), None)

                    if t1_entry is not None and t2_entry is not None:
                        gap = abs(t1_entry - t2_entry)
                        if gap < self.config.junction_clearance_seconds:
                            violations.append(SafetyViolation(
                                rule=RULE_JUNCTION_CLEARANCE,
                                severity="CRITICAL",
                                message=(
                                    f"Simultaneous conflicting junction crossing: Trains {t1} and {t2} "
                                    f"scheduled at junction within {gap}s (minimum clearance required: {self.config.junction_clearance_seconds}s)."
                                ),
                                train_numbers=[t1, t2],
                                section_name=sec,
                                details={
                                    "conflict_gap_sec": gap,
                                    "required_clearance_sec": self.config.junction_clearance_seconds
                                }
                            ))

        return (violations, warnings)
