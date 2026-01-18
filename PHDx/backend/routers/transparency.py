"""
TransparencyLog API Router

Endpoints for audit logging operations.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from ..models.transparency import LogEntry, LogEntryCreate, LogListResponse
from ..services.transparency_log import TransparencyLog, get_transparency_log

router = APIRouter(
    prefix="/transparency",
    tags=["Transparency Log"],
    responses={404: {"description": "Not found"}},
)


@router.post("/log", response_model=LogEntry, summary="Create audit log entry")
async def create_log(
    entry: LogEntryCreate,
    logger: TransparencyLog = Depends(get_transparency_log)
) -> LogEntry:
    """
    Create a new audit log entry.

    - **module**: Name of the module generating the event
    - **action**: Description of the action being performed
    - **status**: Status/outcome of the action
    """
    result = logger.log_event(
        module=entry.module,
        action=entry.action,
        status=entry.status
    )
    return LogEntry(**result)


@router.get("/logs", response_model=LogListResponse, summary="Get all audit logs")
async def get_logs(
    module: Optional[str] = None,
    status: Optional[str] = None,
    logger: TransparencyLog = Depends(get_transparency_log)
) -> LogListResponse:
    """
    Retrieve audit logs with optional filtering.

    - **module**: Filter by module name (optional)
    - **status**: Filter by status (optional)
    """
    if module:
        logs = logger.get_logs_by_module(module)
    elif status:
        logs = logger.get_logs_by_status(status)
    else:
        logs = logger.get_logs()

    return LogListResponse(
        count=len(logs),
        logs=[LogEntry(**log) for log in logs]
    )


@router.delete("/logs", summary="Clear all audit logs")
async def clear_logs(
    logger: TransparencyLog = Depends(get_transparency_log)
) -> dict:
    """
    Clear all audit logs (for testing purposes).

    Returns confirmation of the operation.
    """
    logger.clear_logs()
    return {"status": "cleared", "message": "All logs have been cleared"}
