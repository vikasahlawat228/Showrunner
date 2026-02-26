import asyncio
import logging
from typing import Dict, Optional
from pathlib import Path

import yaml

from showrunner_tool.schemas.sync import SyncStatus
from showrunner_tool.services.google_drive_adapter import GoogleDriveAdapter

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0


class CloudSyncService:
    """Manages upload queues, tracking, and orchestrates syncs to Google Drive.

    Data-safety guarantees (Phase L):
      - Exponential backoff retry (up to MAX_RETRIES)
      - Dead-letter queue via sync_failures table for poison-pill items
      - Delete propagation to Drive Trash
      - Full UoW-routed revert for Time Machine
    """

    def __init__(self, drive_adapter: GoogleDriveAdapter, sqlite_indexer):
        self.adapter = drive_adapter
        self._indexer = sqlite_indexer  # To update local db with drive_file_ids
        self._queue: asyncio.Queue = asyncio.Queue()
        # Initial state should be OFFLINE if no token exists yet
        self.status = SyncStatus.IDLE if self.adapter.service else SyncStatus.OFFLINE
        self._task: Optional[asyncio.Task] = None
        # Load existing mapping from SQLite
        self._drive_id_map: Dict[str, str] = self._load_mappings()

    def _load_mappings(self) -> Dict[str, str]:
        """Loads yaml_path -> drive_file_id from the indexer."""
        try:
            metadata = self._indexer.get_sync_metadata()
            return {m['yaml_path']: m['drive_file_id'] for m in metadata if m.get('drive_file_id')}
        except Exception as e:
            logger.error(f"Failed to load sync mappings: {e}")
            return {}

    def start_worker(self):
        """Start the background queue processor."""
        if not self._task:
            self._task = asyncio.create_task(self.process_queue())
            logger.info("CloudSyncService background worker started.")

    def stop_worker(self):
        """Stop the background queue processor."""
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("CloudSyncService background worker stopped.")

    def disconnect(self):
        """Fully disconnect from Google Drive: revoke tokens, stop worker, drain queue."""
        self.stop_worker()
        self.adapter.disconnect()
        # Drain any pending items from the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        self.status = SyncStatus.OFFLINE
        logger.info("Google Drive disconnected and sync queue drained.")

    async def enqueue_upload(self, yaml_path: str, content: str):
        """Called by UnitOfWork after a local save to queue file for sync."""
        await self._queue.put({"operation": "upload", "yaml_path": yaml_path, "content": content})
        logger.debug("Enqueued upload for %s", yaml_path)

    async def enqueue_delete(self, yaml_path: str):
        """Called by UnitOfWork after a local delete to trash the Drive file."""
        await self._queue.put({"operation": "delete", "yaml_path": yaml_path})
        logger.debug("Enqueued delete for %s", yaml_path)

    async def process_queue(self):
        """Background worker loop with exponential backoff retry."""
        while True:
            try:
                item = await self._queue.get()
                operation = item.get("operation", "upload")
                yaml_path = item["yaml_path"]

                self.status = SyncStatus.SYNCING

                success = False
                last_error = ""

                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        if operation == "upload":
                            await self._process_upload(item)
                        elif operation == "delete":
                            await self._process_delete(item)
                        success = True
                        break
                    except Exception as e:
                        last_error = str(e)
                        if attempt < MAX_RETRIES:
                            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                            logger.warning(
                                "Sync %s for %s failed (attempt %d/%d), retrying in %.1fs: %s",
                                operation, yaml_path, attempt, MAX_RETRIES, wait, e,
                            )
                            await asyncio.sleep(wait)
                        else:
                            logger.error(
                                "Sync %s for %s failed after %d attempts: %s",
                                operation, yaml_path, MAX_RETRIES, e,
                            )

                if not success:
                    # Dead-letter: record failure in SQLite
                    try:
                        self._indexer.record_sync_failure(
                            yaml_path=yaml_path,
                            operation=operation,
                            error_message=last_error,
                            attempt_count=MAX_RETRIES,
                        )
                    except Exception as dle:
                        logger.error("Failed to record sync failure: %s", dle)
                    self.status = SyncStatus.ERROR
                else:
                    if self._queue.empty():
                        self.status = SyncStatus.IDLE

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Unexpected error in sync worker: %s", e)
                self.status = SyncStatus.ERROR

    async def _process_upload(self, item: dict):
        """Upload a single file to Drive."""
        yaml_path = item["yaml_path"]
        content = item["content"]

        drive_file_id = self._drive_id_map.get(yaml_path)
        filename = Path(yaml_path).name

        new_drive_id = await self.adapter.upload_file(content, filename, drive_file_id)

        if drive_file_id != new_drive_id:
            self._drive_id_map[yaml_path] = new_drive_id
            try:
                self._indexer.update_sync_drive_id(yaml_path, new_drive_id)
            except Exception as e:
                logger.error(f"Failed to persist drive ID: {e}")

    async def _process_delete(self, item: dict):
        """Trash a file on Drive."""
        yaml_path = item["yaml_path"]
        drive_file_id = self._drive_id_map.get(yaml_path)
        if drive_file_id:
            await self.adapter.trash_file(drive_file_id)
            logger.info("Trashed Drive file for %s (ID: %s)", yaml_path, drive_file_id)

    async def revert_file(self, yaml_path: str, revision_id: str, uow_factory):
        """Downloads revision from Google Drive, saves locally via UnitOfWork.

        The revert is routed through UoW to ensure that the event log,
        SQLite indexes, and Cloud Sync mappings all stay consistent.
        """
        drive_file_id = self._drive_id_map.get(yaml_path)
        if not drive_file_id:
            raise ValueError(f"No Drive file tracked for {yaml_path}")

        # Download content from Drive
        content = await self.adapter.download_revision(drive_file_id, revision_id)
        if not content:
            raise ValueError(f"Empty content returned for revision {revision_id}")

        # Parse the YAML content
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise ValueError(f"Invalid YAML content for revision {revision_id}")

        # Route through UnitOfWork for full persistence
        if uow_factory:
            uow = uow_factory()
            # Extract entity metadata from the parsed YAML or the indexer
            entity_info = self._indexer.query_entities(
                filters={"yaml_path": yaml_path}
            )
            if entity_info:
                info = entity_info[0]
                uow.save(
                    entity_id=info["id"],
                    entity_type=info["entity_type"],
                    name=info.get("name", ""),
                    yaml_path=yaml_path,
                    data=parsed,
                    event_type="UPDATE",
                    event_payload={"revert_to_revision": revision_id, "data": parsed},
                )
                uow.commit()
                logger.info("Reverted %s to revision %s via UoW", yaml_path, revision_id)
            else:
                logger.warning("No entity found for %s, writing raw content", yaml_path)
                Path(yaml_path).write_text(content, encoding="utf-8")
        else:
            logger.warning("No uow_factory provided, writing raw content for %s", yaml_path)
            Path(yaml_path).write_text(content, encoding="utf-8")

        return content
