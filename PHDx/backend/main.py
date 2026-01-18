"""
PHDx Production Backend - FastAPI Application

Main entry point for the PHDx production API.
Implements verified simulation logic for:
- TransparencyLog: Audit logging
- EthicsAirlock: PII sanitization
- DNAEngine: Style analysis
- Auditor: Compliance scoring
- FeedbackProcessor: Feedback categorization
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import (
    transparency_router,
    airlock_router,
    dna_engine_router,
    auditor_router,
    feedback_router,
)

# Application metadata
APP_TITLE = "PHDx Production API"
APP_DESCRIPTION = """
## PHDx - PhD Thesis Command Center

Production backend implementing the verified PHDx core module logic.

### Modules

* **Transparency Log** - Audit logging for academic transparency compliance
* **Ethics Airlock** - PII detection and sanitization
* **DNA Engine** - Linguistic fingerprint and style analysis
* **Auditor** - Oxford Brookes PhD compliance scoring
* **Feedback Processor** - Supervisor feedback categorization (Traffic Light System)

### Logic Constraints

All modules implement the **exact logic** from the verified simulation:
- PII regex patterns match simulation specification
- Variance formula: `sum((x - mean)^2) / n`
- Weights: Originality 35%, Criticality 35%, Rigour 30%
- Keywords: "blocker" → RED, "consider" → AMBER, "typo" → GREEN
"""
APP_VERSION = "1.0.0"

# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transparency_router)
app.include_router(airlock_router)
app.include_router(dna_engine_router)
app.include_router(auditor_router)
app.include_router(feedback_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": APP_VERSION}


@app.get("/modules", tags=["Info"])
async def list_modules():
    """List all available modules and their endpoints."""
    return {
        "modules": [
            {
                "name": "Transparency Log",
                "prefix": "/transparency",
                "description": "Audit logging for academic transparency",
                "endpoints": [
                    "POST /transparency/log - Create log entry",
                    "GET /transparency/logs - Get all logs",
                    "DELETE /transparency/logs - Clear logs"
                ]
            },
            {
                "name": "Ethics Airlock",
                "prefix": "/airlock",
                "description": "PII detection and sanitization",
                "endpoints": [
                    "POST /airlock/sanitize - Sanitize text",
                    "POST /airlock/detect - Detect PII",
                    "GET /airlock/patterns - Get regex patterns"
                ]
            },
            {
                "name": "DNA Engine",
                "prefix": "/dna",
                "description": "Writing style analysis",
                "endpoints": [
                    "POST /dna/analyze - Analyze writing style",
                    "GET /dna/baseline - Get baseline variance",
                    "PUT /dna/baseline - Set baseline variance"
                ]
            },
            {
                "name": "Auditor",
                "prefix": "/auditor",
                "description": "Compliance scoring (Oxford Brookes criteria)",
                "endpoints": [
                    "POST /auditor/evaluate - Evaluate scores",
                    "GET /auditor/weights - Get scoring weights",
                    "POST /auditor/validate - Validate score submission"
                ]
            },
            {
                "name": "Feedback Processor",
                "prefix": "/feedback",
                "description": "Feedback categorization (Traffic Light System)",
                "endpoints": [
                    "POST /feedback/process - Categorize feedback",
                    "POST /feedback/priority - Get priority items",
                    "POST /feedback/counts - Get category counts"
                ]
            }
        ]
    }


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
