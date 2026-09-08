"""
REST API Router for Safety Validation Engine.

Provides fail-safe gatekeeper endpoints:
1. POST /api/safety/validate - Validates any recommendation or proposed sequence
2. GET  /api/safety/status - System safety health and emergency state
3. GET  /api/safety/rules - Catalog of all 9 formal safety rules
4. GET  /api/safety/audit-log - Historical safety audit logs
5. POST /api/safety/emergency - Emergency trigger and clear controls
"""
import json
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.railway import SafetyAuditLog, Track, RailwaySection
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.railway import SafetyAuditLog, Track, RailwaySection
from safety import DEFAULT_SAFETY_VALIDATOR, DEFAULT_EMERGENCY_MANAGER
from safety.rules import ALL_SAFETY_RULES, RULE_DESCRIPTIONS

router = APIRouter(prefix="/api/safety", tags=["Safety Validation"])


class ValidateSafetyRequest(BaseModel):
    recommendation: Dict[str, Any]
    current_state: Optional[Dict[str, Any]] = None


class EmergencyActionRequest(BaseModel):
    action: str  # "TRIGGER" or "CLEAR"
    reason: Optional[str] = "Manual operator emergency trigger"
    affected_sections: Optional[List[int]] = None
    affected_tracks: Optional[List[int]] = None


@router.post("/validate", response_model=Dict[str, Any])
def validate_plan(
    payload: ValidateSafetyRequest,
    db: Session = Depends(get_db)
):
    """
    Formally inspects a proposed dispatch plan against all 9 safety rules.
    Persists an immutable audit log record to the database.
    """
    rec = payload.recommendation
    state = payload.current_state or {}

    # If current state tracks not provided, fetch from DB
    if "tracks" not in state:
        tracks_db = db.query(Track).all()
        state["tracks"] = {
            t.track_id: {
                "track_id": t.track_id,
                "track_number": t.track_number,
                "is_occupied": (t.status == "OCCUPIED" or t.occupied_by_train is not None),
                "status": t.status,
                "occupied_by_train": t.occupied_by_train
            }
            for t in tracks_db
        }

    val_result = DEFAULT_SAFETY_VALIDATOR.validate(rec, state)
    result_dict = val_result.to_dict()

    # Persist audit record
    try:
        opt_id = rec.get("optimization_id") or rec.get("recommendation_id")
        audit = SafetyAuditLog(
            recommendation_id=opt_id,
            timestamp=result_dict["validated_at"],
            status=result_dict["status"],
            safety_score_status=result_dict["safety_score_status"],
            rules_checked_json=json.dumps(result_dict["rules_checked"]),
            violations_json=json.dumps(result_dict["violations"]),
            warnings_json=json.dumps(result_dict["warnings"]),
            violations_count=len(result_dict["violations"]),
            warnings_count=len(result_dict["warnings"]),
            applied_to_simulation=False,
            summary_notes=(
                f"Validation {result_dict['status']} with {len(result_dict['violations'])} "
                f"violation(s) and {len(result_dict['warnings'])} warning(s)."
            )
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        result_dict["audit_id"] = audit.audit_id
    except Exception as e:
        print(f"[!] Warning: Could not log safety audit record: {e}")

    return result_dict


@router.get("/status", response_model=Dict[str, Any])
def get_safety_status(db: Session = Depends(get_db)):
    """
    Returns real-time safety status of the railway network,
    including emergency state, active violation statistics, and rule coverage.
    """
    em_state = DEFAULT_EMERGENCY_MANAGER.get_emergency_state()
    latest_audit = db.query(SafetyAuditLog).order_by(SafetyAuditLog.audit_id.desc()).first()

    total_audits = db.query(SafetyAuditLog).count()
    approved_audits = db.query(SafetyAuditLog).filter(SafetyAuditLog.status == "APPROVED").count()
    rejected_audits = db.query(SafetyAuditLog).filter(SafetyAuditLog.status == "REJECTED").count()

    system_status = "SAFE"
    if em_state["is_emergency"]:
        system_status = "CRITICAL"
    elif latest_audit and latest_audit.status == "REJECTED":
        system_status = "WARNING"

    latest_audit_dict = None
    if latest_audit:
        try:
            latest_audit_dict = {
                "audit_id": latest_audit.audit_id,
                "timestamp": latest_audit.timestamp,
                "status": latest_audit.status,
                "safety_score_status": latest_audit.safety_score_status,
                "violations_count": len(json.loads(latest_audit.violations_json or "[]")),
                "warnings_count": len(json.loads(latest_audit.warnings_json or "[]")),
                "applied": latest_audit.applied_to_simulation
            }
        except Exception:
            pass

    return {
        "system_status": system_status,
        "emergency_active": em_state["is_emergency"],
        "emergency_details": em_state,
        "total_rules_enforced": len(ALL_SAFETY_RULES),
        "total_audits": total_audits,
        "approved_audits": approved_audits,
        "rejected_audits": rejected_audits,
        "approval_rate_pct": round((approved_audits / max(1, total_audits)) * 100.0, 1),
        "latest_audit": latest_audit_dict,
        "active_constraints": {
            "min_headway_seconds": DEFAULT_SAFETY_VALIDATOR.config.min_headway_seconds,
            "max_network_speed_kmph": DEFAULT_SAFETY_VALIDATOR.config.max_network_speed_kmph,
            "min_stopping_margin_meters": DEFAULT_SAFETY_VALIDATOR.config.min_stopping_margin_meters,
            "junction_clearance_seconds": DEFAULT_SAFETY_VALIDATOR.config.junction_clearance_seconds
        }
    }


@router.get("/rules", response_model=List[Dict[str, Any]])
def get_safety_rules():
    """Returns the formal specification and metadata for all 9 safety rules."""
    rules_list = []
    for r in ALL_SAFETY_RULES:
        meta = RULE_DESCRIPTIONS.get(r, {})
        rules_list.append({
            "rule_id": r,
            "name": meta.get("title") or meta.get("name") or r.replace("_", " ").title(),
            "category": meta.get("category", "General Safety"),
            "severity": meta.get("severity", "HIGH"),
            "description": meta.get("description", "Safety rule constraint verification."),
            "enforced": True
        })
    return rules_list


@router.get("/audit-log", response_model=Dict[str, Any])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns historical safety audit records with detailed violation reports."""
    query = db.query(SafetyAuditLog).order_by(SafetyAuditLog.audit_id.desc())
    if status:
        query = query.filter(SafetyAuditLog.status == status.upper())

    logs = query.limit(limit).all()
    results = []
    for log in logs:
        try:
            viols = json.loads(log.violations_json or "[]")
            warns = json.loads(log.warnings_json or "[]")
            rules = json.loads(log.rules_checked_json or "[]")
        except Exception:
            viols, warns, rules = [], [], []

        results.append({
            "audit_id": log.audit_id,
            "recommendation_id": log.recommendation_id,
            "timestamp": log.timestamp,
            "status": log.status,
            "safety_score_status": log.safety_score_status,
            "rules_checked": rules,
            "violations": viols,
            "warnings": warns,
            "applied_to_simulation": log.applied_to_simulation,
            "summary_notes": log.summary_notes
        })

    return {"total": len(results), "logs": results}


@router.post("/emergency", response_model=Dict[str, Any])
def set_emergency_state(
    payload: EmergencyActionRequest,
    db: Session = Depends(get_db)
):
    """Triggers or clears an emergency halt state across sections and tracks."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if payload.action.upper() == "TRIGGER":
        DEFAULT_EMERGENCY_MANAGER.trigger_emergency(
            reason=payload.reason or "Manual Emergency Trigger",
            affected_sections=payload.affected_sections,
            affected_tracks=payload.affected_tracks
        )
        audit_status = "CRITICAL"
        audit_note = f"EMERGENCY TRIGGERED: {payload.reason}"
    else:
        DEFAULT_EMERGENCY_MANAGER.clear_emergency()
        audit_status = "SAFE"
        audit_note = "Emergency cleared by operator."

    # Record emergency action in audit log
    try:
        audit = SafetyAuditLog(
            timestamp=now_str,
            status="EMERGENCY_CONTROL",
            safety_score_status=audit_status,
            rules_checked_json=json.dumps(["EMERGENCY_STATE"]),
            violations_json=json.dumps([{"rule": "EMERGENCY_STATE", "severity": "CRITICAL", "message": audit_note}]),
            warnings_json="[]",
            applied_to_simulation=True,
            summary_notes=audit_note
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        print(f"[!] Warning: Could not log emergency audit: {e}")

    return {
        "success": True,
        "action": payload.action.upper(),
        "timestamp": now_str,
        "emergency_state": DEFAULT_EMERGENCY_MANAGER.get_emergency_state()
    }
