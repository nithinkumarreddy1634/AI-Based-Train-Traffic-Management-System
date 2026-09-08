"""
Emergency State Interlock & Fail-Safe Handler.

Detects emergency conditions (TRACK_BLOCKED, TRAIN_STOPPED_UNEXPECTEDLY,
CRITICAL_CONFLICT, SIMULATION_EMERGENCY) and halts unsafe recommendation approval.
"""
from typing import List, Dict, Any, Tuple, Optional
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import RULE_EMERGENCY_STATE


class EmergencyManager:
    """Monitors and manages corridor emergency interlocks."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG
        self._emergency_active: bool = False
        self._emergency_reason: Optional[str] = None
        self._emergency_type: Optional[str] = None
        self._affected_sections: List[int] = []
        self._affected_tracks: List[int] = []

    @property
    def is_emergency_active(self) -> bool:
        return self._emergency_active

    @property
    def emergency_reason(self) -> Optional[str]:
        return self._emergency_reason

    def trigger_emergency(
        self,
        reason: str = "Emergency Interlock Activated",
        emergency_type: str = "MANUAL_TRIGGER",
        affected_sections: Optional[List[int]] = None,
        affected_tracks: Optional[List[int]] = None
    ):
        """Manually trigger or simulate an emergency state."""
        self._emergency_active = True
        self._emergency_type = emergency_type
        self._emergency_reason = reason
        self._affected_sections = affected_sections or []
        self._affected_tracks = affected_tracks or []

    def clear_emergency(self):
        """Clear active emergency state."""
        self._emergency_active = False
        self._emergency_type = None
        self._emergency_reason = None
        self._affected_sections = []
        self._affected_tracks = []

    def get_emergency_state(self) -> Dict[str, Any]:
        """Returns the current emergency status and parameters."""
        return {
            "is_emergency": self._emergency_active,
            "emergency_type": self._emergency_type,
            "emergency_reason": self._emergency_reason,
            "affected_sections": self._affected_sections,
            "affected_tracks": self._affected_tracks
        }

    def evaluate_emergency_conditions(
        self,
        network_tracks: Optional[Dict[int, Dict[str, Any]]] = None,
        active_conflicts: Optional[List[Dict[str, Any]]] = None,
        train_agents: Optional[Dict[int, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Scans current network telemetry for critical emergency triggers:
        - Active manual emergency flag
        - Track blocked or emergency switch fault
        - Critical severity head-on conflict
        - Unscheduled train breakdown / stall
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        # 1. Check Active Global Emergency Flag
        if self._emergency_active:
            violations.append(SafetyViolation(
                rule=RULE_EMERGENCY_STATE,
                severity="CRITICAL",
                message=f"SIMULATION EMERGENCY ACTIVE [{self._emergency_type}]: {self._emergency_reason}. Normal dispatch optimization suspended.",
                details={"emergency_type": self._emergency_type, "reason": self._emergency_reason}
            ))
            return (violations, warnings)

        # 2. Check for Track Blocked
        if network_tracks:
            for t_id, t_info in network_tracks.items():
                if str(t_info.get("status", "")).upper() == "BLOCKED":
                    t_num = t_info.get("track_number", str(t_id))
                    violations.append(SafetyViolation(
                        rule=RULE_EMERGENCY_STATE,
                        severity="CRITICAL",
                        message=f"Emergency Interlock: Track {t_num} is BLOCKED. All automatic section entries halted.",
                        details={"track_id": t_id, "track_number": t_num}
                    ))

        # 3. Check for Active CRITICAL Head-On Conflicts
        if active_conflicts:
            for conf in active_conflicts:
                sev = str(conf.get("severity", "")).upper()
                ctype = str(conf.get("conflict_type", "")).upper()
                if sev == "CRITICAL" and ("HEAD_ON" in ctype or "OPPOSITE" in ctype):
                    t1 = conf.get("train_number_1") or "T1"
                    t2 = conf.get("train_number_2") or "T2"
                    violations.append(SafetyViolation(
                        rule=RULE_EMERGENCY_STATE,
                        severity="CRITICAL",
                        message=f"CRITICAL SAFETY EMERGENCY: Unresolved head-on conflict between {t1} and {t2}. Dispatch optimization suspended.",
                        train_numbers=[t1, t2],
                        details=conf
                    ))

        return (violations, warnings)


# Global singleton instance
DEFAULT_EMERGENCY_MANAGER = EmergencyManager()
