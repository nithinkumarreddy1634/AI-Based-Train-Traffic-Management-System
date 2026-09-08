"""
Structured Safety Validation Result Schemas.

Defines strongly typed dataclasses for safety violations, warnings,
rule execution reports, and fail-safe approval statuses.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class SafetyViolation:
    """Represents a specific safety rule breach."""
    rule: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM'
    message: str
    train_numbers: List[str] = field(default_factory=list)
    section_name: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyWarning:
    """Represents a non-blocking operational caution."""
    rule: str
    severity: str  # 'LOW', 'WARNING'
    message: str
    train_numbers: List[str] = field(default_factory=list)
    section_name: Optional[str] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyValidationResult:
    """Comprehensive verdict returned by the safety validation engine."""
    validation_id: int
    recommendation_id: Optional[int]
    status: str  # 'APPROVED', 'REJECTED'
    safety_score_status: str  # 'SAFE', 'WARNING', 'UNSAFE'
    rules_checked: List[str]
    violations: List[SafetyViolation] = field(default_factory=list)
    warnings: List[SafetyWarning] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    candidate_summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_approved(self) -> bool:
        return self.status == "APPROVED" and len(self.violations) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_id": self.validation_id,
            "recommendation_id": self.recommendation_id,
            "status": self.status,
            "safety_score_status": self.safety_score_status,
            "is_approved": self.is_approved,
            "rules_checked": self.rules_checked,
            "violations_count": len(self.violations),
            "warnings_count": len(self.warnings),
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "validated_at": self.validated_at,
            "candidate_summary": self.candidate_summary,
        }

