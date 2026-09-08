"""
Train Simulator Agent.
Models individual train behavior, state transitions, station dwelling, and cumulative delay.
"""

from typing import Dict, Any, Optional, List
from .config import config
from .movement import calculate_motion
from .state_manager import state_manager
from .route_manager import route_manager


class TrainSimulator:
    """Simulates an individual train's physics, schedule adherence, and lifecycle."""

    def __init__(self, data: Dict[str, Any]):
        self.train_id: int = data["train_id"]
        self.train_number: str = data["train_number"]
        self.train_name: str = data["train_name"]
        self.train_type: str = data["train_type"]
        self.priority: str = data["priority"]

        self.source_station_id: int = data["source_station_id"]
        self.destination_station_id: int = data["destination_station_id"]
        self.current_station_id: Optional[int] = data.get("current_station_id")
        self.current_section_id: Optional[int] = data.get("current_section_id")

        self.current_position_km: float = float(data.get("current_position_km", 0.0))
        self.speed_kmph: float = float(data.get("speed_kmph", 0.0))
        self.direction: str = data.get("direction", "UP")
        self.status: str = data.get("status", "SCHEDULED")
        self.current_delay_minutes: float = float(data.get("current_delay_minutes", 0.0))

        # Internal simulation states
        self.dwell_time_remaining_s: float = 0.0
        self.waiting_time_s: float = 0.0
        self.is_completed: bool = (self.status == "ARRIVED")
        self.completion_time_s: Optional[float] = None
        self.scheduled_stops: List[int] = []

        # Phase 6: ML Delay Prediction state
        self.predicted_delay_minutes: float = self.current_delay_minutes
        self.expected_additional_delay: float = 0.0
        self.last_prediction_time: Optional[str] = None

        # Phase 7: AI Traffic Optimization advisory states
        self.hold_until_sim_time_s: float = 0.0
        self.advisory_action: str = "PROCEED"
        self.advisory_reason: Optional[str] = None

    def set_scheduled_stops(self, stops: List[int]):
        self.scheduled_stops = stops

    def step(self, dt: float, sim_time_s: float) -> List[Dict[str, Any]]:
        """
        Advances the train simulation by delta seconds `dt`.
        Returns a list of event dictionaries generated during this step.
        """
        events: List[Dict[str, Any]] = []

        if self.status == "ARRIVED":
            return events

        # Handle SCHEDULED trains ready to depart
        if self.status == "SCHEDULED":
            # Check if source track/first section can be reserved
            first_section_id = route_manager.get_next_section(self, None)
            if first_section_id:
                track_id = state_manager.find_available_track_in_section(first_section_id, self.direction)
                if track_id and state_manager.reserve_track(track_id, self.train_id):
                    self.current_section_id = first_section_id
                    self.current_station_id = None
                    self.current_position_km = 0.0
                    self.status = "RUNNING"
                    events.append({
                        "event_type": "TRAIN_STARTED",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} departed origin for {route_manager.sections[first_section_id]['name']}",
                    })
                else:
                    self.status = "WAITING"
                    events.append({
                        "event_type": "TRAIN_WAITING",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} waiting for departure clearance on section {first_section_id}",
                    })
            return events

        # Handle WAITING trains trying to acquire the next section track
        if self.status == "WAITING":
            self.waiting_time_s += dt
            self.current_delay_minutes = round(self.current_delay_minutes + (dt / 60.0), 1)

            # If train has an active optimization hold order, remain in waiting
            if sim_time_s < self.hold_until_sim_time_s:
                return events

            next_sec_id = route_manager.get_next_section(self, self.current_section_id)
            if next_sec_id:
                track_id = state_manager.find_available_track_in_section(next_sec_id, self.direction)
                if track_id and state_manager.reserve_track(track_id, self.train_id):
                    # Free previous track
                    state_manager.release_track(self.train_id)
                    # Re-reserve new track
                    state_manager.reserve_track(track_id, self.train_id)

                    self.current_section_id = next_sec_id
                    self.current_position_km = 0.0
                    self.status = "RUNNING"
                    events.append({
                        "event_type": "TRAIN_RESUMED",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} resumed movement into {route_manager.sections[next_sec_id]['name']}",
                    })
            return events

        # Handle STOPPED trains (station dwell countdown)
        if self.status == "STOPPED":
            self.dwell_time_remaining_s = max(0.0, self.dwell_time_remaining_s - dt)
            if self.dwell_time_remaining_s <= 0.0:
                # Dwell complete: Check if destination or advance to next section
                if self.current_station_id == self.destination_station_id:
                    self.status = "ARRIVED"
                    self.speed_kmph = 0.0
                    self.is_completed = True
                    self.completion_time_s = sim_time_s
                    state_manager.release_track(self.train_id)
                    events.append({
                        "event_type": "TRAIN_ARRIVED",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} reached final destination Station {self.destination_station_id}",
                    })
                else:
                    next_sec_id = route_manager.get_next_section(self, self.current_section_id)
                    if next_sec_id:
                        track_id = state_manager.find_available_track_in_section(next_sec_id, self.direction)
                        if track_id and state_manager.reserve_track(track_id, self.train_id):
                            state_manager.release_track(self.train_id)
                            state_manager.reserve_track(track_id, self.train_id)
                            self.current_section_id = next_sec_id
                            self.current_station_id = None
                            self.current_position_km = 0.0
                            self.status = "RUNNING"
                            events.append({
                                "event_type": "TRAIN_RESUMED",
                                "train_id": self.train_id,
                                "train_number": self.train_number,
                                "message": f"{self.train_number} departed station stop into {route_manager.sections[next_sec_id]['name']}",
                            })
                        else:
                            self.status = "WAITING"
                            events.append({
                                "event_type": "TRAIN_WAITING",
                                "train_id": self.train_id,
                                "train_number": self.train_number,
                                "message": f"{self.train_number} held at station: next section {next_sec_id} occupied",
                            })
            return events

        # Handle RUNNING / DELAYED trains moving along a section
        if self.status in ("RUNNING", "DELAYED"):
            sec_info = route_manager.sections.get(self.current_section_id or -1)
            if not sec_info:
                return events

            sec_length = sec_info["length_km"]
            max_sec_speed = sec_info["max_speed"]

            # Check if approaching end of section where a stop is required
            next_station_id = route_manager.get_destination_station_for_section(
                self.current_section_id,
                self.source_station_id,
            )
            is_stop = (next_station_id in self.scheduled_stops) or (next_station_id == self.destination_station_id)

            new_speed, new_pos, reached_end = calculate_motion(
                current_speed_kmph=self.speed_kmph,
                current_pos_km=self.current_position_km,
                section_length_km=sec_length,
                train_type=self.train_type,
                max_section_speed_kmph=max_sec_speed,
                dt_seconds=dt,
                is_approaching_stop=is_stop,
            )

            self.speed_kmph = new_speed
            self.current_position_km = new_pos

            if reached_end:
                # Train has arrived at the end station of this section
                exit_station_id = sec_info["end_station_id"] if self.direction == "UP" else sec_info["start_station_id"]
                self.current_station_id = exit_station_id

                events.append({
                    "event_type": "TRAIN_LEFT_SECTION",
                    "train_id": self.train_id,
                    "train_number": self.train_number,
                    "message": f"{self.train_number} completed {sec_info['name']}",
                })

                # Check if this station is the final destination
                if exit_station_id == self.destination_station_id:
                    self.status = "ARRIVED"
                    self.speed_kmph = 0.0
                    self.is_completed = True
                    self.completion_time_s = sim_time_s
                    state_manager.release_track(self.train_id)
                    events.append({
                        "event_type": "TRAIN_ARRIVED",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} arrived at final destination {route_manager.stations[exit_station_id]['name']}",
                    })
                    return events

                # Check if this station is a scheduled intermediate stop
                if exit_station_id in self.scheduled_stops:
                    self.status = "STOPPED"
                    self.speed_kmph = 0.0
                    self.dwell_time_remaining_s = config.DWELL_TIMES_BY_TYPE.get(self.train_type, 30.0)
                    events.append({
                        "event_type": "TRAIN_STOPPED",
                        "train_id": self.train_id,
                        "train_number": self.train_number,
                        "message": f"{self.train_number} stopped at {route_manager.stations[exit_station_id]['name']} for dwell ({int(self.dwell_time_remaining_s)}s)",
                    })
                    return events

                # Otherwise, try transitioning immediately into next section
                next_sec_id = route_manager.get_next_section(self, self.current_section_id)
                if next_sec_id:
                    track_id = state_manager.find_available_track_in_section(next_sec_id, self.direction)
                    if track_id and state_manager.reserve_track(track_id, self.train_id):
                        state_manager.release_track(self.train_id)
                        state_manager.reserve_track(track_id, self.train_id)
                        self.current_section_id = next_sec_id
                        self.current_station_id = None
                        self.current_position_km = 0.0
                        self.status = "RUNNING"
                        events.append({
                            "event_type": "TRAIN_ENTERED_SECTION",
                            "train_id": self.train_id,
                            "train_number": self.train_number,
                            "message": f"{self.train_number} entered {route_manager.sections[next_sec_id]['name']}",
                        })
                    else:
                        self.status = "WAITING"
                        self.speed_kmph = 0.0
                        events.append({
                            "event_type": "TRAIN_WAITING",
                            "train_id": self.train_id,
                            "train_number": self.train_number,
                            "message": f"{self.train_number} waiting: next section {next_sec_id} occupied",
                        })
                else:
                    # No further section: arrive
                    self.status = "ARRIVED"
                    self.speed_kmph = 0.0
                    self.is_completed = True
                    self.completion_time_s = sim_time_s
                    state_manager.release_track(self.train_id)

        return events

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current simulator agent state."""
        sec_info = route_manager.sections.get(self.current_section_id, {}) if self.current_section_id else {}
        sec_name = sec_info.get("name")
        sec_len = sec_info.get("length_km", 20.0)

        src_name = route_manager.stations.get(self.source_station_id, {}).get("name")
        st_name = route_manager.stations.get(self.current_station_id, {}).get("name") if self.current_station_id else None
        dest_name = route_manager.stations.get(self.destination_station_id, {}).get("name") if self.destination_station_id else None
        next_sec_id = route_manager.get_next_section(self, self.current_section_id)
        next_st_name = None
        if next_sec_id:
            dest_st_id = route_manager.get_destination_station_for_section(next_sec_id, self.source_station_id)
            next_st_name = route_manager.stations.get(dest_st_id, {}).get("name")

        # Speed limits
        train_max = config.TRAIN_MAX_SPEED_BY_TYPE.get(self.train_type, 110.0)
        sec_max = sec_info.get("max_speed", train_max)
        max_permitted_speed = min(train_max, sec_max)

        # Section progress percentage
        if self.status == "ARRIVED":
            section_progress_pct = 100.0
        elif self.current_section_id and sec_len > 0:
            section_progress_pct = round(min(100.0, max(0.0, (self.current_position_km / sec_len) * 100.0)), 1)
        else:
            section_progress_pct = 0.0

        # Calculate remaining route distance
        route = route_manager.get_route_for_train(self)
        remaining_km = 0.0
        if self.status == "ARRIVED":
            remaining_km = 0.0
        elif route:
            if self.current_section_id in route:
                curr_idx = route.index(self.current_section_id)
                remaining_km += max(0.0, sec_len - self.current_position_km)
                for s_id in route[curr_idx + 1:]:
                    remaining_km += route_manager.sections.get(s_id, {}).get("length_km", 20.0)
            else:
                for s_id in route:
                    remaining_km += route_manager.sections.get(s_id, {}).get("length_km", 20.0)
        remaining_km = round(remaining_km, 1)

        # Route stations and journey progress flags
        all_route_stations = route_manager.get_ordered_stations_for_train(self)
        current_st_id = self.current_station_id
        passed_current = False
        route_stations_state = []

        for st in all_route_stations:
            sid = st["station_id"]
            is_cur = False
            is_vis = False
            is_up = False

            if self.status == "ARRIVED":
                is_vis = True
                if sid == self.destination_station_id:
                    is_cur = True
            elif current_st_id is not None and sid == current_st_id:
                is_cur = True
                passed_current = True
            elif self.current_section_id:
                # If moving in section, check if section connects from this station
                sec_start = sec_info.get("start_station_id")
                sec_end = sec_info.get("end_station_id")
                if sid == sec_start or sid == sec_end:
                    # In between
                    if not passed_current:
                        is_vis = True
                    else:
                        is_up = True
                elif not passed_current:
                    is_vis = True
                else:
                    is_up = True
            else:
                if sid == self.source_station_id:
                    is_cur = True
                    passed_current = True
                elif not passed_current:
                    is_vis = True
                else:
                    is_up = True

            route_stations_state.append({
                "station_id": sid,
                "station_code": st["station_code"],
                "station_name": st["station_name"],
                "is_visited": is_vis,
                "is_current": is_cur,
                "is_upcoming": is_up,
            })

        return {
            "train_id": self.train_id,
            "train_number": self.train_number,
            "train_name": self.train_name,
            "train_type": self.train_type,
            "priority": self.priority,
            "source_station_id": self.source_station_id,
            "source_station_name": src_name,
            "destination_station_id": self.destination_station_id,
            "destination_station_name": dest_name,
            "current_station_id": self.current_station_id,
            "current_station_name": st_name,
            "current_section_id": self.current_section_id,
            "current_section_name": sec_name,
            "current_position_km": round(self.current_position_km, 2),
            "speed_kmph": round(self.speed_kmph, 1),
            "max_speed_kmph": max_permitted_speed,
            "direction": self.direction,
            "status": self.status,
            "current_delay_minutes": round(self.current_delay_minutes, 1),
            "predicted_delay_minutes": round(self.predicted_delay_minutes, 1),
            "expected_additional_delay": round(self.expected_additional_delay, 1),
            "last_prediction_time": self.last_prediction_time,
            "next_station_name": next_st_name,
            "occupied_track_id": state_manager.get_occupied_track_for_train(self.train_id),
            "section_length_km": sec_len,
            "section_progress_pct": section_progress_pct,
            "remaining_distance_km": remaining_km,
            "route_stations": route_stations_state,
            "advisory_action": self.advisory_action,
            "advisory_reason": self.advisory_reason,
            "hold_until_sim_time_s": self.hold_until_sim_time_s,
        }

