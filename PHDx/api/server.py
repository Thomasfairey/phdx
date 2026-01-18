"""
PHDx FastAPI Server - Headless Backend
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from core import airlock
from core import llm_gateway

BACKUPS_DIR = Path(__file__).parent.parent / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)

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

app = FastAPI(
    title="PHDx API",
    description="PhD Thesis Command Center - Headless Backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
