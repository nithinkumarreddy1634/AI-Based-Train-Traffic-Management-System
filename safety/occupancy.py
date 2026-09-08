"""
Track, Section, and Opposite-Direction Occupancy Validator.

Validates:
1. Track Availability: Checks target track is not occupied by another train, blocked, or under maintenance.
2. Section Capacity: Ensures concurrent occupancy does not exceed section track count.
3. Opposite-Direction Mutex: Prevents simultaneous opposing movements on single-track lines.
"""
from typing import List, Dict, Any, Tuple, Optional, Set
from safety.config import SafetyConfig, DEFAULT_SAFETY_CONFIG
from safety.result import SafetyViolation, SafetyWarning
from safety.rules import (
    RULE_TRACK_OCCUPANCY,
    RULE_SECTION_OCCUPANCY,
    RULE_OPPOSITE_DIRECTION
)


class OccupancyValidator:
    """Validates physical track reservations and mutual exclusion safety."""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or DEFAULT_SAFETY_CONFIG

    def validate_track_availability(
        self,
        schedule_entries: List[Dict[str, Any]],
        network_tracks: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Check that assigned target tracks are not currently occupied, blocked, or under maintenance.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        if not network_tracks:
            return (violations, warnings)

        for entry in schedule_entries:
            train_num = entry.get("train_number", f"T{entry.get('train_id')}")
            track_id = entry.get("target_track_id") or entry.get("occupied_track_id") or entry.get("track_id")

            if not track_id:
                continue

            track_info = network_tracks.get(track_id)
            if not track_info:
                continue

            track_num = track_info.get("track_number", str(track_id))
            track_status = str(track_info.get("status", "AVAILABLE")).upper()
            occupant = track_info.get("occupied_by_train") or track_info.get("occupied_by_train_id")

            # Check if track is blocked or in maintenance
            if track_status == "BLOCKED":
                violations.append(SafetyViolation(
                    rule=RULE_TRACK_OCCUPANCY,
                    severity="CRITICAL",
                    message=f"Train {train_num} routed to Track {track_num} which is marked BLOCKED.",
                    train_numbers=[train_num],
                    details={"track_id": track_id, "track_number": track_num, "status": "BLOCKED"}
                ))
            elif track_status == "MAINTENANCE":
                violations.append(SafetyViolation(
                    rule=RULE_TRACK_OCCUPANCY,
                    severity="CRITICAL",
                    message=f"Train {train_num} routed to Track {track_num} which is under active MAINTENANCE.",
                    train_numbers=[train_num],
                    details={"track_id": track_id, "track_number": track_num, "status": "MAINTENANCE"}
                ))
            elif track_status == "OCCUPIED" and occupant and occupant != entry.get("train_id"):
                # Track occupied by a DIFFERENT train
                violations.append(SafetyViolation(
                    rule=RULE_TRACK_OCCUPANCY,
                    severity="CRITICAL",
                    message=(
                        f"Track collision conflict: Train {train_num} assigned to Track {track_num} "
                        f"which is already occupied by Train ID {occupant}."
                    ),
                    train_numbers=[train_num, f"T{occupant}"],
                    details={"track_id": track_id, "track_number": track_num, "occupant_id": occupant}
                ))

        return (violations, warnings)

    def validate_section_capacity(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Verify that the number of simultaneously dwelling/transiting trains does not exceed track count.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        if len(schedule_entries) < 2:
            return (violations, warnings)

        sec_data = section_info or {}
        is_single = bool(sec_data.get("is_single_track", False))
        tracks = int(sec_data.get("track_count") or sec_data.get("num_tracks") or (1 if is_single else 2))
        sec_len = float(sec_data.get("length_km") or sec_data.get("section_length_km") or 15.0)
        sec_name = sec_data.get("section_name", "Corridor Section")

        # Block signaling allows multiple trains spaced by signal blocks along multi-km sections
        has_block_signaling = sec_data.get("block_signaling", True)
        if "capacity" in sec_data:
            max_capacity = int(sec_data["capacity"])
        elif has_block_signaling and sec_len >= 2.0:
            blocks_per_track = max(1, int(sec_len / 2.5))
            max_capacity = tracks * blocks_per_track
        else:
            max_capacity = tracks

        # Find maximum concurrent overlap
        time_events: List[Tuple[int, str, str]] = []
        for entry in schedule_entries:
            t_num = entry.get("train_number", f"T{entry.get('train_id')}")
            s_time = int(entry.get("entry_time_sec", 0))
            dur = int(entry.get("transit_duration_sec", 600))
            e_time = s_time + dur
            time_events.append((s_time, "ENTER", t_num))
            time_events.append((e_time, "EXIT", t_num))

        time_events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))

        current_trains: Set[str] = set()
        max_concurrent: int = 0
        peak_trains: List[str] = []

        for t_sec, ev_type, t_num in time_events:
            if ev_type == "ENTER":
                current_trains.add(t_num)
                if len(current_trains) > max_concurrent:
                    max_concurrent = len(current_trains)
                    peak_trains = list(current_trains)
            else:
                current_trains.discard(t_num)

        if max_concurrent > max_capacity:
            violations.append(SafetyViolation(
                rule=RULE_SECTION_OCCUPANCY,
                severity="HIGH",
                message=(
                    f"Section capacity exceeded on {sec_name}: "
                    f"{max_concurrent} trains ({', '.join(peak_trains)}) simultaneously scheduled "
                    f"in section with physical capacity of {max_capacity} train(s)."
                ),
                train_numbers=peak_trains,
                section_name=sec_name,
                details={"max_capacity": max_capacity, "concurrent_trains": max_concurrent}
            ))

        return (violations, warnings)

    def validate_opposite_direction(
        self,
        schedule_entries: List[Dict[str, Any]],
        section_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SafetyViolation], List[SafetyWarning]]:
        """
        Detect head-on / opposing direction approach on single-track lines.
        """
        violations: List[SafetyViolation] = []
        warnings: List[SafetyWarning] = []

        sec_data = section_info or {}
        is_single_track = bool(sec_data.get("is_single_track", False))
        sec_name = sec_data.get("section_name", "Section")

        if not is_single_track or len(schedule_entries) < 2:
            return (violations, warnings)

        for i in range(len(schedule_entries)):
            for j in range(i + 1, len(schedule_entries)):
                t1 = schedule_entries[i]
                t2 = schedule_entries[j]

                dir1 = t1.get("direction", "UP").upper()
                dir2 = t2.get("direction", "UP").upper()

                if dir1 != dir2:
                    t1_s = int(t1.get("entry_time_sec", 0))
                    t1_e = t1_s + int(t1.get("transit_duration_sec", 600))

                    t2_s = int(t2.get("entry_time_sec", 0))
                    t2_e = t2_s + int(t2.get("transit_duration_sec", 600))

                    # Check temporal interval overlap: [t1_s, t1_e] overlaps [t2_s, t2_e]
                    if max(t1_s, t2_s) < min(t1_e, t2_e):
                        t1_num = t1.get("train_number", f"T{t1.get('train_id')}")
                        t2_num = t2.get("train_number", f"T{t2.get('train_id')}")
                        conflict_start = max(t1_s, t2_s)
                        conflict_end = min(t1_e, t2_e)

                        violations.append(SafetyViolation(
                            rule=RULE_OPPOSITE_DIRECTION,
                            severity="CRITICAL",
                            message=(
                                f"Catastrophic head-on collision hazard on single-track {sec_name}: "
                                f"Train {t1_num} ({dir1}) and Train {t2_num} ({dir2}) scheduled for concurrent "
                                f"opposing occupancy during window [{conflict_start}s, {conflict_end}s]."
                            ),
                            train_numbers=[t1_num, t2_num],
                            section_name=sec_name,
                            details={
                                "train_1": t1_num,
                                "direction_1": dir1,
                                "window_1": [t1_s, t1_e],
                                "train_2": t2_num,
                                "direction_2": dir2,
                                "window_2": [t2_s, t2_e],
                                "conflict_overlap_seconds": conflict_end - conflict_start,
                                "section": sec_name
                            }
                        ))

        return (violations, warnings)
