from typing import List, Dict, Any
from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Schema for root API endpoint response."""
    status: str = Field(..., json_schema_extra={"example": "online"})
    message: str = Field(..., json_schema_extra={"example": "AI-Powered Train Traffic Control API is running"})
    project: str = Field(..., json_schema_extra={"example": "Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    phase: str = Field(..., json_schema_extra={"example": "Phase 1: Project Foundation & System Setup"})
    docs_url: str = Field(..., json_schema_extra={"example": "/docs"})


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    database: str = Field(..., json_schema_extra={"example": "connected"})
    timestamp: str
    uptime_seconds: float
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    environment: str = Field(..., json_schema_extra={"example": "development"})


class EndpointInfo(BaseModel):
    """Schema describing an individual API endpoint."""
    path: str
    method: str
    description: str


class ApiInfoResponse(BaseModel):
    """Schema for API directory information response."""
    project: str
    version: str
    phase: str
    description: str
    endpoints: List[EndpointInfo]
    modules: Dict[str, str]
