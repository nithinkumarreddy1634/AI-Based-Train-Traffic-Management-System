"""
Route Connectivity & Track Topology Validator.

Verifies that recommended train movements follow a valid, continuous graph
traversal across the railway network to destination.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_ROUTE_CONNECTIVITY


class RouteValidator:
    """Validates network topological connectivity and scheduled corridor paths."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG

    def validate_routes(
        self,
        schedule_entries: List[Dict[str, Any]],
        network_sections: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Validates that proposed section sequences follow contiguous section transitions.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        if not network_sections:
            return (violations, warnings)

        for entry in schedule_entries:
            t_num = entry.get("train_number", f"T{entry.get('train_id')}")

            # Check explicit route_sections sequence if provided
            route_secs = entry.get("route_sections")
            if route_secs and len(route_secs) >= 2:
                for idx in range(len(route_secs) - 1):
                    s1_id = route_secs[idx]
                    s2_id = route_secs[idx + 1]
                    s1 = network_sections.get(s1_id)
                    s2 = network_sections.get(s2_id)
                    if not s1 or not s2:
                        continue
                    s1_nodes = {s1.get("start_station_id"), s1.get("end_station_id")}
                    s2_nodes = {s2.get("start_station_id"), s2.get("end_station_id")}
                    if not (s1_nodes & s2_nodes):
                        violations.append(SafetyViolation(
                            rule=RULE_ROUTE_CONNECTIVITY,
                            severity="HIGH",
                            message=(
                                f"Topological route discontinuity for {t_num}: "
                                f"Section {s1_id} does not connect to Section {s2_id}."
                            ),
                            train_numbers=[t_num],
                            details={"section_1": s1_id, "section_2": s2_id}
                        ))

            curr_sec = entry.get("current_section_id")
            target_sec = entry.get("target_section_id") or entry.get("section_id")

            if not curr_sec or not target_sec or curr_sec == target_sec:
                continue

            sec_curr_info = network_sections.get(curr_sec)
            sec_next_info = network_sections.get(target_sec)

            if not sec_next_info:
                violations.append(SafetyViolation(
                    rule=RULE_ROUTE_CONNECTIVITY,
                    severity="CRITICAL",
                    message=f"Train {t_num} routed to non-existent section ID {target_sec}.",
                    train_numbers=[t_num],
                    details={"current_section": curr_sec, "target_section": target_sec}
                ))
                continue

            # Verify station node connectivity: end station of current must equal start station of next
            c_start = sec_curr_info.get("start_station_id") if sec_curr_info else None
            c_end = sec_curr_info.get("end_station_id") if sec_curr_info else None
            n_start = sec_next_info.get("start_station_id")
            n_end = sec_next_info.get("end_station_id")

            # Check if there is an interlocking junction station connecting the two sections
            is_connected = (c_end in (n_start, n_end)) or (c_start in (n_start, n_end))

            if not is_connected and sec_curr_info:
                violations.append(SafetyViolation(
                    rule=RULE_ROUTE_CONNECTIVITY,
                    severity="HIGH",
                    message=(
                        f"Topological route discontinuity for {t_num}: "
                        f"Section {curr_sec} ({sec_curr_info.get('name')}) does not connect to "
                        f"Section {target_sec} ({sec_next_info.get('name')})."
                    ),
                    train_numbers=[t_num],
                    details={"curr_section_id": curr_sec, "target_section_id": target_sec}
                ))

        return (violations, warnings)
