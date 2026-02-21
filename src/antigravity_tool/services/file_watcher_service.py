"""Real-time file system watcher for Showrunner.

Monitors the project directory for YAML file changes and keeps the
Knowledge Graph / SQLite index in sync. Emits SSE events so the
frontend can refresh automatically.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Debounced event handler
# ---------------------------------------------------------------------------

class _DebouncedYAMLHandler(FileSystemEventHandler):
    """Watchdog handler that coalesces rapid file-system events.

    A per-path timer (default 0.5 s) ensures we only process once even when
    editors trigger multiple quick saves.
    """

    def __init__(
        self,
        callback: Callable[[str, Path], None],
        debounce_seconds: float = 0.5,
    ) -> None:
        super().__init__()
        self._callback = callback
        self._debounce = debounce_seconds
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    # -- internal helpers ---------------------------------------------------

    def _schedule(self, event_type: str, path: Path) -> None:
        key = str(path)
        with self._lock:
            existing = self._timers.pop(key, None)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(
                self._debounce,
                self._fire,
                args=(event_type, path),
            )
            timer.daemon = True
            self._timers[key] = timer
            timer.start()

    def _fire(self, event_type: str, path: Path) -> None:
        with self._lock:
            self._timers.pop(str(path), None)
        try:
            self._callback(event_type, path)
        except Exception:
            logger.exception("File watcher callback error for %s", path)

    # -- watchdog overrides -------------------------------------------------

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix in (".yaml", ".yml") and not path.name.startswith("_"):
            self._schedule("created", path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix in (".yaml", ".yml") and not path.name.startswith("_"):
            self._schedule("modified", path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix in (".yaml", ".yml") and not path.name.startswith("_"):
            self._schedule("deleted", path)

    def cancel_all(self) -> None:
        """Cancel any pending timers on shutdown."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------

class FileWatcherService:
    """Watches the project tree for YAML changes and syncs the Knowledge Graph.

    Usage::

        watcher = FileWatcherService(project_path, kg_service, container_repo, broadcast_fn)
        watcher.start()   # non-blocking — runs in a background thread
        ...
        watcher.stop()     # clean shutdown
    """

    def __init__(
        self,
        project_path: Path,
        knowledge_graph_service: Any,
        container_repo: Any,
        broadcast_fn: Optional[Callable[[dict], None]] = None,
        debounce_seconds: float = 0.5,
    ) -> None:
        self._project_path = project_path
        self._kg_service = knowledge_graph_service
        self._container_repo = container_repo
        self._broadcast_fn = broadcast_fn
        self._observer = Observer()
        self._handler = _DebouncedYAMLHandler(
            callback=self._handle_change,
            debounce_seconds=debounce_seconds,
        )

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Start watching the project directory (recursive)."""
        self._observer.schedule(
            self._handler,
            str(self._project_path),
            recursive=True,
        )
        self._observer.daemon = True
        self._observer.start()
        logger.info("FileWatcher started on %s", self._project_path)

    def stop(self) -> None:
        """Stop the observer and cancel pending debounce timers."""
        self._handler.cancel_all()
        self._observer.stop()
        self._observer.join(timeout=5)
        logger.info("FileWatcher stopped")

    # -- change handler -----------------------------------------------------

    def _handle_change(self, event_type: str, path: Path) -> None:
        """Called (after debounce) when a YAML file is created / modified / deleted."""
        logger.info("File %s: %s", event_type, path)

        # Skip files in directories we don't care about (e.g. prompts, .git)
        rel = str(path.relative_to(self._project_path))
        if any(part.startswith(".") for part in Path(rel).parts):
            return
        if "prompts" in rel:
            return

        try:
            if event_type == "deleted":
                self._kg_service._on_container_delete(path, path.stem)
            else:
                # created or modified → reload and upsert
                container = self._container_repo._load_file(path)
                self._kg_service._on_container_save(path, container)
        except Exception:
            logger.warning("Could not sync %s — skipping", path, exc_info=True)
            # File may not be a valid container; that's fine.

        # Broadcast SSE event
        if self._broadcast_fn is not None:
            self._broadcast_fn({
                "type": "GRAPH_UPDATED",
                "event": event_type,
                "path": rel,
            })
