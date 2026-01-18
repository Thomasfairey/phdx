"""
DNAEngine API Router

Endpoints for writing style analysis.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from ..models.dna_engine import StyleAnalysisRequest, StyleAnalysisResponse
from ..services.dna_engine import DNAEngine, get_dna_engine

router = APIRouter(
    prefix="/dna",
    tags=["DNA Engine"],
    responses={404: {"description": "Not found"}},
)


@router.post("/analyze", response_model=StyleAnalysisResponse, summary="Analyze writing style")
async def analyze_style(
    request: StyleAnalysisRequest,
    engine: DNAEngine = Depends(get_dna_engine)
) -> StyleAnalysisResponse:
    """
    Analyze writing style using sentence length variance.

    Uses exact formula from simulation:
    - Split text by periods
    - Calculate mean sentence length (word count)
    - Calculate variance: sum((x - mean)^2) / n
    - Compare to baseline - 5.0 threshold

    - **text**: Text to analyze for writing style
    - **author_baseline_variance**: Optional baseline variance (default: 15.0)

    Returns variance, style match status, and MATCH/ANOMALY_DETECTED.
    """
    result = engine.analyze_style(
        text=request.text,
        baseline_variance=request.author_baseline_variance
    )

    return StyleAnalysisResponse(
        variance=result["variance"],
        style_match=result["style_match"],
        status=result["status"]
    )


@router.get("/baseline", summary="Get current baseline variance")
async def get_baseline(
    engine: DNAEngine = Depends(get_dna_engine)
) -> dict:
    """
    Get the current author baseline variance.

    Returns the threshold used for style matching.
    """
    return {
        "author_baseline_variance": engine.get_baseline(),
        "match_threshold": engine.get_baseline() - 5.0
    }


@router.put("/baseline", summary="Update baseline variance")
async def set_baseline(
    variance: float,
    engine: DNAEngine = Depends(get_dna_engine)
) -> dict:
    """
    Update the author baseline variance.

    - **variance**: New baseline variance value

    Returns confirmation with the new threshold.
    """
    engine.set_baseline(variance)
    return {
        "status": "updated",
        "author_baseline_variance": variance,
        "match_threshold": variance - 5.0
    }
