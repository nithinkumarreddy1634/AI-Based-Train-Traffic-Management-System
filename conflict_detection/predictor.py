"""
Time-to-Conflict Predictor, Resolution Tracker, and Alert Deduplication.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from .conflict_types import Conflict, ConflictStatus, ConflictType, ConflictSeverity


class TimeToConflictPredictor:
    """Calculates linear time-to-conflict projections based on closing kinematics."""

    @staticmethod
    def calculate_ttc_seconds(
        separation_km: float,
        closing_speed_kmph: float
    ) -> Optional[float]:
        """
        Projects time to point of contact in seconds:
        TTC = (distance / closing_speed) * 3600
        Returns None if trains are not closing (speed <= 0.5 km/h).
        """
        if closing_speed_kmph <= 0.5 or separation_km <= 0.0:
            if separation_km <= 0.05:
                return 0.0
            return None

        ttc_seconds = (separation_km / closing_speed_kmph) * 3600.0
        return round(ttc_seconds, 1)


class ConflictResolutionTracker:
    """
    Maintains active conflict lifecycles, detects when conflicts resolve,
    and maintains historical conflict records.
    """

    def __init__(self, max_history: int = 150):
        self.active_conflicts: Dict[str, Conflict] = {}
        self.resolved_history: List[Conflict] = []
        self.max_history = max_history

    @staticmethod
    def generate_conflict_key(
        conflict_type: ConflictType,
        train_id_1: int,
        train_id_2: Optional[int],
        section_id: Optional[int]
    ) -> str:
        """Deterministic unique key identifying an ongoing conflict."""
        t1, t2 = sorted([train_id_1, train_id_2 or 0])
        s_id = section_id or 0
        return f"{conflict_type.value}_{t1}_{t2}_{s_id}"

    def update(
        self,
        current_conflicts: List[Conflict],
        current_sim_time: float
    ) -> Tuple[List[Conflict], List[Conflict]]:
        """
        Updates tracked conflicts:
        - Adds new conflicts or updates existing ones.
        - Automatically marks absent conflicts as RESOLVED.
        Returns: (newly_detected_conflicts, newly_resolved_conflicts)
        """
        current_keys = {}
        for c in current_conflicts:
            key = self.generate_conflict_key(
                c.conflict_type,
                c.train_id_1,
                c.train_id_2,
                c.section_id
            )
            current_keys[key] = c

        newly_detected: List[Conflict] = []
        newly_resolved: List[Conflict] = []

        # Check for newly resolved conflicts
        active_keys = list(self.active_conflicts.keys())
        for key in active_keys:
            if key not in current_keys:
                # Conflict has cleared!
                conflict = self.active_conflicts.pop(key)
                conflict.status = ConflictStatus.RESOLVED
                conflict.resolved_at = current_sim_time
                if conflict.detected_at is not None:
                    conflict.duration_seconds = round(max(0.0, current_sim_time - conflict.detected_at), 1)
                else:
                    conflict.duration_seconds = 0.0
                
                self.resolved_history.insert(0, conflict)
                if len(self.resolved_history) > self.max_history:
                    self.resolved_history.pop()
                
                newly_resolved.append(conflict)

        # Update or insert current conflicts
        for key, c in current_keys.items():
            if key in self.active_conflicts:
                existing = self.active_conflicts[key]
                # Preserve detected_at and ID
                c.conflict_id = existing.conflict_id
                c.detected_at = existing.detected_at
                self.active_conflicts[key] = c
            else:
                c.detected_at = current_sim_time
                self.active_conflicts[key] = c
                newly_detected.append(c)

        return newly_detected, newly_resolved

    def get_all_active(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.active_conflicts.values()]

    def get_history(self) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.resolved_history]

    def get_conflict_by_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        for c in self.active_conflicts.values():
            if c.conflict_id == conflict_id:
                return c.to_dict()
        for c in self.resolved_history:
            if c.conflict_id == conflict_id:
                return c.to_dict()
        return None

    def reset(self):
        self.active_conflicts.clear()
        self.resolved_history.clear()


class AlertDeduplicator:
    """
    Prevents repetitive alert noise across consecutive simulation ticks.
    Emits alerts only when a new conflict occurs, when severity escalates,
    or after an alert cooldown period has elapsed.
    """

    def __init__(self, cooldown_seconds: float = 60.0):
        self.cooldown_seconds = cooldown_seconds
        # key -> (last_emitted_sim_time, last_severity)
        self._emitted: Dict[str, Tuple[float, str]] = {}

    def should_emit(self, conflict: Conflict, current_sim_time: float) -> bool:
        key = f"{conflict.conflict_type}_{conflict.train_id_1}_{conflict.train_id_2}_{conflict.section_id}"
        sev_str = conflict.severity.value if hasattr(conflict.severity, "value") else str(conflict.severity)

        if key not in self._emitted:
            self._emitted[key] = (current_sim_time, sev_str)
            return True

        last_time, last_sev = self._emitted[key]
        
        # Immediate emit if severity escalated to CRITICAL
        if sev_str == ConflictSeverity.CRITICAL.value and last_sev != ConflictSeverity.CRITICAL.value:
            self._emitted[key] = (current_sim_time, sev_str)
            return True

        # Check cooldown
        if (current_sim_time - last_time) >= self.cooldown_seconds:
            self._emitted[key] = (current_sim_time, sev_str)
            return True

        return False

    def clear(self):
        self._emitted.clear()

