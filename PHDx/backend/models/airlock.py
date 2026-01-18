"""Pydantic models for EthicsAirlock module."""

from typing import Dict, List
from pydantic import BaseModel, Field


class SanitizeRequest(BaseModel):
    """Request model for PII sanitization."""
    text: str = Field(..., description="Text to sanitize for PII")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Contact Participant John-Doe at john.doe@example.com or 07123456789"
            }
        }


class SanitizeResponse(BaseModel):
    """Response model for PII sanitization result."""
    sanitized_text: str = Field(..., description="Text with PII redacted")
    pii_found: bool = Field(..., description="Whether any PII was detected")
    status: str = Field(..., description="INTERVENTION_REQUIRED or CLEAN")

    class Config:
        json_schema_extra = {
            "example": {
                "sanitized_text": "Contact [REDACTED] at [REDACTED] or [REDACTED]",
                "pii_found": True,
                "status": "INTERVENTION_REQUIRED"
            }
        }
