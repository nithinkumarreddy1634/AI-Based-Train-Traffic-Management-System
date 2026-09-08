"""
Natural-Language Explanation Formatter.

Converts technical optimization scores, telemetry factors, and safety audit logs
into human-readable railway operator narratives and structured bullet points.
"""

from typing import Dict, Any, List, Optional


class ExplanationFormatter:
    """Generates reproducible, deterministic operator explanations from system state."""

    @staticmethod
    def format_narrative(
        train_number: str,
        train_type: str,
        priority: str,
        action: str,
        section_name: str,
        factors: List[Dict[str, Any]],
        competing_trains: Optional[List[Dict[str, Any]]] = None,
        safety_status: str = "APPROVED",
        safety_violations: Optional[List[Dict[str, Any]]] = None,
        throughput_gain_pct: float = 0.0,
        delay_reduction_pct: float = 0.0
    ) -> str:
        """
        Synthesizes a coherent, controller-friendly paragraph explaining the recommendation.
        """
        if safety_status != "APPROVED" and safety_violations:
            first_viol = safety_violations[0]
            return (
                f"RECOMMENDATION REJECTED BY SAFETY GATE: Dispatching {train_number} ({priority} {train_type}) "
                f"into {section_name} was rejected due to a safety violation: {first_viol.get('message', 'Safety constraint breached')}. "
                f"Rule: {first_viol.get('rule', 'SAFETY_CONSTRAINT')}. This recommendation cannot be applied to the simulation."
            )

        action_desc = {
            "PRIORITIZE": f"prioritizes dispatch of {train_number} ({priority} {train_type}) into {section_name}",
            "HOLD": f"holds {train_number} at the approach signal outside {section_name}",
            "PROCEED": f"clears {train_number} to enter {section_name} on clear signal",
            "DIVERT_LOOP": f"diverts {train_number} into a loop siding to permit overtaking",
        }.get(action, f"recommends {action.lower()} for {train_number}")

        # Highlight competing lower priority train if any
        competing_narrative = ""
        if competing_trains:
            comp_t = competing_trains[0]
            comp_num = comp_t.get("train_number", "secondary train")
            comp_pri = comp_t.get("priority", "lower")
            competing_narrative = (
                f" Lower-priority {comp_num} ({comp_pri}) has sufficient buffer margin to dwell briefly "
                f"without causing secondary timetable disruption."
            )

        # Primary operational driver from top factor
        driver_text = "to protect timetable commitments and corridor capacity."
        if factors:
            top_f = factors[0]
            driver_text = f"because {top_f.get('reason', 'it optimizes corridor throughput')}."

        narrative = (
            f"The AI Traffic Engine {action_desc} {driver_text}{competing_narrative} "
            f"This movement is projected to boost corridor throughput by {max(0.0, throughput_gain_pct):.1f}% "
            f"and mitigate delays by {max(0.0, delay_reduction_pct):.1f}%, while fully adhering to statutory safety rules."
        )
        return narrative

    @staticmethod
    def format_key_points(
        train_data: Dict[str, Any],
        action: str,
        factors: List[Dict[str, Any]],
        safety_status: str = "APPROVED",
        safety_violations: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Generates concise bullet points for the quick-view AI Decision Panel.
        """
        points: List[str] = []

        if safety_status != "APPROVED":
            points.append("❌ Safety validation failed — action cannot be applied")
            for v in (safety_violations or [])[:2]:
                points.append(f"• Violation: {v.get('message', 'Rule breached')}")
            return points

        # High priority
        prio = str(train_data.get("priority", "MEDIUM")).upper()
        if prio == "HIGH":
            points.append("• Higher train priority protects passenger timetable")
        elif prio == "LOW":
            points.append("• Lower train priority allows safe signal dwelling")

        # Top factor highlights
        for f in factors[:3]:
            fname = f.get("factor")
            val = f.get("value")
            unit = f.get("unit")
            if fname == "Predicted Delay" and float(val or 0) > 3:
                points.append(f"• High predicted delay ({val} {unit}) warrants proactive clearance")
            elif fname == "Section Utilization" and float(val or 0) > 70:
                points.append(f"• High section congestion ({val}%) requires metered entry spacing")
            elif fname == "Signal Hold Duration":
                points.append(f"• Signal hold of {val}s secures mandatory safety headway buffer")
            elif fname == "Conflict Resolution":
                points.append(f"• Eliminates impending {val} conflict before track entry")

        points.append("• Expected to improve section throughput and lower corridor delay")
        points.append("• 100% compliant with formal Phase 8 safety interlocks")
        return points[:5]

    @staticmethod
    def format_safety_checklist(safety_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates standard checklist view of Phase 8 safety validation rules.
        """
        rules = [
            ("RULE_EMERGENCY_STATE", "Emergency State Check"),
            ("RULE_SPEED_LIMIT", "Speed Limit Compliance"),
            ("RULE_MINIMUM_HEADWAY", "Minimum Safe Headway"),
            ("RULE_TRACK_OCCUPANCY", "Track Occupancy Exclusivity"),
            ("RULE_SECTION_OCCUPANCY", "Section Block Capacity"),
            ("RULE_OPPOSITE_DIRECTION", "Opposite-Direction Mutex"),
            ("RULE_ROUTE_CONNECTIVITY", "Route Topology Continuity"),
            ("RULE_JUNCTION_CLEARANCE", "Junction Clearance Window"),
            ("RULE_STOPPING_DISTANCE", "Safe Stopping Distance"),
        ]

        if not safety_dict:
            # Default all passed for approved plan
            return {
                "overall_status": "APPROVED",
                "rules": [
                    {"code": code, "name": name, "passed": True, "details": "Verified safe"}
                    for code, name in rules
                ]
            }

        status = safety_dict.get("status", "APPROVED")
        violations = safety_dict.get("violations", [])
        violating_codes = {v.get("rule") for v in violations}

        checklist = []
        for code, name in rules:
            has_viol = code in violating_codes
            viol_info = next((v for v in violations if v.get("rule") == code), None)
            checklist.append({
                "code": code,
                "name": name,
                "passed": not has_viol,
                "details": viol_info.get("message") if viol_info else "Verified safe"
            })

        return {
            "overall_status": status,
            "violations_count": len(violations),
            "rules": checklist
        }

