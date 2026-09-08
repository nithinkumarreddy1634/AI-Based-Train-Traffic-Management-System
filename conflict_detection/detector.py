"""
ConflictDetector: Main Coordinator for Conflict Detection, Tracking, and Congestion Analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from .conflict_types import Conflict, ConflictType, ConflictSeverity
from .conflict_rules import ConflictRulesEngine
from .predictor import ConflictResolutionTracker, AlertDeduplicator
from .service import CongestionService


class ConflictDetector:
    """Orchestrates comprehensive conflict evaluation and congestion tracking."""

    def __init__(self):
        self.tracker = ConflictResolutionTracker(max_history=200)
        self.deduplicator = AlertDeduplicator(cooldown_seconds=45.0)

    def scan(
        self,
        train_simulators: Dict[int, Any],
        sections: Dict[int, Any],
        tracks: Dict[int, Any],
        stations: Dict[int, Any],
        sim_time_seconds: float,
        section_utilization_map: Optional[Dict[int, float]] = None
    ) -> Dict[str, Any]:
        """
        Executes a full conflict scan across all active train agents and railway topology.
        Returns:
            {
                "active_conflicts": List[Dict],
                "resolved_conflicts": List[Dict],
                "new_conflicts": List[Conflict],
                "newly_resolved": List[Conflict],
                "congestion": List[Dict],
                "bottlenecks": List[Dict],
                "summary": Dict
            }
        """
        detected: List[Conflict] = []
        active_trains = [
            t for t in train_simulators.values()
            if getattr(t, "status", "") in ("RUNNING", "WAITING", "STOPPED", "DELAYED")
        ]

        # Group trains by section
        trains_by_section: Dict[int, List[Any]] = {}
        for t in active_trains:
            sec_id = getattr(t, "current_section_id", None)
            if sec_id is not None:
                trains_by_section.setdefault(sec_id, []).append(t)

        # 1. Section-level conflicts (Same Section, Rear-End, Opposite Direction, Headway)
        for sec_id, t_list in trains_by_section.items():
            sec_info = sections.get(sec_id, {})
            # Check if section has single track or shared line
            sec_tracks = [tr for tr in tracks.values() if tr.get("section_id") == sec_id]
            is_single_track = len(sec_tracks) == 1

            if len(t_list) >= 2:
                for i in range(len(t_list)):
                    for j in range(i + 1, len(t_list)):
                        t1, t2 = t_list[i], t_list[j]

                        # Rule 1: Same Section
                        same_sec_conf = ConflictRulesEngine.evaluate_same_section(
                            t1, t2, sec_id, sec_info, is_single_track=is_single_track
                        )
                        if same_sec_conf:
                            detected.append(same_sec_conf)

                        # Rule 2 & 5: Same direction (Rear-End or Insufficient Headway)
                        if t1.direction == t2.direction:
                            rear_conf = ConflictRulesEngine.evaluate_rear_end(
                                t1, t2, sec_id, sec_info
                            )
                            if rear_conf:
                                detected.append(rear_conf)
                            else:
                                headway_conf = ConflictRulesEngine.evaluate_insufficient_headway(
                                    t1, t2, sec_id, sec_info
                                )
                                if headway_conf:
                                    detected.append(headway_conf)

                        # Rule 3: Opposite direction (Head-On)
                        else:
                            opp_conf = ConflictRulesEngine.evaluate_opposite_direction(
                                t1, t2, sec_id, sec_info, is_single_track=is_single_track
                            )
                            if opp_conf:
                                detected.append(opp_conf)

        # 2. Junction Conflicts (Converging paths toward the same station throat)
        # Check trains approaching same destination or intermediate station within close proximity
        for i in range(len(active_trains)):
            for j in range(i + 1, len(active_trains)):
                t1, t2 = active_trains[i], active_trains[j]
                # Different sections but converging towards same next station
                if t1.current_section_id != t2.current_section_id and t1.current_section_id and t2.current_section_id:
                    sec1 = sections.get(t1.current_section_id, {})
                    sec2 = sections.get(t2.current_section_id, {})

                    # Identify target station for each train
                    target_stn_id_1 = sec1.get("end_station_id") if t1.direction == "UP" else sec1.get("start_station_id")
                    target_stn_id_2 = sec2.get("end_station_id") if t2.direction == "UP" else sec2.get("start_station_id")

                    if target_stn_id_1 and target_stn_id_1 == target_stn_id_2:
                        target_station = stations.get(target_stn_id_1, {})
                        # Calculate distance to station
                        stn_km = target_station.get("distance_from_source_km", 0.0)
                        dist1 = abs(t1.current_position_km - stn_km)
                        dist2 = abs(t2.current_position_km - stn_km)

                        if dist1 <= 5.0 and dist2 <= 5.0:
                            eta1 = (dist1 / max(t1.speed_kmph, 15.0)) * 3600.0
                            eta2 = (dist2 / max(t2.speed_kmph, 15.0)) * 3600.0
                            eta_diff = abs(eta1 - eta2)

                            if eta_diff <= 180.0:
                                junc_conf = ConflictRulesEngine.evaluate_junction(
                                    t1, t2, target_station, eta_diff, dist1, dist2
                                )
                                if junc_conf:
                                    detected.append(junc_conf)

        # Update resolution lifecycle
        newly_detected, newly_resolved = self.tracker.update(detected, sim_time_seconds)

        # 3. Section Congestion Analysis
        congestion_list = []
        util_map = section_utilization_map or {}
        for sec_id, sec_data in sections.items():
            trains_in_sec = trains_by_section.get(sec_id, [])
            util_pct = util_map.get(sec_id, 0.0)
            max_spd = float(sec_data.get("max_speed", 100.0))
            sec_congestion = CongestionService.analyze_section_congestion(
                section_id=sec_id,
                section_data=sec_data,
                trains_in_section=trains_in_sec,
                utilization_percent=util_pct,
                max_speed_kmph=max_spd
            )
            congestion_list.append(sec_congestion)

        # 4. Bottleneck Detection
        bottlenecks = CongestionService.calculate_bottlenecks(congestion_list)

        # Summary statistics
        active_list = self.tracker.get_all_active()
        critical_count = sum(1 for c in active_list if c.get("severity") == ConflictSeverity.CRITICAL.value)
        high_count = sum(1 for c in active_list if c.get("severity") == ConflictSeverity.HIGH.value)
        medium_count = sum(1 for c in active_list if c.get("severity") == ConflictSeverity.MEDIUM.value)
        low_count = sum(1 for c in active_list if c.get("severity") in (ConflictSeverity.LOW.value, ConflictSeverity.INFO.value))

        summary = {
            "total_active_conflicts": len(active_list),
            "critical_conflicts": critical_count,
            "high_conflicts": high_count,
            "medium_conflicts": medium_count,
            "low_conflicts": low_count,
            "total_resolved_conflicts": len(self.tracker.resolved_history),
            "critical_bottlenecks": sum(1 for b in bottlenecks if b.get("traffic_level") == "CRITICAL"),
            "elevated_bottlenecks": sum(1 for b in bottlenecks if b.get("traffic_level") == "ELEVATED"),
        }

        return {
            "active_conflicts": active_list,
            "resolved_conflicts": self.tracker.get_history(),
            "new_conflicts": newly_detected,
            "newly_resolved": newly_resolved,
            "congestion": congestion_list,
            "bottlenecks": bottlenecks,
            "summary": summary,
        }

    def reset(self):
        self.tracker.reset()
        self.deduplicator.clear()


conflict_detector = ConflictDetector()

