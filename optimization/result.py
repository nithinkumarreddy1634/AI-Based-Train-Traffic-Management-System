"""
Structured Optimization Result Schemas.

Defines strongly typed dataclasses for recommendations, comparative before-vs-after metrics,
and multi-factor explainability breakdowns.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class TrainRecommendation:
    """Individual action and dispatch schedule recommendation for a train."""
    train_id: int
    train_number: str
    train_type: str
    priority: str
    action: str  # 'PROCEED', 'HOLD', 'PRIORITIZE', 'DIVERT_LOOP'
    recommended_entry_time_sec: int
    recommended_entry_time: str
    hold_duration_seconds: int
    expected_delay_minutes: float
    expected_exit_time_sec: int
    reason: str
    current_delay_minutes: float = 0.0
    predicted_additional_delay: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BeforeVsAfterMetrics:
    """Rigorous before vs after comparative performance metrics."""
    current_throughput: float
    optimized_throughput: float
    throughput_improvement_pct: float

    current_total_delay: float
    optimized_total_delay: float
    delay_reduction_pct: float

    current_waiting_time: float
    optimized_waiting_time: float
    waiting_time_reduction_pct: float

    current_section_utilization: float
    optimized_section_utilization: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationResult:
    """Complete result returned by the AI traffic optimizer."""
    optimization_id: int
    timestamp: str
    status: str  # 'OPTIMIZED', 'FEASIBLE', 'NO_FEASIBLE_SOLUTION', 'ERROR'
    target_section_id: Optional[int]
    monitored_section_name: str
    train_count: int
    recommended_sequence: List[str]  # List of train numbers in recommended order
    train_recommendations: List[TrainRecommendation]
    expected_throughput: float
    expected_total_delay: float
    expected_waiting_time: float
    optimization_score: float
    before_vs_after: BeforeVsAfterMetrics
    explanation: str
    factor_contributions: Dict[str, float] = field(default_factory=dict)
    solver_diagnostics: Dict[str, Any] = field(default_factory=dict)
    applied: bool = False
    safety_validation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimization_id": self.optimization_id,
            "timestamp": self.timestamp,
            "status": self.status,
            "target_section_id": self.target_section_id,
            "monitored_section_name": self.monitored_section_name,
            "train_count": self.train_count,
            "recommended_sequence": self.recommended_sequence,
            "train_recommendations": [r.to_dict() for r in self.train_recommendations],
            "expected_throughput": round(self.expected_throughput, 2),
            "expected_total_delay": round(self.expected_total_delay, 2),
            "expected_waiting_time": round(self.expected_waiting_time, 2),
            "optimization_score": round(self.optimization_score, 2),
            "before_vs_after": self.before_vs_after.to_dict(),
            "explanation": self.explanation,
            "factor_contributions": self.factor_contributions,
            "solver_diagnostics": self.solver_diagnostics,
            "applied": self.applied,
            "safety_validation": self.safety_validation,
        }


@dataclass
class BenchmarkScenarioResult:
    """Benchmark comparative results for standard testing scenarios."""
    scenario_id: str
    scenario_name: str
    train_count: int
    traffic_level: str
    current_throughput: float
    optimized_throughput: float
    throughput_gain_pct: float
    current_delay: float
    optimized_delay: float
    delay_reduction_pct: float
    current_waiting: float
    optimized_waiting: float
    waiting_reduction_pct: float
    status: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

