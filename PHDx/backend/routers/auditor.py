"""
Auditor API Router

Endpoints for compliance scoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from ..models.auditor import AuditRequest, AuditResponse
from ..services.auditor import Auditor, get_auditor

router = APIRouter(
    prefix="/auditor",
    tags=["Auditor"],
    responses={404: {"description": "Not found"}},
)


@router.post("/evaluate", response_model=AuditResponse, summary="Evaluate compliance scores")
async def evaluate(
    request: AuditRequest,
    auditor: Auditor = Depends(get_auditor)
) -> AuditResponse:
    """
    Evaluate text against Oxford Brookes PhD compliance criteria.

    Uses exact weights from simulation:
    - Originality: 35%
    - Criticality: 35%
    - Rigour: 30%

    - **text**: Text being evaluated
    - **scores**: Dictionary with scores (0-100) for each criterion

    Returns total weighted score rounded to 2 decimal places.
    """
    # Validate required criteria
    if not auditor.validate_scores(request.scores):
        missing = set(auditor.get_weights().keys()) - set(request.scores.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Missing required criteria: {missing}"
        )

    result = auditor.evaluate(
        text=request.text,
        mock_scores=request.scores
    )

    return AuditResponse(
        total_weighted_score=result["total_weighted_score"],
        weights_applied=auditor.get_weights()
    )


@router.get("/weights", summary="Get scoring weights")
async def get_weights(
    auditor: Auditor = Depends(get_auditor)
) -> Dict[str, float]:
    """
    Get the scoring weights for each criterion.

    Returns the exact weights from the simulation constraint:
    - Originality: 0.35
    - Criticality: 0.35
    - Rigour: 0.30
    """
    return auditor.get_weights()


@router.post("/validate", summary="Validate score submission")
async def validate_scores(
    scores: Dict[str, int],
    auditor: Auditor = Depends(get_auditor)
) -> dict:
    """
    Validate that a score submission contains all required criteria.

    - **scores**: Dictionary of scores to validate

    Returns validation result with any missing criteria.
    """
    required = set(auditor.get_weights().keys())
    provided = set(scores.keys())
    missing = required - provided
    extra = provided - required

    return {
        "valid": len(missing) == 0,
        "required_criteria": list(required),
        "provided_criteria": list(provided),
        "missing_criteria": list(missing),
        "extra_criteria": list(extra)
    }
