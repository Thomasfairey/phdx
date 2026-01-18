"""Pydantic models for FeedbackProcessor module."""

from typing import Dict, List
from enum import Enum
from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    """Traffic light categories for feedback."""
    RED = "RED"      # Blockers - critical issues
    AMBER = "AMBER"  # Considerations - things to review
    GREEN = "GREEN"  # Typos - minor fixes


class FeedbackRequest(BaseModel):
    """Request model for feedback processing."""
    text: str = Field(..., description="Feedback text to categorize (newline-separated items)")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a blocker issue\nConsider revising this section\nThere is a typo here"
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for categorized feedback."""
    categories: Dict[str, List[str]] = Field(
        ...,
        description="Feedback items categorized by severity (RED, AMBER, GREEN)"
    )
    total_items: int = Field(..., description="Total number of feedback items processed")

    class Config:
        json_schema_extra = {
            "example": {
                "categories": {
                    "RED": ["This is a blocker issue"],
                    "AMBER": ["Consider revising this section"],
                    "GREEN": ["There is a typo here"]
                },
                "total_items": 3
            }
        }
