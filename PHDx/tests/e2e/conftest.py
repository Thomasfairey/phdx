"""
PHDx E2E Test Configuration

Provides fixtures and configuration for end-to-end API tests.
"""

import pytest
import sys
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (may require running server)"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow-running")


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def mock_config():
    """Provide mock configuration for testing."""
    return {
        "anthropic_api_key": "mock-anthropic-key",
        "openai_api_key": "mock-openai-key",
        "google_api_key": "mock-google-key",
        "pinecone_api_key": None,
        "mock_mode": True,
    }
