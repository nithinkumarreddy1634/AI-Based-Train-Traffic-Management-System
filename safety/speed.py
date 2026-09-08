"""
Speed Limit Compliance Validator.

Calculates Allowed Speed, Recommended Speed, and Speed Difference for every train,
rejecting any recommendation that attempts overspeeding.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_SPEED_LIMIT


class SpeedValidator:
    """Validates that train speeds adhere strictly to rolling stock and civil engineering limits."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG

    def validate_speeds(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Validates recommended train speeds against vehicle and section ceilings.

        Returns (violations, warnings).
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        sec_data = section_info or {}
        sec_max_speed = float(sec_data.get("max_speed_kmph", self.config.max_network_speed_kmph))
        sec_name = sec_data.get("section_name", "Corridor Section")

        for entry in schedule_entries:
            train_num = entry.get("train_number", f"T{entry.get('train_id')}")
            train_type = entry.get("train_type", "PASSENGER").upper()

            # 1. Determine train vehicle speed limit
            type_max = self.config.train_max_speeds.get(train_type, 100.0)
            custom_train_max = entry.get("max_speed_kmph")
            if custom_train_max and float(custom_train_max) > 0:
                train_max = float(custom_train_max)
            else:
                train_max = type_max

            # 2. Compute Allowed Speed
            allowed_speed = min(train_max, sec_max_speed, self.config.max_network_speed_kmph)

            # 3. Recommended / Operating Speed
            recommended_speed = float(entry.get("current_speed_kmph") or entry.get("speed_kmph") or 60.0)

            # 4. Calculate Speed Difference
            speed_diff = round(recommended_speed - allowed_speed, 1)

            entry["speed_audit"] = {
                "allowed_speed_kmph": allowed_speed,
                "recommended_speed_kmph": recommended_speed,
                "speed_difference_kmph": speed_diff
            }

            # 5. Check Violation
            if speed_diff > self.config.overspeed_tolerance_kmph:
                violations.append(SafetyViolation(
                    rule=RULE_SPEED_LIMIT,
                    severity="CRITICAL",
                    message=(
                        f"Train {train_num} exceeds speed limit: "
                        f"recommended speed {recommended_speed} km/h > allowed speed {allowed_speed} km/h "
                        f"(overspeed by +{speed_diff} km/h)."
                    ),
                    train_numbers=[train_num],
                    section_name=sec_name,
                    details={
                        "allowed_speed_kmph": allowed_speed,
                        "recommended_speed_kmph": recommended_speed,
                        "speed_difference_kmph": speed_diff,
                        "section_max_speed": sec_max_speed,
                        "vehicle_max_speed": train_max
                    }
                ))
            elif speed_diff > -5.0:
                # Close to limit warning
                warnings.append(SafetyWarning(
                    rule=RULE_SPEED_LIMIT,
                    severity="LOW",
                    message=f"Train {train_num} operating within 5 km/h of maximum speed ({recommended_speed}/{allowed_speed} km/h).",
                    train_numbers=[train_num],
                    section_name=sec_name,
                    recommendation="Monitor track curvature and braking response."
                ))

        return (violations, warnings)

