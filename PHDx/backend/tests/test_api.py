"""
API Integration Tests for PHDx Production Backend

Tests the FastAPI endpoints to ensure they correctly expose
the service layer functionality.
"""

import pytest
from fastapi.testclient import TestClient

from ..main import app
from ..services.transparency_log import TransparencyLog


@pytest.fixture
def client():
    """Create test client."""
    # Clear logs before each test
    logger = TransparencyLog()
    logger.clear_logs()
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    logger = TransparencyLog()
    logger.clear_logs()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test that health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestTransparencyEndpoints:
    """Tests for transparency log endpoints."""

    def test_create_log_entry(self, client):
        """Test creating a new log entry."""
        response = client.post("/transparency/log", json={
            "module": "TestModule",
            "action": "TestAction",
            "status": "SUCCESS"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "TestModule"
        assert data["action"] == "TestAction"
        assert data["status"] == "SUCCESS"
        assert "timestamp" in data

    def test_get_all_logs(self, client):
        """Test retrieving all logs."""
        # Create some logs
        client.post("/transparency/log", json={
            "module": "Module1",
            "action": "Action1",
            "status": "Status1"
        })
        client.post("/transparency/log", json={
            "module": "Module2",
            "action": "Action2",
            "status": "Status2"
        })

        response = client.get("/transparency/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_filter_logs_by_module(self, client):
        """Test filtering logs by module name."""
        client.post("/transparency/log", json={
            "module": "Airlock",
            "action": "Action1",
            "status": "Status1"
        })
        client.post("/transparency/log", json={
            "module": "DNA_Engine",
            "action": "Action2",
            "status": "Status2"
        })

        response = client.get("/transparency/logs?module=Airlock")
        data = response.json()
        assert data["count"] == 1
        assert data["logs"][0]["module"] == "Airlock"


class TestAirlockEndpoints:
    """Tests for ethics airlock endpoints."""

    def test_sanitize_with_pii(self, client):
        """Test sanitizing text with PII."""
        response = client.post("/airlock/sanitize", json={
            "text": "Contact john@example.com for info"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["pii_found"] == True
        assert data["status"] == "INTERVENTION_REQUIRED"
        assert "[REDACTED]" in data["sanitized_text"]
        assert "john@example.com" not in data["sanitized_text"]

    def test_sanitize_clean_text(self, client):
        """Test sanitizing clean text."""
        response = client.post("/airlock/sanitize", json={
            "text": "This is clean text"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["pii_found"] == False
        assert data["status"] == "CLEAN"
        assert data["sanitized_text"] == "This is clean text"

    def test_detect_pii(self, client):
        """Test detecting PII without redacting."""
        response = client.post("/airlock/detect", json={
            "text": "Email: test@test.com, Phone: 07123456789"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["pii_found"] == True
        assert "email" in data["types_found"]
        assert "phone" in data["types_found"]

    def test_get_patterns(self, client):
        """Test getting PII patterns."""
        response = client.get("/airlock/patterns")

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "phone" in data
        assert "names" in data


class TestDNAEngineEndpoints:
    """Tests for DNA engine endpoints."""

    def test_analyze_style(self, client):
        """Test style analysis."""
        response = client.post("/dna/analyze", json={
            "text": "Short. This is a longer sentence with more words.",
            "author_baseline_variance": 15.0
        })

        assert response.status_code == 200
        data = response.json()
        assert "variance" in data
        assert "style_match" in data
        assert data["status"] in ["MATCH", "ANOMALY_DETECTED"]

    def test_get_baseline(self, client):
        """Test getting baseline variance."""
        response = client.get("/dna/baseline")

        assert response.status_code == 200
        data = response.json()
        assert data["author_baseline_variance"] == 15.0
        assert data["match_threshold"] == 10.0

    def test_set_baseline(self, client):
        """Test setting baseline variance."""
        response = client.put("/dna/baseline?variance=20.0")

        assert response.status_code == 200
        data = response.json()
        assert data["author_baseline_variance"] == 20.0
        assert data["match_threshold"] == 15.0


class TestAuditorEndpoints:
    """Tests for auditor endpoints."""

    def test_evaluate_scores(self, client):
        """Test evaluating compliance scores."""
        response = client.post("/auditor/evaluate", json={
            "text": "Test thesis text",
            "scores": {
                "Originality": 80,
                "Criticality": 70,
                "Rigour": 90
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total_weighted_score"] == 79.5
        assert data["weights_applied"]["Originality"] == 0.35
        assert data["weights_applied"]["Criticality"] == 0.35
        assert data["weights_applied"]["Rigour"] == 0.30

    def test_missing_criteria_error(self, client):
        """Test error when criteria are missing."""
        response = client.post("/auditor/evaluate", json={
            "text": "Test text",
            "scores": {
                "Originality": 80
                # Missing Criticality and Rigour
            }
        })

        assert response.status_code == 400
        assert "Missing required criteria" in response.json()["detail"]

    def test_get_weights(self, client):
        """Test getting scoring weights."""
        response = client.get("/auditor/weights")

        assert response.status_code == 200
        data = response.json()
        assert data["Originality"] == 0.35
        assert data["Criticality"] == 0.35
        assert data["Rigour"] == 0.30


class TestFeedbackEndpoints:
    """Tests for feedback processor endpoints."""

    def test_process_feedback(self, client):
        """Test processing feedback into categories."""
        response = client.post("/feedback/process", json={
            "text": "This is a blocker\nConsider this\nThere is a typo"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["categories"]["RED"]) == 1
        assert len(data["categories"]["AMBER"]) == 1
        assert len(data["categories"]["GREEN"]) == 1
        assert data["total_items"] == 3

    def test_get_priority_items(self, client):
        """Test getting only priority (blocker) items."""
        response = client.post("/feedback/priority", json={
            "text": "This is a blocker\nConsider this\nAnother blocker"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["priority_items"]) == 2

    def test_get_counts(self, client):
        """Test getting item counts by category."""
        response = client.post("/feedback/counts", json={
            "text": "Blocker 1\nBlocker 2\nConsider this\nTypo here"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["RED"] == 2
        assert data["AMBER"] == 1
        assert data["GREEN"] == 1
        assert data["total"] == 4
