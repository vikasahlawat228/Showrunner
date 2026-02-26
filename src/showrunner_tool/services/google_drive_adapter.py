import hashlib
import logging
import os
import json
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

from showrunner_tool.schemas.sync import RevisionHistory

logger = logging.getLogger(__name__)

# Scopes required for the app. Using drive.file for safety.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveAdapter:
    """Wrapper around Google Drive API v3.

    Data-safety guarantees (Phase L):
      - trash_file() for soft-delete (30-day recovery via Drive Trash)
      - keepRevisionForever support for milestone pinning
      - md5Checksum verification after upload
    """

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initialize the Drive service if tokens exist."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing Google Drive token: {e}")
                creds = None

        if creds and creds.valid:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive service initialized successfully.")

    async def exchange_auth_code(self, auth_code: str, redirect_uri: str) -> bool:
        """Exchanges an auth code for a refresh token and saves it."""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_path, 
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully exchanged auth code and saved token.json")
            return True
        except Exception as e:
            logger.error(f"Failed to exchange auth code: {e}")
            return False

    def disconnect(self):
        """Revokes stored credentials and tears down the Drive service."""
        self.service = None
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            logger.info("Removed token.json — Google Drive disconnected.")

    def _ensure_valid_creds(self) -> bool:
        """Refreshes credentials if they are expired. Returns True if service is usable."""
        if not self.service:
            return False
        if not os.path.exists(self.token_path):
            self.service = None
            return False
        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.service = build('drive', 'v3', credentials=creds)
                logger.info("Refreshed expired Google Drive token.")
            return creds is not None and creds.valid
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            self.service = None
            return False

    async def upload_file(
        self,
        content: str,
        filename: str,
        drive_file_id: Optional[str] = None,
        keep_forever: bool = False,
    ) -> str:
        """Creates or updates a file on Drive with optional revision pinning.

        Args:
            content: File content as string.
            filename: Name for the file on Drive.
            drive_file_id: Existing Drive ID to update, or None to create.
            keep_forever: If True, pin this revision so Drive won't auto-purge it.

        Returns:
            The drive_file_id (existing or newly created).
        """
        if not self._ensure_valid_creds():
            logger.warning("Drive service not initialized. Skipping upload.")
            return drive_file_id

        content_bytes = content.encode('utf-8')
        local_md5 = hashlib.md5(content_bytes).hexdigest()

        try:
            file_metadata = {'name': filename}
            media = MediaIoBaseUpload(io.BytesIO(content_bytes), mimetype='application/x-yaml')

            if drive_file_id:
                # Update existing file
                file = self.service.files().update(
                    fileId=drive_file_id,
                    media_body=media,
                    fields='id,md5Checksum',
                    keepRevisionForever=keep_forever,
                ).execute()
                logger.info(f"Updated file {filename} (ID: {drive_file_id})")
            else:
                # Create new file
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,md5Checksum',
                    keepRevisionForever=keep_forever,
                ).execute()
                drive_file_id = file.get('id')
                logger.info(f"Created new file {filename} (ID: {drive_file_id})")

            # Checksum verification
            remote_md5 = file.get('md5Checksum', '')
            if remote_md5 and remote_md5 != local_md5:
                logger.error(
                    "Checksum mismatch for %s: local=%s, remote=%s",
                    filename, local_md5, remote_md5,
                )
                raise IOError(f"Checksum mismatch after upload for {filename}")

            return drive_file_id
        except Exception as e:
            logger.error(f"Drive upload failed for {filename}: {e}")
            raise

    async def trash_file(self, drive_file_id: str) -> None:
        """Move a file to Google Drive Trash (30-day recovery window)."""
        if not self._ensure_valid_creds():
            logger.warning("Drive service not initialized. Skipping trash.")
            return

        try:
            self.service.files().update(
                fileId=drive_file_id,
                body={"trashed": True},
            ).execute()
            logger.info(f"Trashed Drive file (ID: {drive_file_id})")
        except Exception as e:
            logger.error(f"Failed to trash Drive file {drive_file_id}: {e}")
            raise

    async def list_revisions(self, drive_file_id: str) -> List[RevisionHistory]:
        """Lists revisions for a Drive file."""
        if not self.service:
            return []

        try:
            results = self.service.revisions().list(
                fileId=drive_file_id,
                fields="revisions(id, modifiedTime, size, keepForever)",
            ).execute()
            revisions = []
            for rev in results.get('revisions', []):
                revisions.append(RevisionHistory(
                    revision_id=rev['id'],
                    modified_time=rev['modifiedTime'],
                    size=int(rev.get('size', 0)),
                    user_name="Cloud User",
                    keep_forever=rev.get('keepForever', False),
                ))
            return revisions
        except Exception as e:
            logger.error(f"Failed to list revisions for {drive_file_id}: {e}")
            return []

    async def download_revision(self, drive_file_id: str, revision_id: str) -> str:
        """Downloads specific revision content."""
        if not self.service:
            return ""

        try:
            content = self.service.revisions().get_media(fileId=drive_file_id, revisionId=revision_id).execute()
            return content.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to download revision {revision_id} for {drive_file_id}: {e}")
            return ""
