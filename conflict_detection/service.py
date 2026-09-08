"""
Section Congestion Analysis and Rule-Based Bottleneck Detection Service.
Provides transparent scoring and explainable congestion metrics for railway sections.
"""

from typing import Dict, List, Any, Optional
from .conflict_types import CongestionLevel


class CongestionService:
    """Analyzes corridor traffic flow, section congestion levels, and bottleneck scores."""

    @staticmethod
    def analyze_section_congestion(
        section_id: int,
        section_data: Dict[str, Any],
        trains_in_section: List[Any],
        utilization_percent: float,
        max_speed_kmph: float
    ) -> Dict[str, Any]:
        """
        Evaluates congestion metrics for a single section:
        - active_train_count
        - waiting_train_count
        - average_speed_kmph
        - speed_drop_percent
        - congestion_level (LOW, MODERATE, HIGH, CRITICAL)
        """
        active_count = len(trains_in_section)
        waiting_count = sum(1 for t in trains_in_section if getattr(t, "status", "") in ("WAITING", "STOPPED"))
        
        if active_count > 0:
            avg_speed = sum(getattr(t, "speed_kmph", 0.0) for t in trains_in_section) / active_count
        else:
            avg_speed = max_speed_kmph

        max_spd = max(1.0, max_speed_kmph)
        speed_drop_pct = max(0.0, round(((max_spd - avg_speed) / max_spd) * 100.0, 1))

        # Classify congestion level
        if waiting_count >= 2 or (active_count >= 2 and utilization_percent >= 80.0):
            level = CongestionLevel.CRITICAL
        elif waiting_count >= 1 or (active_count >= 2 and speed_drop_pct >= 40.0) or utilization_percent >= 60.0:
            level = CongestionLevel.HIGH
        elif active_count >= 1 or utilization_percent >= 30.0:
            level = CongestionLevel.MODERATE
        else:
            level = CongestionLevel.LOW

        return {
            "section_id": section_id,
            "section_name": section_data.get("name", f"Section {section_id}"),
            "length_km": section_data.get("length_km", 0.0),
            "max_speed_kmph": max_speed_kmph,
            "active_train_count": active_count,
            "waiting_train_count": waiting_count,
            "average_speed_kmph": round(avg_speed, 1),
            "speed_drop_percent": speed_drop_pct,
            "utilization_percent": round(utilization_percent, 1),
            "congestion_level": level.value,
            "train_numbers": [getattr(t, "train_number", "") for t in trains_in_section],
        }

    @classmethod
    def calculate_bottlenecks(
        cls,
        congestion_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transparent multi-criteria bottleneck ranking:
        Score = 0.30 * Density + 0.30 * Waiting + 0.25 * Utilization + 0.15 * SpeedDrop
        Output ranked 0 to 100 with explainable text breakdown.
        """
        scored_sections = []

        for item in congestion_data:
            sec_id = item["section_id"]
            sec_name = item["section_name"]
            active_cnt = item["active_train_count"]
            wait_cnt = item["waiting_train_count"]
            util_pct = item["utilization_percent"]
            speed_drop = item["speed_drop_percent"]
            avg_speed = item["average_speed_kmph"]

            # 1. Density score (capped at 100)
            density_score = min(100.0, active_cnt * 50.0)

            # 2. Waiting train score
            waiting_score = min(100.0, wait_cnt * 50.0)

            # 3. Utilization score (0 - 100)
            utilization_score = min(100.0, util_pct)

            # 4. Speed degradation score (0 - 100)
            speed_drop_score = min(100.0, speed_drop)

            # Composite weighted formula
            bottleneck_score = (
                (0.30 * density_score) +
                (0.30 * waiting_score) +
                (0.25 * utilization_score) +
                (0.15 * speed_drop_score)
            )
            bottleneck_score = round(bottleneck_score, 1)

            # Generate natural language explanation
            reasons = []
            if wait_cnt > 0:
                reasons.append(f"{wait_cnt} train(s) queued/waiting")
            if util_pct >= 60.0:
                reasons.append(f"high capacity utilization ({util_pct:.1f}%)")
            if speed_drop >= 30.0:
                reasons.append(f"significant speed drop ({speed_drop:.1f}% below limit)")
            if active_cnt >= 2:
                reasons.append(f"{active_cnt} active concurrent trains")

            explanation = "; ".join(reasons) if reasons else "Nominal operating conditions"

            # Recommended mitigation
            if bottleneck_score >= 70.0:
                recommendation = "High Priority: stagger departures or divert freight traffic to alternate loop"
                traffic_level = "CRITICAL"
            elif bottleneck_score >= 45.0:
                recommendation = "Medium: regulate approach speeds to prevent queuing at entry block"
                traffic_level = "ELEVATED"
            else:
                recommendation = "Low: corridor throughput within designed tolerance"
                traffic_level = "NORMAL"

            scored_sections.append({
                "section_id": sec_id,
                "section_name": sec_name,
                "bottleneck_score": bottleneck_score,
                "traffic_level": traffic_level,
                "active_train_count": active_cnt,
                "waiting_train_count": wait_cnt,
                "utilization": util_pct,
                "average_speed": avg_speed,
                "speed_drop_percent": speed_drop,
                "explanation": explanation,
                "recommendation": recommendation,
                "factors": {
                    "density_score": density_score,
                    "waiting_score": waiting_score,
                    "utilization_score": utilization_score,
                    "speed_drop_score": speed_drop_score,
                }
            })

        # Sort by bottleneck_score descending
        scored_sections.sort(key=lambda x: x["bottleneck_score"], reverse=True)
        return scored_sections

