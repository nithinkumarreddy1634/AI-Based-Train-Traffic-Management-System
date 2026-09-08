from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
from ..models.railway import (
    StationStatus,
    SectionStatus,
    TrackDirection,
    TrackStatus,
    TrainType,
    TrainPriority,
    TrainStatus,
)


# --- Station Schemas ---
class StationBase(BaseModel):
    station_code: str = Field(..., min_length=2, max_length=10, json_schema_extra={"example": "SEC01"})
    station_name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Central Station"})
    latitude: float = Field(0.0, json_schema_extra={"example": 28.6139})
    longitude: float = Field(0.0, json_schema_extra={"example": 77.2090})
    number_of_platforms: int = Field(2, ge=1, le=20, json_schema_extra={"example": 4})
    status: str = Field(StationStatus.ACTIVE.value, json_schema_extra={"example": "ACTIVE"})

    @field_validator("status")
    @classmethod
    def validate_station_status(cls, v: str) -> str:
        valid = [s.value for s in StationStatus]
        if v.upper() not in valid:
            raise ValueError(f"Invalid station status: {v}. Must be one of {valid}")
        return v.upper()


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    station_code: Optional[str] = Field(None, min_length=2, max_length=10)
    station_name: Optional[str] = Field(None, min_length=2, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    number_of_platforms: Optional[int] = Field(None, ge=1, le=20)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_station_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = [s.value for s in StationStatus]
            if v.upper() not in valid:
                raise ValueError(f"Invalid station status: {v}. Must be one of {valid}")
            return v.upper()
        return v


class StationResponse(StationBase):
    station_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Track Schemas ---
class TrackBase(BaseModel):
    section_id: int
    track_number: int = Field(1, ge=1, le=10, json_schema_extra={"example": 1})
    direction: str = Field(TrackDirection.BOTH.value, json_schema_extra={"example": "UP"})
    maximum_speed: float = Field(100.0, gt=0, json_schema_extra={"example": 110.0})
    status: str = Field(TrackStatus.AVAILABLE.value, json_schema_extra={"example": "AVAILABLE"})
    occupied_by_train: Optional[int] = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        valid = [d.value for d in TrackDirection]
        if v.upper() not in valid:
            raise ValueError(f"Invalid direction: {v}. Must be one of {valid}")
        return v.upper()

    @field_validator("status")
    @classmethod
    def validate_track_status(cls, v: str) -> str:
        valid = [s.value for s in TrackStatus]
        if v.upper() not in valid:
            raise ValueError(f"Invalid track status: {v}. Must be one of {valid}")
        return v.upper()


class TrackCreate(TrackBase):
    pass


class TrackUpdate(BaseModel):
    section_id: Optional[int] = None
    track_number: Optional[int] = Field(None, ge=1, le=10)
    direction: Optional[str] = None
    maximum_speed: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None
    occupied_by_train: Optional[int] = None


class TrackResponse(TrackBase):
    track_id: int
    occupied_train_number: Optional[str] = None
    occupied_train_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Section Schemas ---
class SectionBase(BaseModel):
    section_name: str = Field(..., min_length=2, max_length=120, json_schema_extra={"example": "Central - North Section"})
    start_station_id: int
    end_station_id: int
    length_km: float = Field(..., gt=0, json_schema_extra={"example": 25.5})
    maximum_speed_kmph: float = Field(110.0, gt=0, json_schema_extra={"example": 120.0})
    number_of_tracks: int = Field(2, ge=1, le=6, json_schema_extra={"example": 2})
    status: str = Field(SectionStatus.AVAILABLE.value, json_schema_extra={"example": "AVAILABLE"})

    @field_validator("status")
    @classmethod
    def validate_section_status(cls, v: str) -> str:
        valid = [s.value for s in SectionStatus]
        if v.upper() not in valid:
            raise ValueError(f"Invalid section status: {v}. Must be one of {valid}")
        return v.upper()

    @model_validator(mode="after")
    def validate_different_stations(self):
        if self.start_station_id == self.end_station_id:
            raise ValueError("start_station_id and end_station_id cannot be the same")
        return self


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    section_name: Optional[str] = Field(None, min_length=2, max_length=120)
    start_station_id: Optional[int] = None
    end_station_id: Optional[int] = None
    length_km: Optional[float] = Field(None, gt=0)
    maximum_speed_kmph: Optional[float] = Field(None, gt=0)
    number_of_tracks: Optional[int] = Field(None, ge=1, le=6)
    status: Optional[str] = None


class SectionResponse(SectionBase):
    section_id: int
    start_station_code: Optional[str] = None
    start_station_name: Optional[str] = None
    end_station_code: Optional[str] = None
    end_station_name: Optional[str] = None
    tracks: List[TrackResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Train Schemas ---
class TrainBase(BaseModel):
    train_number: str = Field(..., min_length=2, max_length=20, json_schema_extra={"example": "EXP-101"})
    train_name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Central Express"})
    train_type: str = Field(TrainType.EXPRESS.value, json_schema_extra={"example": "EXPRESS"})
    priority: str = Field(TrainPriority.HIGH.value, json_schema_extra={"example": "HIGH"})
    source_station_id: int
    destination_station_id: int
    current_station_id: Optional[int] = None
    current_section_id: Optional[int] = None
    current_position_km: float = Field(0.0, ge=0)
    speed_kmph: float = Field(0.0, ge=0)
    direction: str = Field("UP", json_schema_extra={"example": "UP"})
    status: str = Field(TrainStatus.SCHEDULED.value, json_schema_extra={"example": "RUNNING"})
    scheduled_departure: str = Field(..., json_schema_extra={"example": "08:00"})
    scheduled_arrival: str = Field(..., json_schema_extra={"example": "10:30"})
    actual_departure: Optional[str] = None
    actual_arrival: Optional[str] = None
    current_delay_minutes: float = Field(0.0, ge=0)

    @field_validator("train_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid = [t.value for t in TrainType]
        if v.upper() not in valid:
            raise ValueError(f"Invalid train type: {v}. Must be one of {valid}")
        return v.upper()

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = [p.value for p in TrainPriority]
        if v.upper() not in valid:
            raise ValueError(f"Invalid priority: {v}. Must be one of {valid}")
        return v.upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = [s.value for s in TrainStatus]
        if v.upper() not in valid:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid}")
        return v.upper()

    @model_validator(mode="after")
    def validate_different_terminals(self):
        if self.source_station_id == self.destination_station_id:
            raise ValueError("source_station_id and destination_station_id cannot be the same")
        return self


class TrainCreate(TrainBase):
    pass


class TrainUpdate(BaseModel):
    train_number: Optional[str] = Field(None, min_length=2, max_length=20)
    train_name: Optional[str] = Field(None, min_length=2, max_length=100)
    train_type: Optional[str] = None
    priority: Optional[str] = None
    source_station_id: Optional[int] = None
    destination_station_id: Optional[int] = None
    current_station_id: Optional[int] = None
    current_section_id: Optional[int] = None
    current_position_km: Optional[float] = Field(None, ge=0)
    speed_kmph: Optional[float] = Field(None, ge=0)
    direction: Optional[str] = None
    status: Optional[str] = None
    scheduled_departure: Optional[str] = None
    scheduled_arrival: Optional[str] = None
    actual_departure: Optional[str] = None
    actual_arrival: Optional[str] = None
    current_delay_minutes: Optional[float] = Field(None, ge=0)


class TrainResponse(TrainBase):
    train_id: int
    source_station_name: Optional[str] = None
    destination_station_name: Optional[str] = None
    current_station_name: Optional[str] = None
    current_section_name: Optional[str] = None
    occupied_track_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# --- Schedule Schemas ---
class ScheduleResponse(BaseModel):
    schedule_id: int
    train_id: int
    train_number: str
    train_name: str
    station_id: int
    station_code: str
    station_name: str
    stop_sequence: int
    scheduled_arrival: Optional[str] = None
    scheduled_departure: Optional[str] = None
    platform_number: int

    model_config = ConfigDict(from_attributes=True)


# --- Network & Dashboard Schemas ---
class NetworkConnection(BaseModel):
    from_station_id: int
    to_station_id: int
    section_id: int
    section_name: str
    length_km: float
    status: str
    tracks_count: int


class NetworkResponse(BaseModel):
    stations: List[StationResponse]
    sections: List[SectionResponse]
    tracks: List[TrackResponse]
    trains: List[TrainResponse]
    connections: List[NetworkConnection]


class DashboardStatsResponse(BaseModel):
    total_trains: int
    active_trains: int
    delayed_trains: int
    scheduled_trains: int
    total_sections: int
    occupied_sections: int
    available_sections: int
    total_tracks: int
    occupied_tracks: int
    track_utilization_percent: float
    system_status: str
