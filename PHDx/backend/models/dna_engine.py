"""Pydantic models for DNAEngine module."""

from typing import Optional
from pydantic import BaseModel, Field


class StyleAnalysisRequest(BaseModel):
    """Request model for style analysis."""
    text: str = Field(..., description="Text to analyze for writing style")
    author_baseline_variance: Optional[float] = Field(
        default=15.0,
        description="Author's baseline sentence variance for comparison"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a sample text. It has multiple sentences. Some are longer than others to test variance.",
                "author_baseline_variance": 15.0
            }
        }


class StyleAnalysisResponse(BaseModel):
    """Response model for style analysis result."""
    variance: float = Field(..., description="Calculated sentence length variance")
    style_match: bool = Field(..., description="Whether style matches author baseline")
    status: str = Field(..., description="MATCH or ANOMALY_DETECTED")

    class Config:
        json_schema_extra = {
            "example": {
                "variance": 12.5,
                "style_match": True,
                "status": "MATCH"
            }
        }
