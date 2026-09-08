"""
Feature Analyzer for Explainable AI Train Traffic Decisions.

Identifies, quantifies, and ranks empirical operational features that influenced
an AI dispatching or routing recommendation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class DecisionFactor:
    """Represents an individual influencing operational factor with impact rating."""
    factor: str
    value: Any
    unit: str
    impact: str  # 'HIGH', 'MEDIUM', 'LOW'
    importance_score: float  # Normalized 0-100 scale
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeatureAnalyzer:
    """Analyzes telemetry, schedule, and section congestion to extract key decision drivers."""

    @staticmethod
    def analyze_factors(
        train_data: Dict[str, Any],
        recommendation: Dict[str, Any],
        section_info: Optional[Dict[str, Any]] = None,
        traffic_state: Optional[Dict[str, Any]] = None,
        active_conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts and scores concrete operational factors influencing the decision.
        Returns factors sorted by importance_score in descending order.
        """
        factors: List[DecisionFactor] = []
        sec = section_info or {}
        traf = traffic_state or {}
        confs = active_conflicts or []

        # 1. Train Priority Factor
        priority = str(train_data.get("priority", "MEDIUM")).upper()
        if priority == "HIGH":
            factors.append(DecisionFactor(
                factor="Train Priority",
                value="HIGH",
                unit="class",
                impact="HIGH",
                importance_score=88.0,
                reason="High-priority service (Rajdhani/Shatabdi/Superfast) given dispatch precedence to protect timetable punctuality"
            ))
        elif priority == "LOW":
            factors.append(DecisionFactor(
                factor="Train Priority",
                value="LOW",
                unit="class",
                impact="LOW",
                importance_score=35.0,
                reason="Lower freight priority allows safe dwelling/holding without passenger schedule disruption"
            ))
        else:
            factors.append(DecisionFactor(
                factor="Train Priority",
                value="MEDIUM",
                unit="class",
                impact="MEDIUM",
                importance_score=60.0,
                reason="Standard passenger service balanced against corridor headway"
            ))

        # 2. Predicted Delay (from Phase 6 ML service)
        pred_delay = float(
            train_data.get("predicted_delay_minutes",
            train_data.get("current_delay_minutes", 0.0) + train_data.get("predicted_additional_delay", 0.0))
        )
        if pred_delay >= 10.0:
            factors.append(DecisionFactor(
                factor="Predicted Delay",
                value=round(pred_delay, 1),
                unit="min",
                impact="HIGH",
                importance_score=92.0,
                reason=f"Train is projected to accrue {pred_delay:.1f} min delay; urgent dispatch required to halt cascading propagation"
            ))
        elif pred_delay >= 4.0:
            factors.append(DecisionFactor(
                factor="Predicted Delay",
                value=round(pred_delay, 1),
                unit="min",
                impact="MEDIUM",
                importance_score=68.0,
                reason=f"Moderate delay of {pred_delay:.1f} min detected; dispatch adjustment preserves recovery margin"
            ))
        else:
            factors.append(DecisionFactor(
                factor="Predicted Delay",
                value=round(pred_delay, 1),
                unit="min",
                impact="LOW",
                importance_score=40.0,
                reason="Minimal current delay; train is operating close to scheduled timetable"
            ))

        # 3. Section Utilization & Congestion
        utilization = float(sec.get("utilization_pct", traf.get("section_utilization", 60.0)))
        if utilization >= 75.0:
            factors.append(DecisionFactor(
                factor="Section Utilization",
                value=round(utilization, 1),
                unit="%",
                impact="HIGH",
                importance_score=85.0,
                reason=f"Section is heavily loaded at {utilization:.1f}% capacity; strict metering prevents gridlock"
            ))
        elif utilization >= 50.0:
            factors.append(DecisionFactor(
                factor="Section Utilization",
                value=round(utilization, 1),
                unit="%",
                impact="MEDIUM",
                importance_score=55.0,
                reason=f"Normal operating density ({utilization:.1f}%); sufficient block headway buffers available"
            ))
        else:
            factors.append(DecisionFactor(
                factor="Section Utilization",
                value=round(utilization, 1),
                unit="%",
                impact="LOW",
                importance_score=30.0,
                reason=f"Light traffic density ({utilization:.1f}%); corridor capacity readily available"
            ))

        # 4. Waiting Train Count & Hold Duration
        hold_sec = int(recommendation.get("hold_duration_seconds", 0))
        waiting_count = int(traf.get("waiting_train_count", 0))
        if hold_sec > 0:
            factors.append(DecisionFactor(
                factor="Signal Hold Duration",
                value=hold_sec,
                unit="sec",
                impact="HIGH" if hold_sec >= 120 else "MEDIUM",
                importance_score=78.0,
                reason=f"Holding train at approach signal for {hold_sec}s creates mandatory safe headway clearance for leading movement"
            ))
        elif waiting_count > 2:
            factors.append(DecisionFactor(
                factor="Corridor Queue Depth",
                value=waiting_count,
                unit="trains",
                impact="HIGH",
                importance_score=80.0,
                reason=f"{waiting_count} trains currently queued in corridor; prioritized release clears approach throat"
            ))

        # 5. Conflict Severity
        train_confs = [
            c for c in confs
            if c.get("train1_id") == train_data.get("train_id") or
               c.get("train2_id") == train_data.get("train_id") or
               c.get("train_number") == train_data.get("train_number")
        ]
        if train_confs:
            top_conf = train_confs[0]
            severity = str(top_conf.get("severity", "WARNING")).upper()
            factors.append(DecisionFactor(
                factor="Conflict Resolution",
                value=severity,
                unit="level",
                impact="HIGH" if severity == "CRITICAL" else "MEDIUM",
                importance_score=95.0 if severity == "CRITICAL" else 75.0,
                reason=f"Directly resolves {severity.lower()} conflict ({top_conf.get('conflict_type', 'spacing')}) before block entry"
            ))

        # 6. Speed Profile & Margin
        current_spd = float(train_data.get("speed_kmph", 0.0))
        max_spd = float(sec.get("max_speed_kmph", sec.get("maximum_speed_kmph", 110.0)))
        rec_spd = float(recommendation.get("recommended_speed", current_spd or 80.0))
        if rec_spd < max_spd and recommendation.get("action") == "PROCEED":
            factors.append(DecisionFactor(
                factor="Dynamic Speed Regulation",
                value=round(rec_spd, 1),
                unit="km/h",
                impact="MEDIUM",
                importance_score=62.0,
                reason=f"Advising {rec_spd:.0f} km/h maintains steady flow without triggering red signal deceleration"
            ))

        # 7. Distance to Section / Route Progress
        pos_km = float(train_data.get("current_position_km", 0.0))
        dist_sec = float(train_data.get("distance_to_section_km", max(0.0, 15.0 - pos_km)))
        if dist_sec <= 3.0:
            factors.append(DecisionFactor(
                factor="Proximity to Entry Signal",
                value=round(dist_sec, 1),
                unit="km",
                impact="HIGH",
                importance_score=82.0,
                reason=f"Train is within {dist_sec:.1f} km of block boundary; immediate routing determination required"
            ))

        # Sort descending by importance score
        factors.sort(key=lambda x: -x.importance_score)
        return [f.to_dict() for f in factors]

