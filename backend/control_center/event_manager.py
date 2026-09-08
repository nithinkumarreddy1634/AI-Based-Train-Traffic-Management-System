"""
Centralized Event Manager for Phase 11: Real-Time Intelligent Control Center.

Maintains a unified event stream, in-memory circular cache for ultra-fast telemetry,
and SQLite persistence for full auditability.
"""

from collections import deque
from datetime import datetime
import json
import threading
from typing import List, Dict, Any, Optional

try:
    from app.database import SessionLocal
    from app.models.railway import SystemEvent
except ImportError:
    from backend.app.database import SessionLocal
    from backend.app.models.railway import SystemEvent


# Standard Event Types
EVENT_TYPES = {
    "TRAIN_STARTED": ("SIMULATION", "INFO"),
    "TRAIN_DELAYED": ("TRAFFIC", "WARNING"),
    "TRAIN_ARRIVED": ("SIMULATION", "SUCCESS"),
    "TRAIN_WAITING": ("TRAFFIC", "WARNING"),
    "SECTION_OCCUPIED": ("SIMULATION", "INFO"),
    "SECTION_RELEASED": ("SIMULATION", "INFO"),
    "CONFLICT_DETECTED": ("TRAFFIC", "WARNING"),
    "CONGESTION_DETECTED": ("TRAFFIC", "WARNING"),
    "BOTTLENECK_DETECTED": ("TRAFFIC", "WARNING"),
    "AI_RECOMMENDATION": ("AI", "INFO"),
    "SAFETY_APPROVED": ("SAFETY", "SUCCESS"),
    "SAFETY_REJECTED": ("SAFETY", "CRITICAL"),
    "CONTROLLER_APPROVED": ("CONTROLLER", "SUCCESS"),
    "CONTROLLER_REJECTED": ("CONTROLLER", "WARNING"),
    "MANUAL_OVERRIDE": ("CONTROLLER", "INFO"),
    "EMERGENCY_CREATED": ("EMERGENCY", "CRITICAL"),
    "EMERGENCY_RESOLVED": ("EMERGENCY", "SUCCESS"),
}


class EventManager:
    """Manages publishing, caching, filtering, and retrieval of real-time control center events."""

    def __init__(self, max_buffer_size: int = 500):
        self.max_buffer_size = max_buffer_size
        self._buffer: deque = deque(maxlen=max_buffer_size)
        self._lock = threading.Lock()
        self._seq_id = 0

    def publish(
        self,
        event_type: str,
        message: str,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        train_id: Optional[int] = None,
        section_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        persist_db: bool = True
    ) -> Dict[str, Any]:
        """Publishes an event to the stream and records it in memory and database."""
        event_type = event_type.upper()
        default_cat, default_sev = EVENT_TYPES.get(event_type, ("OPERATIONAL", "INFO"))
        cat = category or default_cat
        sev = severity or default_sev
        now_iso = datetime.now().isoformat()
        now_time = datetime.now().strftime("%H:%M:%S")

        with self._lock:
            self._seq_id += 1
            evt_id = self._seq_id
            event_obj = {
                "id": evt_id,
                "event_type": event_type,
                "category": cat,
                "severity": sev,
                "message": message,
                "train_id": train_id,
                "section_id": section_id,
                "details": details or {},
                "timestamp": now_time,
                "iso_timestamp": now_iso,
            }
            self._buffer.append(event_obj)

        if persist_db:
            try:
                db = SessionLocal()
                try:
                    db_evt = SystemEvent(
                        event_type=event_type,
                        category=cat,
                        severity=sev,
                        train_id=train_id,
                        section_id=section_id,
                        message=message,
                        details_json=json.dumps(details or {}),
                        timestamp=now_time
                    )
                    db.add(db_evt)
                    db.commit()
                finally:
                    db.close()
            except Exception as err:
                # Do not block on db failure
                print(f"[!] Warning: Failed to persist event to DB: {err}")

        return event_obj

    def get_events(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        train_id: Optional[int] = None,
        section_id: Optional[int] = None,
        since_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves events matching optional filter criteria, ordered newest first."""
        with self._lock:
            items = list(self._buffer)

        results = []
        for evt in reversed(items):
            if since_id is not None and evt["id"] <= since_id:
                continue
            if category and evt["category"].upper() != category.upper():
                continue
            if severity and evt["severity"].upper() != severity.upper():
                continue
            if train_id is not None and evt.get("train_id") != train_id:
                continue
            if section_id is not None and evt.get("section_id") != section_id:
                continue
            results.append(evt)
            if len(results) >= limit:
                break

        return results

    def clear(self):
        """Clears in-memory buffer."""
        with self._lock:
            self._buffer.clear()
            self._seq_id = 0


event_manager = EventManager()

