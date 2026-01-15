"""
Airlock - Data Connector Module

Google OAuth 2.0 authentication and document loading utilities for the PhD
writing assistant. Provides secure access to Google Drive, Docs, and Sheets,
as well as local file parsing capabilities.
"""

import os
import json
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# OAuth 2.0 Scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]

# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent / 'config'
CLIENT_SECRET_PATH = CONFIG_DIR / 'client_secret.json'
TOKEN_PATH = CONFIG_DIR / 'token.json'


def authenticate_user() -> Credentials:
    """
    Authenticate user via Google OAuth 2.0.

    Loads credentials from config/token.json if valid, otherwise launches
    the browser-based OAuth flow to obtain new credentials.

    Returns:
        google.oauth2.credentials.Credentials: Authenticated credentials object.

    Raises:
        FileNotFoundError: If client_secret.json is not found.
    """
    creds = None

    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Check for existing token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # If no valid credentials, initiate OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            creds.refresh(Request())
        else:
            # Run full OAuth flow
            if not CLIENT_SECRET_PATH.exists():
                raise FileNotFoundError(
                    f"Client secret not found at {CLIENT_SECRET_PATH}. "
                    "Please download OAuth credentials from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds


def list_recent_docs(limit: int = 10) -> list[dict]:
    """
    List the most recently modified Google Docs and Sheets.

    Args:
        limit: Maximum number of documents to return (default 10).

    Returns:
        List of dictionaries with keys: 'name', 'id', 'type'.
    """
    creds = authenticate_user()
    service = build('drive', 'v3', credentials=creds)

    # Query for Google Docs and Sheets, ordered by modified time
    query = (
        "mimeType='application/vnd.google-apps.document' or "
        "mimeType='application/vnd.google-apps.spreadsheet'"
    )

    try:
        results = service.files().list(
            q=query,
            pageSize=limit,
            orderBy='modifiedTime desc',
            fields='files(id, name, mimeType)'
        ).execute()

        files = results.get('files', [])

        # Map MIME types to friendly names
        mime_type_map = {
            'application/vnd.google-apps.document': 'doc',
            'application/vnd.google-apps.spreadsheet': 'sheet',
        }

        return [
            {
                'name': f['name'],
                'id': f['id'],
                'type': mime_type_map.get(f['mimeType'], 'unknown'),
            }
            for f in files
        ]

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def load_google_doc(doc_id: str) -> str:
    """
    Load the full text content of a Google Doc.

    Args:
        doc_id: The Google Doc ID.

    Returns:
        Extracted text content as a string.
    """
    creds = authenticate_user()
    service = build('docs', 'v1', credentials=creds)

    try:
        document = service.documents().get(documentId=doc_id).execute()

        # Parse document structure to extract text
        text_content = _extract_text_from_doc(document)
        return text_content

    except HttpError as error:
        print(f"An error occurred: {error}")
        return ""


def _extract_text_from_doc(document: dict) -> str:
    """
    Extract plain text from a Google Docs JSON structure.

    Args:
        document: The document JSON from the Docs API.

    Returns:
        Concatenated text content.
    """
    text_parts = []

    body = document.get('body', {})
    content = body.get('content', [])

    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            elements = paragraph.get('elements', [])

            for elem in elements:
                if 'textRun' in elem:
                    text = elem['textRun'].get('content', '')
                    text_parts.append(text)

        elif 'table' in element:
            # Handle table content
            table = element['table']
            for row in table.get('tableRows', []):
                for cell in row.get('tableCells', []):
                    cell_content = cell.get('content', [])
                    for cell_elem in cell_content:
                        if 'paragraph' in cell_elem:
                            for p_elem in cell_elem['paragraph'].get('elements', []):
                                if 'textRun' in p_elem:
                                    text = p_elem['textRun'].get('content', '')
                                    text_parts.append(text)

    return ''.join(text_parts)


def load_local_file(uploaded_file) -> str:
    """
    Load text content from a Streamlit UploadedFile object.

    Supports .docx (Word) and .pdf files.

    Args:
        uploaded_file: Streamlit UploadedFile object.

    Returns:
        Extracted text content as a string.

    Raises:
        ValueError: If file type is not supported.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith('.docx'):
        return _load_docx(uploaded_file)
    elif filename.endswith('.pdf'):
        return _load_pdf(uploaded_file)
    elif filename.endswith('.txt'):
        return uploaded_file.read().decode('utf-8')
    else:
        raise ValueError(
            f"Unsupported file type: {filename}. "
            "Supported formats: .docx, .pdf, .txt"
        )


def _load_docx(uploaded_file) -> str:
    """
    Extract text from a .docx file.

    Args:
        uploaded_file: File-like object containing .docx data.

    Returns:
        Extracted text content.
    """
    from docx import Document
    from io import BytesIO

    # Reset file pointer if needed
    uploaded_file.seek(0)

    doc = Document(BytesIO(uploaded_file.read()))

    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text)

    return '\n\n'.join(paragraphs)


def _load_pdf(uploaded_file) -> str:
    """
    Extract text from a .pdf file.

    Args:
        uploaded_file: File-like object containing PDF data.

    Returns:
        Extracted text content.
    """
    from pypdf import PdfReader
    from io import BytesIO

    # Reset file pointer if needed
    uploaded_file.seek(0)

    reader = PdfReader(BytesIO(uploaded_file.read()))

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return '\n\n'.join(text_parts)


# Utility functions for Streamlit integration
def get_auth_status() -> dict:
    """
    Check the current authentication status.

    Returns:
        Dictionary with 'authenticated' bool and 'message' string.
    """
    if not CLIENT_SECRET_PATH.exists():
        return {
            'authenticated': False,
            'message': 'OAuth not configured. Please add client_secret.json to config/'
        }

    if not TOKEN_PATH.exists():
        return {
            'authenticated': False,
            'message': 'Not authenticated. Click to sign in with Google.'
        }

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds.valid:
            return {
                'authenticated': True,
                'message': 'Connected to Google Drive'
            }
        elif creds.expired and creds.refresh_token:
            return {
                'authenticated': False,
                'message': 'Token expired. Click to refresh.'
            }
        else:
            return {
                'authenticated': False,
                'message': 'Invalid credentials. Please re-authenticate.'
            }
    except Exception as e:
        return {
            'authenticated': False,
            'message': f'Error checking credentials: {str(e)}'
        }


def get_credentials() -> Optional[Credentials]:
    """
    Get current credentials if valid, otherwise return None.

    Returns:
        Credentials object if authenticated and valid, None otherwise.
    """
    if not TOKEN_PATH.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds.valid:
            return creds
        elif creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed credentials
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
            return creds
    except Exception:
        pass

    return None


def clear_credentials() -> None:
    """Remove stored OAuth token to force re-authentication."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
