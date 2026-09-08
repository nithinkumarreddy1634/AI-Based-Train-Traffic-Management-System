"""
Scenario Controller for Phase 11: Real-Time Intelligent Control Center.

Manages loading, launching, pausing, resuming, and resetting standard and custom
traffic simulation scenarios without destroying the underlying network structure.
"""

from datetime import datetime
import json
from typing import Dict, Any, Optional, List

try:
    from app.database import SessionLocal
    from app.models.railway import Scenario
except ImportError:
    from backend.app.database import SessionLocal
    from backend.app.models.railway import Scenario

try:
    from backend.analytics.scenario_manager import ScenarioManager
except ImportError:
    from analytics.scenario_manager import ScenarioManager
try:
    from .event_manager import event_manager
except ImportError:
    from control_center.event_manager import event_manager


class ScenarioController:
    """Controls scenario lifecycle and custom traffic scenario synthesis."""

    def __init__(self):
        self.scenario_manager = ScenarioManager()
        self.current_scenario_id: str = "normal_traffic"
        self.current_scenario_meta: Dict[str, Any] = {
            "id": "normal_traffic",
            "name": "Normal Operating Traffic",
            "description": "Standard timetable with 12 operating trains, mixed express and local services.",
            "traffic_density": "normal",
            "num_trains": 12,
            "is_custom": False
        }

    def list_available_scenarios(self) -> List[Dict[str, Any]]:
        """Returns standard scenarios plus any custom scenarios stored in SQLite."""
        standard = self.scenario_manager.list_scenarios()
        all_scenarios = [dict(s) for s in standard]

        # Add default normal traffic entry
        if not any(s["id"] == "normal_traffic" for s in all_scenarios):
            all_scenarios.insert(0, self.current_scenario_meta)

        # Load custom scenarios from DB
        try:
            db = SessionLocal()
            try:
                custom_recs = db.query(Scenario).filter(Scenario.is_custom == True).all()
                for cr in custom_recs:
                    all_scenarios.append({
                        "id": cr.scenario_id,
                        "name": cr.name,
                        "description": cr.description,
                        "traffic_density": cr.traffic_density,
                        "num_trains": cr.num_trains,
                        "is_custom": True
                    })
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to query custom scenarios from DB: {err}")

        return all_scenarios

    def load_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Loads the selected standard or custom scenario into the simulation engine.
        Resets simulator state and initializes fleet and route topology.
        """
        from simulation import simulation_engine

        # 1. Stop active simulation loop if running
        if simulation_engine.is_running:
            simulation_engine.stop()

        # 2. Check if scenario is a standard benchmark scenario
        sc_id_lookup = "medium_traffic" if scenario_id == "normal_traffic" else scenario_id
        state = self.scenario_manager.create_initial_state(sc_id_lookup)

        # 3. Initialize simulation engine with scenario assets
        simulation_engine.initialize(
            stations=state["stations"],
            sections=state["sections"],
            tracks=state["tracks"],
            trains=state["trains"],
            schedules=state["schedules"]
        )

        sc_meta = self.scenario_manager.get_scenario(scenario_id) or {
            "id": scenario_id,
            "name": scenario_id.replace("_", " ").title(),
            "description": f"Loaded traffic scenario: {scenario_id}",
            "traffic_density": "standard",
            "num_trains": len(state["trains"])
        }

        self.current_scenario_id = scenario_id
        self.current_scenario_meta = sc_meta

        event_manager.publish(
            event_type="TRAIN_STARTED",
            message=f"Scenario '{sc_meta.get('name')}' loaded successfully with {len(state['trains'])} active trains.",
            severity="INFO",
            details={"scenario_id": scenario_id, "train_count": len(state["trains"])}
        )

        return {
            "success": True,
            "scenario_id": scenario_id,
            "name": sc_meta.get("name"),
            "train_count": len(state["trains"]),
            "sections_count": len(state["sections"]),
            "tracks_count": len(state["tracks"]),
            "status": "INITIALIZED",
            "message": f"Scenario {scenario_id} loaded into simulation engine."
        }

    def start_scenario(self) -> Dict[str, Any]:
        """Starts real-time simulation progression."""
        from simulation import simulation_engine

        simulation_engine.start()
        event_manager.publish(
            event_type="TRAIN_STARTED",
            message=f"Simulation started for scenario '{self.current_scenario_meta.get('name')}'.",
            severity="SUCCESS"
        )
        return {"success": True, "status": "RUNNING", "sim_time": simulation_engine.formatted_sim_time}

    def pause_scenario(self) -> Dict[str, Any]:
        """Pauses simulation progression."""
        from simulation import simulation_engine

        simulation_engine.pause()
        event_manager.publish(
            event_type="SECTION_OCCUPIED",
            message=f"Simulation paused at {simulation_engine.formatted_sim_time}.",
            severity="INFO"
        )
        return {"success": True, "status": "PAUSED", "sim_time": simulation_engine.formatted_sim_time}

    def resume_scenario(self) -> Dict[str, Any]:
        """Resumes paused simulation."""
        from simulation import simulation_engine

        simulation_engine.resume()
        event_manager.publish(
            event_type="TRAIN_STARTED",
            message=f"Simulation resumed at {simulation_engine.formatted_sim_time}.",
            severity="INFO"
        )
        return {"success": True, "status": "RUNNING", "sim_time": simulation_engine.formatted_sim_time}

    def reset_scenario(self) -> Dict[str, Any]:
        """Resets the current scenario back to time 00:00:00."""
        from simulation import simulation_engine

        simulation_engine.stop()
        return self.load_scenario(self.current_scenario_id)

    def create_custom_scenario(
        self,
        name: str,
        num_trains: int = 15,
        traffic_level: str = "medium",
        delayed_trains: int = 3,
        priority_trains: int = 4,
        bottleneck_section_id: Optional[int] = None,
        duration_minutes: float = 60.0
    ) -> Dict[str, Any]:
        """
        Synthesizes, validates, and stores a custom scenario.
        Strictly rejects invalid parameters (negative counts, impossible bounds).
        """
        # Strict validation
        if not name or len(name.strip()) < 3:
            return {"success": False, "error": "Scenario name must be at least 3 characters."}

        if num_trains < 2 or num_trains > 50:
            return {"success": False, "error": "Number of trains must be between 2 and 50."}

        if delayed_trains < 0 or delayed_trains > num_trains:
            return {"success": False, "error": "Delayed trains cannot exceed total number of trains."}

        if priority_trains < 0 or priority_trains > num_trains:
            return {"success": False, "error": "Priority trains cannot exceed total number of trains."}

        if duration_minutes <= 0 or duration_minutes > 720:
            return {"success": False, "error": "Duration must be between 1 and 720 minutes."}

        scenario_slug = f"custom_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"

        config = {
            "name": name,
            "num_trains": num_trains,
            "traffic_density": traffic_level.lower(),
            "delayed_trains": delayed_trains,
            "priority_trains": priority_trains,
            "bottleneck_section_id": bottleneck_section_id,
            "duration_seconds": duration_minutes * 60.0
        }

        # Store in SQLite
        try:
            db = SessionLocal()
            try:
                sc_rec = Scenario(
                    scenario_id=scenario_slug,
                    name=name,
                    description=f"Custom scenario with {num_trains} trains, {delayed_trains} delayed, {priority_trains} high priority.",
                    traffic_density=traffic_level.lower(),
                    num_trains=num_trains,
                    config_json=json.dumps(config),
                    is_custom=True
                )
                db.add(sc_rec)
                db.commit()
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to persist custom scenario: {err}")

        event_manager.publish(
            event_type="TRAIN_STARTED",
            message=f"Custom traffic scenario '{name}' ({num_trains} trains) created and ready to load.",
            severity="INFO",
            details=config
        )

        return {
            "success": True,
            "scenario_id": scenario_slug,
            "name": name,
            "config": config,
            "message": "Custom scenario successfully created."
        }


scenario_controller = ScenarioController()
