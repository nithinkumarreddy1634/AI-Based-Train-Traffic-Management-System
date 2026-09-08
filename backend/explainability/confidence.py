"""
Decision Confidence Calculator for Explainable AI Train Traffic Decisions.

Computes transparent, multi-factor confidence ratings (HIGH, MEDIUM, LOW)
based on observable data completeness, optimizer margin, and safety verification.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


DISCLAIMER_TEXT = (
    "Decision confidence is an internal decision-support indicator and is not a probability of operational safety."
)


@dataclass
class ConfidenceReport:
    """Detailed confidence breakdown for an AI recommendation."""
    level: str  # 'HIGH', 'MEDIUM', 'LOW'
    score: float  # 0.0 to 100.0 scale
    factors: Dict[str, float]
    rationale: str
    disclaimer: str = DISCLAIMER_TEXT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfidenceCalculator:
    """Assesses empirical decision confidence without claiming statistical certainty."""

    @staticmethod
    def calculate_confidence(
        optimization_status: str,
        safety_validation_status: str,
        safety_violations_count: int,
        score_margin: float = 15.0,
        candidates_count: int = 4,
        data_completeness_pct: float = 100.0,
        ml_prediction_available: bool = True
    ) -> ConfidenceReport:
        """
        Computes composite confidence score from measurable parameters:
        1. Optimization status (OPTIMIZED = 30 pts, FEASIBLE = 20 pts, fallback = 10 pts)
        2. Safety Validation (CLEAN APPROVED = 30 pts, WARNINGS = 15 pts, REJECTED = 0 pts)
        3. Solution Margin over alternatives (up to 20 pts)
        4. Data Completeness & ML availability (up to 20 pts)
        """
        factor_scores: Dict[str, float] = {}

        # 1. Optimizer convergence factor (max 30)
        if optimization_status == "OPTIMIZED":
            factor_scores["solver_convergence"] = 30.0
        elif optimization_status == "FEASIBLE":
            factor_scores["solver_convergence"] = 22.0
        else:
            factor_scores["solver_convergence"] = 8.0

        # 2. Safety Validation cleanliness (max 30)
        if safety_validation_status == "APPROVED" and safety_violations_count == 0:
            factor_scores["safety_verification"] = 30.0
        elif safety_validation_status == "APPROVED":
            factor_scores["safety_verification"] = 18.0
        else:
            # If rejected by safety, confidence drops to zero
            factor_scores["safety_verification"] = 0.0

        # 3. Decision margin over candidate alternatives (max 20)
        if score_margin >= 20.0 and candidates_count >= 3:
            factor_scores["alternative_separation"] = 20.0
        elif score_margin >= 10.0 and candidates_count >= 2:
            factor_scores["alternative_separation"] = 14.0
        elif candidates_count >= 1:
            factor_scores["alternative_separation"] = 8.0
        else:
            factor_scores["alternative_separation"] = 4.0

        # 4. Telemetry completeness & ML prediction quality (max 20)
        data_score = 10.0 * (min(100.0, max(0.0, data_completeness_pct)) / 100.0)
        ml_score = 10.0 if ml_prediction_available else 4.0
        factor_scores["telemetry_completeness"] = round(data_score + ml_score, 1)

        total_score = round(sum(factor_scores.values()), 1)

        # Categorize
        if safety_validation_status != "APPROVED" or safety_violations_count > 0:
            level = "LOW"
            rationale = "Low confidence: recommendation triggered safety validation constraints and cannot be applied."
        elif total_score >= 80.0:
            level = "HIGH"
            rationale = (
                f"High confidence ({total_score}/100): Optimal solver convergence with {candidates_count} evaluated "
                f"candidates, robust {score_margin:.1f} pt margin over runner-up, and 100% clean safety audit."
            )
        elif total_score >= 55.0:
            level = "MEDIUM"
            rationale = (
                f"Moderate confidence ({total_score}/100): Feasible dispatch solution identified with acceptable "
                f"headway separation, though alternative margins or telemetry certainty are moderate."
            )
        else:
            level = "LOW"
            rationale = f"Low confidence ({total_score}/100): Constrained solution space or high corridor contention."

        return ConfidenceReport(
            level=level,
            score=total_score,
            factors=factor_scores,
            rationale=rationale,
            disclaimer=DISCLAIMER_TEXT
        )

