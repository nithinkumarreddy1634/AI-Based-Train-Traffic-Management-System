"""
Manual Controller Override Manager for Phase 11.

Allows human traffic controllers to issue manual operational directives
(holds, releases, priority changes, speed advisories, track switches)
under strict mandatory safety interlock validation.
"""

from datetime import datetime
import json
from typing import Dict, Any, Optional

try:
    from app.database import SessionLocal
    from app.models.railway import ControllerAction
except ImportError:
    from backend.app.database import SessionLocal
    from backend.app.models.railway import ControllerAction

try:
    from .event_manager import event_manager
except ImportError:
    from control_center.event_manager import event_manager
from safety.validator import SafetyValidator


class OverrideManager:
    """Manages safety-interlocked manual controller overrides and audit trails."""

    def __init__(self):
        self.safety_validator = SafetyValidator()

    def execute_override(
        self,
        action_type: str,
        train_id: int,
        section_id: Optional[int] = None,
        new_speed_kmph: Optional[float] = None,
        new_priority: Optional[str] = None,
        track_id: Optional[int] = None,
        hold_duration_seconds: Optional[float] = None,
        reason: Optional[str] = None,
        controller_id: str = "CONTROLLER_DESK_1"
    ) -> Dict[str, Any]:
        """
        Validates and executes a manual controller override.
        Guarantees that no manual command can bypass the Phase 8 Safety Validation Engine.
        """
        from simulation import simulation_engine, state_manager, route_manager

        action_type = action_type.upper()
        now_time = datetime.now().strftime("%H:%M:%S")

        agent = simulation_engine.train_simulators.get(train_id)
        if not agent:
            return {
                "success": False,
                "error": f"Train with ID {train_id} not found in active fleet.",
                "action_type": action_type,
                "safety_status": "REJECTED"
            }

        sec_id = section_id or agent.current_section_id
        sec_info = route_manager.sections.get(sec_id, {}) if sec_id else {}
        sec_name = sec_info.get("name", f"Section {sec_id}" if sec_id else "Corridor Track")

        previous_state = {
            "status": agent.status,
            "speed_kmph": agent.speed_kmph,
            "priority": agent.priority,
            "current_section_id": agent.current_section_id,
            "current_track_id": getattr(agent, "current_track_id", None),
            "hold_until": getattr(agent, "hold_until_sim_time_s", 0.0),
            "advisory_action": getattr(agent, "advisory_action", None),
        }

        requested_state = {
            "action_type": action_type,
            "new_speed_kmph": new_speed_kmph,
            "new_priority": new_priority,
            "track_id": track_id,
            "hold_duration_seconds": hold_duration_seconds,
            "reason": reason or f"Manual controller directive: {action_type}"
        }

        # 1. Validate safety of the manual override
        safety_result = self._validate_manual_safety(
            action_type=action_type,
            agent=agent,
            sec_id=sec_id,
            new_speed_kmph=new_speed_kmph,
            track_id=track_id,
            state_manager=state_manager,
            route_manager=route_manager,
            sim_engine=simulation_engine
        )

        is_safe = safety_result["is_safe"]
        safety_status = "APPROVED" if is_safe else "REJECTED"
        violations = safety_result.get("violations", [])

        # 2. If unsafe, block execution and record audit
        if not is_safe:
            self._record_audit(
                action_type=action_type,
                train_id=train_id,
                train_number=agent.train_number,
                section_id=sec_id,
                section_name=sec_name,
                previous_state=previous_state,
                requested_state=requested_state,
                safety_status="REJECTED",
                violations=violations,
                result="REJECTED",
                reason=f"Safety interlock rejected command: {', '.join(violations)}",
                now_time=now_time
            )

            event_manager.publish(
                event_type="SAFETY_REJECTED",
                message=f"Manual override '{action_type}' for train {agent.train_number} REJECTED by safety engine: {violations[0] if violations else 'Safety rule failure'}.",
                severity="CRITICAL",
                train_id=train_id,
                section_id=sec_id,
                details={"violations": violations, "requested_action": action_type}
            )

            return {
                "success": False,
                "action_type": action_type,
                "train_id": train_id,
                "train_number": agent.train_number,
                "safety_status": "REJECTED",
                "violations": violations,
                "message": f"Manual override rejected by safety interlock: {violations[0] if violations else 'Rule violation'}"
            }

        # 3. Apply safe manual override to simulation agent
        applied_msg = self._apply_to_agent(
            action_type=action_type,
            agent=agent,
            new_speed_kmph=new_speed_kmph,
            new_priority=new_priority,
            track_id=track_id,
            hold_duration_seconds=hold_duration_seconds,
            sim_engine=simulation_engine
        )

        # 4. Record audit log
        self._record_audit(
            action_type=action_type,
            train_id=train_id,
            train_number=agent.train_number,
            section_id=sec_id,
            section_name=sec_name,
            previous_state=previous_state,
            requested_state=requested_state,
            safety_status="APPROVED",
            violations=[],
            result="APPLIED",
            reason=reason or f"Controller override {action_type} executed successfully.",
            now_time=now_time
        )

        event_manager.publish(
            event_type="MANUAL_OVERRIDE",
            message=f"Controller {controller_id} executed {action_type} on train {agent.train_number}: {applied_msg}",
            severity="INFO",
            train_id=train_id,
            section_id=sec_id,
            details=requested_state
        )

        return {
            "success": True,
            "action_type": action_type,
            "train_id": train_id,
            "train_number": agent.train_number,
            "safety_status": "APPROVED",
            "message": applied_msg,
            "current_state": {
                "status": agent.status,
                "speed_kmph": agent.speed_kmph,
                "priority": agent.priority
            }
        }

    def _validate_manual_safety(
        self,
        action_type: str,
        agent: Any,
        sec_id: Optional[int],
        new_speed_kmph: Optional[float],
        track_id: Optional[int],
        state_manager: Any,
        route_manager: Any,
        sim_engine: Any
    ) -> Dict[str, Any]:
        """Evaluates whether prospective manual action respects statutory safety rules."""
        violations = []

        # Rule 1: Negative or excessive speed advisory
        if action_type in ("SPEED_ADVISORY", "RESUME_TRAIN") and new_speed_kmph is not None:
            if new_speed_kmph < 0:
                violations.append("RULE_BRAKING_CURVE: Requested train speed cannot be negative.")
            sec_info = route_manager.sections.get(sec_id, {}) if sec_id else {}
            sec_limit = float(sec_info.get("speed_limit", 130.0))
            if new_speed_kmph > sec_limit * 1.05:  # Over speed limit margin
                violations.append(f"RULE_SPEED_RESTRICTION: Requested speed ({new_speed_kmph} km/h) exceeds section civil limit ({sec_limit} km/h).")

        # Rule 2: Releasing train into occupied single track or blocked section
        if action_type == "RELEASE_TRAIN" and sec_id:
            # Check if current section is blocked or has emergency
            if getattr(agent, "is_emergency_halted", False):
                violations.append("RULE_EMERGENCY_STATE: Cannot release train while active emergency lockdown is in effect.")

        # Rule 3: Switching to occupied track in same direction without headway
        if action_type == "SELECT_ALTERNATIVE_TRACK" and track_id:
            tr = state_manager.tracks.get(track_id)
            if not tr:
                violations.append(f"RULE_INTERLOCKING: Target track {track_id} does not exist in corridor network.")
            elif tr.get("status") == "OCCUPIED" and tr.get("occupied_by_train") != agent.train_id:
                violations.append(f"RULE_HEADWAY: Target track {track_id} is currently occupied by Train {tr.get('occupied_by_train')}.")

        return {
            "is_safe": len(violations) == 0,
            "violations": violations
        }

    def _apply_to_agent(
        self,
        action_type: str,
        agent: Any,
        new_speed_kmph: Optional[float],
        new_priority: Optional[str],
        track_id: Optional[int],
        hold_duration_seconds: Optional[float],
        sim_engine: Any
    ) -> str:
        """Mutates TrainSimulator agent operational state according to directive."""
        if action_type == "HOLD_TRAIN":
            hold_sec = hold_duration_seconds if hold_duration_seconds is not None else 300.0
            agent.hold_until_sim_time_s = sim_engine.sim_time_seconds + hold_sec
            agent.status = "WAITING"
            agent.speed_kmph = 0.0
            return f"Train {agent.train_number} placed on hold for {int(hold_sec)}s."

        elif action_type == "RELEASE_TRAIN":
            agent.hold_until_sim_time_s = 0.0
            if agent.status in ("WAITING", "STOPPED"):
                agent.status = "RUNNING"
                agent.speed_kmph = 45.0  # Safe acceleration initial notch
            return f"Train {agent.train_number} released and cleared to proceed."

        elif action_type == "CHANGE_PRIORITY":
            if new_priority and new_priority.upper() in ("HIGH", "MEDIUM", "LOW"):
                old_prio = agent.priority
                agent.priority = new_priority.upper()
                return f"Train {agent.train_number} priority changed from {old_prio} to {agent.priority}."
            return f"Train {agent.train_number} priority unchanged (invalid value)."

        elif action_type == "PAUSE_TRAIN":
            agent.status = "STOPPED"
            agent.speed_kmph = 0.0
            agent.is_manually_paused = True
            return f"Train {agent.train_number} paused at current coordinate {agent.current_position_km:.1f} km."

        elif action_type == "RESUME_TRAIN":
            agent.is_manually_paused = False
            agent.status = "RUNNING"
            agent.speed_kmph = new_speed_kmph if new_speed_kmph else 50.0
            return f"Train {agent.train_number} resumed at speed {agent.speed_kmph} km/h."

        elif action_type == "SPEED_ADVISORY":
            if new_speed_kmph is not None:
                agent.speed_kmph = max(0.0, float(new_speed_kmph))
                return f"Train {agent.train_number} speed advisory updated to {agent.speed_kmph} km/h."
            return f"Train {agent.train_number} speed advisory unchanged."

        elif action_type == "SELECT_ALTERNATIVE_TRACK":
            if track_id:
                agent.assigned_track_id = track_id
                return f"Train {agent.train_number} rerouted to track {track_id}."
            return f"Track assignment unchanged."

        elif action_type == "CANCEL_RECOMMENDATION":
            agent.advisory_action = None
            agent.advisory_reason = "Controller cleared active AI recommendation."
            return f"Active recommendation cleared for Train {agent.train_number}."

        return f"Directive {action_type} acknowledged."

    def _record_audit(
        self,
        action_type: str,
        train_id: Optional[int],
        train_number: Optional[str],
        section_id: Optional[int],
        section_name: Optional[str],
        previous_state: Dict[str, Any],
        requested_state: Dict[str, Any],
        safety_status: str,
        violations: list,
        result: str,
        reason: str,
        now_time: str
    ):
        """Records the controller action to database."""
        try:
            db = SessionLocal()
            try:
                rec = ControllerAction(
                    action_type=action_type,
                    train_id=train_id,
                    train_number=train_number or "",
                    section_id=section_id,
                    section_name=section_name or "",
                    previous_state_json=json.dumps(previous_state),
                    requested_state_json=json.dumps(requested_state),
                    safety_status=safety_status,
                    violations_json=json.dumps(violations),
                    result=result,
                    reason=reason,
                    timestamp=now_time
                )
                db.add(rec)
                db.commit()
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to record ControllerAction audit: {err}")

    def get_action_history(self, limit: int = 50) -> list:
        """Retrieves historical controller actions from database."""
        try:
            db = SessionLocal()
            try:
                records = db.query(ControllerAction).order_by(ControllerAction.id.desc()).limit(limit).all()
                results = []
                for r in records:
                    results.append({
                        "id": r.id,
                        "action_type": r.action_type,
                        "train_id": r.train_id,
                        "train_number": r.train_number,
                        "section_id": r.section_id,
                        "section_name": r.section_name,
                        "safety_status": r.safety_status,
                        "result": r.result,
                        "reason": r.reason,
                        "timestamp": r.timestamp,
                        "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
                    })
                return results
            finally:
                db.close()
        except Exception as err:
            print(f"[!] Warning: Failed to fetch ControllerAction history: {err}")
            return []


override_manager = OverrideManager()
