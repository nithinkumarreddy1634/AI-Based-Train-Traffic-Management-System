"""
Phase 10: Explainable AI Decision Engine & Intelligent Control Recommendations Package.
"""

from .feature_analyzer import FeatureAnalyzer, DecisionFactor
from .confidence import ConfidenceCalculator, ConfidenceReport, DISCLAIMER_TEXT
from .explanation_formatter import ExplanationFormatter
from .recommendation_explainer import RecommendationExplainer
from .decision_explainer import DecisionExplainer

DEFAULT_FEATURE_ANALYZER = FeatureAnalyzer()
DEFAULT_CONFIDENCE_CALCULATOR = ConfidenceCalculator()
DEFAULT_FORMATTER = ExplanationFormatter()
DEFAULT_RECOMMENDATION_EXPLAINER = RecommendationExplainer()
DEFAULT_DECISION_EXPLAINER = DecisionExplainer()

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

