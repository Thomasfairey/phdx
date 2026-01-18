"""FastAPI routers for PHDx production backend."""

from .transparency import router as transparency_router
from .airlock import router as airlock_router
from .dna_engine import router as dna_engine_router
from .auditor import router as auditor_router
from .feedback import router as feedback_router

__all__ = [
    "transparency_router",
    "airlock_router",
    "dna_engine_router",
    "auditor_router",
    "feedback_router",
]
