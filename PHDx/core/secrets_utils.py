"""
Secrets Utilities for PHDx

Provides a unified way to access secrets that works with both:
- Environment variables (.env files) for local development
- Streamlit secrets for cloud deployment
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret from Streamlit secrets (cloud) or environment variables (local).

    Priority:
    1. Streamlit secrets (st.secrets) - for Streamlit Cloud deployment
    2. Environment variables (os.environ) - for local development
    3. Default value if neither is available

    Args:
        key: The name of the secret to retrieve
        default: Default value if secret is not found

    Returns:
        The secret value or default
    """
    # Try Streamlit secrets first (for cloud deployment)
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Fall back to environment variables
    return os.getenv(key, default)


def has_secret(key: str) -> bool:
    """Check if a secret exists (in either Streamlit secrets or environment)."""
    return get_secret(key) is not None
