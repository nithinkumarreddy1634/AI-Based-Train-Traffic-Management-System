"""
Deterministic domain rules for detecting 5 classes of railway traffic conflicts:
1. SAME_SECTION
2. REAR_END
3. OPPOSITE_DIRECTION
4. JUNCTION
5. INSUFFICIENT_HEADWAY
"""

import uuid
from typing import Optional, List, Dict, Any
from .conflict_types import (
    Conflict,
    ConflictType,
    ConflictSeverity,
    ConflictUrgency,
    ConflictStatus,
)
from .headway import HeadwayCalculator
from .severity import SeverityEvaluator
from .predictor import TimeToConflictPredictor


class ConflictRulesEngine:
    """Evaluates spatial, directional, and temporal conditions between trains."""

    @staticmethod
    def _generate_id(prefix: str = "CONF") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def evaluate_same_section(
        cls,
        train_a: Any,
        train_b: Any,
        section_id: int,
        section_info: Dict[str, Any],
        is_single_track: bool = False
    ) -> Optional[Conflict]:
        """
        Rule 1: Same Section Conflict.
        Triggered when two active trains occupy the same block section simultaneously.
        """
        if train_a.status in ("ARRIVED", "SCHEDULED") or train_b.status in ("ARRIVED", "SCHEDULED"):
            return None

        sec_name = section_info.get("name", f"Section {section_id}")
        sep_km = HeadwayCalculator.calculate_separation_km(
            train_a.current_position_km,
            train_b.current_position_km
        )

        # Same section on single track is critical; on double track it is investigated further
        # for headway or rear-end, but if on the exact same track or same block section:
        closing_speed = HeadwayCalculator.calculate_relative_speed_kmph(
            train_a.speed_kmph, train_a.direction,
            train_b.speed_kmph, train_b.direction
        )

        ttc = TimeToConflictPredictor.calculate_ttc_seconds(sep_km, closing_speed)
        severity, urgency = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.SAME_SECTION,
            time_to_conflict_seconds=ttc,
            distance_km=sep_km,
            is_single_track=is_single_track,
            priority_1=train_a.priority,
            priority_2=train_b.priority,
            closing_speed_kmph=closing_speed
        )

        # Decide which train should be advised to hold
        higher_p = train_a if train_a.priority <= train_b.priority else train_b
        lower_p = train_b if higher_p == train_a else train_a

        explanation = (
            f"Both Train {train_a.train_number} and Train {train_b.train_number} occupy "
            f"section '{sec_name}' simultaneously with {sep_km:.2f} km separation."
        )
        recommendation = (
            f"Hold Train {lower_p.train_number} ({lower_p.train_name}) or route to passing loop; "
            f"grant clear block to Train {higher_p.train_number}."
        )

        return Conflict(
            conflict_id=cls._generate_id("SEC"),
            conflict_type=ConflictType.SAME_SECTION,
            severity=severity,
            urgency=urgency,
            train_id_1=train_a.train_id,
            train_number_1=train_a.train_number,
            train_id_2=train_b.train_id,
            train_number_2=train_b.train_number,
            section_id=section_id,
            section_name=sec_name,
            distance_km=sep_km,
            time_to_conflict_seconds=ttc,
            relative_speed_kmph=closing_speed,
            explanation=explanation,
            recommendation=recommendation,
        )

    @classmethod
    def evaluate_rear_end(
        cls,
        train_a: Any,
        train_b: Any,
        section_id: Optional[int],
        section_info: Dict[str, Any]
    ) -> Optional[Conflict]:
        """
        Rule 2: Rear-End Conflict.
        Triggered when two trains are moving in the same direction on the same route/section,
        and the following train is closing distance within stopping distance threshold.
        """
        if train_a.direction != train_b.direction:
            return None
        if train_a.status in ("ARRIVED", "SCHEDULED") or train_b.status in ("ARRIVED", "SCHEDULED"):
            return None

        # Determine which is leading and which is following based on direction and position
        is_up = (train_a.direction == "UP")
        # For UP: position increases with time. Thus higher position is leading.
        # For DOWN: position decreases with time. Thus lower position is leading.
        if is_up:
            if train_a.current_position_km >= train_b.current_position_km:
                lead, follow = train_a, train_b
            else:
                lead, follow = train_b, train_a
        else:
            if train_a.current_position_km <= train_b.current_position_km:
                lead, follow = train_a, train_b
            else:
                lead, follow = train_b, train_a

        sep_km = HeadwayCalculator.calculate_separation_km(lead.current_position_km, follow.current_position_km)
        closing_speed = follow.speed_kmph - lead.speed_kmph

        # If following train is faster, or separation is dangerously small (< stopping distance)
        stop_dist = HeadwayCalculator.calculate_stopping_distance_km(follow.speed_kmph)
        is_dangerously_close = (sep_km <= stop_dist + 0.3)
        is_closing_fast = (closing_speed > 5.0 and sep_km <= 3.5)

        if not (is_dangerously_close or is_closing_fast):
            return None

        ttc = TimeToConflictPredictor.calculate_ttc_seconds(
            sep_km,
            max(closing_speed, 10.0 if is_dangerously_close else closing_speed)
        )

        severity, urgency = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.REAR_END,
            time_to_conflict_seconds=ttc,
            distance_km=sep_km,
            priority_1=lead.priority,
            priority_2=follow.priority,
            closing_speed_kmph=max(0.0, closing_speed)
        )

        sec_name = section_info.get("name", "Corridor Block")
        safe_target_speed = max(0.0, lead.speed_kmph - 15.0)

        explanation = (
            f"Train {follow.train_number} is closing on leading Train {lead.train_number} "
            f"in {sec_name} (gap: {sep_km:.2f} km, closing rate: {closing_speed:.1f} km/h)."
        )
        recommendation = (
            f"Regulate speed of Train {follow.train_number} down to {int(safe_target_speed)} km/h "
            f"or initiate signal amber caution to maintain stopping buffer."
        )

        return Conflict(
            conflict_id=cls._generate_id("REAR"),
            conflict_type=ConflictType.REAR_END,
            severity=severity,
            urgency=urgency,
            train_id_1=follow.train_id,
            train_number_1=follow.train_number,
            train_id_2=lead.train_id,
            train_number_2=lead.train_number,
            section_id=section_id,
            section_name=sec_name,
            distance_km=sep_km,
            time_to_conflict_seconds=ttc,
            relative_speed_kmph=closing_speed,
            explanation=explanation,
            recommendation=recommendation,
        )

    @classmethod
    def evaluate_opposite_direction(
        cls,
        train_a: Any,
        train_b: Any,
        section_id: Optional[int],
        section_info: Dict[str, Any],
        is_single_track: bool = False
    ) -> Optional[Conflict]:
        """
        Rule 3: Opposite Direction Conflict.
        Triggered when two trains are moving towards each other (UP vs DOWN) on the same section
        or single track corridor.
        """
        if train_a.direction == train_b.direction:
            return None
        if train_a.status in ("ARRIVED", "SCHEDULED") or train_b.status in ("ARRIVED", "SCHEDULED"):
            return None

        # Check if approaching each other:
        # UP train starts lower km and moves UP. DOWN train starts higher km and moves DOWN.
        up_train = train_a if train_a.direction == "UP" else train_b
        down_train = train_b if train_a.direction == "UP" else train_a

        # If up_train is at smaller km and down_train is at larger km, they are heading towards each other!
        if up_train.current_position_km > down_train.current_position_km:
            # They have already passed each other or are moving away
            return None

        sep_km = HeadwayCalculator.calculate_separation_km(
            train_a.current_position_km,
            train_b.current_position_km
        )

        # Only evaluate if in the same section or within proximity (<= 8.0 km)
        if sep_km > 8.0:
            return None

        closing_speed = train_a.speed_kmph + train_b.speed_kmph
        ttc = TimeToConflictPredictor.calculate_ttc_seconds(sep_km, closing_speed)

        severity, urgency = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.OPPOSITE_DIRECTION,
            time_to_conflict_seconds=ttc,
            distance_km=sep_km,
            is_single_track=is_single_track,
            priority_1=train_a.priority,
            priority_2=train_b.priority,
            closing_speed_kmph=closing_speed
        )

        sec_name = section_info.get("name", "Single/Bi-directional Line")
        higher_p = train_a if train_a.priority <= train_b.priority else train_b
        lower_p = train_b if higher_p == train_a else train_a

        explanation = (
            f"Opposing trains {train_a.train_number} (UP) and {train_b.train_number} (DOWN) "
            f"approaching head-on in {sec_name} with {sep_km:.2f} km separation."
        )
        recommendation = (
            f"URGENT: Divert lower-priority Train {lower_p.train_number} to nearest passing siding; "
            f"ensure absolute block clearance for Train {higher_p.train_number}."
        )

        return Conflict(
            conflict_id=cls._generate_id("HEAD"),
            conflict_type=ConflictType.OPPOSITE_DIRECTION,
            severity=severity,
            urgency=urgency,
            train_id_1=train_a.train_id,
            train_number_1=train_a.train_number,
            train_id_2=train_b.train_id,
            train_number_2=train_b.train_number,
            section_id=section_id,
            section_name=sec_name,
            distance_km=sep_km,
            time_to_conflict_seconds=ttc,
            relative_speed_kmph=closing_speed,
            explanation=explanation,
            recommendation=recommendation,
        )

    @classmethod
    def evaluate_junction(
        cls,
        train_a: Any,
        train_b: Any,
        junction_station: Dict[str, Any],
        eta_diff_seconds: float,
        dist_a_km: float,
        dist_b_km: float
    ) -> Optional[Conflict]:
        """
        Rule 4: Junction Conflict.
        Triggered when two trains on converging sections arrive at a common station throat / junction
        within an overlapping arrival window (< 180 seconds) and distance < 4 km.
        """
        if train_a.status in ("ARRIVED", "SCHEDULED") or train_b.status in ("ARRIVED", "SCHEDULED"):
            return None

        stn_name = junction_station.get("name", "Junction")
        avg_dist = round((dist_a_km + dist_b_km) / 2.0, 2)

        ttc = max(10.0, round(eta_diff_seconds, 1))
        severity, urgency = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.JUNCTION,
            time_to_conflict_seconds=ttc,
            distance_km=avg_dist,
            priority_1=train_a.priority,
            priority_2=train_b.priority
        )

        higher_p = train_a if train_a.priority <= train_b.priority else train_b
        lower_p = train_b if higher_p == train_a else train_a

        explanation = (
            f"Converging arrival at {stn_name} junction: Train {train_a.train_number} ({dist_a_km:.1f} km away) "
            f"and Train {train_b.train_number} ({dist_b_km:.1f} km away) have overlapping arrival window (~{int(eta_diff_seconds)}s)."
        )
        recommendation = (
            f"Give path priority through {stn_name} interlocking to Train {higher_p.train_number}; "
            f"hold Train {lower_p.train_number} at approach home signal."
        )

        return Conflict(
            conflict_id=cls._generate_id("JUNC"),
            conflict_type=ConflictType.JUNCTION,
            severity=severity,
            urgency=urgency,
            train_id_1=train_a.train_id,
            train_number_1=train_a.train_number,
            train_id_2=train_b.train_id,
            train_number_2=train_b.train_number,
            section_name=f"{stn_name} Interlocking",
            distance_km=avg_dist,
            time_to_conflict_seconds=ttc,
            explanation=explanation,
            recommendation=recommendation,
        )

    @classmethod
    def evaluate_insufficient_headway(
        cls,
        train_a: Any,
        train_b: Any,
        section_id: Optional[int],
        section_info: Dict[str, Any]
    ) -> Optional[Conflict]:
        """
        Rule 5: Insufficient Headway.
        Triggered when two trains in same direction maintain a separation smaller than required
        dynamic headway buffer, but not yet an immediate rear-end collision hazard.
        """
        if train_a.direction != train_b.direction:
            return None
        if train_a.status in ("ARRIVED", "SCHEDULED") or train_b.status in ("ARRIVED", "SCHEDULED"):
            return None

        is_up = (train_a.direction == "UP")
        if is_up:
            lead, follow = (train_a, train_b) if train_a.current_position_km >= train_b.current_position_km else (train_b, train_a)
        else:
            lead, follow = (train_a, train_b) if train_a.current_position_km <= train_b.current_position_km else (train_b, train_a)

        sep_km = HeadwayCalculator.calculate_separation_km(lead.current_position_km, follow.current_position_km)
        is_violated, req_headway = HeadwayCalculator.is_headway_insufficient(sep_km, follow.speed_kmph)

        if not is_violated:
            return None

        # Time buffer at following speed
        ttc = (sep_km / max(follow.speed_kmph, 20.0)) * 3600.0

        severity, urgency = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.INSUFFICIENT_HEADWAY,
            time_to_conflict_seconds=ttc,
            distance_km=sep_km,
            priority_1=lead.priority,
            priority_2=follow.priority
        )

        sec_name = section_info.get("name", "Corridor")
        explanation = (
            f"Headway between Train {follow.train_number} and Train {lead.train_number} is "
            f"{sep_km:.2f} km (required: {req_headway:.2f} km) in {sec_name}."
        )
        recommendation = (
            f"Maintain safe spacing: moderate Train {follow.train_number} speed to restore >= {req_headway:.1f} km headway."
        )

        return Conflict(
            conflict_id=cls._generate_id("HEADWAY"),
            conflict_type=ConflictType.INSUFFICIENT_HEADWAY,
            severity=severity,
            urgency=urgency,
            train_id_1=follow.train_id,
            train_number_1=follow.train_number,
            train_id_2=lead.train_id,
            train_number_2=lead.train_number,
            section_id=section_id,
            section_name=sec_name,
            distance_km=sep_km,
            time_to_conflict_seconds=round(ttc, 1),
            explanation=explanation,
            recommendation=recommendation,
        )

