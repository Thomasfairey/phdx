"""
Secrets Utilities for PHDx

Provides a unified way to access secrets that works with both:
- Environment variables (.env files) for local development
- Streamlit secrets for cloud deployment

Also handles secure storage of OAuth tokens for Google Drive sync.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Storage paths
CONFIG_DIR = Path(__file__).parent.parent / 'config'
TOKENS_DIR = CONFIG_DIR / 'tokens'
ENCRYPTION_KEY_PATH = CONFIG_DIR / '.encryption_key'


def get_secret(key: str, default: str = None) -> str:
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
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Fall back to environment variables
    return os.getenv(key, default)


def has_secret(key: str) -> bool:
    """Check if a secret exists (in either Streamlit secrets or environment)."""
    return get_secret(key) is not None


# =============================================================================
# OAuth Token Storage (Secure, Encrypted)
# =============================================================================

def _get_or_create_encryption_key() -> bytes:
    """Get or create the encryption key for token storage."""
    ENCRYPTION_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)

    if ENCRYPTION_KEY_PATH.exists():
        return ENCRYPTION_KEY_PATH.read_bytes()

    # Generate new key
    key = Fernet.generate_key()
    ENCRYPTION_KEY_PATH.write_bytes(key)
    # Restrict permissions (Unix only)
    try:
        os.chmod(ENCRYPTION_KEY_PATH, 0o600)
    except Exception:
        pass
    return key


def _get_cipher() -> Fernet:
    """Get the Fernet cipher for encryption/decryption."""
    key = _get_or_create_encryption_key()
    return Fernet(key)


def store_oauth_tokens(user_id: str, tokens: dict) -> None:
    """
    Securely store OAuth tokens for a user.

    Args:
        user_id: Unique identifier for the user
        tokens: Dictionary containing access_token, refresh_token, etc.
    """
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)

    # Add metadata
    token_data = {
        **tokens,
        'stored_at': datetime.now().isoformat(),
        'user_id': user_id,
    }

    # Encrypt and store
    cipher = _get_cipher()
    encrypted = cipher.encrypt(json.dumps(token_data).encode())

    token_path = TOKENS_DIR / f'{user_id}.token'
    token_path.write_bytes(encrypted)

    # Restrict permissions
    try:
        os.chmod(token_path, 0o600)
    except Exception:
        pass


def get_oauth_tokens(user_id: str) -> Optional[dict]:
    """
    Retrieve stored OAuth tokens for a user.

    Args:
        user_id: Unique identifier for the user

    Returns:
        Token dictionary or None if not found
    """
    token_path = TOKENS_DIR / f'{user_id}.token'

    if not token_path.exists():
        return None

    try:
        cipher = _get_cipher()
        encrypted = token_path.read_bytes()
        decrypted = cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    except Exception:
        return None


def delete_oauth_tokens(user_id: str) -> bool:
    """
    Delete stored OAuth tokens for a user.

    Args:
        user_id: Unique identifier for the user

    Returns:
        True if deleted, False if not found
    """
    token_path = TOKENS_DIR / f'{user_id}.token'

    if token_path.exists():
        token_path.unlink()
        return True
    return False


def update_oauth_tokens(user_id: str, updates: dict) -> Optional[dict]:
    """
    Update specific fields in stored OAuth tokens.

    Args:
        user_id: Unique identifier for the user
        updates: Dictionary of fields to update

    Returns:
        Updated token dictionary or None if not found
    """
    tokens = get_oauth_tokens(user_id)
    if tokens is None:
        return None

    tokens.update(updates)
    tokens['updated_at'] = datetime.now().isoformat()
    store_oauth_tokens(user_id, tokens)
    return tokens


def list_stored_users() -> list[str]:
    """List all user IDs with stored tokens."""
    if not TOKENS_DIR.exists():
        return []

    return [
        f.stem for f in TOKENS_DIR.glob('*.token')
    ]


# =============================================================================
# Sync State Storage (for change detection)
# =============================================================================

SYNC_STATE_DIR = CONFIG_DIR / 'sync_state'


def store_sync_state(user_id: str, folder_id: str, state: dict) -> None:
    """
    Store sync state for change detection.

    Args:
        user_id: User identifier
        folder_id: Google Drive folder ID
        state: Dictionary with file IDs and their modifiedTime
    """
    SYNC_STATE_DIR.mkdir(parents=True, exist_ok=True)

    state_data = {
        'user_id': user_id,
        'folder_id': folder_id,
        'files': state,
        'synced_at': datetime.now().isoformat(),
    }

    state_path = SYNC_STATE_DIR / f'{user_id}_{folder_id}.json'
    state_path.write_text(json.dumps(state_data, indent=2))


def get_sync_state(user_id: str, folder_id: str) -> Optional[dict]:
    """
    Get stored sync state for a folder.

    Args:
        user_id: User identifier
        folder_id: Google Drive folder ID

    Returns:
        Sync state dictionary or None
    """
    state_path = SYNC_STATE_DIR / f'{user_id}_{folder_id}.json'

    if not state_path.exists():
        return None

    try:
        return json.loads(state_path.read_text())
    except Exception:
        return None


def delete_sync_state(user_id: str, folder_id: str) -> bool:
    """Delete sync state for a folder."""
    state_path = SYNC_STATE_DIR / f'{user_id}_{folder_id}.json'

    if state_path.exists():
        state_path.unlink()
        return True
    return False
