"""
Central Simulation Engine.
Orchestrates the discrete simulation loop, clock, state stepping, event logging, WebSocket distribution, and database persistence.
"""

import asyncio
import datetime
import time
from typing import Dict, List, Any, Optional, Set
from collections import deque
from fastapi import WebSocket

from .config import config
from .state_manager import state_manager
from .route_manager import route_manager
from .train_simulator import TrainSimulator
from conflict_detection import conflict_detector
from ml.models.predict import delay_prediction_service


class SimulationEngine:
    """Singleton simulation engine coordinating train agents and real-time streaming."""

    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = False
        self.speed_multiplier: float = config.DEFAULT_SPEED_MULTIPLIER

        self.sim_time_seconds: float = 0.0
        self.tick_count: int = 0
        self.completed_trains_count: int = 0

        self.train_simulators: Dict[int, TrainSimulator] = {}
        self.event_log: deque = deque(maxlen=config.MAX_EVENT_LOG_SIZE)
        self.alerts_log: deque = deque(maxlen=100)
        self.section_occupied_seconds: Dict[int, float] = {}
        self.websocket_clients: Set[WebSocket] = set()

        self._loop_task: Optional[asyncio.Task] = None
        self._initial_train_data: List[Dict[str, Any]] = []
        self._alert_id_seq: int = 0
        self._notified_delay_trains: Set[int] = set()
        self.last_conflict_scan_result: Dict[str, Any] = {}

    @property
    def is_ready(self) -> bool:
        return bool(self.train_simulators)


    def initialize(self, stations: List[Any], sections: List[Any], tracks: List[Any], trains: List[Any], schedules: List[Any]):
        """Initializes simulation infrastructure from database models."""
        self.is_running = False
        self.is_paused = False
        self.sim_time_seconds = 0.0
        self.tick_count = 0
        self.completed_trains_count = 0
        self.last_conflict_scan_result = {}
        conflict_detector.reset()

        route_manager.build_network_graph(stations, sections, schedules)
        state_manager.initialize_tracks(tracks)

        self._initial_train_data = []
        self.train_simulators.clear()
        self.event_log.clear()
        self.alerts_log.clear()
        self._alert_id_seq = 0
        self._notified_delay_trains.clear()
        self.section_occupied_seconds = {
            s["id"]: 0.0 for s in route_manager.sections.values()
        }

        # Build schedule stops map: train_id -> list of station_ids
        schedules_by_train: Dict[int, List[int]] = {}
        for sc in schedules:
            t_id = sc.train_id if hasattr(sc, "train_id") else sc["train_id"]
            st_id = sc.station_id if hasattr(sc, "station_id") else sc["station_id"]
            schedules_by_train.setdefault(t_id, []).append(st_id)

        for tr in trains:
            t_data = {
                "train_id": tr.train_id if hasattr(tr, "train_id") else tr["train_id"],
                "train_number": tr.train_number if hasattr(tr, "train_number") else tr["train_number"],
                "train_name": tr.train_name if hasattr(tr, "train_name") else tr["train_name"],
                "train_type": tr.train_type if hasattr(tr, "train_type") else tr["train_type"],
                "priority": tr.priority if hasattr(tr, "priority") else tr["priority"],
                "source_station_id": tr.source_station_id if hasattr(tr, "source_station_id") else tr["source_station_id"],
                "destination_station_id": tr.destination_station_id if hasattr(tr, "destination_station_id") else tr["destination_station_id"],
                "current_station_id": tr.current_station_id if hasattr(tr, "current_station_id") else tr.get("current_station_id"),
                "current_section_id": tr.current_section_id if hasattr(tr, "current_section_id") else tr.get("current_section_id"),
                "current_position_km": float(tr.current_position_km if hasattr(tr, "current_position_km") else tr.get("current_position_km", 0.0)),
                "speed_kmph": float(tr.speed_kmph if hasattr(tr, "speed_kmph") else tr.get("speed_kmph", 0.0)),
                "direction": tr.direction if hasattr(tr, "direction") else tr.get("direction", "UP"),
                "status": tr.status if hasattr(tr, "status") else tr.get("status", "SCHEDULED"),
                "current_delay_minutes": float(tr.current_delay_minutes if hasattr(tr, "current_delay_minutes") else tr.get("current_delay_minutes", 0.0)),
            }
            self._initial_train_data.append(dict(t_data))
            agent = TrainSimulator(t_data)
            agent.set_scheduled_stops(schedules_by_train.get(agent.train_id, []))
            self.train_simulators[agent.train_id] = agent

        self._record_event("SIMULATION_INITIALIZED", None, None, "Simulation engine initialized with corridor network.")

    def start(self):
        """Starts the background simulation loop."""
        if self.is_running and not self.is_paused:
            return

        self.is_running = True
        self.is_paused = False
        try:
            loop = asyncio.get_running_loop()
            if not self._loop_task or self._loop_task.done():
                self._loop_task = loop.create_task(self._tick_loop())
        except RuntimeError:
            # Fallback if invoked outside an active event loop thread
            pass
        self._record_event("SIMULATION_STARTED", None, None, f"Simulation started at {self.speed_multiplier}x speed.")

    def pause(self):
        """Pauses the simulation loop without resetting states."""
        if not self.is_running or self.is_paused:
            return
        self.is_paused = True
        self._record_event("SIMULATION_PAUSED", None, None, "Simulation paused.")

    def resume(self):
        """Resumes a paused simulation."""
        if not self.is_running or not self.is_paused:
            return
        self.is_paused = False
        self._record_event("SIMULATION_RESUMED", None, None, "Simulation resumed.")

    def stop(self):
        """Stops the background simulation loop without resetting agents."""
        self.is_running = False
        self.is_paused = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
        self._record_event("SIMULATION_STOPPED", None, None, "Simulation stopped.")

    def reset(self, stations: List[Any], sections: List[Any], tracks: List[Any], trains: List[Any], schedules: List[Any]):
        """Stops the loop and resets all agents back to initial state."""
        self.is_running = False
        self.is_paused = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
        self.initialize(stations, sections, tracks, trains, schedules)
        self._record_event("SIMULATION_RESET", None, None, "Simulation reset to initial scenario baseline.")

    def set_speed_multiplier(self, multiplier: float) -> bool:
        if multiplier in config.ALLOWED_SPEED_MULTIPLIERS:
            self.speed_multiplier = float(multiplier)
            self._record_event("SPEED_CHANGED", None, None, f"Simulation speed changed to {multiplier}x.")
            return True
        return False

    @property
    def formatted_sim_time(self) -> str:
        """Returns elapsed simulation time formatted as HH:MM:SS."""
        total_seconds = int(self.sim_time_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def throughput_trains_per_hour(self) -> float:
        """Calculates completed train arrivals per simulation hour."""
        if self.sim_time_seconds <= 0:
            return 0.0
        hours = self.sim_time_seconds / 3600.0
        return round(self.completed_trains_count / hours, 2)

    def _record_event(self, event_type: str, train_id: Optional[int], train_number: Optional[str], message: str):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": now_str,
            "sim_time": self.formatted_sim_time,
            "event_type": event_type,
            "train_id": train_id,
            "train_number": train_number,
            "message": message,
        }
        self.event_log.appendleft(entry)

    def _record_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        train_number: Optional[str] = None,
        section_name: Optional[str] = None,
    ):
        self._alert_id_seq += 1
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "id": self._alert_id_seq,
            "timestamp": now_str,
            "sim_time": self.formatted_sim_time,
            "alert_type": alert_type,
            "severity": severity,  # "INFO", "WARNING", "CRITICAL"
            "train_number": train_number,
            "section_name": section_name,
            "message": message,
        }
        self.alerts_log.appendleft(entry)

    async def _tick_loop(self):
        """Asynchronous execution loop ticking train physics."""
        try:
            while self.is_running:
                if not self.is_paused:
                    dt = config.TICK_INTERVAL_SECONDS * self.speed_multiplier
                    self.sim_time_seconds += dt
                    self.tick_count += 1

                    # Track cumulative section occupancy duration
                    for sec_id in route_manager.sections.keys():
                        if state_manager.is_section_occupied(sec_id):
                            self.section_occupied_seconds[sec_id] = (
                                self.section_occupied_seconds.get(sec_id, 0.0) + dt
                            )

                    # Step each train agent
                    completed_now = 0
                    for train_agent in self.train_simulators.values():
                        was_completed = train_agent.is_completed
                        step_events = train_agent.step(dt, self.sim_time_seconds)
                        for ev in step_events:
                            ev_type = ev["event_type"]
                            self._record_event(
                                ev_type,
                                ev.get("train_id"),
                                ev.get("train_number"),
                                ev["message"],
                            )

                            # Map events to dispatcher alerts
                            t_num = ev.get("train_number")
                            if ev_type == "TRAIN_WAITING":
                                self._record_alert(
                                    "TRAIN_WAITING",
                                    "WARNING",
                                    ev["message"],
                                    train_number=t_num,
                                )
                            elif ev_type == "TRAIN_ARRIVED":
                                self._record_alert(
                                    "TRAIN_ARRIVED",
                                    "INFO",
                                    ev["message"],
                                    train_number=t_num,
                                )
                            elif ev_type == "TRAIN_STOPPED":
                                self._record_alert(
                                    "TRAIN_STOPPED",
                                    "INFO",
                                    ev["message"],
                                    train_number=t_num,
                                )

                        # Alert on significant delay accrual
                        if train_agent.current_delay_minutes >= 5.0 and train_agent.train_id not in self._notified_delay_trains:
                            self._notified_delay_trains.add(train_agent.train_id)
                            sev = "CRITICAL" if train_agent.current_delay_minutes >= 10.0 else "WARNING"
                            self._record_alert(
                                "TRAIN_DELAYED",
                                sev,
                                f"Train {train_agent.train_number} delayed by {train_agent.current_delay_minutes} min",
                                train_number=train_agent.train_number,
                            )

                        if not was_completed and train_agent.is_completed:
                            completed_now += 1

                    self.completed_trains_count += completed_now

                    # Periodic traffic density check
                    if self.tick_count % 15 == 0:
                        density_info = self.get_traffic_density()
                        for sec_stat in density_info.get("sections", []):
                            if sec_stat["density"] in ("HIGH", "CRITICAL"):
                                self._record_alert(
                                    "HIGH_TRAFFIC",
                                    "WARNING" if sec_stat["density"] == "HIGH" else "CRITICAL",
                                    f"Elevated traffic density ({sec_stat['density']}) on {sec_stat['section_name']} ({sec_stat['train_count']} trains)",
                                    section_name=sec_stat["section_name"],
                                )

                    # Periodic conflict and congestion analysis (every 2 ticks)
                    if self.tick_count % 2 == 0:
                        util_map = {
                            s_id: min(100.0, round((self.section_occupied_seconds.get(s_id, 0.0) / max(1.0, self.sim_time_seconds)) * 100.0, 1))
                            for s_id in route_manager.sections.keys()
                        }
                        scan_res = conflict_detector.scan(
                            train_simulators=self.train_simulators,
                            sections=route_manager.sections,
                            tracks=state_manager.tracks,
                            stations=route_manager.stations,
                            sim_time_seconds=self.sim_time_seconds,
                            section_utilization_map=util_map,
                        )
                        self.last_conflict_scan_result = scan_res

                        # Alert on newly detected or escalated conflicts with deduplication
                        for conf in scan_res.get("new_conflicts", []):
                            if conflict_detector.deduplicator.should_emit(conf, self.sim_time_seconds):
                                self._record_alert(
                                    alert_type=f"CONFLICT_{conf.conflict_type.value}",
                                    severity=conf.severity.value,
                                    message=f"[{conf.conflict_type.value}] {conf.explanation} Recommendation: {conf.recommendation}",
                                    train_number=f"{conf.train_number_1}/{conf.train_number_2}" if conf.train_number_2 else conf.train_number_1,
                                    section_name=conf.section_name,
                                )

                    # Periodic ML train delay predictions (every 20 ticks = 10s)
                    if self.tick_count % 20 == 0:
                        self._run_delay_predictions()

                    # Periodic DB state synchronization
                    if self.tick_count % config.DB_SYNC_INTERVAL_TICKS == 0:
                        self._sync_to_database()

                    # Broadcast frame to WebSocket clients
                    await self._broadcast_state()

                # Sleep real-time duration
                sleep_seconds = config.TICK_INTERVAL_SECONDS / max(1.0, self.speed_multiplier)
                await asyncio.sleep(min(0.5, sleep_seconds))

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[!] Simulation tick error: {e}")

    def _sync_to_database(self):
        """Persists current in-memory train and track states to SQLite DB asynchronously."""
        try:
            from app.database.session import SessionLocal
            from app.models.railway import Train, Track, RailwaySection

            db = SessionLocal()
            try:
                for agent in self.train_simulators.values():
                    db_train = db.query(Train).filter(Train.train_id == agent.train_id).first()
                    if db_train:
                        db_train.current_position_km = agent.current_position_km
                        db_train.speed_kmph = agent.speed_kmph
                        db_train.status = agent.status
                        db_train.current_delay_minutes = agent.current_delay_minutes
                        db_train.current_section_id = agent.current_section_id
                        db_train.current_station_id = agent.current_station_id

                for t_id, track_data in state_manager.tracks.items():
                    db_track = db.query(Track).filter(Track.track_id == t_id).first()
                    if db_track:
                        db_track.status = track_data["status"]
                        db_track.occupied_by_train = track_data["occupied_by_train"]

                for sec_id in route_manager.sections.keys():
                    db_sec = db.query(RailwaySection).filter(RailwaySection.section_id == sec_id).first()
                    if db_sec:
                        is_occ = state_manager.is_section_occupied(sec_id)
                        db_sec.status = "OCCUPIED" if is_occ else "AVAILABLE"

                db.commit()
            finally:
                db.close()
        except Exception as err:
            # Non-fatal log
            print(f"[!] DB Sync warning: {err}")

    async def _broadcast_state(self):
        """Sends current state snapshot to all connected WebSocket subscribers."""
        if not self.websocket_clients:
            return

        payload = self.get_live_state()
        dead_sockets = set()

        for ws in self.websocket_clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_sockets.add(ws)

        for ws in dead_sockets:
            self.websocket_clients.discard(ws)

    def register_websocket(self, websocket: WebSocket):
        self.websocket_clients.add(websocket)

    def unregister_websocket(self, websocket: WebSocket):
        self.websocket_clients.discard(websocket)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Calculates real-time top statistics required for control-room monitoring."""
        total_trains = len(self.train_simulators)
        running_trains = sum(1 for t in self.train_simulators.values() if t.status == "RUNNING")
        waiting_trains = sum(1 for t in self.train_simulators.values() if t.status == "WAITING")
        delayed_trains = sum(1 for t in self.train_simulators.values() if t.current_delay_minutes > 0 or t.status == "DELAYED")
        arrived_trains = sum(1 for t in self.train_simulators.values() if t.status == "ARRIVED")
        stopped_trains = sum(1 for t in self.train_simulators.values() if t.status == "STOPPED")

        total_sections = len(route_manager.sections)
        occupied_sections = sum(1 for s_id in route_manager.sections.keys() if state_manager.is_section_occupied(s_id))

        total_tracks = len(state_manager.tracks)
        occupied_tracks = sum(1 for tr in state_manager.tracks.values() if tr.get("status") == "OCCUPIED")

        return {
            "total_trains": total_trains,
            "running_trains": running_trains,
            "waiting_trains": waiting_trains,
            "delayed_trains": delayed_trains,
            "arrived_trains": arrived_trains,
            "stopped_trains": stopped_trains,
            "total_sections": total_sections,
            "occupied_sections": occupied_sections,
            "total_tracks": total_tracks,
            "occupied_tracks": occupied_tracks,
            "throughput_trains_per_hour": self.throughput_trains_per_hour,
            "completed_trains": self.completed_trains_count,
            "simulation_time": self.formatted_sim_time,
            "simulation_seconds": round(self.sim_time_seconds, 1),
            "running": self.is_running,
            "paused": self.is_paused,
            "speed_multiplier": self.speed_multiplier,
        }

    def get_sections_live(self) -> List[Dict[str, Any]]:
        """Returns instantaneous block section status, occupancy, active trains, density, and utilization."""
        result = []
        for sec_id, sec_data in route_manager.sections.items():
            start_st = route_manager.stations.get(sec_data["start_station_id"], {})
            end_st = route_manager.stations.get(sec_data["end_station_id"], {})

            # Active trains in this section
            active_trains_in_sec = [
                t.train_number for t in self.train_simulators.values() if t.current_section_id == sec_id
            ]

            # Tracks belonging to this section
            tracks_for_sec = [t for t in state_manager.tracks.values() if t.get("section_id") == sec_id]
            track_count = len(tracks_for_sec)
            has_occupied = any(t.get("status") == "OCCUPIED" for t in tracks_for_sec) or len(active_trains_in_sec) > 0
            has_blocked = any(t.get("status") == "BLOCKED" for t in tracks_for_sec)
            has_maint = any(t.get("status") == "MAINTENANCE" for t in tracks_for_sec)

            if has_blocked:
                sec_status = "BLOCKED"
            elif has_maint:
                sec_status = "MAINTENANCE"
            elif has_occupied:
                sec_status = "OCCUPIED"
            else:
                sec_status = "AVAILABLE"

            # Utilization %
            occ_s = self.section_occupied_seconds.get(sec_id, 0.0)
            util_pct = round((occ_s / max(1.0, self.sim_time_seconds)) * 100.0, 1) if self.sim_time_seconds > 0 else 0.0

            # Density classification
            train_count = len(active_trains_in_sec)
            if train_count == 0:
                density = "LOW"
            elif train_count == 1:
                density = "MEDIUM"
            elif train_count == 2:
                density = "HIGH"
            else:
                density = "CRITICAL"

            result.append({
                "section_id": sec_id,
                "section_name": sec_data["name"],
                "start_station_id": sec_data["start_station_id"],
                "start_station_name": start_st.get("name", "Unknown"),
                "start_station_code": start_st.get("code", "ST01"),
                "end_station_id": sec_data["end_station_id"],
                "end_station_name": end_st.get("name", "Unknown"),
                "end_station_code": end_st.get("code", "ST02"),
                "length_km": sec_data["length_km"],
                "maximum_speed_kmph": sec_data["max_speed"],
                "track_count": track_count if track_count > 0 else 2,
                "status": sec_status,
                "current_trains": active_trains_in_sec,
                "utilization_percent": min(100.0, util_pct),
                "cumulative_occupied_seconds": round(occ_s, 1),
                "density_level": density,
            })
        return result

    def get_tracks_live(self) -> List[Dict[str, Any]]:
        """Returns list of all physical tracks with dynamic occupancy."""
        tracks = []
        for tr in state_manager.tracks.values():
            item = dict(tr)
            train_id = item.get("occupied_by_train")
            if train_id and train_id in self.train_simulators:
                item["occupied_train_number"] = self.train_simulators[train_id].train_number
                item["occupied_train_name"] = self.train_simulators[train_id].train_name
            tracks.append(item)
        return tracks

    def get_traffic_density(self) -> Dict[str, Any]:
        """Calculates traffic density distribution across network sections."""
        section_densities = []
        total_trains_in_sections = 0

        for sec_id, sec_data in route_manager.sections.items():
            trains_in_sec = [
                t.train_number for t in self.train_simulators.values() if t.current_section_id == sec_id
            ]
            count = len(trains_in_sec)
            total_trains_in_sections += count

            if count == 0:
                density = "LOW"
            elif count == 1:
                density = "MEDIUM"
            elif count == 2:
                density = "HIGH"
            else:
                density = "CRITICAL"

            section_densities.append({
                "section_id": sec_id,
                "section_name": sec_data["name"],
                "train_count": count,
                "trains": trains_in_sec,
                "density": density,
            })

        num_sections = max(1, len(route_manager.sections))
        avg_density = total_trains_in_sections / num_sections
        if avg_density < 0.5:
            net_density = "LOW"
        elif avg_density < 1.0:
            net_density = "MEDIUM"
        elif avg_density < 1.8:
            net_density = "HIGH"
        else:
            net_density = "CRITICAL"

        return {
            "network_density": net_density,
            "average_trains_per_section": round(avg_density, 2),
            "total_active_trains_in_sections": total_trains_in_sections,
            "sections": section_densities,
        }

    def get_utilization(self) -> List[Dict[str, Any]]:
        """Returns per-section cumulative occupancy and utilization percentage."""
        res = []
        for sec_id, sec_data in route_manager.sections.items():
            occ_s = self.section_occupied_seconds.get(sec_id, 0.0)
            util_pct = round((occ_s / max(1.0, self.sim_time_seconds)) * 100.0, 1) if self.sim_time_seconds > 0 else 0.0
            res.append({
                "section_id": sec_id,
                "section_name": sec_data["name"],
                "cumulative_occupied_seconds": round(occ_s, 1),
                "total_simulation_seconds": round(self.sim_time_seconds, 1),
                "utilization_percent": min(100.0, util_pct),
            })
        return res

    def get_throughput_metrics(self) -> Dict[str, Any]:
        """Returns throughput statistics and completed train counts."""
        sim_hours = self.sim_time_seconds / 3600.0 if self.sim_time_seconds > 0 else 0.0
        return {
            "completed_trains": self.completed_trains_count,
            "simulation_seconds": round(self.sim_time_seconds, 1),
            "simulation_hours": round(sim_hours, 3),
            "throughput_trains_per_hour": self.throughput_trains_per_hour,
        }

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of dispatcher alerts, optionally filtered by severity."""
        alerts = list(self.alerts_log)
        if severity and severity.upper() != "ALL":
            alerts = [a for a in alerts if a.get("severity") == severity.upper()]
        return alerts

    def clear_alerts(self):
        """Clears all alerts in buffer."""
        self.alerts_log.clear()

    def clear_events(self):
        """Clears all simulation events in buffer."""
        self.event_log.clear()

    def get_status(self) -> Dict[str, Any]:
        """Returns high-level status of the simulation engine."""
        active_count = sum(1 for t in self.train_simulators.values() if t.status in ("RUNNING", "WAITING", "STOPPED"))
        delayed_count = sum(1 for t in self.train_simulators.values() if t.current_delay_minutes > 0)
        return {
            "running": self.is_running,
            "paused": self.is_paused,
            "simulation_time": self.formatted_sim_time,
            "simulation_seconds": round(self.sim_time_seconds, 1),
            "speed_multiplier": self.speed_multiplier,
            "active_trains": active_count,
            "delayed_trains": delayed_count,
            "completed_trains": self.completed_trains_count,
            "throughput_trains_per_hour": self.throughput_trains_per_hour,
        }

    def get_live_trains(self) -> List[Dict[str, Any]]:
        """Returns array of active train telemetry."""
        return [agent.to_dict() for agent in self.train_simulators.values()]

    def get_live_state(self) -> Dict[str, Any]:
        """Returns complete system snapshot including conflicts and congestion."""
        scan_res = self.last_conflict_scan_result or {}
        return {
            "status": self.get_status(),
            "summary": self.get_dashboard_summary(),
            "trains": self.get_live_trains(),
            "sections": self.get_sections_live(),
            "tracks": self.get_tracks_live(),
            "alerts": list(self.alerts_log)[:30],
            "density": self.get_traffic_density(),
            "utilization": self.get_utilization(),
            "events": list(self.event_log)[:20],
            "conflicts": scan_res.get("active_conflicts", []),
            "resolved_conflicts": scan_res.get("resolved_conflicts", [])[:20],
            "congestion": scan_res.get("congestion", []),
            "bottlenecks": scan_res.get("bottlenecks", []),
            "conflict_summary": scan_res.get("summary", {
                "total_active_conflicts": 0,
                "critical_conflicts": 0,
                "high_conflicts": 0,
                "medium_conflicts": 0,
                "low_conflicts": 0,
                "total_resolved_conflicts": 0,
                "critical_bottlenecks": 0,
                "elevated_bottlenecks": 0,
            }),
            "ml_predictions": self.get_live_predictions(),
            "model_info": delay_prediction_service.get_metadata() if delay_prediction_service.is_ready else {},
        }

    def get_conflicts(
        self,
        active_only: bool = True,
        severity: Optional[str] = None,
        section_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Returns active or all conflicts, with optional filtering."""
        if not self.last_conflict_scan_result:
            # Force a scan if not run yet
            util_map = {
                s_id: min(100.0, round((self.section_occupied_seconds.get(s_id, 0.0) / max(1.0, self.sim_time_seconds)) * 100.0, 1))
                for s_id in route_manager.sections.keys()
            }
            self.last_conflict_scan_result = conflict_detector.scan(
                train_simulators=self.train_simulators,
                sections=route_manager.sections,
                tracks=state_manager.tracks,
                stations=route_manager.stations,
                sim_time_seconds=self.sim_time_seconds,
                section_utilization_map=util_map,
            )

        items = self.last_conflict_scan_result.get("active_conflicts", [])
        if not active_only:
            items = items + self.last_conflict_scan_result.get("resolved_conflicts", [])

        if severity and severity.upper() != "ALL":
            items = [c for c in items if c.get("severity") == severity.upper()]

        if section_id is not None:
            items = [c for c in items if c.get("section_id") == section_id]

        return items

    def get_conflict_history(self) -> List[Dict[str, Any]]:
        """Returns historical resolved conflicts."""
        return conflict_detector.tracker.get_history()

    def get_conflict_by_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Finds a conflict by ID from active or resolved registry."""
        return conflict_detector.tracker.get_conflict_by_id(conflict_id)

    def get_congestion(self, section_id: Optional[int] = None) -> Any:
        """Returns network section congestion or a specific section's metric."""
        if not self.last_conflict_scan_result:
            util_map = {
                s_id: min(100.0, round((self.section_occupied_seconds.get(s_id, 0.0) / max(1.0, self.sim_time_seconds)) * 100.0, 1))
                for s_id in route_manager.sections.keys()
            }
            self.last_conflict_scan_result = conflict_detector.scan(
                train_simulators=self.train_simulators,
                sections=route_manager.sections,
                tracks=state_manager.tracks,
                stations=route_manager.stations,
                sim_time_seconds=self.sim_time_seconds,
                section_utilization_map=util_map,
            )

        congestion_list = self.last_conflict_scan_result.get("congestion", [])
        if section_id is not None:
            for item in congestion_list:
                if item["section_id"] == section_id:
                    return item
            return None
        return congestion_list

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """Returns ranked bottlenecks with transparent scoring breakdown."""
        if not self.last_conflict_scan_result:
            util_map = {
                s_id: min(100.0, round((self.section_occupied_seconds.get(s_id, 0.0) / max(1.0, self.sim_time_seconds)) * 100.0, 1))
                for s_id in route_manager.sections.keys()
            }
            self.last_conflict_scan_result = conflict_detector.scan(
                train_simulators=self.train_simulators,
                sections=route_manager.sections,
                tracks=state_manager.tracks,
                stations=route_manager.stations,
                sim_time_seconds=self.sim_time_seconds,
                section_utilization_map=util_map,
            )
        return self.last_conflict_scan_result.get("bottlenecks", [])

    def _run_delay_predictions(self):
        """Extracts operational features for active trains and computes ML delay predictions."""
        try:
            if not delay_prediction_service.is_ready:
                delay_prediction_service.load_artifacts()

            density_info = self.get_traffic_density()
            net_density = density_info.get("network_density", "LOW")
            density_pct = 75.0 if net_density == "CRITICAL" else (50.0 if net_density == "HIGH" else (30.0 if net_density == "MEDIUM" else 15.0))

            db_records = []
            now_iso = datetime.datetime.now().isoformat()

            for agent in self.train_simulators.values():
                if agent.status == "ARRIVED":
                    continue

                # Section-level conditions
                sec_id = agent.current_section_id
                sec_info = route_manager.sections.get(sec_id, {}) if sec_id else {}
                num_trains_sec = sum(1 for a in self.train_simulators.values() if a.current_section_id == sec_id) if sec_id else 1
                waiting_sec = sum(1 for a in self.train_simulators.values() if a.current_section_id == sec_id and a.status in ("WAITING", "STOPPED")) if sec_id else 0

                occ_s = self.section_occupied_seconds.get(sec_id, 0.0) if sec_id else 0.0
                util_pct = min(100.0, round((occ_s / max(1.0, self.sim_time_seconds)) * 100.0, 1)) if self.sim_time_seconds > 0 else 20.0

                max_speed = float(sec_info.get("max_speed", config.TRAIN_MAX_SPEED_BY_TYPE.get(agent.train_type, 110.0)))
                remaining_km = getattr(agent, "remaining_distance_km", 30.0)
                if not remaining_km or remaining_km <= 0:
                    remaining_km = 30.0

                stops_remaining = len([s for s in getattr(agent, "route_stations", []) if s.get("is_upcoming")])

                features = {
                    "train_type": agent.train_type,
                    "priority": agent.priority,
                    "scheduled_duration": 60.0,
                    "distance_remaining_km": remaining_km,
                    "current_speed_kmph": agent.speed_kmph,
                    "maximum_speed_kmph": max_speed,
                    "current_delay_minutes": agent.current_delay_minutes,
                    "number_of_stops_remaining": stops_remaining,
                    "station_dwell_time": 3.0,
                    "number_of_trains_in_section": max(1, num_trains_sec),
                    "section_utilization": util_pct,
                    "traffic_density": density_pct,
                    "waiting_train_count": waiting_sec,
                    "time_of_day": "MORNING",
                    "day_type": "WEEKDAY",
                }

                pred_res = delay_prediction_service.predict(features)
                agent.predicted_delay_minutes = pred_res["predicted_delay_minutes"]
                agent.expected_additional_delay = pred_res["expected_additional_delay"]
                agent.last_prediction_time = self.formatted_sim_time

                db_records.append({
                    "train_id": agent.train_id,
                    "predicted_delay_minutes": agent.predicted_delay_minutes,
                    "expected_additional_delay": agent.expected_additional_delay,
                    "current_delay_minutes": agent.current_delay_minutes,
                    "prediction_timestamp": now_iso,
                    "model_version": delay_prediction_service.metadata.get("version", "1.0.0") if delay_prediction_service.metadata else "1.0.0",
                })

            # Asynchronously / batch save to DB
            if db_records:
                self._persist_predictions_to_db(db_records)

        except Exception as e:
            print(f"[!] Delay prediction error: {e}")

    def _persist_predictions_to_db(self, records: List[Dict[str, Any]]):
        """Stores prediction snapshots in SQLite database."""
        try:
            from app.database.session import SessionLocal
            from app.models.railway import DelayPrediction

            db = SessionLocal()
            try:
                for r in records:
                    p = DelayPrediction(
                        train_id=r["train_id"],
                        predicted_delay_minutes=r["predicted_delay_minutes"],
                        expected_additional_delay=r["expected_additional_delay"],
                        current_delay_minutes=r["current_delay_minutes"],
                        prediction_timestamp=r["prediction_timestamp"],
                        model_version=r["model_version"],
                    )
                    db.add(p)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[!] Prediction DB persistence error: {e}")

    def get_live_predictions(self) -> List[Dict[str, Any]]:
        """Returns real-time delay predictions for all active trains."""
        results = []
        for a in self.train_simulators.values():
            if a.status == "ARRIVED":
                continue
            pred_delay = getattr(a, "predicted_delay_minutes", a.current_delay_minutes)
            add_delay = getattr(a, "expected_additional_delay", 0.0)
            results.append({
                "train_id": a.train_id,
                "train_number": a.train_number,
                "train_name": a.train_name,
                "train_type": a.train_type,
                "priority": a.priority,
                "current_delay_minutes": round(a.current_delay_minutes, 1),
                "predicted_delay_minutes": round(pred_delay, 1),
                "expected_additional_delay": round(add_delay, 1),
                "current_speed_kmph": round(a.speed_kmph, 1),
                "status": a.status,
                "distance_remaining_km": round(getattr(a, "remaining_distance_km", 20.0), 1),
                "last_prediction_time": getattr(a, "last_prediction_time", self.formatted_sim_time),
            })
        return results

    def apply_optimization_plan(self, train_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies advisory dispatch actions (holds and priority sequencing) to active train agents.
        """
        applied_count = 0
        for rec in train_recommendations:
            tid = rec.get("train_id")
            if tid in self.train_simulators:
                agent = self.train_simulators[tid]
                agent.advisory_action = rec.get("action", "PROCEED")
                agent.advisory_reason = rec.get("reason", "")
                hold_sec = rec.get("hold_duration_seconds", 0)
                if hold_sec > 0:
                    agent.hold_until_sim_time_s = self.sim_time_seconds + hold_sec
                else:
                    agent.hold_until_sim_time_s = 0.0
                applied_count += 1

        self._record_event(
            "OPTIMIZATION_PLAN_APPLIED",
            None,
            None,
            f"AI Traffic Optimization plan applied to {applied_count} active train agents."
        )
        return {
            "status": "APPLIED",
            "applied_train_count": applied_count,
            "sim_time_seconds": self.sim_time_seconds,
            "message": f"Successfully committed dispatch plan for {applied_count} trains."
        }

    def preview_optimization_plan(self, train_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Forward-projects train timeline under the recommended schedule without mutating live simulation state.
        """
        timeline = []
        for rec in train_recommendations:
            tid = rec.get("train_id")
            agent = self.train_simulators.get(tid)
            train_num = rec.get("train_number") or (agent.train_number if agent else f"T{tid}")
            entry_offset = rec.get("recommended_entry_time_sec", 0)
            hold_sec = rec.get("hold_duration_seconds", 0)
            timeline.append({
                "train_id": tid,
                "train_number": train_num,
                "action": rec.get("action", "PROCEED"),
                "entry_offset_sec": entry_offset,
                "projected_entry_sim_time": self.sim_time_seconds + entry_offset,
                "hold_duration_sec": hold_sec,
                "expected_delay_min": rec.get("expected_delay_minutes", 0.0),
                "reason": rec.get("reason", "")
            })
        timeline.sort(key=lambda x: x["entry_offset_sec"])
        return {
            "status": "PREVIEW_READY",
            "sim_time_seconds": self.sim_time_seconds,
            "projected_timeline": timeline,
            "train_count": len(timeline)
        }


simulation_engine = SimulationEngine()

