"""
Drive Sync Service for PHDx

Provides robust Google Drive synchronization with:
- OAuth2 authentication flow
- Recursive folder listing
- Document export (Google Docs → text)
- Change detection (only sync modified files)
- Background sync support
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.secrets_utils import (
    get_secret,
    store_oauth_tokens,
    get_oauth_tokens,
    delete_oauth_tokens,
    update_oauth_tokens,
    store_sync_state,
    get_sync_state,
)

# Set up logging
logger = logging.getLogger(__name__)

# Configuration
CONFIG_DIR = Path(__file__).parent.parent / 'config'
CLIENT_SECRETS_PATH = CONFIG_DIR / 'client_secret.json'

# OAuth2 Scopes - read-only access to Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
]

# Google Docs MIME type
GOOGLE_DOC_MIME_TYPE = 'application/vnd.google-apps.document'
GOOGLE_FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'


class ExportFormat(str, Enum):
    """Supported export formats for Google Docs."""
    PLAIN_TEXT = 'text/plain'
    HTML = 'text/html'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    PDF = 'application/pdf'


@dataclass
class DriveFile:
    """Represents a file in Google Drive."""
    id: str
    name: str
    mime_type: str
    modified_time: str
    parent_id: Optional[str] = None
    web_view_link: Optional[str] = None
    size: Optional[int] = None

    @property
    def is_google_doc(self) -> bool:
        return self.mime_type == GOOGLE_DOC_MIME_TYPE

    @property
    def is_folder(self) -> bool:
        return self.mime_type == GOOGLE_FOLDER_MIME_TYPE


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    files_found: int = 0
    files_changed: int = 0
    files_synced: int = 0
    errors: list[str] = field(default_factory=list)
    changed_files: list[DriveFile] = field(default_factory=list)
    synced_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DriveSyncService:
    """
    Service for synchronizing Google Drive folders with PHDx.

    Handles:
    - OAuth2 authentication
    - Recursive folder listing
    - Document export
    - Change detection
    """

    def __init__(self, user_id: str):
        """
        Initialize the sync service for a user.

        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self._credentials: Optional[Credentials] = None
        self._drive_service = None
        self._people_service = None

    # =========================================================================
    # OAuth2 Authentication
    # =========================================================================

    def get_auth_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Get the OAuth2 authorization URL.

        Args:
            redirect_uri: Callback URL after authorization
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        if not CLIENT_SECRETS_PATH.exists():
            raise FileNotFoundError(
                f"Client secrets not found at {CLIENT_SECRETS_PATH}. "
                "Download OAuth credentials from Google Cloud Console."
            )

        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH),
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state,
        )

        return auth_url

    def handle_auth_callback(self, code: str, redirect_uri: str) -> dict:
        """
        Handle the OAuth2 callback and store tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in auth request

        Returns:
            User info dictionary
        """
        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRETS_PATH),
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store tokens securely
        token_data = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes) if credentials.scopes else SCOPES,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
        }

        store_oauth_tokens(self.user_id, token_data)
        self._credentials = credentials

        # Get user info
        return self._get_user_info()

    def _get_user_info(self) -> dict:
        """Get user profile information."""
        if not self._people_service:
            self._people_service = build('people', 'v1', credentials=self._credentials)

        try:
            profile = self._people_service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,photos'
            ).execute()

            names = profile.get('names', [{}])
            emails = profile.get('emailAddresses', [{}])
            photos = profile.get('photos', [{}])

            return {
                'name': names[0].get('displayName', 'Unknown') if names else 'Unknown',
                'email': emails[0].get('value', '') if emails else '',
                'photo_url': photos[0].get('url', '') if photos else '',
            }
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")
            return {'name': 'Unknown', 'email': '', 'photo_url': ''}

    def is_authenticated(self) -> bool:
        """Check if the user has valid stored credentials."""
        return self._load_credentials() is not None

    def _load_credentials(self) -> Optional[Credentials]:
        """Load and refresh credentials from storage."""
        if self._credentials and self._credentials.valid:
            return self._credentials

        token_data = get_oauth_tokens(self.user_id)
        if not token_data:
            return None

        try:
            credentials = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes', SCOPES),
            )

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

                # Update stored tokens
                update_oauth_tokens(self.user_id, {
                    'access_token': credentials.token,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                })

            if credentials.valid:
                self._credentials = credentials
                return credentials

        except Exception as e:
            logger.error(f"Failed to load/refresh credentials: {e}")

        return None

    def logout(self) -> bool:
        """
        Log out the user by deleting stored tokens.

        Returns:
            True if tokens were deleted
        """
        self._credentials = None
        self._drive_service = None
        return delete_oauth_tokens(self.user_id)

    def _get_drive_service(self):
        """Get or create the Drive API service."""
        if self._drive_service:
            return self._drive_service

        credentials = self._load_credentials()
        if not credentials:
            raise RuntimeError("Not authenticated. Call get_auth_url() first.")

        self._drive_service = build('drive', 'v3', credentials=credentials)
        return self._drive_service

    # =========================================================================
    # Folder Sync
    # =========================================================================

    def sync_folder(
        self,
        folder_id: str,
        recursive: bool = True,
        force: bool = False,
    ) -> SyncResult:
        """
        Sync a Google Drive folder, detecting changed files.

        Args:
            folder_id: Google Drive folder ID (or 'root' for root folder)
            recursive: Whether to sync subfolders
            force: Force sync even if files haven't changed

        Returns:
            SyncResult with details of the operation
        """
        result = SyncResult(success=False)

        try:
            # Get all files in folder
            all_files = self._list_folder_recursive(folder_id) if recursive else self._list_folder(folder_id)

            # Filter to Google Docs only
            docs = [f for f in all_files if f.is_google_doc]
            result.files_found = len(docs)

            # Load previous sync state
            prev_state = get_sync_state(self.user_id, folder_id)
            prev_files = prev_state.get('files', {}) if prev_state else {}

            # Detect changes
            current_state = {}
            changed_files = []

            for doc in docs:
                current_state[doc.id] = {
                    'name': doc.name,
                    'modified_time': doc.modified_time,
                }

                # Check if file is new or modified
                prev_info = prev_files.get(doc.id)
                if force or not prev_info or prev_info.get('modified_time') != doc.modified_time:
                    changed_files.append(doc)

            result.files_changed = len(changed_files)
            result.changed_files = changed_files

            # Save new state
            store_sync_state(self.user_id, folder_id, current_state)

            result.files_synced = len(changed_files)
            result.success = True

        except HttpError as e:
            result.errors.append(f"Google API error: {e}")
            logger.error(f"Sync folder error: {e}")
        except Exception as e:
            result.errors.append(f"Sync error: {str(e)}")
            logger.error(f"Sync folder error: {e}")

        return result

    def _list_folder(self, folder_id: str) -> list[DriveFile]:
        """List files in a specific folder."""
        service = self._get_drive_service()

        query = f"'{folder_id}' in parents and trashed = false"

        files = []
        page_token = None

        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, modifiedTime, parents, webViewLink, size)',
                pageToken=page_token,
                pageSize=100,
            ).execute()

            for item in response.get('files', []):
                files.append(DriveFile(
                    id=item['id'],
                    name=item['name'],
                    mime_type=item['mimeType'],
                    modified_time=item.get('modifiedTime', ''),
                    parent_id=item.get('parents', [None])[0],
                    web_view_link=item.get('webViewLink'),
                    size=item.get('size'),
                ))

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return files

    def _list_folder_recursive(
        self,
        folder_id: str,
        _visited: Optional[set] = None,
    ) -> list[DriveFile]:
        """Recursively list all files in a folder and subfolders."""
        if _visited is None:
            _visited = set()

        if folder_id in _visited:
            return []

        _visited.add(folder_id)

        all_files = []
        items = self._list_folder(folder_id)

        for item in items:
            if item.is_folder:
                # Recurse into subfolders
                all_files.extend(self._list_folder_recursive(item.id, _visited))
            else:
                all_files.append(item)

        return all_files

    # =========================================================================
    # Document Export
    # =========================================================================

    def export_doc(
        self,
        file_id: str,
        format: ExportFormat = ExportFormat.PLAIN_TEXT,
    ) -> str:
        """
        Export a Google Doc to the specified format.

        Args:
            file_id: Google Drive file ID
            format: Export format (default: plain text)

        Returns:
            Document content as string
        """
        service = self._get_drive_service()

        try:
            # Use export for Google Docs
            response = service.files().export(
                fileId=file_id,
                mimeType=format.value,
            ).execute()

            if isinstance(response, bytes):
                return response.decode('utf-8')
            return response

        except HttpError as e:
            if e.resp.status == 404:
                raise FileNotFoundError(f"Document {file_id} not found")
            raise

    def export_doc_as_html(self, file_id: str) -> str:
        """Export a Google Doc as HTML."""
        return self.export_doc(file_id, ExportFormat.HTML)

    def export_doc_as_text(self, file_id: str) -> str:
        """Export a Google Doc as plain text."""
        return self.export_doc(file_id, ExportFormat.PLAIN_TEXT)

    def get_file_metadata(self, file_id: str) -> Optional[DriveFile]:
        """Get metadata for a specific file."""
        service = self._get_drive_service()

        try:
            item = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, modifiedTime, parents, webViewLink, size',
            ).execute()

            return DriveFile(
                id=item['id'],
                name=item['name'],
                mime_type=item['mimeType'],
                modified_time=item.get('modifiedTime', ''),
                parent_id=item.get('parents', [None])[0],
                web_view_link=item.get('webViewLink'),
                size=item.get('size'),
            )
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def list_folders(self, parent_id: str = 'root') -> list[DriveFile]:
        """List folders in a specific parent folder."""
        service = self._get_drive_service()

        query = f"'{parent_id}' in parents and mimeType = '{GOOGLE_FOLDER_MIME_TYPE}' and trashed = false"

        folders = []
        page_token = None

        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
                pageToken=page_token,
                pageSize=100,
            ).execute()

            for item in response.get('files', []):
                folders.append(DriveFile(
                    id=item['id'],
                    name=item['name'],
                    mime_type=item['mimeType'],
                    modified_time=item.get('modifiedTime', ''),
                ))

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return folders

    def search_docs(self, query: str, folder_id: Optional[str] = None) -> list[DriveFile]:
        """
        Search for Google Docs by name.

        Args:
            query: Search query (partial name match)
            folder_id: Optional folder to search within

        Returns:
            List of matching files
        """
        service = self._get_drive_service()

        search_query = f"name contains '{query}' and mimeType = '{GOOGLE_DOC_MIME_TYPE}' and trashed = false"
        if folder_id:
            search_query += f" and '{folder_id}' in parents"

        docs = []
        page_token = None

        while True:
            response = service.files().list(
                q=search_query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink)',
                pageToken=page_token,
                pageSize=50,
            ).execute()

            for item in response.get('files', []):
                docs.append(DriveFile(
                    id=item['id'],
                    name=item['name'],
                    mime_type=item['mimeType'],
                    modified_time=item.get('modifiedTime', ''),
                    web_view_link=item.get('webViewLink'),
                ))

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return docs


# =============================================================================
# Background Sync Manager
# =============================================================================

class SyncManager:
    """
    Manages background sync for multiple users.

    Tracks active users and their sync configurations.
    """

    def __init__(self):
        self._active_syncs: dict[str, dict] = {}
        self._last_sync: dict[str, datetime] = {}

    def register_sync(
        self,
        user_id: str,
        folder_id: str,
        interval_minutes: int = 10,
    ) -> None:
        """
        Register a folder for background sync.

        Args:
            user_id: User identifier
            folder_id: Folder to sync
            interval_minutes: Sync interval
        """
        key = f"{user_id}:{folder_id}"
        self._active_syncs[key] = {
            'user_id': user_id,
            'folder_id': folder_id,
            'interval_minutes': interval_minutes,
            'registered_at': datetime.now().isoformat(),
        }

    def unregister_sync(self, user_id: str, folder_id: str) -> bool:
        """Unregister a folder from background sync."""
        key = f"{user_id}:{folder_id}"
        if key in self._active_syncs:
            del self._active_syncs[key]
            return True
        return False

    def get_pending_syncs(self) -> list[dict]:
        """Get list of syncs that are due to run."""
        now = datetime.now()
        pending = []

        for key, config in self._active_syncs.items():
            last_sync = self._last_sync.get(key)
            interval = config['interval_minutes']

            if last_sync is None:
                pending.append(config)
            else:
                elapsed = (now - last_sync).total_seconds() / 60
                if elapsed >= interval:
                    pending.append(config)

        return pending

    def mark_synced(self, user_id: str, folder_id: str) -> None:
        """Mark a sync as completed."""
        key = f"{user_id}:{folder_id}"
        self._last_sync[key] = datetime.now()

    def run_pending_syncs(self) -> list[SyncResult]:
        """
        Run all pending syncs.

        Returns:
            List of sync results
        """
        results = []

        for config in self.get_pending_syncs():
            user_id = config['user_id']
            folder_id = config['folder_id']

            try:
                service = DriveSyncService(user_id)
                if service.is_authenticated():
                    result = service.sync_folder(folder_id)
                    results.append(result)

                    if result.success:
                        self.mark_synced(user_id, folder_id)
                        logger.info(
                            f"Synced {folder_id} for user {user_id}: "
                            f"{result.files_changed} changed files"
                        )
                else:
                    logger.warning(f"User {user_id} not authenticated, skipping sync")

            except Exception as e:
                logger.error(f"Sync failed for {user_id}/{folder_id}: {e}")
                results.append(SyncResult(
                    success=False,
                    errors=[str(e)],
                ))

        return results

    def list_active_syncs(self) -> list[dict]:
        """List all active sync configurations."""
        return list(self._active_syncs.values())


# Global sync manager instance
_sync_manager: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    """Get or create the global sync manager."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
