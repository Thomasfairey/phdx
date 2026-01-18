"""Pydantic models for TransparencyLog module."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class LogEntryCreate(BaseModel):
    """Request model for creating a new log entry."""
    module: str = Field(..., description="Module name that generated the event")
    action: str = Field(..., description="Action being performed")
    status: str = Field(..., description="Status of the action")


class LogEntry(BaseModel):
    """Response model for a single log entry."""
    timestamp: str = Field(..., description="ISO format timestamp")
    module: str = Field(..., description="Module name that generated the event")
    action: str = Field(..., description="Action being performed")
    status: str = Field(..., description="Status of the action")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00.000000",
                "module": "Airlock",
                "action": "PII Scrubbing",
                "status": "CLEAN"
            }
        }


class LogListResponse(BaseModel):
    """Response model for listing all log entries."""
    count: int = Field(..., description="Total number of log entries")
    logs: List[LogEntry] = Field(default_factory=list, description="List of log entries")
