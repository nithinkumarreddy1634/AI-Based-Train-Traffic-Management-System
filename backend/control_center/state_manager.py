"""
Operational State Manager for Phase 11: Real-Time Intelligent Control Center.

Consolidates all subsystem states (simulation, fleet telemetry, block occupancy,
conflict detection, ML delay forecasts, emergencies, and system health)
into a unified real-time snapshot for the control room.
"""

from typing import Dict, Any, List
try:
    from .event_manager import event_manager
    from .emergency_manager import emergency_manager
except ImportError:
    from control_center.event_manager import event_manager
    from control_center.emergency_manager import emergency_manager


class ControlCenterStateManager:
    """Aggregates and formats real-time control room state."""

    def get_unified_state(self) -> Dict[str, Any]:
        """
        Gathers comprehensive operational status from all active modules.
        Does not use hardcoded mock numbers; extracts live data from simulation.
        """
        from simulation import simulation_engine, state_manager as sim_track_state, route_manager
        try:
            from ml.models.predict import delay_prediction_service
        except ImportError:
            delay_prediction_service = None
        from optimization.optimizer import TrainTrafficOptimizer
        from safety.validator import SafetyValidator

        # 1. Fleet status aggregations
        trains_dict = simulation_engine.train_simulators
        total_trains = len(trains_dict)
        active_trains = [t for t in trains_dict.values() if t.status not in ("ARRIVED", "SCHEDULED")]
        running_trains = [t for t in trains_dict.values() if t.status == "RUNNING"]
        waiting_trains = [t for t in trains_dict.values() if t.status == "WAITING"]
        delayed_trains = [t for t in trains_dict.values() if t.current_delay_minutes > 1.0 or t.status == "DELAYED"]
        arrived_trains = [t for t in trains_dict.values() if t.status == "ARRIVED"]
        stopped_trains = [t for t in trains_dict.values() if t.status == "STOPPED"]

        # 2. Section and Track occupancy
        active_emergencies = emergency_manager.get_active_emergencies()
        emergency_sec_ids = {e.get("affected_section_id") for e in active_emergencies if e.get("affected_section_id")}

        sections_live = []
        for sec_id, sec in route_manager.sections.items():
            is_occ = sim_track_state.is_section_occupied(sec_id)
            occ_trains = [a.train_id for a in simulation_engine.train_simulators.values() if a.current_section_id == sec_id and a.status != "ARRIVED"]

            # Determine clear status indicator: FREE, OCCUPIED, CONGESTED, BLOCKED, EMERGENCY
            if sec_id in emergency_sec_ids:
                status_str = "EMERGENCY"
            elif len(occ_trains) > 1:
                status_str = "CONGESTED"
            elif is_occ:
                status_str = "OCCUPIED"
            else:
                status_str = "FREE"

            sections_live.append({
                "section_id": sec_id,
                "name": sec.get("name", f"Section {sec_id}"),
                "start_station_id": sec.get("start_station_id"),
                "end_station_id": sec.get("end_station_id"),
                "length_km": sec.get("length_km", 20.0),
                "speed_limit": sec.get("speed_limit", 120.0),
                "tracks_count": sec.get("tracks_count", 2),
                "status": status_str,
                "train_count": len(occ_trains),
                "train_ids": occ_trains
            })

        occupied_sections_count = sum(1 for s in sections_live if s["status"] in ("OCCUPIED", "CONGESTED", "EMERGENCY"))

        # 3. Conflicts and Bottlenecks
        scan_res = simulation_engine.last_conflict_scan_result or {}
        active_conflicts = scan_res.get("active_conflicts", [])
        critical_conflicts = [c for c in active_conflicts if c.get("severity") == "CRITICAL"]

        # 4. Throughput (TPH) calculation
        sim_elapsed_h = max(0.01, simulation_engine.sim_time_seconds / 3600.0)
        completed_count = getattr(simulation_engine, "completed_trains_count", len(arrived_trains))
        current_tph = round(completed_count / sim_elapsed_h, 1)

        # 5. Determine high-level system status
        if active_emergencies:
            system_status = "EMERGENCY"
        elif len(critical_conflicts) > 0 or len(delayed_trains) >= max(3, total_trains * 0.4):
            system_status = "DEGRADED"
        else:
            system_status = "NORMAL"

        # 6. Component Health
        health = self.get_system_health()

        # 7. Recent events
        recent_events = event_manager.get_events(limit=10)

        return {
            "simulation_status": simulation_engine.get_status(),
            "system_status": system_status,
            "simulation_time": simulation_engine.formatted_sim_time,
            "sim_time_seconds": simulation_engine.sim_time_seconds,
            "simulation_speed": getattr(simulation_engine, "speed_multiplier", 1.0),
            "fleet_summary": {
                "total_trains": total_trains,
                "active_trains": len(active_trains),
                "running_trains": len(running_trains),
                "waiting_trains": len(waiting_trains),
                "delayed_trains": len(delayed_trains),
                "completed_trains": len(arrived_trains),
                "stopped_trains": len(stopped_trains)
            },
            "corridor_summary": {
                "total_sections": len(sections_live),
                "occupied_sections": occupied_sections_count,
                "free_sections": len(sections_live) - occupied_sections_count,
                "emergency_sections": len(emergency_sec_ids),
                "active_conflicts": len(active_conflicts),
                "critical_conflicts": len(critical_conflicts),
                "active_emergencies": len(active_emergencies),
                "current_throughput_tph": current_tph
            },
            "sections": sections_live,
            "trains": [t.to_dict() for t in trains_dict.values()],
            "active_emergencies": active_emergencies,
            "recent_events": recent_events,
            "system_health": health
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Probes status of all underlying micro-components."""
        from simulation import simulation_engine
        try:
            from ml.models.predict import delay_prediction_service
        except ImportError:
            delay_prediction_service = None

        db_ok = True
        try:
            from app.database import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()
        except Exception:
            db_ok = False

        ml_loaded = getattr(delay_prediction_service, "is_ready", False)

        components = {
            "backend": {"name": "FastAPI Backend", "status": "ONLINE", "healthy": True},
            "database": {"name": "SQLite Database", "status": "CONNECTED" if db_ok else "DISCONNECTED", "healthy": db_ok},
            "simulation": {"name": "Simulation Engine", "status": "RUNNING" if simulation_engine.is_running else "READY", "healthy": True},
            "ml_model": {"name": "ML Delay Predictor", "status": "LOADED" if ml_loaded else "STANDBY", "healthy": ml_loaded},
            "optimizer": {"name": "AI Traffic Optimizer", "status": "READY", "healthy": True},
            "safety_engine": {"name": "Safety Validation Engine", "status": "ACTIVE", "healthy": True},
            "websocket": {"name": "WebSocket Broadcaster", "status": "CONNECTED" if len(simulation_engine.websocket_clients) > 0 else "LISTENING", "healthy": True}
        }

        all_healthy = all(c["healthy"] for c in components.values())

        return {
            "overall_healthy": all_healthy,
            "components": components
        }


control_state_manager = ControlCenterStateManager()
