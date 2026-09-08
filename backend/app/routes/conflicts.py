"""
FastAPI Routes for Phase 5: Train Conflict Detection and Congestion Analysis.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from simulation import simulation_engine

router = APIRouter(prefix="/api", tags=["Conflicts & Congestion"])


@router.get("/conflicts", summary="Get all conflicts with optional filters")
def get_conflicts(
    active_only: bool = Query(True, description="Filter for active conflicts only"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)"),
    section_id: Optional[int] = Query(None, description="Filter by section ID")
):
    """Returns detected railway traffic conflicts according to filters."""
    conflicts = simulation_engine.get_conflicts(
        active_only=active_only,
        severity=severity,
        section_id=section_id
    )
    return {
        "count": len(conflicts),
        "active_only": active_only,
        "severity_filter": severity,
        "section_id_filter": section_id,
        "conflicts": conflicts
    }


@router.get("/conflicts/active", summary="Get current active conflicts")
def get_active_conflicts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    section_id: Optional[int] = Query(None, description="Filter by section ID")
):
    """Returns currently active unresolved railway conflicts."""
    conflicts = simulation_engine.get_conflicts(
        active_only=True,
        severity=severity,
        section_id=section_id
    )
    return {
        "count": len(conflicts),
        "conflicts": conflicts
    }


@router.get("/conflicts/history", summary="Get resolved conflict history")
def get_conflict_history():
    """Returns historical resolved conflicts with duration and resolution timestamps."""
    history = simulation_engine.get_conflict_history()
    return {
        "count": len(history),
        "history": history
    }


@router.get("/conflicts/{conflict_id}", summary="Get conflict by ID")
def get_conflict_detail(conflict_id: str):
    """Returns comprehensive details, kinematics, and recommendations for a specific conflict."""
    conflict = simulation_engine.get_conflict_by_id(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail=f"Conflict '{conflict_id}' not found.")
    return conflict


@router.get("/congestion", summary="Get corridor congestion analysis")
def get_congestion():
    """Returns real-time congestion analysis across all railway sections."""
    data = simulation_engine.get_congestion()
    return {
        "count": len(data),
        "congestion": data
    }


@router.get("/congestion/{section_id}", summary="Get congestion for a specific section")
def get_section_congestion(section_id: int):
    """Returns detailed congestion metrics for a single section."""
    sec_data = simulation_engine.get_congestion(section_id=section_id)
    if not sec_data:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found in congestion analysis.")
    return sec_data


@router.get("/bottlenecks", summary="Get ranked bottleneck sections")
def get_bottlenecks():
    """Returns transparent multi-criteria bottleneck ranking across all sections."""
    bottlenecks = simulation_engine.get_bottlenecks()
    return {
        "count": len(bottlenecks),
        "bottlenecks": bottlenecks
    }

