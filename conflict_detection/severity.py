"""
Severity and Urgency Evaluation Engine for Railway Conflicts.
Deterministic, multi-factor scoring based on closure rates, separation, priority, and track geometry.
"""

from typing import Optional, Tuple
from .conflict_types import ConflictType, ConflictSeverity, ConflictUrgency


class SeverityEvaluator:
    """Evaluates conflict severity and urgency using transparent domain rules."""

    @classmethod
    def evaluate_urgency(
        cls,
        time_to_conflict_seconds: Optional[float],
        distance_km: float,
        conflict_type: ConflictType
    ) -> ConflictUrgency:
        """
        Determines temporal urgency:
        - IMMEDIATE: < 60s or < 1.0 km, or head-on collision course
        - SOON: 60 - 180s or 1.0 - 3.0 km
        - MONITOR: > 180s
        """
        if conflict_type == ConflictType.OPPOSITE_DIRECTION and distance_km < 4.0:
            return ConflictUrgency.IMMEDIATE

        if time_to_conflict_seconds is not None:
            if time_to_conflict_seconds <= 60.0:
                return ConflictUrgency.IMMEDIATE
            elif time_to_conflict_seconds <= 180.0:
                return ConflictUrgency.SOON
            else:
                return ConflictUrgency.MONITOR

        # Distance fallback if time-to-conflict is indeterminate (e.g. stationary train ahead)
        if distance_km < 1.0:
            return ConflictUrgency.IMMEDIATE
        elif distance_km <= 3.0:
            return ConflictUrgency.SOON
        else:
            return ConflictUrgency.MONITOR

    @classmethod
    def evaluate_severity(
        cls,
        conflict_type: ConflictType,
        time_to_conflict_seconds: Optional[float],
        distance_km: float,
        is_single_track: bool = False,
        priority_1: int = 2,
        priority_2: int = 2,
        closing_speed_kmph: float = 0.0
    ) -> ConflictSeverity:
        """
        Calculates severity level:
        CRITICAL: Head-on conflict on single track, or TTC <= 60s, or distance < 0.8km
        HIGH: TTC <= 120s, or distance < 1.8km, or same-section on single track
        MEDIUM: TTC <= 300s, or junction convergence, or insufficient headway
        LOW: Mild headway deficit closing slowly
        INFO: Cautionary monitoring
        """
        # Rule 1: Opposite direction on same section or single track is always CRITICAL
        if conflict_type == ConflictType.OPPOSITE_DIRECTION:
            if is_single_track or distance_km < 5.0:
                return ConflictSeverity.CRITICAL
            return ConflictSeverity.HIGH

        # Rule 2: Immediate collision risk (short TTC or small physical gap)
        if time_to_conflict_seconds is not None and time_to_conflict_seconds <= 60.0:
            return ConflictSeverity.CRITICAL
        if distance_km < 0.8:
            return ConflictSeverity.CRITICAL

        # High priority trains (priority 1 = Express / Vande Bharat) escalate severity
        is_high_priority = (priority_1 == 1 or priority_2 == 1)

        # Rule 3: High severity thresholds
        if time_to_conflict_seconds is not None and time_to_conflict_seconds <= 120.0:
            return ConflictSeverity.CRITICAL if is_high_priority else ConflictSeverity.HIGH
        if distance_km < 1.8:
            return ConflictSeverity.HIGH
        if conflict_type == ConflictType.SAME_SECTION and is_single_track:
            return ConflictSeverity.HIGH

        # Rule 4: Medium severity thresholds
        if time_to_conflict_seconds is not None and time_to_conflict_seconds <= 300.0:
            return ConflictSeverity.HIGH if is_high_priority else ConflictSeverity.MEDIUM
        if distance_km < 3.5:
            return ConflictSeverity.MEDIUM
        if conflict_type in (ConflictType.JUNCTION, ConflictType.REAR_END):
            return ConflictSeverity.MEDIUM

        # Rule 5: Low / Info
        if conflict_type == ConflictType.INSUFFICIENT_HEADWAY:
            return ConflictSeverity.LOW

        return ConflictSeverity.INFO

    @classmethod
    def evaluate(
        cls,
        conflict_type: ConflictType,
        time_to_conflict_seconds: Optional[float],
        distance_km: float,
        is_single_track: bool = False,
        priority_1: int = 2,
        priority_2: int = 2,
        closing_speed_kmph: float = 0.0
    ) -> Tuple[ConflictSeverity, ConflictUrgency]:
        """Convenience method returning both (severity, urgency)."""
        urgency = cls.evaluate_urgency(time_to_conflict_seconds, distance_km, conflict_type)
        severity = cls.evaluate_severity(
            conflict_type=conflict_type,
            time_to_conflict_seconds=time_to_conflict_seconds,
            distance_km=distance_km,
            is_single_track=is_single_track,
            priority_1=priority_1,
            priority_2=priority_2,
            closing_speed_kmph=closing_speed_kmph
        )
        return severity, urgency

