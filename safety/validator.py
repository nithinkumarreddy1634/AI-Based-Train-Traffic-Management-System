"""
Central Safety Validation Engine.

Executes the formal 9-stage verification pipeline:
1. Emergency State Check
2. Speed Limit Check
3. Minimum Headway Check
4. Track Occupancy Check
5. Section Capacity Check
6. Opposite Direction Mutex Check
7. Route Connectivity Check
8. Junction Interlocking Check
9. Safe Stopping Distance Check
"""
from typing import List, Dict, Any, Optional
import datetime
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyValidationResult, SafetyViolation, SafetyWarning
from safety.rules import (
    RULE_EMERGENCY_STATE,
    RULE_SPEED_LIMIT,
    RULE_MINIMUM_HEADWAY,
    RULE_TRACK_OCCUPANCY,
    RULE_SECTION_OCCUPANCY,
    RULE_OPPOSITE_DIRECTION,
    RULE_ROUTE_CONNECTIVITY,
    RULE_JUNCTION_CLEARANCE,
    RULE_STOPPING_DISTANCE,
    ALL_SAFETY_RULES
)
from safety.speed import SpeedValidator
from safety.headway import HeadwayValidator
from safety.occupancy import OccupancyValidator
from safety.route import RouteValidator
from safety.junction import JunctionValidator
from safety.stopping_distance import StoppingDistanceValidator
from safety.emergency import EmergencyManager, DEFAULT_EMERGENCY_MANAGER


class SafetyValidator:
    """Independent formal safety validator acting as a fail-safe gatekeeper."""

    def __init__(
        self,
        config: Optional[SafetyConfig] = None,
        emergency_manager: Optional[EmergencyManager] = None
    ):
        self.config = config or DEFAULT_SAFETY_CONFIG
        self.emergency_manager = emergency_manager or DEFAULT_EMERGENCY_MANAGER

        self.speed_validator = SpeedValidator(self.config)
        self.headway_validator = HeadwayValidator(self.config)
        self.occupancy_validator = OccupancyValidator(self.config)
        self.route_validator = RouteValidator(self.config)
        self.junction_validator = JunctionValidator(self.config)
        self.stopping_validator = StoppingDistanceValidator(self.config)

        self._validation_seq = 0

    def validate(
        self,
        recommendation: Dict[str, Any],
        current_state: Optional[Dict[str, Any]] = None
    ) -> SafetyValidationResult:
        """
        Validates a proposed dispatch schedule against all 9 formal safety rules.

        Args:
            recommendation: Optimization result or dictionary with train recommendations.
            current_state: Live network state (sections, tracks, active conflicts).

        Returns:
            SafetyValidationResult with APPROVED or REJECTED status.
        """
        self._validation_seq += 1
        val_id = self._validation_seq
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rec_id = recommendation.get("optimization_id")
        recs_list = recommendation.get("train_recommendations", [])
        if not recs_list and isinstance(recommendation.get("recommended_sequence"), list):
            # Format minimal entries if passed directly
            recs_list = [{"train_number": t, "train_id": idx + 1, "entry_time_sec": idx * 120}
                         for idx, t in enumerate(recommendation["recommended_sequence"])]

        state = current_state or {}
        sec_info = state.get("section_info") or {
            "section_id": recommendation.get("target_section_id", 1),
            "section_name": recommendation.get("monitored_section_name", "Corridor Section"),
            "max_speed_kmph": 110.0,
            "track_count": 2,
            "is_single_track": False
        }
        tracks = state.get("tracks", {})
        sections = state.get("sections", {})
        active_conflicts = state.get("conflicts", [])

        rules_checked = [
            RULE_EMERGENCY_STATE,
            RULE_SPEED_LIMIT,
            RULE_MINIMUM_HEADWAY,
            RULE_TRACK_OCCUPANCY,
            RULE_SECTION_OCCUPANCY,
            RULE_OPPOSITE_DIRECTION,
            RULE_ROUTE_CONNECTIVITY,
            RULE_JUNCTION_CLEARANCE,
            RULE_STOPPING_DISTANCE,
        ]

        all_violations: List[SafetyViolation] = []
        all_warnings: List[SafetyWarning] = []

        # Stage 1: Emergency State Check
        em_viols, em_warns = self.emergency_manager.evaluate_emergency_conditions(
            network_tracks=tracks,
            active_conflicts=active_conflicts
        )
        all_violations.extend(em_viols)
        all_warnings.extend(em_warns)

        # Stage 2: Speed Limit Check
        sp_viols, sp_warns = self.speed_validator.validate_speeds(recs_list, sec_info)
        all_violations.extend(sp_viols)
        all_warnings.extend(sp_warns)

        # Stage 3: Minimum Headway Check
        hw_viols, hw_warns = self.headway_validator.validate_headway(recs_list, sec_info)
        all_violations.extend(hw_viols)
        all_warnings.extend(hw_warns)

        # Stage 4: Track Occupancy Check
        to_viols, to_warns = self.occupancy_validator.validate_track_availability(recs_list, tracks)
        all_violations.extend(to_viols)
        all_warnings.extend(to_warns)

        # Stage 5: Section Capacity Check
        sc_viols, sc_warns = self.occupancy_validator.validate_section_capacity(recs_list, sec_info)
        all_violations.extend(sc_viols)
        all_warnings.extend(sc_warns)

        # Stage 6: Opposite-Direction Mutex Check
        od_viols, od_warns = self.occupancy_validator.validate_opposite_direction(recs_list, sec_info)
        all_violations.extend(od_viols)
        all_warnings.extend(od_warns)

        # Stage 7: Route Connectivity Check
        rt_viols, rt_warns = self.route_validator.validate_routes(recs_list, sections)
        all_violations.extend(rt_viols)
        all_warnings.extend(rt_warns)

        # Stage 8: Junction Interlocking Check
        jn_viols, jn_warns = self.junction_validator.validate_junctions(recs_list, active_conflicts)
        all_violations.extend(jn_viols)
        all_warnings.extend(jn_warns)

        # Stage 9: Safe Stopping Distance Check
        sd_viols, sd_warns = self.stopping_validator.validate_stopping_distances(recs_list, sec_info)
        all_violations.extend(sd_viols)
        all_warnings.extend(sd_warns)

        # Final Decision Synthesis
        if len(all_violations) > 0:
            status = "REJECTED"
            score_status = "UNSAFE"
        elif len(all_warnings) > 0:
            status = "APPROVED"
            score_status = "WARNING"
        else:
            status = "APPROVED"
            score_status = "SAFE"

        summary = {
            "total_trains": len(recs_list),
            "critical_violations": sum(1 for v in all_violations if v.severity == "CRITICAL"),
            "high_violations": sum(1 for v in all_violations if v.severity == "HIGH"),
            "total_warnings": len(all_warnings),
            "monitored_section": sec_info.get("section_name", "Corridor"),
        }

        return SafetyValidationResult(
            validation_id=val_id,
            recommendation_id=rec_id,
            status=status,
            safety_score_status=score_status,
            rules_checked=rules_checked,
            violations=all_violations,
            warnings=all_warnings,
            validated_at=now_str,
            candidate_summary=summary
        )


# Global singleton instance
DEFAULT_SAFETY_VALIDATOR = SafetyValidator()

