"""
Phase 9: AI vs Traditional Scheduling Evaluation & Performance Analytics Package.
"""

from .metrics import (
    TrainMetrics,
    SimulationMetrics,
    calculate_throughput,
    calculate_delay_metrics,
    calculate_waiting_metrics,
    calculate_improvement,
)
from .baseline_scheduler import BaselineScheduler
from .scenario_manager import ScenarioManager
from .evaluator import ScenarioEvaluator
from .comparison_engine import ComparisonEngine
from .report_generator import ReportGenerator

DEFAULT_SCENARIO_MANAGER = ScenarioManager()
DEFAULT_EVALUATOR = ScenarioEvaluator()
DEFAULT_COMPARISON_ENGINE = ComparisonEngine(
    scenario_manager=DEFAULT_SCENARIO_MANAGER,
    evaluator=DEFAULT_EVALUATOR
)

__all__ = [
    "TrainMetrics",
    "SimulationMetrics",
    "calculate_throughput",
    "calculate_delay_metrics",
    "calculate_waiting_metrics",
    "calculate_improvement",
    "BaselineScheduler",
    "ScenarioManager",
    "ScenarioEvaluator",
    "ComparisonEngine",
    "ReportGenerator",
    "DEFAULT_SCENARIO_MANAGER",
    "DEFAULT_EVALUATOR",
    "DEFAULT_COMPARISON_ENGINE",
]

