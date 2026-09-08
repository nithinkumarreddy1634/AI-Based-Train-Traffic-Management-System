"""
Root forwarding package for Phase 9 Analytics.
Ensures `import analytics` works transparently from workspace root.
"""

import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from analytics import (
    TrainMetrics,
    SimulationMetrics,
    calculate_throughput,
    calculate_delay_metrics,
    calculate_waiting_metrics,
    calculate_improvement,
    BaselineScheduler,
    ScenarioManager,
    ScenarioEvaluator,
    ComparisonEngine,
    ReportGenerator,
    DEFAULT_SCENARIO_MANAGER,
    DEFAULT_EVALUATOR,
    DEFAULT_COMPARISON_ENGINE,
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

