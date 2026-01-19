"""
PHDx FastAPI Server - Headless Backend

Includes:
- Core API endpoints for the web client
- Extension API (/api/v1/extension) for Google Docs Sidebar
- OAuth2 authentication for Google Drive sync
- Background sync worker for Drive folders
"""

import sys
import json
import asyncio
import logging
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Literal
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Header, Depends, APIRouter, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from core import airlock
from core import llm_gateway
from core.airlock import (
    ExtensionAuthError,
    validate_env_api_key,
    generate_extension_api_key,
    list_extension_api_keys,
    revoke_extension_api_key,
)
from core.llm_gateway import get_router as get_llm_router, EngineType
from core.red_thread import check_continuity, RedThreadResult
from core.dna_engine import (
    calculate_sentence_complexity,
    analyze_hedging_frequency,
    extract_transition_vocabulary,
)
from core.drive_sync import (
    DriveSyncService,
    SyncResult,
    DriveFile,
    ExportFormat,
    get_sync_manager,
)
from core.secrets_utils import get_oauth_tokens, list_stored_users

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKUPS_DIR = Path(__file__).parent.parent / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)


# =============================================================================
# Core API Models
# =============================================================================

class GenerateRequest(BaseModel):
    doc_id: str
    prompt: str
    model: str = "claude"


class GenerateResponse(BaseModel):
    success: bool
    text: str
    model: str
    tokens_used: int
    scrubbed: bool
    error: Optional[str] = None


class StatusResponse(BaseModel):
    system: str
    models: list[str]


class AuthResponse(BaseModel):
    email: str
    name: str
    authenticated: bool
    mock: Optional[bool] = None


class FileInfo(BaseModel):
    id: str
    name: str
    source: str
    path: str
    modified: str
    size_bytes: int


class SnapshotRequest(BaseModel):
    doc_id: str
    timestamp: str
    content: str


class SnapshotResponse(BaseModel):
    success: bool
    filename: str
    path: str
    size_bytes: int
    error: Optional[str] = None


class SyncRequest(BaseModel):
    doc_id: str
    content: str
    section_title: Optional[str] = None


class SyncResponse(BaseModel):
    success: bool
    doc_url: Optional[str] = None
    characters_synced: int
    error: Optional[str] = None


# =============================================================================
# Extension API Models
# =============================================================================

class AnalysisMode(str, Enum):
    """Analysis modes for the extension."""
    DNA = "dna"
    RED_THREAD = "red_thread"


class ExtensionAnalyzeRequest(BaseModel):
    """Request model for extension analyze-selection endpoint."""
    text: str = Field(..., min_length=10, description="Selected text to analyze")
    mode: AnalysisMode = Field(..., description="Analysis mode: 'dna' or 'red_thread'")
    user_context: Optional[str] = Field(None, description="Additional context from user")


class DNACardData(BaseModel):
    """DNA analysis card data for the sidebar UI."""
    card_type: Literal["dna"] = "dna"
    sentence_metrics: dict = Field(..., description="Sentence complexity metrics")
    hedging_analysis: dict = Field(..., description="Hedging frequency analysis")
    transitions: dict = Field(..., description="Transition vocabulary analysis")
    style_summary: str = Field(..., description="Brief style summary")


class RedThreadCardData(BaseModel):
    """Red Thread analysis card data for the sidebar UI."""
    card_type: Literal["red_thread"] = "red_thread"
    continuity_score: int = Field(..., ge=0, le=100)
    thread_status: str = Field(..., description="'solid' or 'broken'")
    status: str = Field(..., description="Human-readable status")
    analysis: str = Field(..., description="Detailed analysis text")
    missing_links: list[dict] = Field(default_factory=list)
    graph_preview: Optional[dict] = Field(None, description="Simplified graph for preview")


class ExtensionAnalyzeResponse(BaseModel):
    """Response model for extension analyze-selection endpoint."""
    success: bool
    mode: str
    card_data: dict = Field(..., description="Card data for UI rendering")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    error: Optional[str] = None


class ExtensionHealthResponse(BaseModel):
    """Health check response for the extension."""
    status: str
    version: str
    available_modes: list[str]


class APIKeyResponse(BaseModel):
    """Response for API key generation."""
    key: str
    key_id: str
    name: str
    expires_at: str


class APIKeyListResponse(BaseModel):
    """Response for listing API keys."""
    keys: list[dict]


# =============================================================================
# CORS Configuration
# =============================================================================

# Allowed origins for CORS
# Google Apps Script executes from script.googleusercontent.com
ALLOWED_ORIGINS = [
    "https://script.googleusercontent.com",
    "https://script.google.com",
    "https://*.googleusercontent.com",
    "http://localhost:3000",  # Local Next.js dev
    "http://localhost:8000",  # Local API testing
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]


# =============================================================================
# Background Sync Task
# =============================================================================

SYNC_INTERVAL_MINUTES = 10
_background_task: Optional[asyncio.Task] = None


async def background_sync_worker():
    """
    Background worker that runs sync_folder every 10 minutes for active users.
    """
    sync_manager = get_sync_manager()

    while True:
        try:
            # Wait for the interval
            await asyncio.sleep(SYNC_INTERVAL_MINUTES * 60)

            # Run pending syncs
            logger.info("Running background sync...")
            results = sync_manager.run_pending_syncs()

            # Log results
            for result in results:
                if result.success:
                    logger.info(f"Sync completed: {result.files_changed} files changed")
                else:
                    logger.warning(f"Sync failed: {result.errors}")

        except asyncio.CancelledError:
            logger.info("Background sync worker cancelled")
            break
        except Exception as e:
            logger.error(f"Background sync error: {e}")
            # Continue running despite errors
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global _background_task

    # Startup: Start background sync worker
    logger.info("Starting background sync worker...")
    _background_task = asyncio.create_task(background_sync_worker())

    yield

    # Shutdown: Cancel background task
    if _background_task:
        logger.info("Stopping background sync worker...")
        _background_task.cancel()
        try:
            await _background_task
        except asyncio.CancelledError:
            pass


# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="PHDx API",
    description="PhD Thesis Command Center - Headless Backend with Extension Support",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware with specific origins for Google Apps Script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development; restrict in production
    allow_origin_regex=r"https://.*\.googleusercontent\.com",  # Google Apps Script
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# =============================================================================
# Extension Auth Dependency
# =============================================================================

async def verify_extension_auth(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to verify extension API key.

    Expects: Authorization: Bearer <api_key>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_result = validate_env_api_key(authorization)
        return auth_result
    except ExtensionAuthError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Extension API Router (/api/v1/extension)
# =============================================================================

extension_router = APIRouter(
    prefix="/api/v1/extension",
    tags=["Extension"],
    responses={401: {"description": "Unauthorized"}},
)


@extension_router.get("/health", response_model=ExtensionHealthResponse)
async def extension_health():
    """
    Health check endpoint for the Google Docs extension.

    No authentication required - allows extension to verify server is reachable.
    """
    return ExtensionHealthResponse(
        status="healthy",
        version="2.1.0",
        available_modes=["dna", "red_thread"],
    )


@extension_router.post("/analyze-selection", response_model=ExtensionAnalyzeResponse)
async def analyze_selection(
    request: ExtensionAnalyzeRequest,
    auth: dict = Depends(verify_extension_auth),
):
    """
    Analyze selected text from Google Docs.

    Routes to DNA Engine or Red Thread Engine based on mode.
    Returns strict JSON card data for the sidebar UI.

    **Authentication:** Bearer token required

    **Modes:**
    - `dna`: Linguistic fingerprint analysis (sentence structure, hedging, transitions)
    - `red_thread`: Argument continuity analysis (logic flow, missing links)
    """
    import time
    start_time = time.time()

    try:
        if request.mode == AnalysisMode.DNA:
            # DNA Analysis - use local analysis functions (fast, no LLM needed)
            sentence_metrics = calculate_sentence_complexity(request.text)
            hedging = analyze_hedging_frequency(request.text)
            transitions = extract_transition_vocabulary(request.text)

            # Generate style summary
            style_summary = _generate_style_summary(sentence_metrics, hedging, transitions)

            card_data = DNACardData(
                sentence_metrics=sentence_metrics,
                hedging_analysis=hedging,
                transitions=transitions,
                style_summary=style_summary,
            ).model_dump()

        elif request.mode == AnalysisMode.RED_THREAD:
            # Red Thread Analysis - uses hierarchical logic check
            result = check_continuity(request.text)

            # Create simplified graph preview for sidebar
            graph_preview = None
            if result.get('visual_graph_nodes'):
                graph_preview = {
                    'node_count': len(result.get('visual_graph_nodes', [])),
                    'edge_count': len(result.get('visual_graph_edges', [])),
                    'has_broken_links': len(result.get('missing_links', [])) > 0,
                }

            card_data = RedThreadCardData(
                continuity_score=result.get('continuity_score', 0),
                thread_status=result.get('thread_status', 'unknown'),
                status=result.get('status', 'Unknown'),
                analysis=result.get('analysis', 'Analysis unavailable'),
                missing_links=result.get('missing_links', []),
                graph_preview=graph_preview,
            ).model_dump()

        else:
            raise HTTPException(status_code=400, detail=f"Unknown mode: {request.mode}")

        processing_time_ms = int((time.time() - start_time) * 1000)

        return ExtensionAnalyzeResponse(
            success=True,
            mode=request.mode.value,
            card_data=card_data,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        return ExtensionAnalyzeResponse(
            success=False,
            mode=request.mode.value,
            card_data={},
            processing_time_ms=processing_time_ms,
            error=str(e),
        )


@extension_router.post("/generate-key", response_model=APIKeyResponse)
async def generate_api_key(
    name: str = "google-docs-extension",
    expires_days: int = 90,
):
    """
    Generate a new API key for the extension.

    **Note:** This endpoint should be protected in production.
    For MVP, it's accessible to allow initial setup.

    The key is only returned once - store it securely!
    """
    result = generate_extension_api_key(name=name, expires_days=expires_days)
    return APIKeyResponse(
        key=result['key'],
        key_id=result['key_id'],
        name=result['name'],
        expires_at=result['expires_at'],
    )


@extension_router.get("/keys", response_model=APIKeyListResponse)
async def list_api_keys():
    """
    List all extension API keys (without the actual keys).

    **Note:** This endpoint should be protected in production.
    """
    keys = list_extension_api_keys()
    return APIKeyListResponse(keys=keys)


@extension_router.delete("/keys/{key_id}")
async def revoke_api_key(key_id: str):
    """
    Revoke an extension API key.

    **Note:** This endpoint should be protected in production.
    """
    if revoke_extension_api_key(key_id):
        return {"success": True, "message": f"Key {key_id} revoked"}
    raise HTTPException(status_code=404, detail=f"Key {key_id} not found")


def _generate_style_summary(sentence_metrics: dict, hedging: dict, transitions: dict) -> str:
    """Generate a brief style summary from analysis results."""
    parts = []

    # Sentence length characterization
    avg_len = sentence_metrics.get('average_length', 0)
    if avg_len < 15:
        parts.append("Concise sentences")
    elif avg_len < 25:
        parts.append("Moderate sentence length")
    else:
        parts.append("Complex, lengthy sentences")

    # Hedging characterization
    hedging_density = hedging.get('hedging_density_per_1000_words', 0)
    if hedging_density < 5:
        parts.append("direct assertive tone")
    elif hedging_density < 15:
        parts.append("balanced hedging")
    else:
        parts.append("cautious academic hedging")

    # Transition preferences
    preferred = transitions.get('preferred_categories', [])
    if preferred:
        parts.append(f"favors {preferred[0]} transitions")

    return "; ".join(parts) + "."


# Include extension router
app.include_router(extension_router)


# =============================================================================
# OAuth2 / Drive Sync API
# =============================================================================

# Store for OAuth state tokens (CSRF protection)
_oauth_states: dict[str, dict] = {}

# OAuth Response Models
class OAuthLoginResponse(BaseModel):
    """Response with OAuth authorization URL."""
    auth_url: str
    state: str


class OAuthUserInfo(BaseModel):
    """User information from OAuth."""
    user_id: str
    name: str
    email: str
    photo_url: Optional[str] = None
    authenticated: bool = True


class DriveFileResponse(BaseModel):
    """Drive file information."""
    id: str
    name: str
    mime_type: str
    modified_time: str
    web_view_link: Optional[str] = None
    is_google_doc: bool


class DriveFolderListResponse(BaseModel):
    """List of Drive folders."""
    folders: list[DriveFileResponse]


class SyncFolderRequest(BaseModel):
    """Request to sync a folder."""
    folder_id: str
    recursive: bool = True
    force: bool = False


class SyncResultResponse(BaseModel):
    """Result of sync operation."""
    success: bool
    files_found: int
    files_changed: int
    errors: list[str] = []
    changed_files: list[DriveFileResponse] = []
    synced_at: str


class ExportDocRequest(BaseModel):
    """Request to export a document."""
    file_id: str
    format: str = "text/plain"


class ExportDocResponse(BaseModel):
    """Exported document content."""
    file_id: str
    name: str
    content: str
    format: str


class RegisterSyncRequest(BaseModel):
    """Request to register background sync."""
    folder_id: str
    interval_minutes: int = 10


# Drive Sync Router
drive_router = APIRouter(
    prefix="/api/v1/drive",
    tags=["Drive Sync"],
)


def get_base_url() -> str:
    """Get the base URL for OAuth callbacks."""
    import os
    return os.environ.get('PHDX_BASE_URL', 'http://localhost:8000')


@drive_router.get("/auth/login", response_model=OAuthLoginResponse)
async def oauth_login(
    user_id: str = Query(..., description="Unique user identifier"),
):
    """
    Initiate OAuth2 login flow.

    Returns an authorization URL to redirect the user to.
    """
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
    }

    # Get auth URL
    redirect_uri = f"{get_base_url()}/api/v1/drive/auth/callback"
    service = DriveSyncService(user_id)

    try:
        auth_url = service.get_auth_url(redirect_uri, state=state)
        return OAuthLoginResponse(auth_url=auth_url, state=state)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@drive_router.get("/auth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
):
    """
    Handle OAuth2 callback from Google.

    Exchanges the authorization code for tokens and stores them.
    """
    # Verify state token
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state token")

    user_id = state_data['user_id']
    redirect_uri = f"{get_base_url()}/api/v1/drive/auth/callback"

    try:
        service = DriveSyncService(user_id)
        user_info = service.handle_auth_callback(code, redirect_uri)

        # Redirect to success page or return JSON
        frontend_url = get_base_url().replace(':8000', ':3000')  # Assume frontend on 3000
        return RedirectResponse(
            url=f"{frontend_url}/settings?auth=success&user={user_id}"
        )

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@drive_router.get("/auth/status", response_model=OAuthUserInfo)
async def oauth_status(
    user_id: str = Query(..., description="User identifier"),
):
    """
    Check OAuth authentication status for a user.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        return OAuthUserInfo(
            user_id=user_id,
            name="",
            email="",
            authenticated=False,
        )

    # Get user info
    try:
        user_info = service._get_user_info()
        return OAuthUserInfo(
            user_id=user_id,
            name=user_info.get('name', ''),
            email=user_info.get('email', ''),
            photo_url=user_info.get('photo_url'),
            authenticated=True,
        )
    except Exception:
        return OAuthUserInfo(
            user_id=user_id,
            name="",
            email="",
            authenticated=True,  # Has tokens but couldn't get info
        )


@drive_router.post("/auth/logout")
async def oauth_logout(
    user_id: str = Query(..., description="User identifier"),
):
    """
    Log out a user by deleting their stored tokens.
    """
    service = DriveSyncService(user_id)
    deleted = service.logout()

    return {"success": deleted, "user_id": user_id}


@drive_router.get("/folders", response_model=DriveFolderListResponse)
async def list_drive_folders(
    user_id: str = Query(..., description="User identifier"),
    parent_id: str = Query("root", description="Parent folder ID"),
):
    """
    List folders in Google Drive.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        folders = service.list_folders(parent_id)
        return DriveFolderListResponse(
            folders=[
                DriveFileResponse(
                    id=f.id,
                    name=f.name,
                    mime_type=f.mime_type,
                    modified_time=f.modified_time,
                    web_view_link=f.web_view_link,
                    is_google_doc=f.is_google_doc,
                )
                for f in folders
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@drive_router.post("/sync", response_model=SyncResultResponse)
async def sync_folder(
    request: SyncFolderRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Sync a Google Drive folder.

    Detects changed files since last sync.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        result = service.sync_folder(
            folder_id=request.folder_id,
            recursive=request.recursive,
            force=request.force,
        )

        return SyncResultResponse(
            success=result.success,
            files_found=result.files_found,
            files_changed=result.files_changed,
            errors=result.errors,
            changed_files=[
                DriveFileResponse(
                    id=f.id,
                    name=f.name,
                    mime_type=f.mime_type,
                    modified_time=f.modified_time,
                    web_view_link=f.web_view_link,
                    is_google_doc=f.is_google_doc,
                )
                for f in result.changed_files
            ],
            synced_at=result.synced_at,
        )
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@drive_router.post("/export", response_model=ExportDocResponse)
async def export_document(
    request: ExportDocRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Export a Google Doc to text or HTML.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get file metadata
        metadata = service.get_file_metadata(request.file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        # Determine export format
        format_map = {
            'text/plain': ExportFormat.PLAIN_TEXT,
            'text/html': ExportFormat.HTML,
            'application/pdf': ExportFormat.PDF,
        }
        export_format = format_map.get(request.format, ExportFormat.PLAIN_TEXT)

        # Export document
        content = service.export_doc(request.file_id, export_format)

        return ExportDocResponse(
            file_id=request.file_id,
            name=metadata.name,
            content=content,
            format=request.format,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@drive_router.post("/background-sync/register")
async def register_background_sync(
    request: RegisterSyncRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Register a folder for background sync.

    The folder will be synced automatically every N minutes.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated")

    sync_manager = get_sync_manager()
    sync_manager.register_sync(
        user_id=user_id,
        folder_id=request.folder_id,
        interval_minutes=request.interval_minutes,
    )

    return {
        "success": True,
        "user_id": user_id,
        "folder_id": request.folder_id,
        "interval_minutes": request.interval_minutes,
    }


@drive_router.delete("/background-sync/unregister")
async def unregister_background_sync(
    user_id: str = Query(..., description="User identifier"),
    folder_id: str = Query(..., description="Folder ID"),
):
    """
    Unregister a folder from background sync.
    """
    sync_manager = get_sync_manager()
    removed = sync_manager.unregister_sync(user_id, folder_id)

    return {"success": removed, "user_id": user_id, "folder_id": folder_id}


@drive_router.get("/background-sync/status")
async def get_background_sync_status():
    """
    Get status of all active background syncs.
    """
    sync_manager = get_sync_manager()
    active_syncs = sync_manager.list_active_syncs()

    return {
        "active_syncs": active_syncs,
        "total": len(active_syncs),
    }


@drive_router.post("/background-sync/run-now")
async def run_background_sync_now(background_tasks: BackgroundTasks):
    """
    Manually trigger background sync for all registered folders.
    """
    def run_sync():
        sync_manager = get_sync_manager()
        results = sync_manager.run_pending_syncs()
        logger.info(f"Manual sync completed: {len(results)} syncs run")

    background_tasks.add_task(run_sync)

    return {"success": True, "message": "Sync triggered in background"}


# Include drive router
app.include_router(drive_router)


# =============================================================================
# Core API Endpoints
# =============================================================================

@app.get("/status", response_model=StatusResponse)
async def get_status():
    models = llm_gateway.get_available_models()
    return StatusResponse(system="online", models=models)


@app.get("/auth/google", response_model=AuthResponse)
async def authenticate_google():
    user = airlock.authenticate_user()
    return AuthResponse(
        email=user.get("email", ""),
        name=user.get("name", ""),
        authenticated=user.get("authenticated", False),
        mock=user.get("mock")
    )


@app.get("/files/recent", response_model=list[FileInfo])
async def list_recent_files(limit: int = 10):
    docs = airlock.list_recent_docs(limit=limit)
    return [
        FileInfo(
            id=doc["id"],
            name=doc["name"],
            source=doc["source"],
            path=doc["path"],
            modified=doc["modified"],
            size_bytes=doc["size_bytes"]
        )
        for doc in docs
    ]


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    doc_result = airlock.get_document_text(request.doc_id)
    if not doc_result["success"]:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_result.get('error', 'Unknown error')}")
    result = llm_gateway.generate(prompt=request.prompt, model=request.model, context=doc_result["text"])
    return GenerateResponse(
        success=result["success"],
        text=result.get("text", ""),
        model=result["model"],
        tokens_used=result.get("tokens_used", 0),
        scrubbed=result.get("scrubbed", False),
        error=result.get("error")
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/snapshot", response_model=SnapshotResponse)
async def save_snapshot(request: SnapshotRequest):
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
        return SnapshotResponse(success=True, filename=filename, path=str(filepath), size_bytes=file_size)
    except Exception as e:
        return SnapshotResponse(success=False, filename="", path="", size_bytes=0, error=str(e))


@app.post("/sync/google", response_model=SyncResponse)
async def sync_to_google(request: SyncRequest):
    try:
        result = airlock.update_google_doc(doc_id=request.doc_id, content=request.content, section_title=request.section_title)
        return SyncResponse(success=result.get("success", False), doc_url=result.get("doc_url"), characters_synced=len(request.content), error=result.get("error"))
    except Exception as e:
        return SyncResponse(success=False, doc_url=None, characters_synced=0, error=str(e))


# =============================================================================
# DNA Style Suggestion API
# =============================================================================

class StyleEdit(BaseModel):
    """A single style edit suggestion."""
    original: str = Field(..., description="Original text to be replaced")
    suggested: str = Field(..., description="Suggested replacement text")
    reason: str = Field(..., description="Why this change is suggested")
    category: str = Field(..., description="Category: 'hedging', 'clarity', 'conciseness', 'tone', 'grammar'")
    start_index: int = Field(..., description="Start index in original text")
    end_index: int = Field(..., description="End index in original text")


class DNAStyleRequest(BaseModel):
    """Request for DNA style analysis and suggestions."""
    text: str = Field(..., min_length=20, description="Text to analyze and improve")
    style_profile: Optional[str] = Field(None, description="Optional style profile to match")


class DNAStyleResponse(BaseModel):
    """Response with style analysis and edit suggestions."""
    original_text: str
    improved_text: str
    edits: list[StyleEdit] = Field(default_factory=list)
    style_metrics: dict = Field(default_factory=dict)
    summary: str


@app.post("/dna/suggest-edits", response_model=DNAStyleResponse)
async def suggest_style_edits(request: DNAStyleRequest):
    """
    Analyze text and suggest style improvements.

    Returns a diff-compatible response with original, improved text,
    and detailed edit suggestions with reasons.
    """
    import re

    original_text = request.text

    # Get style metrics
    sentence_metrics = calculate_sentence_complexity(original_text)
    hedging = analyze_hedging_frequency(original_text)
    transitions = extract_transition_vocabulary(original_text)

    # Use LLM to generate style suggestions
    llm_router = get_llm_router()

    system_prompt = """You are an academic writing editor. Analyze the text and suggest improvements.
Return a JSON object with this exact structure:
{
    "improved_text": "The full improved text",
    "edits": [
        {
            "original": "exact original phrase",
            "suggested": "improved phrase",
            "reason": "Brief explanation",
            "category": "hedging|clarity|conciseness|tone|grammar"
        }
    ],
    "summary": "Brief overall assessment"
}

Focus on:
- Removing unnecessary hedging (very, really, quite, somewhat)
- Eliminating pleonasms (very unique → unique)
- Improving clarity and conciseness
- Maintaining academic tone
- Fixing grammar issues

Return ONLY valid JSON, no markdown."""

    prompt = f"""Analyze and improve this academic text:

{original_text}

Provide specific edits with reasons. Be precise about what to change and why."""

    try:
        response = llm_router.generate(
            prompt=prompt,
            engine=EngineType.DNA,  # Routes to TIER_CREATIVE (GPT-4o)
            system_prompt=system_prompt,
        )

        # Parse response
        content = response.content.strip()
        if content.startswith('```'):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)

        import json as json_module
        data = json_module.loads(content)

        # Build edits with indices
        edits = []
        for edit in data.get('edits', []):
            original_phrase = edit.get('original', '')
            # Find the phrase in text
            start_idx = original_text.lower().find(original_phrase.lower())
            if start_idx >= 0:
                edits.append(StyleEdit(
                    original=original_phrase,
                    suggested=edit.get('suggested', original_phrase),
                    reason=edit.get('reason', 'Style improvement'),
                    category=edit.get('category', 'clarity'),
                    start_index=start_idx,
                    end_index=start_idx + len(original_phrase),
                ))

        return DNAStyleResponse(
            original_text=original_text,
            improved_text=data.get('improved_text', original_text),
            edits=edits,
            style_metrics={
                'sentence_complexity': sentence_metrics,
                'hedging': hedging,
                'transitions': transitions,
            },
            summary=data.get('summary', 'Analysis complete.'),
        )

    except Exception as e:
        # Fallback: return basic analysis without LLM suggestions
        return DNAStyleResponse(
            original_text=original_text,
            improved_text=original_text,
            edits=[],
            style_metrics={
                'sentence_complexity': sentence_metrics,
                'hedging': hedging,
                'transitions': transitions,
            },
            summary=f"Style analysis complete. LLM suggestions unavailable: {str(e)}",
        )


@app.post("/dna/analyze")
async def analyze_dna(request: DNAStyleRequest):
    """
    Simple DNA variance analysis (legacy endpoint).
    """
    sentence_metrics = calculate_sentence_complexity(request.text)
    hedging = analyze_hedging_frequency(request.text)

    # Calculate variance score based on metrics
    avg_sentence_len = sentence_metrics.get('average_length', 15)
    hedging_density = hedging.get('hedging_density_per_1000_words', 0)

    # Variance formula: higher variance = more human-like
    variance = min(15, max(0, (avg_sentence_len / 3) + (hedging_density / 2)))

    return {
        'variance': round(variance, 2),
        'style_match': variance > 5.0,
        'status': 'Human' if variance > 10 else 'Mixed' if variance > 5 else 'Robotic',
    }


# =============================================================================
# Red Thread API (direct access)
# =============================================================================

class RedThreadCheckRequest(BaseModel):
    """Request for red thread continuity check."""
    introduction: str = Field(..., min_length=50, description="Introduction/Chapter 1 text")
    discussion: str = Field(..., min_length=50, description="Discussion/Conclusion text")


class VisualGraphNode(BaseModel):
    """Node in the argument flow graph."""
    id: str
    label: str
    type: str  # 'question', 'argument', 'evidence', 'conclusion'
    chapter: str


class VisualGraphEdge(BaseModel):
    """Edge in the argument flow graph."""
    source: str
    target: str
    label: Optional[str] = None
    strength: float = 1.0


class MissingLinkDetail(BaseModel):
    """Details about a missing logical link."""
    from_chapter: str
    to_chapter: str
    description: str
    severity: str = "medium"  # 'high', 'medium', 'low'
    suggestion: str


class RedThreadCheckResponse(BaseModel):
    """Response for red thread check - compatible with RedThreadModule.tsx."""
    continuity_score: int
    thread_status: str  # 'solid' or 'broken'
    status: str
    analysis: str
    missing_links: list[MissingLinkDetail] = Field(default_factory=list)
    visual_graph_nodes: list[VisualGraphNode] = Field(default_factory=list)
    visual_graph_edges: list[VisualGraphEdge] = Field(default_factory=list)


@app.post("/red-thread/check", response_model=RedThreadCheckResponse)
async def check_red_thread(request: RedThreadCheckRequest):
    """
    Check argument continuity between introduction and discussion.

    This endpoint is used by the RedThreadModule.tsx component.
    Returns visual graph data for the Golden Thread visualization.
    """
    # Combine intro and discussion for analysis
    combined_text = f"""CHAPTER 1: INTRODUCTION

{request.introduction}

CHAPTER 5: CONCLUSION

{request.discussion}"""

    result = check_continuity(combined_text)

    # Parse missing links
    missing_links = []
    for ml in result.get('missing_links', []):
        try:
            missing_links.append(MissingLinkDetail(
                from_chapter=ml.get('from_chapter', 'unknown'),
                to_chapter=ml.get('to_chapter', 'unknown'),
                description=ml.get('description', 'No description'),
                severity=ml.get('severity', 'medium'),
                suggestion=ml.get('suggestion', 'Review the connection'),
            ))
        except Exception:
            pass

    # Parse visual graph nodes
    graph_nodes = []
    for node in result.get('visual_graph_nodes', []):
        try:
            graph_nodes.append(VisualGraphNode(
                id=node.get('id', f'node_{len(graph_nodes)}'),
                label=node.get('label', 'Unknown'),
                type=node.get('type', 'argument'),
                chapter=node.get('chapter', 'unknown'),
            ))
        except Exception:
            pass

    # Parse visual graph edges
    graph_edges = []
    for edge in result.get('visual_graph_edges', []):
        try:
            graph_edges.append(VisualGraphEdge(
                source=edge.get('source', ''),
                target=edge.get('target', ''),
                label=edge.get('label'),
                strength=edge.get('strength', 1.0),
            ))
        except Exception:
            pass

    return RedThreadCheckResponse(
        continuity_score=result.get('continuity_score', 0),
        thread_status=result.get('thread_status', 'unknown'),
        status=result.get('status', 'Unknown'),
        analysis=result.get('analysis', 'Analysis unavailable'),
        missing_links=missing_links,
        visual_graph_nodes=graph_nodes,
        visual_graph_edges=graph_edges,
    )


# =============================================================================
# Project Graph API (Living Thesis Graph)
# =============================================================================

class ChapterStatus(str, Enum):
    """Status of a thesis chapter."""
    DRAFT = "draft"
    REVIEWING = "reviewing"
    SOLID = "solid"
    ISSUES = "issues"


class ChapterNodeResponse(BaseModel):
    """A chapter node in the thesis graph."""
    id: str
    name: str
    doc_id: Optional[str] = None
    status: ChapterStatus
    last_synced: Optional[str] = None
    logic_errors: int = 0
    word_count: Optional[int] = None
    web_view_link: Optional[str] = None


class LogicConnectionResponse(BaseModel):
    """A logical connection between chapters."""
    source: str
    target: str
    status: str  # 'solid' or 'broken'
    error_description: Optional[str] = None
    severity: Optional[str] = None


class ProjectGraphResponse(BaseModel):
    """Complete thesis graph data for visualization."""
    chapters: list[ChapterNodeResponse]
    connections: list[LogicConnectionResponse]
    last_analyzed: Optional[str] = None
    overall_score: Optional[int] = None


# Store for analyzed chapter data (in-memory cache)
_chapter_analysis_cache: dict[str, dict] = {}


def _determine_chapter_status(chapter_id: str, logic_errors: int, last_synced: Optional[str]) -> ChapterStatus:
    """Determine the status of a chapter based on analysis results."""
    if logic_errors > 0:
        return ChapterStatus.ISSUES

    if not last_synced:
        return ChapterStatus.DRAFT

    # Check if recently synced (within last hour = reviewing)
    try:
        synced_time = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
        now = datetime.now(synced_time.tzinfo) if synced_time.tzinfo else datetime.now()
        hours_since_sync = (now - synced_time).total_seconds() / 3600

        if hours_since_sync < 1:
            return ChapterStatus.REVIEWING
    except Exception:
        pass

    return ChapterStatus.SOLID


def _detect_chapter_order(name: str) -> int:
    """Extract chapter order from name (e.g., 'Chapter 1' -> 1)."""
    import re

    # Try to find chapter number
    match = re.search(r'chapter\s*(\d+)', name.lower())
    if match:
        return int(match.group(1))

    # Common chapter keywords in order
    keywords = [
        ('introduction', 1),
        ('literature', 2),
        ('method', 3),
        ('result', 4),
        ('discussion', 5),
        ('conclusion', 6),
        ('appendix', 7),
    ]

    name_lower = name.lower()
    for keyword, order in keywords:
        if keyword in name_lower:
            return order

    return 99  # Unknown chapters at end


@app.get("/api/project/graph", response_model=ProjectGraphResponse)
async def get_project_graph(
    user_id: str = Query(..., description="User identifier"),
    folder_id: Optional[str] = Query(None, description="Specific folder to analyze"),
    force_refresh: bool = Query(False, description="Force re-analysis"),
):
    """
    Get the Living Thesis Graph data.

    Returns chapters as nodes and logical connections as edges,
    with status indicators based on Red Thread analysis.

    This endpoint combines Drive sync data with Red Thread analysis
    to provide a real-time view of thesis structure and health.
    """
    try:
        service = DriveSyncService(user_id)

        # Check authentication
        if not service.is_authenticated():
            # Return demo data for unauthenticated users
            return _get_demo_graph_data()

        # Get synced files
        chapters: list[ChapterNodeResponse] = []
        chapter_contents: dict[str, str] = {}

        try:
            # If folder_id provided, sync that folder
            if folder_id:
                sync_result = service.sync_folder(folder_id, recursive=True, force=force_refresh)
                files = sync_result.changed_files if sync_result.success else []
            else:
                # List all Google Docs from root
                files = service.list_files(mime_type='application/vnd.google-apps.document')
        except Exception as e:
            logger.warning(f"Could not fetch Drive files: {e}")
            files = []

        # Filter for chapter-like documents
        chapter_files = []
        for f in files:
            name_lower = f.name.lower()
            # Include files that look like chapters
            if any(kw in name_lower for kw in ['chapter', 'introduction', 'literature', 'method', 'result', 'discussion', 'conclusion']):
                chapter_files.append(f)

        # Sort by detected chapter order
        chapter_files.sort(key=lambda f: _detect_chapter_order(f.name))

        # Build chapter nodes
        for idx, f in enumerate(chapter_files):
            chapter_id = f"ch{idx + 1}"

            # Try to get cached analysis
            cache_key = f"{user_id}_{f.id}"
            cached = _chapter_analysis_cache.get(cache_key)

            logic_errors = 0
            word_count = None

            if cached and not force_refresh:
                logic_errors = cached.get('logic_errors', 0)
                word_count = cached.get('word_count')
            else:
                # Export and analyze document
                try:
                    content = service.export_doc(f.id, ExportFormat.PLAIN_TEXT)
                    word_count = len(content.split())
                    chapter_contents[chapter_id] = content

                    # Cache the content
                    _chapter_analysis_cache[cache_key] = {
                        'content': content,
                        'word_count': word_count,
                        'logic_errors': 0,
                        'analyzed_at': datetime.now().isoformat(),
                    }
                except Exception as e:
                    logger.warning(f"Could not export document {f.id}: {e}")

            status = _determine_chapter_status(chapter_id, logic_errors, f.modified_time)

            chapters.append(ChapterNodeResponse(
                id=chapter_id,
                name=f.name,
                doc_id=f.id,
                status=status,
                last_synced=f.modified_time,
                logic_errors=logic_errors,
                word_count=word_count,
                web_view_link=f.web_view_link,
            ))

        # If no chapters found, return demo data
        if not chapters:
            return _get_demo_graph_data()

        # Build connections between adjacent chapters
        connections: list[LogicConnectionResponse] = []

        for i in range(len(chapters) - 1):
            source = chapters[i]
            target = chapters[i + 1]

            # Analyze connection between chapters
            source_content = chapter_contents.get(source.id, '')
            target_content = chapter_contents.get(target.id, '')

            connection_status = 'solid'
            error_description = None

            if source_content and target_content:
                # Run Red Thread analysis on the connection
                try:
                    combined = f"""CHAPTER {i + 1}:

{source_content[:2000]}

CHAPTER {i + 2}:

{target_content[:2000]}"""

                    result = check_continuity(combined)

                    if result.get('thread_status') == 'broken':
                        connection_status = 'broken'
                        missing = result.get('missing_links', [])
                        if missing:
                            error_description = missing[0].get('description', 'Logic break detected')

                        # Update logic errors count
                        cache_key = f"{user_id}_{source.doc_id}"
                        if cache_key in _chapter_analysis_cache:
                            _chapter_analysis_cache[cache_key]['logic_errors'] = len(missing)
                            # Update chapter status
                            source.logic_errors = len(missing)
                            source.status = ChapterStatus.ISSUES

                except Exception as e:
                    logger.warning(f"Connection analysis failed: {e}")

            connections.append(LogicConnectionResponse(
                source=source.id,
                target=target.id,
                status=connection_status,
                error_description=error_description,
                severity='high' if connection_status == 'broken' else None,
            ))

        # Also check intro-conclusion connection
        if len(chapters) >= 2:
            intro = chapters[0]
            conclusion = chapters[-1]

            intro_content = chapter_contents.get(intro.id, '')
            conclusion_content = chapter_contents.get(conclusion.id, '')

            if intro_content and conclusion_content:
                try:
                    combined = f"""INTRODUCTION:

{intro_content[:2000]}

CONCLUSION:

{conclusion_content[:2000]}"""

                    result = check_continuity(combined)

                    intro_conclusion_status = 'solid' if result.get('thread_status') == 'solid' else 'broken'
                    error_desc = None

                    if intro_conclusion_status == 'broken':
                        missing = result.get('missing_links', [])
                        if missing:
                            error_desc = missing[0].get('description', 'Introduction-conclusion mismatch')

                    connections.append(LogicConnectionResponse(
                        source=intro.id,
                        target=conclusion.id,
                        status=intro_conclusion_status,
                        error_description=error_desc,
                        severity='high' if intro_conclusion_status == 'broken' else None,
                    ))
                except Exception:
                    pass

        # Calculate overall score
        total_connections = len(connections)
        solid_connections = sum(1 for c in connections if c.status == 'solid')
        overall_score = int((solid_connections / total_connections * 100)) if total_connections > 0 else 100

        return ProjectGraphResponse(
            chapters=chapters,
            connections=connections,
            last_analyzed=datetime.now().isoformat(),
            overall_score=overall_score,
        )

    except Exception as e:
        logger.error(f"Project graph error: {e}")
        # Return demo data on error
        return _get_demo_graph_data()


def _get_demo_graph_data() -> ProjectGraphResponse:
    """Return demo graph data for testing/unauthenticated users."""
    now = datetime.now()

    chapters = [
        ChapterNodeResponse(
            id="ch1",
            name="Chapter 1: Introduction",
            status=ChapterStatus.SOLID,
            last_synced=(now - timedelta(minutes=2)).isoformat(),
            logic_errors=0,
            word_count=3500,
        ),
        ChapterNodeResponse(
            id="ch2",
            name="Chapter 2: Literature Review",
            status=ChapterStatus.REVIEWING,
            last_synced=(now - timedelta(minutes=15)).isoformat(),
            logic_errors=0,
            word_count=8200,
        ),
        ChapterNodeResponse(
            id="ch3",
            name="Chapter 3: Methodology",
            status=ChapterStatus.SOLID,
            last_synced=(now - timedelta(hours=1)).isoformat(),
            logic_errors=0,
            word_count=5100,
        ),
        ChapterNodeResponse(
            id="ch4",
            name="Chapter 4: Results",
            status=ChapterStatus.ISSUES,
            last_synced=(now - timedelta(minutes=30)).isoformat(),
            logic_errors=2,
            word_count=4800,
        ),
        ChapterNodeResponse(
            id="ch5",
            name="Chapter 5: Discussion",
            status=ChapterStatus.DRAFT,
            last_synced=(now - timedelta(hours=2)).isoformat(),
            logic_errors=0,
            word_count=2100,
        ),
        ChapterNodeResponse(
            id="ch6",
            name="Chapter 6: Conclusion",
            status=ChapterStatus.ISSUES,
            last_synced=(now - timedelta(hours=3)).isoformat(),
            logic_errors=3,
            word_count=1800,
        ),
    ]

    connections = [
        LogicConnectionResponse(source="ch1", target="ch2", status="solid"),
        LogicConnectionResponse(source="ch2", target="ch3", status="solid"),
        LogicConnectionResponse(source="ch3", target="ch4", status="solid"),
        LogicConnectionResponse(
            source="ch4",
            target="ch5",
            status="broken",
            error_description="Results not adequately connected to discussion themes",
            severity="high",
        ),
        LogicConnectionResponse(
            source="ch5",
            target="ch6",
            status="broken",
            error_description="Missing link between discussion insights and conclusions",
            severity="medium",
        ),
        LogicConnectionResponse(
            source="ch1",
            target="ch6",
            status="broken",
            error_description="Introduction claims not fully addressed in conclusion",
            severity="high",
        ),
    ]

    return ProjectGraphResponse(
        chapters=chapters,
        connections=connections,
        last_analyzed=now.isoformat(),
        overall_score=68,
    )


# =============================================================================
# War Room API (Viva Voce Simulator)
# =============================================================================

from core.auditor import VivaSimulator, simulate_defense

# Global Viva Simulator instance (maintains session state)
_viva_simulator: Optional[VivaSimulator] = None


def get_viva_simulator() -> VivaSimulator:
    """Get or create the global VivaSimulator instance."""
    global _viva_simulator
    if _viva_simulator is None:
        _viva_simulator = VivaSimulator()
    return _viva_simulator


class WarRoomStartRequest(BaseModel):
    """Request to start a War Room defense session."""
    thesis_text: str = Field(..., min_length=500, description="Full thesis text to analyze")


class WarRoomAnswerRequest(BaseModel):
    """Request to submit an answer in War Room."""
    answer: str = Field(..., min_length=10, description="Candidate's answer to the examiner's question")


class WarRoomQuestionResponse(BaseModel):
    """Response containing an examiner question."""
    success: bool
    question: Optional[str] = None
    question_number: int = 0
    session_active: bool = False
    error: Optional[str] = None


class WarRoomAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    success: bool
    rating: Optional[str] = None  # WEAK, EVASIVE, ADEQUATE, STRONG
    feedback: Optional[str] = None
    next_question: Optional[str] = None
    question_number: int = 0
    session_active: bool = False
    error: Optional[str] = None


class WarRoomSummaryResponse(BaseModel):
    """Response with defense session summary."""
    success: bool
    summary: Optional[dict] = None
    session_active: bool = False
    error: Optional[str] = None


class WarRoomStatusResponse(BaseModel):
    """Response with session status."""
    session_active: bool
    thesis_loaded: bool
    questions_asked: int
    answers_given: int


# War Room Router
warroom_router = APIRouter(
    prefix="/api/war-room",
    tags=["War Room"],
)


@warroom_router.post("/start", response_model=WarRoomQuestionResponse)
async def start_war_room(
    request: WarRoomStartRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Start a War Room defense simulation.

    Loads the thesis and generates the first hostile question.
    The examiner will identify weaknesses and probe aggressively.
    """
    simulator = get_viva_simulator()

    # Load thesis context
    load_result = simulator.load_thesis_context(user_id, request.thesis_text)
    if not load_result.get("success"):
        return WarRoomQuestionResponse(
            success=False,
            error=load_result.get("error", "Failed to load thesis"),
            session_active=False,
        )

    # Start defense
    start_result = simulator.start_defense(user_id)

    return WarRoomQuestionResponse(
        success=start_result.get("success", False),
        question=start_result.get("question"),
        question_number=start_result.get("question_number", 1),
        session_active=start_result.get("session_active", False),
        error=start_result.get("error"),
    )


@warroom_router.post("/answer", response_model=WarRoomAnswerResponse)
async def submit_war_room_answer(
    request: WarRoomAnswerRequest,
    user_id: str = Query(..., description="User identifier"),
):
    """
    Submit an answer to the examiner's question.

    The examiner will rate the answer and fire the next question.
    """
    simulator = get_viva_simulator()

    result = simulator.respond_to_answer(user_id, request.answer)

    return WarRoomAnswerResponse(
        success=result.get("success", False),
        rating=result.get("rating"),
        feedback=result.get("feedback"),
        next_question=result.get("next_question"),
        question_number=result.get("question_number", 0),
        session_active=result.get("session_active", False),
        error=result.get("error"),
    )


@warroom_router.post("/end", response_model=WarRoomSummaryResponse)
async def end_war_room(
    user_id: str = Query(..., description="User identifier"),
):
    """
    End the defense session and get summary.

    Returns performance statistics and final verdict.
    """
    simulator = get_viva_simulator()

    result = simulator.end_defense(user_id)

    return WarRoomSummaryResponse(
        success=result.get("success", False),
        summary=result.get("summary"),
        session_active=result.get("session_active", False),
        error=result.get("error"),
    )


@warroom_router.get("/status", response_model=WarRoomStatusResponse)
async def get_war_room_status(
    user_id: str = Query(..., description="User identifier"),
):
    """
    Get current War Room session status.
    """
    simulator = get_viva_simulator()

    status = simulator.get_session_status(user_id)

    return WarRoomStatusResponse(
        session_active=status.get("session_active", False),
        thesis_loaded=status.get("thesis_loaded", False),
        questions_asked=status.get("questions_asked", 0),
        answers_given=status.get("answers_given", 0),
    )


@warroom_router.post("/load-from-drive")
async def load_thesis_from_drive(
    user_id: str = Query(..., description="User identifier"),
    folder_id: Optional[str] = Query(None, description="Drive folder ID"),
):
    """
    Load thesis text from synced Google Drive files.

    Retrieves all chapter documents and combines them for the defense simulation.
    """
    service = DriveSyncService(user_id)

    if not service.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google Drive")

    try:
        # Get all Google Docs
        if folder_id:
            sync_result = service.sync_folder(folder_id, recursive=True)
            files = sync_result.changed_files if sync_result.success else []
        else:
            files = service.list_files(mime_type='application/vnd.google-apps.document')

        # Filter for chapter-like documents
        chapter_files = []
        for f in files:
            name_lower = f.name.lower()
            if any(kw in name_lower for kw in ['chapter', 'introduction', 'literature', 'method', 'result', 'discussion', 'conclusion']):
                chapter_files.append(f)

        if not chapter_files:
            raise HTTPException(status_code=404, detail="No chapter documents found in Drive")

        # Sort by chapter order
        chapter_files.sort(key=lambda f: _detect_chapter_order(f.name))

        # Export and combine all chapters
        combined_text = ""
        chapter_names = []

        for f in chapter_files:
            try:
                content = service.export_doc(f.id, ExportFormat.PLAIN_TEXT)
                combined_text += f"\n\n{'='*60}\n{f.name}\n{'='*60}\n\n{content}"
                chapter_names.append(f.name)
            except Exception as e:
                logger.warning(f"Could not export {f.name}: {e}")

        if not combined_text.strip():
            raise HTTPException(status_code=500, detail="Failed to extract text from chapters")

        # Load into simulator
        simulator = get_viva_simulator()
        load_result = simulator.load_thesis_context(user_id, combined_text)

        if not load_result.get("success"):
            raise HTTPException(status_code=500, detail=load_result.get("error", "Failed to load thesis"))

        return {
            "success": True,
            "chapters_loaded": chapter_names,
            "word_count": load_result.get("word_count", 0),
            "message": f"Loaded {len(chapter_names)} chapters. Ready for examination."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Load from Drive error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include War Room router
app.include_router(warroom_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
