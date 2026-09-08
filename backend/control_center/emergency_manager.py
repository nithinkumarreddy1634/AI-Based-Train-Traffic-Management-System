"""
Simulated Emergency Manager for Phase 11: Real-Time Intelligent Control Center.

Handles injection of synthetic railway disruption events, evaluates operational impact,
and triggers AI re-optimization with Phase 8 safety validation to generate safe recovery responses.

NOTE: This is strictly a simulation and decision-support modeling tool.
It does not interface with physical signaling or real railway infrastructure.
"""

from datetime import datetime
import json
from typing import List, Dict, Any, Optional

try:
    from app.database import SessionLocal
    from app.models.railway import EmergencyEvent
except ImportError:
    from backend.app.database import SessionLocal
    from backend.app.models.railway import EmergencyEvent

try:
    from .event_manager import event_manager
except ImportError:
    from control_center.event_manager import event_manager
from safety.validator import SafetyValidator


class EmergencyManager:
    """Manages simulated emergency events, corridor asset impact, and safe AI mitigation responses."""

    def __init__(self):
        self.safety_validator = SafetyValidator()
        self._active_events: Dict[int, Dict[str, Any]] = {}
        self._id_seq = 0

    def create_event(
        self,
        event_type: str,
        affected_section_id: Optional[int] = None,
        affected_train_id: Optional[int] = None,
        severity: str = "HIGH",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates and activates a simulated emergency incident.
        Updates affected train and section simulation statuses.
        """
        from simulation import simulation_engine, route_manager

        event_type = event_type.upper()
        severity = severity.upper()
        now_time = datetime.now().strftime("%H:%M:%S")

        sec_name = None
        if affected_section_id:
            sec_info = route_manager.sections.get(affected_section_id, {})
            sec_name = sec_info.get("name", f"Section {affected_section_id}")

        train_num = None
        if affected_train_id:
            agent = simulation_engine.train_simulators.get(affected_train_id)
            if agent:
                train_num = agent.train_number
                if not affected_section_id:
                    affected_section_id = agent.current_section_id
                    sec_info = route_manager.sections.get(affected_section_id, {})
                    sec_name = sec_info.get("name")

        self._id_seq += 1
        evt_id = self._id_seq

        # Evaluate impact on corridor
        impact = self._calculate_impact(
            event_type=event_type,
            sec_id=affected_section_id,
            train_id=affected_train_id,
            sim_engine=simulation_engine
        )

        event_dict = {
            "id": evt_id,
            "event_type": event_type,
            "affected_section_id": affected_section_id,
            "affected_section_name": sec_name,
            "affected_train_id": affected_train_id,
            "affected_train_number": train_num,
            "severity": severity,
            "status": "ACTIVE",
            "description": description or f"Simulated incident: {event_type} on {sec_name or train_num or 'Corridor'}",
            "impact_summary": impact,
            "ai_recommendation_id": None,
            "safety_status": "PENDING",
            "resolution_notes": None,
            "timestamp": now_time,
            "resolved_at": None,
        }

        self._active_events[evt_id] = event_dict

        # Apply immediate emergency effect to simulation entities
        self._apply_emergency_effects(event_dict, simulation_engine)

        # Persist to SQLite
        try:
            db = SessionLocal()
            try:
                db_record = EmergencyEvent(
                    event_type=event_type,
                    affected_section_id=affected_section_id,
                    affected_section_name=sec_name,
                    affected_train_id=affected_train_id,
                    affected_train_number=train_num,
                    severity=severity,
                    status="ACTIVE",
                    impact_summary_json=json.dumps(impact),
                    safety_status="PENDING",
                    timestamp=now_time
                )
                db.add(db_record)
                db.commit()
                event_dict["id"] = db_record.id
                self._active_events[db_record.id] = event_dict
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to persist EmergencyEvent: {err}")

        event_manager.publish(
            event_type="EMERGENCY_CREATED",
            message=f"SIMULATED EMERGENCY [{severity}]: {event_dict['description']}. Affected trains: {len(impact['affected_train_ids'])}.",
            severity="CRITICAL",
            train_id=affected_train_id,
            section_id=affected_section_id,
            details={"event_id": evt_id, "impact": impact}
        )

        return event_dict

    def _calculate_impact(
        self,
        event_type: str,
        sec_id: Optional[int],
        train_id: Optional[int],
        sim_engine: Any
    ) -> Dict[str, Any]:
        """Calculates immediate and cascading disruption impact on the network."""
        affected_trains = []
        projected_cascade_delay_min = 0.0

        for agent in sim_engine.train_simulators.values():
            if agent.status == "ARRIVED":
                continue
            is_affected = False
            if train_id and agent.train_id == train_id:
                is_affected = True
                projected_cascade_delay_min += 25.0
            elif sec_id and agent.current_section_id == sec_id:
                is_affected = True
                projected_cascade_delay_min += 15.0
            elif sec_id and getattr(agent, "next_section_id", None) == sec_id:
                # Approaching train
                is_affected = True
                projected_cascade_delay_min += 10.0

            if is_affected:
                affected_trains.append({
                    "train_id": agent.train_id,
                    "train_number": agent.train_number,
                    "current_delay": agent.current_delay_minutes,
                    "status": agent.status
                })

        return {
            "affected_trains_count": len(affected_trains),
            "affected_train_ids": [t["train_id"] for t in affected_trains],
            "affected_train_numbers": [t["train_number"] for t in affected_trains],
            "projected_cascade_delay_minutes": round(projected_cascade_delay_min, 1),
            "section_closed": event_type in ("TRACK_BLOCKAGE", "SECTION_UNAVAILABLE", "EMERGENCY_STOP"),
            "speed_restriction_kmph": 0.0 if event_type in ("TRACK_BLOCKAGE", "SECTION_UNAVAILABLE") else (30.0 if event_type == "SIGNAL_UNAVAILABLE" else 45.0)
        }

    def _apply_emergency_effects(self, event_dict: Dict[str, Any], sim_engine: Any):
        """Halts or slows trains in the emergency zone."""
        evt_type = event_dict["event_type"]
        sec_id = event_dict["affected_section_id"]
        target_tid = event_dict["affected_train_id"]

        for agent in sim_engine.train_simulators.values():
            if agent.status == "ARRIVED":
                continue
            if target_tid and agent.train_id == target_tid:
                agent.status = "STOPPED"
                agent.speed_kmph = 0.0
                agent.is_emergency_halted = True
                agent.current_delay_minutes += 15.0
            elif sec_id and agent.current_section_id == sec_id:
                if evt_type in ("TRACK_BLOCKAGE", "SECTION_UNAVAILABLE", "EMERGENCY_STOP"):
                    agent.status = "STOPPED"
                    agent.speed_kmph = 0.0
                    agent.is_emergency_halted = True
                elif evt_type == "SIGNAL_UNAVAILABLE":
                    agent.speed_kmph = min(agent.speed_kmph, 25.0)  # Caution speed

    def generate_safe_response(self, event_id: int) -> Dict[str, Any]:
        """
        Generates an AI recovery plan for the active emergency,
        strictly validated by the Phase 8 Safety Validation Engine.
        """
        from simulation import simulation_engine, route_manager, state_manager
        from optimization.optimizer import TrainTrafficOptimizer

        event = self._active_events.get(event_id)
        if not event:
            return {"success": False, "error": f"Emergency event {event_id} not found."}

        sec_id = event.get("affected_section_id")
        sec_name = event.get("affected_section_name", "Incident Zone")

        # Collect active trains requiring diversion or holding
        candidate_trains = []
        for a in simulation_engine.train_simulators.values():
            if a.status != "ARRIVED":
                candidate_trains.append(a.to_dict())

        # Synthesize advisory recovery recommendations with statutory headway spacing
        recommended_actions = []
        for idx, t in enumerate(candidate_trains):
            tid = t["train_id"]
            agent = simulation_engine.train_simulators.get(tid)
            if not agent:
                continue

            entry_time = idx * 180  # Staggered by statutory headway (>= 120s)
            if t.get("current_section_id") == sec_id:
                # Inside emergency zone: Hold securely
                recommended_actions.append({
                    "train_id": tid,
                    "train_number": t["train_number"],
                    "action": "HOLD",
                    "target_section_id": sec_id,
                    "target_section_name": sec_name,
                    "recommended_speed_kmph": 0.0,
                    "hold_duration_seconds": 600,
                    "recommended_entry_time_sec": entry_time,
                    "entry_time_sec": entry_time,
                    "reason": f"Emergency hold: {event['event_type']} active in section."
                })
            else:
                # Approaching corridor: Regulate speed to avoid tail-to-nose jam
                recommended_actions.append({
                    "train_id": tid,
                    "train_number": t["train_number"],
                    "action": "PROCEED",
                    "target_section_id": t.get("current_section_id"),
                    "target_section_name": "Corridor Approach",
                    "recommended_speed_kmph": 45.0,
                    "hold_duration_seconds": 0,
                    "recommended_entry_time_sec": entry_time,
                    "entry_time_sec": entry_time,
                    "reason": "Speed advisory: Buffer separation behind incident zone."
                })

        # Run Phase 8 Safety Validation
        validation = self.safety_validator.validate(
            recommendation={
                "train_recommendations": recommended_actions,
                "target_section_id": sec_id,
                "simulation_time_seconds": simulation_engine.sim_time_seconds
            },
            current_state={
                "sections": route_manager.sections,
                "tracks": state_manager.tracks,
                "trains": candidate_trains,
                "conflicts": simulation_engine.last_conflict_scan_result.get("active_conflicts", []) if simulation_engine.last_conflict_scan_result else []
            }
        )

        val_dict = validation.to_dict() if hasattr(validation, "to_dict") else {
            "status": getattr(validation, "status", "APPROVED"),
            "rules_checked": [r.code if hasattr(r, "code") else str(r) for r in getattr(validation, "rules_checked", [])],
            "violations": [v.rule_code if hasattr(v, "rule_code") else str(v) for v in getattr(validation, "violations", [])],
        }
        safety_status = val_dict.get("status", "APPROVED")
        event["safety_status"] = safety_status

        response_payload = {
            "emergency_id": event_id,
            "event_type": event["event_type"],
            "safety_status": safety_status,
            "rules_checked": val_dict.get("rules_checked", []),
            "violations": val_dict.get("violations", []),
            "recommendations": recommended_actions,
            "mitigation_strategy": f"Controlled emergency holding of {len(recommended_actions)} trains with 0 speed in incident zone.",
            "status": "SAFE_RESPONSE_READY"
        }

        event_manager.publish(
            event_type="AI_RECOMMENDATION",
            message=f"AI generated safe emergency mitigation response for incident #{event_id} ({safety_status}).",
            severity="INFO" if safety_status == "APPROVED" else "CRITICAL",
            section_id=sec_id,
            details=response_payload
        )

        return response_payload

    def resolve_event(self, event_id: int, resolution_notes: Optional[str] = None) -> Dict[str, Any]:
        """Clears an active emergency and restores corridor operations."""
        from simulation import simulation_engine

        event = self._active_events.get(event_id)
        if not event:
            return {"success": False, "error": f"Event {event_id} not found."}

        event["status"] = "RESOLVED"
        event["resolved_at"] = datetime.now().strftime("%H:%M:%S")
        event["resolution_notes"] = resolution_notes or "Track and signaling cleared. Operations restored to normal."

        # Unhalt trains that were stopped by this emergency
        sec_id = event.get("affected_section_id")
        for agent in simulation_engine.train_simulators.values():
            if getattr(agent, "is_emergency_halted", False):
                if not sec_id or agent.current_section_id == sec_id or agent.train_id == event.get("affected_train_id"):
                    agent.is_emergency_halted = False
                    agent.status = "RUNNING"
                    agent.speed_kmph = 45.0  # Resume at initial cautionary notch

        # Update DB
        try:
            db = SessionLocal()
            try:
                db_evt = db.query(EmergencyEvent).filter(EmergencyEvent.id == event_id).first()
                if db_evt:
                    db_evt.status = "RESOLVED"
                    db_evt.resolved_at = event["resolved_at"]
                    db_evt.resolution_notes = event["resolution_notes"]
                    db.commit()
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to update resolved EmergencyEvent in DB: {err}")

        event_manager.publish(
            event_type="EMERGENCY_RESOLVED",
            message=f"Emergency #{event_id} ({event['event_type']}) RESOLVED: {event['resolution_notes']}",
            severity="SUCCESS",
            section_id=sec_id,
            details={"event_id": event_id}
        )

        return {
            "success": True,
            "event_id": event_id,
            "status": "RESOLVED",
            "message": f"Emergency {event_id} marked resolved. Normal dispatch rules restored."
        }

    def get_active_emergencies(self) -> List[Dict[str, Any]]:
        """Returns list of currently active emergency events."""
        return [e for e in self._active_events.values() if e.get("status") == "ACTIVE"]

    def get_all_emergencies(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns all emergency events (active and historical)."""
        try:
            db = SessionLocal()
            try:
                records = db.query(EmergencyEvent).order_by(EmergencyEvent.id.desc()).limit(limit).all()
                results = []
                for r in records:
                    impact = json.loads(r.impact_summary_json) if r.impact_summary_json else {}
                    results.append({
                        "id": r.id,
                        "event_type": r.event_type,
                        "affected_section_id": r.affected_section_id,
                        "affected_section_name": r.affected_section_name,
                        "affected_train_id": r.affected_train_id,
                        "affected_train_number": r.affected_train_number,
                        "severity": r.severity,
                        "status": r.status,
                        "impact_summary": impact,
                        "safety_status": r.safety_status,
                        "resolution_notes": r.resolution_notes,
                        "timestamp": r.timestamp,
                        "resolved_at": r.resolved_at
                    })
                return results
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to fetch emergencies from DB: {err}")
            return list(self._active_events.values())


emergency_manager = EmergencyManager()
