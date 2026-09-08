"""
Conflict Types, Severity, Urgency and Data Structures for Phase 5.
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import time


class ConflictType(str, Enum):
    SAME_SECTION = "SAME_SECTION"
    REAR_END = "REAR_END"
    OPPOSITE_DIRECTION = "OPPOSITE_DIRECTION"
    JUNCTION = "JUNCTION"
    INSUFFICIENT_HEADWAY = "INSUFFICIENT_HEADWAY"


class ConflictSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConflictUrgency(str, Enum):
    IMMEDIATE = "IMMEDIATE"   # < 60 seconds or < 1.0 km
    SOON = "SOON"             # 60 - 180 seconds or 1.0 - 3.0 km
    MONITOR = "MONITOR"       # > 180 seconds or > 3.0 km


class ConflictStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class CongestionLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Conflict:
    """Represents a detected railway traffic conflict between trains or infrastructure."""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    urgency: ConflictUrgency
    train_id_1: int
    train_number_1: str
    train_id_2: Optional[int] = None
    train_number_2: Optional[str] = None
    section_id: Optional[int] = None
    section_name: Optional[str] = None
    track_id: Optional[int] = None
    distance_km: float = 0.0
    time_to_conflict_seconds: Optional[float] = None
    relative_speed_kmph: float = 0.0
    explanation: str = ""
    recommendation: str = ""
    status: ConflictStatus = ConflictStatus.ACTIVE
    detected_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["conflict_type"] = self.conflict_type.value if hasattr(self.conflict_type, "value") else str(self.conflict_type)
        data["severity"] = self.severity.value if hasattr(self.severity, "value") else str(self.severity)
        data["urgency"] = self.urgency.value if hasattr(self.urgency, "value") else str(self.urgency)
        data["status"] = self.status.value if hasattr(self.status, "value") else str(self.status)
        return data

