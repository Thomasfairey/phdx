"""
PHDx FastAPI Server - Headless Backend

Includes:
- Core API endpoints for the web client
- Extension API (/api/v1/extension) for Google Docs Sidebar
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional, Literal

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Header, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
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
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="PHDx API",
    description="PhD Thesis Command Center - Headless Backend with Extension Support",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
