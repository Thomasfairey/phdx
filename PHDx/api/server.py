"""
PHDx FastAPI Server - Headless Backend

Production-ready API server with:
- Environment-based configuration
- CORS with configurable origins
- Rate limiting
- Comprehensive error handling
- Health checks
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core import airlock
from core import llm_gateway
from core.config import get_config, Environment
from core.ethics_utils import scrub_text, get_usage_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BACKUPS_DIR = Path(__file__).parent.parent / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        now = datetime.now().timestamp()
        minute_ago = now - 60

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > minute_ago
        ]

        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False

        self.requests[client_id].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """Rate limit dependency."""
    config = get_config()
    if not config.rate_limit.enabled:
        return

    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class GenerateRequest(BaseModel):
    """Request to generate text content."""
    doc_id: Optional[str] = None
    prompt: str = Field(..., min_length=1, max_length=50000)
    model: str = "claude"
    context: Optional[str] = None


class GenerateResponse(BaseModel):
    """Response from text generation."""
    success: bool
    text: str
    model: str
    tokens_used: int
    scrubbed: bool
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """System status response."""
    system: str
    environment: str
    models: List[str]
    version: str = "2.0.0"


class AuthResponse(BaseModel):
    """Authentication response."""
    email: str
    name: str
    authenticated: bool
    mock: Optional[bool] = None


class FileInfo(BaseModel):
    """File information."""
    id: str
    name: str
    type: str
    source: str = "google_drive"
    path: Optional[str] = None
    modified: Optional[str] = None
    size_bytes: Optional[int] = None


class SnapshotRequest(BaseModel):
    """Request to save a snapshot."""
    doc_id: str
    timestamp: str
    content: str


class SnapshotResponse(BaseModel):
    """Response from snapshot save."""
    success: bool
    filename: str = ""
    path: str = ""
    size_bytes: int = 0
    error: Optional[str] = None


class SyncRequest(BaseModel):
    """Request to sync to Google Docs."""
    doc_id: str
    content: str
    section_title: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from Google Docs sync."""
    success: bool
    doc_url: Optional[str] = None
    characters_synced: int = 0
    error: Optional[str] = None


class SanitizeRequest(BaseModel):
    """Request to sanitize text."""
    text: str = Field(..., min_length=1, max_length=100000)


class SanitizeResponse(BaseModel):
    """Response from text sanitization."""
    sanitized_text: str
    pii_found: bool
    redactions_count: int = 0


class AuditRequest(BaseModel):
    """Request to audit text."""
    text: str = Field(..., min_length=100)
    chapter_context: Optional[str] = None


class ConsistencyRequest(BaseModel):
    """Request to check consistency."""
    text: str = Field(..., min_length=50)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: str = "UNKNOWN_ERROR"


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    config = get_config()
    logger.info(f"Starting PHDx API in {config.environment.value} mode")

    # Validate configuration
    issues = config.validate()
    if issues:
        for issue in issues:
            logger.warning(f"Config issue: {issue}")

    yield

    logger.info("Shutting down PHDx API")


# Create FastAPI app
config = get_config()

app = FastAPI(
    title="PHDx API",
    description="PhD Thesis Command Center - Production Backend",
    version="2.0.0",
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors.allowed_origins,
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allowed_methods,
    allow_headers=config.cors.allowed_headers,
)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": f"HTTP_{exc.status_code}"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "detail": str(exc) if config.debug else None
        }
    )


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/ready")
async def readiness_check():
    """Readiness check - verifies dependencies are available."""
    checks = {
        "config_valid": get_config().is_valid(),
        "backups_dir_exists": BACKUPS_DIR.exists(),
    }
    all_ready = all(checks.values())
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status and available models."""
    config = get_config()
    try:
        models = llm_gateway.get_available_models()
    except Exception:
        models = []

    return StatusResponse(
        system="online",
        environment=config.environment.value,
        models=models,
        version="2.0.0"
    )


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.get("/auth/google", response_model=AuthResponse)
async def authenticate_google():
    """Get Google authentication status."""
    try:
        user = airlock.get_user_info()
        return AuthResponse(
            email=user.get("email", ""),
            name=user.get("name", ""),
            authenticated=user.get("authenticated", False),
            mock=user.get("mock")
        )
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return AuthResponse(
            email="",
            name="",
            authenticated=False,
            mock=None
        )


# =============================================================================
# FILE ENDPOINTS
# =============================================================================

@app.get("/files/recent", response_model=List[FileInfo])
async def list_recent_files(limit: int = 10, dependencies=[Depends(check_rate_limit)]):
    """List recent Google Docs and Sheets."""
    try:
        docs = airlock.list_recent_docs(limit=limit)
        return [
            FileInfo(
                id=doc["id"],
                name=doc["name"],
                type=doc.get("type", "unknown"),
                source="google_drive"
            )
            for doc in docs
        ]
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GENERATION ENDPOINTS
# =============================================================================

@app.post("/generate", response_model=GenerateResponse, dependencies=[Depends(check_rate_limit)])
async def generate_text(request: GenerateRequest):
    """Generate text using LLM with optional document context."""
    context_text = request.context or ""

    # If doc_id provided, load document
    if request.doc_id:
        doc_result = airlock.get_document_text(request.doc_id)
        if not doc_result["success"]:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_result.get('error', 'Unknown error')}"
            )
        context_text = doc_result["text"]

    # Map model preference to task type
    task_type = "drafting" if request.model.lower() in ("claude", "anthropic") else "audit"

    try:
        result = llm_gateway.generate_content(
            prompt=request.prompt,
            task_type=task_type,
            context_text=context_text
        )
        return GenerateResponse(
            success=True,
            text=result.get("content", ""),
            model=result.get("model_used", request.model),
            tokens_used=result.get("tokens_estimated", 0),
            scrubbed=False,
            error=None
        )
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return GenerateResponse(
            success=False,
            text="",
            model=request.model,
            tokens_used=0,
            scrubbed=False,
            error=str(e)
        )


# =============================================================================
# AIRLOCK (PII SANITIZATION) ENDPOINTS
# =============================================================================

@app.post("/airlock/sanitize", response_model=SanitizeResponse, dependencies=[Depends(check_rate_limit)])
async def sanitize_text(request: SanitizeRequest):
    """Sanitize text by removing PII."""
    try:
        result = scrub_text(request.text, include_names=True)
        return SanitizeResponse(
            sanitized_text=result["scrubbed_text"],
            pii_found=result["total_redactions"] > 0,
            redactions_count=result["total_redactions"]
        )
    except Exception as e:
        logger.error(f"Sanitization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUDITOR ENDPOINTS
# =============================================================================

@app.post("/auditor/evaluate", dependencies=[Depends(check_rate_limit)])
async def evaluate_draft(request: AuditRequest):
    """Evaluate draft against Oxford Brookes criteria."""
    try:
        from core.auditor import BrookesAuditor
        auditor = BrookesAuditor()
        report = auditor.audit_draft(request.text, request.chapter_context or "")
        return report
    except Exception as e:
        logger.error(f"Audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auditor/criteria")
async def get_criteria():
    """Get Oxford Brookes marking criteria."""
    try:
        from core.auditor import get_marking_criteria
        return get_marking_criteria()
    except Exception as e:
        logger.error(f"Error getting criteria: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# RED THREAD (CONSISTENCY) ENDPOINTS
# =============================================================================

@app.post("/red-thread/check", dependencies=[Depends(check_rate_limit)])
async def check_consistency(request: ConsistencyRequest):
    """Check text consistency against indexed thesis content."""
    try:
        from core.red_thread import RedThreadEngine
        engine = RedThreadEngine()
        report = engine.get_consistency_report_for_ui(request.text)
        return report
    except Exception as e:
        logger.error(f"Consistency check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/red-thread/index")
async def index_chapters():
    """Index thesis chapters for consistency checking."""
    try:
        from core.red_thread import RedThreadEngine
        engine = RedThreadEngine()
        result = engine.index_existing_chapters()
        return result
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/red-thread/stats")
async def get_index_stats():
    """Get Red Thread index statistics."""
    try:
        from core.red_thread import RedThreadEngine
        engine = RedThreadEngine()
        return engine.get_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DNA ENGINE ENDPOINTS
# =============================================================================

@app.post("/dna/analyze", dependencies=[Depends(check_rate_limit)])
async def analyze_writing_style():
    """Analyze writing style from drafts folder."""
    try:
        from core.dna_engine import generate_author_dna
        profile = generate_author_dna()
        if profile:
            return {"success": True, "profile": profile}
        return {"success": False, "error": "No documents found in drafts folder"}
    except Exception as e:
        logger.error(f"DNA analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dna/profile")
async def get_dna_profile():
    """Get existing DNA profile if available."""
    try:
        from core.dna_engine import DATA_DIR
        profile_path = DATA_DIR / "author_dna.json"
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                return json.load(f)
        return {"error": "No DNA profile found. Run /dna/analyze first."}
    except Exception as e:
        logger.error(f"Profile read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SNAPSHOT ENDPOINTS
# =============================================================================

@app.post("/snapshot", response_model=SnapshotResponse)
async def save_snapshot(request: SnapshotRequest):
    """Save a document snapshot for backup."""
    try:
        safe_doc_id = request.doc_id.replace(":", "_").replace("/", "_")
        safe_timestamp = request.timestamp.replace(":", "-").replace(".", "-")
        filename = f"{safe_doc_id}_{safe_timestamp}.json"
        filepath = BACKUPS_DIR / filename

        snapshot_data = {
            "doc_id": request.doc_id,
            "timestamp": request.timestamp,
            "content": request.content,
            "saved_at": datetime.now().isoformat(),
            "word_count": len(request.content.split())
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

        file_size = filepath.stat().st_size
        return SnapshotResponse(
            success=True,
            filename=filename,
            path=str(filepath),
            size_bytes=file_size
        )
    except Exception as e:
        logger.error(f"Snapshot error: {e}")
        return SnapshotResponse(success=False, error=str(e))


# =============================================================================
# GOOGLE SYNC ENDPOINTS
# =============================================================================

@app.post("/sync/google", response_model=SyncResponse)
async def sync_to_google(request: SyncRequest):
    """Sync content to Google Docs."""
    try:
        result = airlock.update_google_doc(
            doc_id=request.doc_id,
            content=request.content,
            section_title=request.section_title
        )
        return SyncResponse(
            success=result.get("success", False),
            doc_url=result.get("doc_url"),
            characters_synced=len(request.content),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return SyncResponse(success=False, error=str(e))


# =============================================================================
# USAGE STATISTICS
# =============================================================================

@app.get("/stats/usage")
async def get_ai_usage_stats():
    """Get AI usage statistics."""
    try:
        return get_usage_stats()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    config = get_config()
    uvicorn.run(
        "api.server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level.lower()
    )
