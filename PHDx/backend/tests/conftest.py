"""
Pytest configuration and fixtures for PHDx backend tests.
"""

import pytest
from fastapi.testclient import TestClient

from ..main import app
from ..services.transparency_log import TransparencyLog


@pytest.fixture
def client():
    """Create a fresh test client for each test."""
    # Clear logs before test
    logger = TransparencyLog()
    logger.clear_logs()

    yield TestClient(app)

    # Clean up after test
    logger.clear_logs()


@pytest.fixture
def transparency_log():
    """Create a fresh TransparencyLog instance."""
    logger = TransparencyLog()
    logger.clear_logs()
    yield logger
    logger.clear_logs()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Import singleton getters
    from ..services.transparency_log import get_transparency_log
    from ..services.ethics_airlock import get_ethics_airlock
    from ..services.dna_engine import get_dna_engine
    from ..services.auditor import get_auditor
    from ..services.feedback_processor import get_feedback_processor

    # Clear the transparency log
    log = get_transparency_log()
    log.clear_logs()

    # Reset DNA engine baseline
    dna = get_dna_engine()
    dna.set_baseline(15.0)

    yield

    # Cleanup
    log.clear_logs()
