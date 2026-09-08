"""
Kinematic Safe Stopping Distance Validator.

Validates that trains approaching red signals, occupied block boundaries, or holding loops
have sufficient physical braking distance to come to a complete safe stop.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_STOPPING_DISTANCE
from safety.constraints import SafetyConstraintUtils


class StoppingDistanceValidator:
    """Validates safe braking distance margins in the discrete-time simulation."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG
        self.utils = SafetyConstraintUtils(self.config)

    def validate_stopping_distances(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Calculates required stopping distance for each train and validates against available separation distance.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        sec_name = (section_info or {}).get("section_name", "Approach Block")

        for entry in schedule_entries:
            t_num = entry.get("train_number", f"T{entry.get('train_id')}")
            speed_kmph = float(entry.get("current_speed_kmph") or entry.get("speed_kmph") or 60.0)

            # Available separation distance to restriction or leading train (meters)
            if "distance_to_target_meters" in entry:
                dist_available_m = float(entry["distance_to_target_meters"])
            elif "available_distance_meters" in entry:
                dist_available_m = float(entry["available_distance_meters"])
            elif "distance_to_target_m" in entry:
                dist_available_m = float(entry["distance_to_target_m"])
            else:
                dist_available_km = float(entry.get("distance_to_restriction_km") or entry.get("distance_to_section_km") or 5.0)
                dist_available_m = dist_available_km * 1000.0

            req_stop_dist_m = self.utils.compute_service_stopping_distance(speed_kmph)

            entry["braking_audit"] = {
                "speed_kmph": speed_kmph,
                "required_stopping_distance_m": req_stop_dist_m,
                "available_distance_m": dist_available_m,
                "safety_margin_m": round(dist_available_m - req_stop_dist_m, 1)
            }

            if dist_available_m < req_stop_dist_m:
                deficit = round(req_stop_dist_m - dist_available_m, 1)
                violations.append(SafetyViolation(
                    rule=RULE_STOPPING_DISTANCE,
                    severity="CRITICAL",
                    message=(
                        f"Insufficient braking distance for {t_num}: traveling at {speed_kmph} km/h "
                        f"requires {req_stop_dist_m}m stopping distance, but only {round(dist_available_m, 1)}m "
                        f"available (deficit: {deficit}m)."
                    ),
                    train_numbers=[t_num],
                    section_name=sec_name,
                    details={
                        "speed_kmph": speed_kmph,
                        "required_m": req_stop_dist_m,
                        "available_m": dist_available_m,
                        "deficit_m": deficit
                    }
                ))
            elif dist_available_m < (req_stop_dist_m + self.config.emergency_stop_threshold_meters):
                warnings.append(SafetyWarning(
                    rule=RULE_STOPPING_DISTANCE,
                    severity="LOW",
                    message=f"Train {t_num} approaching braking boundary with low safety buffer margin ({round(dist_available_m - req_stop_dist_m, 1)}m).",
                    train_numbers=[t_num],
                    section_name=sec_name,
                    recommendation="Pre-warn driver / set preliminary yellow aspect."
                ))

        return (violations, warnings)
