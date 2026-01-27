#!/usr/bin/env python3
"""
Test script for the Airlock data connector module.

This script tests Google OAuth authentication and lists recent documents
to verify the connection is working properly.

Usage:
    python tests/test_airlock.py

Prerequisites:
    1. Place your client_secret.json in the config/ directory
    2. Run this script - it will open a browser for authentication on first run
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.airlock import (
    authenticate_user,
    list_recent_docs,
    get_auth_status,
    CLIENT_SECRET_PATH,
    TOKEN_PATH,
)


def main():
    """Run authentication test and list recent documents."""
    print("=" * 60)
    print("AIRLOCK - Data Connector Test")
    print("=" * 60)
    print()

    # Check configuration status
    print("[1] Checking configuration...")
    print(f"    Client secret path: {CLIENT_SECRET_PATH}")
    print(f"    Token path: {TOKEN_PATH}")
    print()

    status = get_auth_status()
    print(f"    Current status: {status['message']}")
    print()

    if not CLIENT_SECRET_PATH.exists():
        print("ERROR: client_secret.json not found!")
        print()
        print("To set up OAuth credentials:")
        print("  1. Go to Google Cloud Console (console.cloud.google.com)")
        print("  2. Create a new project or select an existing one")
        print("  3. Enable the Google Drive, Docs, and Sheets APIs")
        print("  4. Create OAuth 2.0 credentials (Desktop app type)")
        print("  5. Download the JSON and save it as:")
        print(f"     {CLIENT_SECRET_PATH}")
        print()
        return 1

    # Attempt authentication
    print("[2] Authenticating with Google...")
    try:
        authenticate_user()  # Test auth works
        print("    Authentication successful!")
        print()
    except Exception as e:
        print(f"    Authentication failed: {e}")
        return 1

    # List recent documents
    print("[3] Fetching recent documents from Google Drive...")
    print()

    docs = list_recent_docs(limit=10)

    if not docs:
        print("    No Google Docs or Sheets found in your Drive.")
        print("    (This might be normal if you haven't created any yet)")
    else:
        print(f"    Found {len(docs)} recent document(s):")
        print()
        print(f"    {'#':<4} {'Type':<8} {'Name':<40} {'ID'}")
        print("    " + "-" * 80)

        for i, doc in enumerate(docs, 1):
            doc_type = doc['type'].upper()
            name = doc['name'][:38] + '..' if len(doc['name']) > 40 else doc['name']
            doc_id = doc['id']
            print(f"    {i:<4} {doc_type:<8} {name:<40} {doc_id}")

    print()
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

    # Optional: Test loading a specific document
    if docs:
        print()
        print("To test loading a document, you can run:")
        print("    from core.airlock import load_google_doc")
        print(f"    text = load_google_doc('{docs[0]['id']}')")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
