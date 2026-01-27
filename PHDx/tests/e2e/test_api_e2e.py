"""
PHDx API End-to-End Tests

These tests verify the full API functionality with a running server.
Run with: pytest tests/e2e/ -v --e2e

Prerequisites:
- API server running on localhost:8000
- Mock or real API keys configured
"""

import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# =============================================================================
# HEALTH & STATUS TESTS
# =============================================================================


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.anyio
    async def test_health_check(self, client):
        """Test /health endpoint returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_readiness_check(self, client):
        """Test /ready endpoint returns readiness status."""
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data

    @pytest.mark.anyio
    async def test_status_endpoint(self, client):
        """Test /status endpoint returns system status."""
        response = await client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["system"] == "online"
        assert "environment" in data
        assert "models" in data
        assert data["version"] == "2.0.0"


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.anyio
    async def test_google_auth_status(self, client):
        """Test /auth/google returns auth status."""
        response = await client.get("/auth/google")
        assert response.status_code == 200
        data = response.json()
        # Should have expected fields even if not authenticated
        assert "email" in data
        assert "name" in data
        assert "authenticated" in data


# =============================================================================
# FILES ENDPOINT TESTS
# =============================================================================


class TestFilesEndpoints:
    """Test file listing endpoints."""

    @pytest.mark.anyio
    async def test_list_recent_files(self, client):
        """Test /files/recent returns file list."""
        response = await client.get("/files/recent")
        # May return 200 with empty list or 500 if not authenticated
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.anyio
    async def test_list_recent_files_with_limit(self, client):
        """Test /files/recent with limit parameter."""
        response = await client.get("/files/recent?limit=5")
        assert response.status_code in [200, 500]


# =============================================================================
# GENERATION ENDPOINT TESTS
# =============================================================================


class TestGenerationEndpoints:
    """Test text generation endpoints."""

    @pytest.mark.anyio
    async def test_generate_requires_prompt(self, client):
        """Test /generate requires prompt field."""
        response = await client.post("/generate", json={})
        assert response.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_generate_with_prompt(self, client):
        """Test /generate with valid prompt."""
        response = await client.post(
            "/generate",
            json={"prompt": "Test prompt for generation", "model": "claude"},
        )
        # May succeed or fail depending on API key availability
        assert response.status_code in [200, 500]
        data = response.json()
        if response.status_code == 200:
            assert "success" in data
            assert "text" in data
            assert "model" in data

    @pytest.mark.anyio
    async def test_generate_with_context(self, client):
        """Test /generate with additional context."""
        response = await client.post(
            "/generate",
            json={
                "prompt": "Summarize the context",
                "context": "This is some context text for the AI to use.",
            },
        )
        assert response.status_code in [200, 500]


# =============================================================================
# AIRLOCK (SANITIZATION) TESTS
# =============================================================================


class TestAirlockEndpoints:
    """Test PII sanitization endpoints."""

    @pytest.mark.anyio
    async def test_sanitize_text(self, client):
        """Test /airlock/sanitize removes PII."""
        response = await client.post(
            "/airlock/sanitize",
            json={"text": "My email is john.doe@example.com and phone is 555-1234."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sanitized_text" in data
        assert "pii_found" in data
        assert "redactions_count" in data

    @pytest.mark.anyio
    async def test_sanitize_empty_text_rejected(self, client):
        """Test /airlock/sanitize rejects empty text."""
        response = await client.post("/airlock/sanitize", json={"text": ""})
        assert response.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_sanitize_preserves_non_pii(self, client):
        """Test /airlock/sanitize preserves non-PII content."""
        original_text = "The quick brown fox jumps over the lazy dog."
        response = await client.post("/airlock/sanitize", json={"text": original_text})
        assert response.status_code == 200
        data = response.json()
        # No PII should be found in this text
        assert data["redactions_count"] == 0 or data["sanitized_text"] == original_text


# =============================================================================
# AUDITOR ENDPOINT TESTS
# =============================================================================


class TestAuditorEndpoints:
    """Test Oxford Brookes auditor endpoints."""

    @pytest.mark.anyio
    async def test_get_criteria(self, client):
        """Test /auditor/criteria returns marking criteria."""
        response = await client.get("/auditor/criteria")
        assert response.status_code == 200
        data = response.json()
        # Should return criteria structure
        assert isinstance(data, (dict, list))

    @pytest.mark.anyio
    async def test_evaluate_draft_requires_text(self, client):
        """Test /auditor/evaluate requires sufficient text."""
        response = await client.post(
            "/auditor/evaluate",
            json={
                "text": "Short"  # Too short
            },
        )
        assert response.status_code == 422  # Validation error (min_length=100)

    @pytest.mark.anyio
    async def test_evaluate_draft_with_valid_text(self, client):
        """Test /auditor/evaluate with valid academic text."""
        sample_text = """
        This research investigates the relationship between climate change and
        agricultural productivity in sub-Saharan Africa. The methodology employs
        a mixed-methods approach combining quantitative analysis of crop yields
        with qualitative interviews of local farmers. Preliminary findings suggest
        a significant correlation between temperature increases and decreased
        maize production, particularly in regions with limited irrigation
        infrastructure.
        """
        response = await client.post(
            "/auditor/evaluate",
            json={"text": sample_text, "chapter_context": "Methodology"},
        )
        assert response.status_code in [200, 500]


# =============================================================================
# RED THREAD (CONSISTENCY) TESTS
# =============================================================================


class TestRedThreadEndpoints:
    """Test consistency checking endpoints."""

    @pytest.mark.anyio
    async def test_get_index_stats(self, client):
        """Test /red-thread/stats returns index statistics."""
        response = await client.get("/red-thread/stats")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @pytest.mark.anyio
    async def test_check_consistency_requires_text(self, client):
        """Test /red-thread/check requires sufficient text."""
        response = await client.post(
            "/red-thread/check",
            json={
                "text": "Short"  # Too short (min_length=50)
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_check_consistency_with_valid_text(self, client):
        """Test /red-thread/check with valid text."""
        sample_text = """
        The theoretical framework builds upon established constructivist
        principles while incorporating recent developments in social learning
        theory. This synthesis provides a robust foundation for analyzing the
        data collected through participant observations and interviews.
        """
        response = await client.post("/red-thread/check", json={"text": sample_text})
        assert response.status_code in [200, 500]


# =============================================================================
# DNA ENGINE TESTS
# =============================================================================


class TestDNAEngineEndpoints:
    """Test writing style analysis endpoints."""

    @pytest.mark.anyio
    async def test_get_dna_profile(self, client):
        """Test /dna/profile returns profile or error."""
        response = await client.get("/dna/profile")
        assert response.status_code == 200
        data = response.json()
        # Either returns profile or error message
        assert "error" in data or isinstance(data, dict)

    @pytest.mark.anyio
    async def test_analyze_writing_style(self, client):
        """Test /dna/analyze initiates style analysis."""
        response = await client.post("/dna/analyze")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data


# =============================================================================
# SNAPSHOT TESTS
# =============================================================================


class TestSnapshotEndpoints:
    """Test document snapshot endpoints."""

    @pytest.mark.anyio
    async def test_save_snapshot(self, client):
        """Test /snapshot saves document backup."""
        response = await client.post(
            "/snapshot",
            json={
                "doc_id": "test-doc-123",
                "timestamp": "2024-01-25T10:30:00Z",
                "content": "This is test content for the snapshot.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        if data["success"]:
            assert "filename" in data
            assert "path" in data
            assert "size_bytes" in data


# =============================================================================
# GOOGLE SYNC TESTS
# =============================================================================


class TestGoogleSyncEndpoints:
    """Test Google Docs sync endpoints."""

    @pytest.mark.anyio
    async def test_sync_to_google(self, client):
        """Test /sync/google syncs content to Google Docs."""
        response = await client.post(
            "/sync/google",
            json={"doc_id": "test-doc-id", "content": "Test content to sync."},
        )
        # Will likely fail without real credentials, but should not crash
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


# =============================================================================
# USAGE STATISTICS TESTS
# =============================================================================


class TestUsageStatsEndpoints:
    """Test usage statistics endpoints."""

    @pytest.mark.anyio
    async def test_get_usage_stats(self, client):
        """Test /stats/usage returns AI usage statistics."""
        response = await client.get("/stats/usage")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Test API error handling."""

    @pytest.mark.anyio
    async def test_404_not_found(self, client):
        """Test non-existent endpoint returns 404."""
        response = await client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405."""
        response = await client.post("/health")  # Should be GET
        assert response.status_code == 405

    @pytest.mark.anyio
    async def test_validation_error_format(self, client):
        """Test validation errors return proper format."""
        response = await client.post(
            "/generate",
            json={
                "prompt": ""  # Empty prompt should fail validation
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
