from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ..database.session import get_db
from ..services.railway_service import RailwayService
from ..schemas.railway import (
    StationCreate,
    StationUpdate,
    StationResponse,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    TrackCreate,
    TrackUpdate,
    TrackResponse,
    TrainCreate,
    TrainUpdate,
    TrainResponse,
    ScheduleResponse,
    NetworkResponse,
    DashboardStatsResponse,
)

router = APIRouter(prefix="/api", tags=["Railway Infrastructure & Operations"])


# =============================================================================
# STATIONS
# =============================================================================
@router.get(
    "/stations",
    response_model=List[StationResponse],
    summary="List All Stations",
    description="Retrieve all railway stations including operational status and platform counts.",
)
def get_stations(db: Session = Depends(get_db)):
    return RailwayService.get_all_stations(db)


@router.get(
    "/stations/{station_id}",
    response_model=StationResponse,
    summary="Get Station By ID",
    description="Retrieve details of a specific railway station by its unique ID.",
)
def get_station(station_id: int, db: Session = Depends(get_db)):
    return RailwayService.get_station_by_id(db, station_id)


@router.post(
    "/stations",
    response_model=StationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Station",
    description="Add a new railway station to the network.",
)
def create_station(data: StationCreate, db: Session = Depends(get_db)):
    return RailwayService.create_station(db, data)


@router.put(
    "/stations/{station_id}",
    response_model=StationResponse,
    summary="Update Station",
    description="Update parameters of an existing station.",
)
def update_station(station_id: int, data: StationUpdate, db: Session = Depends(get_db)):
    return RailwayService.update_station(db, station_id, data)


@router.delete(
    "/stations/{station_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Station",
    description="Remove a station from the network.",
)
def delete_station(station_id: int, db: Session = Depends(get_db)):
    RailwayService.delete_station(db, station_id)
    return None


# =============================================================================
# SECTIONS
# =============================================================================
@router.get(
    "/sections",
    response_model=List[SectionResponse],
    summary="List All Sections",
    description="Retrieve all railway track sections connecting stations.",
)
def get_sections(db: Session = Depends(get_db)):
    return RailwayService.get_all_sections(db)


@router.get(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Get Section By ID",
    description="Retrieve details of a specific railway section.",
)
def get_section(section_id: int, db: Session = Depends(get_db)):
    return RailwayService.get_section_by_id(db, section_id)


@router.post(
    "/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Section",
    description="Create a new railway section connecting two distinct stations.",
)
def create_section(data: SectionCreate, db: Session = Depends(get_db)):
    return RailwayService.create_section(db, data)


@router.put(
    "/sections/{section_id}",
    response_model=SectionResponse,
    summary="Update Section",
    description="Update section attributes like speed limit or operational status.",
)
def update_section(section_id: int, data: SectionUpdate, db: Session = Depends(get_db)):
    return RailwayService.update_section(db, section_id, data)


@router.delete(
    "/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Section",
    description="Remove a railway section and its child tracks.",
)
def delete_section(section_id: int, db: Session = Depends(get_db)):
    RailwayService.delete_section(db, section_id)
    return None


# =============================================================================
# TRACKS
# =============================================================================
@router.get(
    "/tracks",
    response_model=List[TrackResponse],
    summary="List All Tracks",
    description="Retrieve all individual railway tracks and their occupancy state.",
)
def get_tracks(db: Session = Depends(get_db)):
    return RailwayService.get_all_tracks(db)


@router.get(
    "/tracks/{track_id}",
    response_model=TrackResponse,
    summary="Get Track By ID",
    description="Retrieve details of a specific track.",
)
def get_track(track_id: int, db: Session = Depends(get_db)):
    return RailwayService.get_track_by_id(db, track_id)


@router.post(
    "/tracks",
    response_model=TrackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Track",
    description="Add a track to a section.",
)
def create_track(data: TrackCreate, db: Session = Depends(get_db)):
    return RailwayService.create_track(db, data)


@router.put(
    "/tracks/{track_id}",
    response_model=TrackResponse,
    summary="Update Track",
    description="Update track direction, status, or assign/clear train occupancy.",
)
def update_track(track_id: int, data: TrackUpdate, db: Session = Depends(get_db)):
    return RailwayService.update_track(db, track_id, data)


# =============================================================================
# TRAINS
# =============================================================================
@router.get(
    "/trains",
    response_model=List[TrainResponse],
    summary="List Trains",
    description="Retrieve all trains with optional filtering by type, priority, status, or search query.",
)
def get_trains(
    train_type: Optional[str] = Query(None, description="Filter by train type (EXPRESS, PASSENGER, LOCAL, FREIGHT)"),
    priority: Optional[str] = Query(None, description="Filter by priority (HIGH, MEDIUM, LOW)"),
    train_status: Optional[str] = Query(None, alias="status", description="Filter by status (RUNNING, SCHEDULED, DELAYED, etc.)"),
    search: Optional[str] = Query(None, description="Search by train number or name"),
    db: Session = Depends(get_db),
):
    return RailwayService.get_all_trains(
        db,
        train_type=train_type,
        priority=priority,
        train_status=train_status,
        search=search,
    )


@router.get(
    "/trains/{train_id}",
    response_model=TrainResponse,
    summary="Get Train By ID",
    description="Retrieve full live telemetry and parameters for a specific train.",
)
def get_train(train_id: int, db: Session = Depends(get_db)):
    return RailwayService.get_train_by_id(db, train_id)


@router.post(
    "/trains",
    response_model=TrainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Train",
    description="Register a new train in the railway corridor.",
)
def create_train(data: TrainCreate, db: Session = Depends(get_db)):
    return RailwayService.create_train(db, data)


@router.put(
    "/trains/{train_id}",
    response_model=TrainResponse,
    summary="Update Train",
    description="Update speed, location, delay, or status of a train.",
)
def update_train(train_id: int, data: TrainUpdate, db: Session = Depends(get_db)):
    return RailwayService.update_train(db, train_id, data)


@router.delete(
    "/trains/{train_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Train",
    description="Remove a train and release its occupied tracks.",
)
def delete_train(train_id: int, db: Session = Depends(get_db)):
    RailwayService.delete_train(db, train_id)
    return None


# =============================================================================
# NETWORK GRAPH
# =============================================================================
@router.get(
    "/network",
    response_model=NetworkResponse,
    summary="Get Complete Railway Network",
    description="Retrieve the complete railway network topology, stations, sections, tracks, and active trains.",
)
def get_network(db: Session = Depends(get_db)):
    return RailwayService.get_complete_network(db)


# =============================================================================
# TRAIN SCHEDULES
# =============================================================================
@router.get(
    "/schedules",
    response_model=List[ScheduleResponse],
    summary="Get Train Schedules",
    description="Retrieve all timetabled stops and platforms for trains operating on the corridor.",
)
def get_schedules(db: Session = Depends(get_db)):
    return RailwayService.get_all_schedules(db)


# =============================================================================
# DASHBOARD REAL-TIME STATS
# =============================================================================
@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Get Dashboard Statistics",
    description="Calculates live operational metrics from database tables for display on the dashboard.",
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    return RailwayService.get_dashboard_stats(db)
