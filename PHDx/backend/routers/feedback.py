"""
FeedbackProcessor API Router

Endpoints for feedback categorization using traffic light system.
"""

from fastapi import APIRouter, Depends
from typing import Any, Dict, List, Union

from ..models.feedback import FeedbackRequest, FeedbackResponse
from ..services.feedback_processor import FeedbackProcessor, get_feedback_processor

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback Processor"],
    responses={404: {"description": "Not found"}},
)


@router.post("/process", response_model=FeedbackResponse, summary="Process and categorize feedback")
async def process_feedback(
    request: FeedbackRequest,
    processor: FeedbackProcessor = Depends(get_feedback_processor)
) -> FeedbackResponse:
    """
    Process and categorize supervisor feedback using traffic light system.

    Uses exact keyword matching from simulation:
    - "blocker" (case-insensitive) -> RED (critical)
    - "consider" (case-insensitive) -> AMBER (review needed)
    - "typo" (case-insensitive) -> GREEN (minor fix)

    - **text**: Feedback text with items separated by newlines

    Returns categorized feedback items by severity.
    """
    categories = processor.process(request.text)
    total_items = sum(len(items) for items in categories.values())

    return FeedbackResponse(
        categories=categories,
        total_items=total_items
    )


@router.post("/priority", summary="Get priority (blocker) items")
async def get_priority_items(
    request: FeedbackRequest,
    processor: FeedbackProcessor = Depends(get_feedback_processor)
) -> Dict[str, Any]:
    """
    Get only the priority (RED/blocker) items from feedback.

    - **text**: Feedback text with items separated by newlines

    Returns only the critical items that need immediate attention.
    """
    categories = processor.process(request.text)
    priority_items = processor.get_priority_items(categories)

    return {
        "priority_items": priority_items,
        "count": len(priority_items)
    }


@router.post("/counts", summary="Get item counts by category")
async def get_counts(
    request: FeedbackRequest,
    processor: FeedbackProcessor = Depends(get_feedback_processor)
) -> Dict[str, Any]:
    """
    Get counts of items in each category.

    - **text**: Feedback text with items separated by newlines

    Returns count per category (RED, AMBER, GREEN).
    """
    categories = processor.process(request.text)
    counts = processor.count_by_category(categories)
    counts["total"] = sum(counts.values())

    return counts
