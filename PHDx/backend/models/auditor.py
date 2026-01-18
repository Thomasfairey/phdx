"""Pydantic models for Auditor module."""

from typing import Dict, Optional
from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    """Request model for compliance audit evaluation."""
    text: str = Field(..., description="Text to evaluate")
    scores: Dict[str, int] = Field(
        ...,
        description="Scores for each criterion: Originality, Criticality, Rigour (0-100)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This research contributes to the field by...",
                "scores": {
                    "Originality": 85,
                    "Criticality": 78,
                    "Rigour": 82
                }
            }
        }


class AuditResponse(BaseModel):
    """Response model for compliance audit result."""
    total_weighted_score: float = Field(
        ...,
        description="Total weighted score (Originality: 35%, Criticality: 35%, Rigour: 30%)"
    )
    weights_applied: Dict[str, float] = Field(
        ...,
        description="Weights applied to each criterion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_weighted_score": 81.65,
                "weights_applied": {
                    "Originality": 0.35,
                    "Criticality": 0.35,
                    "Rigour": 0.30
                }
            }
        }
