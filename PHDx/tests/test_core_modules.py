"""
Unit tests for PHDx core modules.

These tests use mocking to avoid dependencies on external APIs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json


# =============================================================================
# LLM GATEWAY TESTS
# =============================================================================

class TestLLMGateway:
    """Tests for core/llm_gateway.py"""

    def test_estimate_tokens(self):
        """Token estimation should be approximately chars/4."""
        from core.llm_gateway import estimate_tokens

        # Basic test
        assert estimate_tokens("") == 0
        assert estimate_tokens("test") == 1  # 4 chars / 4 = 1
        assert estimate_tokens("hello world test") == 4  # 16 chars / 4 = 4

        # Longer text
        long_text = "x" * 4000
        assert estimate_tokens(long_text) == 1000

    def test_route_task_drafting(self):
        """Drafting tasks should route to writer model."""
        from core.llm_gateway import _route_task

        mock_models = {'context': None, 'writer': Mock(), 'auditor': Mock()}

        assert _route_task("drafting", 1000, mock_models) == "writer"
        assert _route_task("synthesis", 1000, mock_models) == "writer"
        assert _route_task("writing", 1000, mock_models) == "writer"
        assert _route_task("draft", 1000, mock_models) == "writer"

    def test_route_task_auditing(self):
        """Auditing tasks should route to auditor model."""
        from core.llm_gateway import _route_task

        mock_models = {'context': None, 'writer': Mock(), 'auditor': Mock()}

        assert _route_task("audit", 1000, mock_models) == "auditor"
        assert _route_task("critique", 1000, mock_models) == "auditor"
        assert _route_task("review", 1000, mock_models) == "auditor"
        assert _route_task("check", 1000, mock_models) == "auditor"

    def test_route_task_heavy_lift_with_context(self):
        """Heavy lift (>30k tokens) should use context model if available."""
        from core.llm_gateway import _route_task, HEAVY_LIFT_THRESHOLD

        mock_models = {'context': Mock(), 'writer': Mock(), 'auditor': Mock()}

        # Above threshold should use context
        assert _route_task("drafting", HEAVY_LIFT_THRESHOLD + 1, mock_models) == "context"
        assert _route_task("audit", HEAVY_LIFT_THRESHOLD + 1, mock_models) == "context"

    def test_route_task_heavy_lift_fallback(self):
        """Heavy lift should fall back to writer if context unavailable."""
        from core.llm_gateway import _route_task, HEAVY_LIFT_THRESHOLD

        mock_models = {'context': None, 'writer': Mock(), 'auditor': Mock()}

        assert _route_task("drafting", HEAVY_LIFT_THRESHOLD + 1, mock_models) == "writer"

    def test_route_task_unknown_defaults_to_writer(self):
        """Unknown task types should default to writer."""
        from core.llm_gateway import _route_task

        mock_models = {'context': None, 'writer': Mock(), 'auditor': Mock()}

        assert _route_task("unknown_task", 1000, mock_models) == "writer"
        assert _route_task("random", 500, mock_models) == "writer"


# =============================================================================
# AIRLOCK TESTS
# =============================================================================

class TestAirlock:
    """Tests for core/airlock.py"""

    def test_extract_text_from_doc(self):
        """Test Google Doc JSON text extraction."""
        from core.airlock import _extract_text_from_doc

        # Simple paragraph
        doc = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {'textRun': {'content': 'Hello '}},
                                {'textRun': {'content': 'World'}}
                            ]
                        }
                    }
                ]
            }
        }
        assert _extract_text_from_doc(doc) == 'Hello World'

    def test_extract_text_from_doc_with_table(self):
        """Test text extraction from tables."""
        from core.airlock import _extract_text_from_doc

        doc = {
            'body': {
                'content': [
                    {
                        'table': {
                            'tableRows': [
                                {
                                    'tableCells': [
                                        {
                                            'content': [
                                                {
                                                    'paragraph': {
                                                        'elements': [
                                                            {'textRun': {'content': 'Cell 1'}}
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
        assert 'Cell 1' in _extract_text_from_doc(doc)

    def test_extract_text_from_empty_doc(self):
        """Test handling of empty document."""
        from core.airlock import _extract_text_from_doc

        assert _extract_text_from_doc({}) == ''
        assert _extract_text_from_doc({'body': {}}) == ''
        assert _extract_text_from_doc({'body': {'content': []}}) == ''

    def test_get_auth_status_no_client_secret(self):
        """Auth status should indicate missing client secret."""
        import core.airlock as airlock_module

        # Patch the module-level constant
        with patch.object(airlock_module, 'CLIENT_SECRET_PATH') as mock_path:
            mock_path.exists.return_value = False

            status = airlock_module.get_auth_status()
            assert status['authenticated'] is False
            assert 'oauth' in status['message'].lower() or 'client_secret' in status['message'].lower()


# =============================================================================
# DNA ENGINE TESTS
# =============================================================================

class TestDNAEngine:
    """Tests for core/dna_engine.py"""

    def test_calculate_sentence_complexity(self):
        """Test sentence complexity calculation."""
        from core.dna_engine import calculate_sentence_complexity

        # Simple text
        result = calculate_sentence_complexity("This is a test. Another sentence here.")
        assert 'average_length' in result
        assert 'total_sentences' in result
        assert result['total_sentences'] == 2

    def test_calculate_sentence_complexity_empty(self):
        """Test handling of empty text."""
        from core.dna_engine import calculate_sentence_complexity

        result = calculate_sentence_complexity("")
        assert result['total_sentences'] == 0
        assert result['average_length'] == 0

    def test_analyze_hedging_frequency(self):
        """Test hedging language detection."""
        from core.dna_engine import analyze_hedging_frequency

        text = "It suggests that perhaps the data might indicate something."
        result = analyze_hedging_frequency(text)

        assert 'total_hedges' in result
        assert result['total_hedges'] > 0  # Should detect "suggests", "perhaps", "might"
        assert 'hedging_density_per_1000_words' in result

    def test_extract_transition_vocabulary(self):
        """Test transition word extraction."""
        from core.dna_engine import extract_transition_vocabulary

        text = "Furthermore, this is important. However, there are challenges. Therefore, we conclude."
        result = extract_transition_vocabulary(text)

        assert 'total_transitions' in result
        assert result['total_transitions'] >= 3
        assert 'by_category' in result

    def test_chunk_text_for_analysis(self):
        """Test text chunking."""
        from core.dna_engine import chunk_text_for_analysis

        # Create text with 5000 words
        words = ["word"] * 5000
        text = " ".join(words)

        chunks = chunk_text_for_analysis(text, chunk_size=2000)
        assert len(chunks) == 3  # 5000/2000 = 2.5, rounds up to 3


# =============================================================================
# AUDITOR TESTS
# =============================================================================

class TestAuditor:
    """Tests for core/auditor.py"""

    def test_marking_criteria_structure(self):
        """Test that marking criteria is properly structured."""
        from core.auditor import OXFORD_BROOKES_CRITERIA

        assert 'institution' in OXFORD_BROOKES_CRITERIA
        assert OXFORD_BROOKES_CRITERIA['institution'] == 'Oxford Brookes University'

        assert 'criteria' in OXFORD_BROOKES_CRITERIA
        criteria = OXFORD_BROOKES_CRITERIA['criteria']

        # Check all three criteria exist
        assert 'originality' in criteria
        assert 'criticality' in criteria
        assert 'rigour' in criteria

        # Check weights sum to 1.0
        total_weight = sum(c['weight'] for c in criteria.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_criteria_summary(self):
        """Test criteria summary generation."""
        from core.auditor import BrookesAuditor

        auditor = BrookesAuditor()
        summary = auditor.get_criteria_summary()

        assert 'institution' in summary
        assert 'criteria' in summary
        assert 'grade_scale' in summary
        assert len(summary['criteria']) == 3


# =============================================================================
# RED THREAD TESTS
# =============================================================================

class TestRedThread:
    """Tests for core/red_thread.py"""

    def test_extract_paragraphs(self):
        """Test paragraph extraction."""
        from core.red_thread import RedThreadEngine

        engine = RedThreadEngine(use_local=True)

        text = """This is the first paragraph with enough words to be extracted properly.

        This is the second paragraph which also has sufficient words for extraction.

        Short."""

        paragraphs = engine._extract_paragraphs(text, min_words=5)

        # Should have 2 paragraphs (the short one is filtered)
        assert len(paragraphs) == 2

    def test_score_to_label(self):
        """Test consistency score labeling."""
        from core.red_thread import RedThreadEngine

        engine = RedThreadEngine(use_local=True)

        assert engine._score_to_label(100) == "Excellent"
        assert engine._score_to_label(95) == "Excellent"
        assert engine._score_to_label(85) == "Good"
        assert engine._score_to_label(70) == "Fair"
        assert engine._score_to_label(50) == "Needs Review"
        assert engine._score_to_label(30) == "Critical Issues"


# =============================================================================
# SECRETS UTILS TESTS
# =============================================================================

class TestSecretsUtils:
    """Tests for core/secrets_utils.py"""

    def test_get_secret_from_env(self):
        """Test secret retrieval from environment variables."""
        from core.secrets_utils import get_secret
        import os

        # Set a test env var
        os.environ['TEST_SECRET_KEY'] = 'test_value'

        try:
            result = get_secret('TEST_SECRET_KEY')
            assert result == 'test_value'
        finally:
            del os.environ['TEST_SECRET_KEY']

    def test_get_secret_default(self):
        """Test default value when secret not found."""
        from core.secrets_utils import get_secret

        result = get_secret('NONEXISTENT_KEY', 'default_value')
        assert result == 'default_value'

    def test_has_secret(self):
        """Test secret existence check."""
        from core.secrets_utils import has_secret
        import os

        os.environ['TEST_EXISTS'] = 'value'

        try:
            assert has_secret('TEST_EXISTS') is True
            assert has_secret('DOES_NOT_EXIST') is False
        finally:
            del os.environ['TEST_EXISTS']


# =============================================================================
# API SERVER TESTS
# =============================================================================

class TestAPIServer:
    """Tests for api/server.py"""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI."""
        from fastapi.testclient import TestClient
        from api.server import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_status_endpoint(self, client):
        """Test status endpoint."""
        with patch('core.llm_gateway.get_available_models', return_value=['writer', 'auditor']):
            response = client.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert data['system'] == 'online'
            assert 'models' in data
