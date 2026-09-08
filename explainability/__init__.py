"""
Root forwarding package for Phase 10 Explainability.
Ensures `import explainability` works transparently from workspace root.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from explainability import (
    FeatureAnalyzer,
    DecisionFactor,
    ConfidenceCalculator,
    ConfidenceReport,
    DISCLAIMER_TEXT,
    ExplanationFormatter,
    RecommendationExplainer,
    DecisionExplainer,
    DEFAULT_FEATURE_ANALYZER,
    DEFAULT_CONFIDENCE_CALCULATOR,
    DEFAULT_FORMATTER,
    DEFAULT_RECOMMENDATION_EXPLAINER,
    DEFAULT_DECISION_EXPLAINER,
)

__all__ = [
    "FeatureAnalyzer",
    "DecisionFactor",
    "ConfidenceCalculator",
    "ConfidenceReport",
    "DISCLAIMER_TEXT",
    "ExplanationFormatter",
    "RecommendationExplainer",
    "DecisionExplainer",
    "DEFAULT_FEATURE_ANALYZER",
    "DEFAULT_CONFIDENCE_CALCULATOR",
    "DEFAULT_FORMATTER",
    "DEFAULT_RECOMMENDATION_EXPLAINER",
    "DEFAULT_DECISION_EXPLAINER",
]

