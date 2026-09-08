"""
Conflict Detection and Congestion Analysis Package.
Phase 5: Real-time detection of 5 conflict classes, headway enforcement,
transparent bottleneck scoring, and explainable advisory recommendations.
"""

from .conflict_types import (
    Conflict,
    ConflictType,
    ConflictSeverity,
    ConflictUrgency,
    ConflictStatus,
    CongestionLevel,
)
from .headway import HeadwayCalculator
from .severity import SeverityEvaluator
from .conflict_rules import ConflictRulesEngine
from .predictor import TimeToConflictPredictor, ConflictResolutionTracker, AlertDeduplicator
from .service import CongestionService
from .detector import ConflictDetector, conflict_detector

__all__ = [
    "Conflict",
    "ConflictType",
    "ConflictSeverity",
    "ConflictUrgency",
    "ConflictStatus",
    "CongestionLevel",
    "HeadwayCalculator",
    "SeverityEvaluator",
    "ConflictRulesEngine",
    "TimeToConflictPredictor",
    "ConflictResolutionTracker",
    "AlertDeduplicator",
    "CongestionService",
    "ConflictDetector",
    "conflict_detector",
]

