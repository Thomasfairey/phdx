"""
EthicsAirlock API Router

Endpoints for PII detection and sanitization.
"""

from fastapi import APIRouter, Depends
from typing import Dict

from ..models.airlock import SanitizeRequest, SanitizeResponse
from ..services.ethics_airlock import EthicsAirlock, get_ethics_airlock

router = APIRouter(
    prefix="/airlock",
    tags=["Ethics Airlock"],
    responses={404: {"description": "Not found"}},
)


@router.post("/sanitize", response_model=SanitizeResponse, summary="Sanitize text for PII")
async def sanitize_text(
    request: SanitizeRequest,
    airlock: EthicsAirlock = Depends(get_ethics_airlock)
) -> SanitizeResponse:
    """
    Sanitize text by detecting and redacting PII.

    Uses exact regex patterns from simulation:
    - Email addresses
    - UK phone numbers (+44 or 07 prefix)
    - Participant names (with CamelCase and hyphen support)

    - **text**: Text to sanitize for PII

    Returns sanitized text and detection status.
    """
    sanitized_text, pii_found = airlock.sanitize(request.text)
    status = "INTERVENTION_REQUIRED" if pii_found else "CLEAN"

    return SanitizeResponse(
        sanitized_text=sanitized_text,
        pii_found=pii_found,
        status=status
    )


@router.post("/detect", summary="Detect PII without redacting")
async def detect_pii(
    request: SanitizeRequest,
    airlock: EthicsAirlock = Depends(get_ethics_airlock)
) -> Dict:
    """
    Detect PII in text without redacting.

    Useful for analysis or preview before sanitization.

    - **text**: Text to analyze for PII

    Returns dictionary of detected PII by type.
    """
    detected = airlock.detect_pii(request.text)
    return {
        "detected_pii": detected,
        "pii_found": bool(detected),
        "types_found": list(detected.keys())
    }


@router.get("/patterns", summary="Get PII detection patterns")
async def get_patterns(
    airlock: EthicsAirlock = Depends(get_ethics_airlock)
) -> Dict[str, str]:
    """
    Get the regex patterns used for PII detection.

    Returns the exact patterns from the simulation constraint.
    """
    return airlock.get_patterns()
