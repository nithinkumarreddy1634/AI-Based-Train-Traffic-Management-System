"""
AI-Powered Train Traffic Optimization Module (Phase 7).

Maximizing section throughput using constraint-based scheduling, safety headway
enforcement, Phase 6 ML delay mitigation, and priority-weighted sequence optimization.
"""
from optimization.config import OptimizationConfig, DEFAULT_CONFIG
from optimization.result import (
    TrainRecommendation,
    BeforeVsAfterMetrics,
    OptimizationResult,
    BenchmarkScenarioResult
)
from optimization.scoring import ThroughputService, ScoringEngine
from optimization.objective import OptimizationObjective
from optimization.constraints import ConstraintValidator
from optimization.candidate_generator import CandidateSequenceGenerator
from optimization.scheduler import CPSATScheduler
from optimization.optimizer import TrainTrafficOptimizer, DEFAULT_OPTIMIZER

__all__ = [
    "OptimizationConfig",
    "DEFAULT_CONFIG",
    "TrainRecommendation",
    "BeforeVsAfterMetrics",
    "OptimizationResult",
    "BenchmarkScenarioResult",
    "ThroughputService",
    "ScoringEngine",
    "OptimizationObjective",
    "ConstraintValidator",
    "CandidateSequenceGenerator",
    "CPSATScheduler",
    "TrainTrafficOptimizer",
    "DEFAULT_OPTIMIZER",
]

