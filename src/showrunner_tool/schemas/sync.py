from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SyncStatus(str, Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    OFFLINE = "offline"


class DriveConfig(BaseModel):
    """Google Drive Sync Configuration."""
    enabled: bool = False
    folder_id: Optional[str] = None           # Root folder ID in Google Drive
    last_sync: Optional[str] = None           # ISO Timestamp


class RevisionHistory(BaseModel):
    """A Google Drive File Revision."""
    revision_id: str
    modified_time: str
    size: int
    user_name: str
    keep_forever: bool = False


class SyncFailure(BaseModel):
    """Dead-letter record for a sync operation that exhausted all retries."""
    yaml_path: str
    operation: str  # "upload" or "delete"
    error_message: str
    attempt_count: int = 0
    first_failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
