"""
REST API Router for Phase 9: AI vs Traditional Scheduling Evaluation & Performance Analytics.

Provides endpoints for:
1. GET  /api/analytics/scenarios - Catalog of standardized benchmark scenarios
2. POST /api/analytics/run - Run head-to-head simulation experiment
3. GET  /api/analytics/experiments - History of benchmark experiments
4. GET  /api/analytics/experiments/{id} - Experiment detail and run records
5. GET  /api/analytics/compare/{id} - Head-to-head comparison summary and scores
6. GET  /api/analytics/metrics/{id} - Detailed run-by-run and train-level metrics
7. GET  /api/analytics/export/{id} - Export experiment data as CSV or JSON
"""

import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.railway import Experiment, ExperimentResult, ComparisonResult
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.railway import Experiment, ExperimentResult, ComparisonResult

from analytics import (
    DEFAULT_SCENARIO_MANAGER,
    DEFAULT_COMPARISON_ENGINE,
    ReportGenerator,
)

router = APIRouter(prefix="/api/analytics", tags=["Evaluation & Performance Analytics"])


class RunExperimentRequest(BaseModel):
    scenario_id: str = Field(default="medium_traffic", description="Benchmark scenario identifier")
    runs_count: int = Field(default=1, ge=1, le=10, description="Number of simulation repetitions (1 to 10)")
    name: Optional[str] = Field(default=None, description="Custom experiment name")
    description: Optional[str] = Field(default=None, description="Custom experiment notes")


@router.get("/scenarios", response_model=List[Dict[str, Any]])
def get_benchmark_scenarios():
    """Returns the catalog of 6 standardized repeatable benchmark scenarios."""
    return DEFAULT_SCENARIO_MANAGER.list_scenarios()


@router.post("/run", response_model=Dict[str, Any])
def run_benchmark_experiment(
    payload: RunExperimentRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a head-to-head evaluation experiment between Traditional Baseline and AI Optimization.
    Runs under strictly identical initial conditions and persists results to SQLite.
    """
    try:
        result = DEFAULT_COMPARISON_ENGINE.run_experiment(
            scenario_id=payload.scenario_id,
            runs_count=payload.runs_count,
            name=payload.name,
            description=payload.description,
            db_session=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment simulation failed: {str(e)}")


@router.get("/experiments", response_model=List[Dict[str, Any]])
def list_experiments(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists historical benchmark experiments from database."""
    exps = db.query(Experiment).order_by(Experiment.experiment_id.desc()).limit(limit).all()
    results = []
    for exp in exps:
        comp = db.query(ComparisonResult).filter(ComparisonResult.experiment_id == exp.experiment_id).first()
        results.append({
            "experiment_id": exp.experiment_id,
            "name": exp.name,
            "description": exp.description,
            "scenario_name": exp.scenario_name,
            "traffic_density": exp.traffic_density,
            "num_trains": exp.num_trains,
            "delay_profile": exp.delay_profile,
            "runs_count": exp.runs_count,
            "status": exp.status,
            "timestamp": exp.timestamp,
            "throughput_gain_pct": comp.throughput_gain_pct if comp else 0.0,
            "delay_reduction_pct": comp.delay_reduction_pct if comp else 0.0,
            "overall_performance_score": comp.overall_performance_score if comp else 0.0,
            "safety_compliant": comp.safety_compliant if comp else True,
        })
    return results


@router.get("/experiments/{experiment_id}", response_model=Dict[str, Any])
def get_experiment_detail(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """Returns complete details of a specific experiment including runs and comparisons."""
    exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    comp = db.query(ComparisonResult).filter(ComparisonResult.experiment_id == experiment_id).first()
    results = db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).all()

    trad_runs = []
    ai_runs = []
    for r in results:
        r_dict = {
            "result_id": r.result_id,
            "run_number": r.run_number,
            "scheduler_type": r.scheduler_type,
            "throughput_tph": r.throughput_tph,
            "completed_trains": r.completed_trains,
            "avg_delay_minutes": r.avg_delay_minutes,
            "max_delay_minutes": r.max_delay_minutes,
            "min_delay_minutes": r.min_delay_minutes,
            "total_delay_minutes": r.total_delay_minutes,
            "median_delay_minutes": r.median_delay_minutes,
            "total_waiting_time": r.total_waiting_time,
            "avg_waiting_time": r.avg_waiting_time,
            "max_waiting_time": r.max_waiting_time,
            "section_utilization_pct": r.section_utilization_pct,
            "peak_traffic_density": r.peak_traffic_density,
            "bottleneck_duration_sec": r.bottleneck_duration_sec,
            "total_conflicts": r.total_conflicts,
            "critical_conflicts": r.critical_conflicts,
            "resolved_conflicts": r.resolved_conflicts,
            "safety_violations": r.safety_violations,
            "unsafe_plans_applied": r.unsafe_plans_applied,
            "avg_journey_time_min": r.avg_journey_time_min,
            "detailed_metrics": json.loads(r.detailed_metrics_json) if r.detailed_metrics_json else {},
        }
        if r.scheduler_type == "TRADITIONAL":
            trad_runs.append(r_dict)
        else:
            ai_runs.append(r_dict)

    stats = json.loads(comp.statistical_summary_json) if (comp and comp.statistical_summary_json) else {}

    return {
        "experiment_id": exp.experiment_id,
        "name": exp.name,
        "description": exp.description,
        "scenario_name": exp.scenario_name,
        "traffic_density": exp.traffic_density,
        "num_trains": exp.num_trains,
        "delay_profile": exp.delay_profile,
        "simulation_duration": exp.simulation_duration,
        "runs_count": exp.runs_count,
        "status": exp.status,
        "timestamp": exp.timestamp,
        "traditional_runs": trad_runs,
        "ai_runs": ai_runs,
        "traditional_summary": stats.get("traditional", {}),
        "ai_summary": stats.get("ai", {}),
        "comparison": {
            "throughput_gain_pct": comp.throughput_gain_pct if comp else 0.0,
            "delay_reduction_pct": comp.delay_reduction_pct if comp else 0.0,
            "waiting_time_reduction_pct": comp.waiting_time_reduction_pct if comp else 0.0,
            "conflict_reduction_pct": comp.conflict_reduction_pct if comp else 0.0,
            "overall_performance_score": comp.overall_performance_score if comp else 0.0,
            "safety_compliant": comp.safety_compliant if comp else True,
            "summary_text": comp.summary_text if comp else "",
        } if comp else {}
    }


@router.get("/compare/{experiment_id}", response_model=Dict[str, Any])
def get_experiment_comparison(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """Returns comparative KPIs and scoring for a given experiment."""
    comp = db.query(ComparisonResult).filter(ComparisonResult.experiment_id == experiment_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison result not found")

    stats = json.loads(comp.statistical_summary_json) if comp.statistical_summary_json else {}

    return {
        "experiment_id": comp.experiment_id,
        "throughput_gain_pct": comp.throughput_gain_pct,
        "delay_reduction_pct": comp.delay_reduction_pct,
        "waiting_time_reduction_pct": comp.waiting_time_reduction_pct,
        "conflict_reduction_pct": comp.conflict_reduction_pct,
        "overall_performance_score": comp.overall_performance_score,
        "safety_compliant": comp.safety_compliant,
        "summary_text": comp.summary_text,
        "statistical_summary": stats,
    }


@router.get("/metrics/{experiment_id}", response_model=Dict[str, Any])
def get_experiment_metrics(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """Returns granular train-level and time-series metrics for the experiment."""
    results = db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).all()
    if not results:
        raise HTTPException(status_code=404, detail="Metrics not found")

    runs = []
    for r in results:
        runs.append({
            "run_number": r.run_number,
            "scheduler_type": r.scheduler_type,
            "throughput_tph": r.throughput_tph,
            "completed_trains": r.completed_trains,
            "avg_delay_minutes": r.avg_delay_minutes,
            "total_waiting_time": r.total_waiting_time,
            "detailed": json.loads(r.detailed_metrics_json) if r.detailed_metrics_json else {}
        })

    return {
        "experiment_id": experiment_id,
        "runs": runs,
    }


@router.get("/export/{experiment_id}")
def export_experiment(
    experiment_id: int,
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Exports benchmark experiment data as downloadable CSV or JSON."""
    exp_detail = get_experiment_detail(experiment_id, db)

    if format.lower() == "json":
        json_content = ReportGenerator.generate_json(exp_detail)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}.json"}
        )

    csv_content = ReportGenerator.generate_csv(exp_detail)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}.csv"}
    )
