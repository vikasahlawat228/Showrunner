"""LRU cache with file-modification-time invalidation for YAML entities."""

from __future__ import annotations

import os
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, Optional, TypeVar

from antigravity_tool.schemas.dal import CacheStats

T = TypeVar("T")


class MtimeCache(Generic[T]):
    """LRU cache that invalidates entries when the underlying file changes.

    Key design:
    - get() does os.stat() to compare mtime -- returns cached if unchanged
    - put() stores entity with current file mtime
    - invalidate() removes a single entry
    - Thread-safe via threading.Lock
    - Bounded size with LRU eviction
    """

    def __init__(self, max_size: int = 500):
        self._max_size = max_size
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, path: Path) -> Optional[T]:
        """Return cached entity if file hasn't changed, else None.

        Checks os.stat(path).st_mtime against stored mtime.
        Returns None on cache miss or mtime mismatch (caller should re-read
        from disk).
        """
        key = str(path)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None

            # Check if file still exists and mtime matches
            try:
                current_mtime = os.stat(path).st_mtime
            except OSError:
                # File was deleted -- invalidate
                self._cache.pop(key, None)
                self._misses += 1
                return None

            if current_mtime != entry.mtime:
                # File changed -- invalidate
                self._cache.pop(key, None)
                self._misses += 1
                return None

            # Cache hit -- move to end (most recently used)
            self._cache.move_to_end(key)
            entry.accessed_at = datetime.now(timezone.utc)
            self._hits += 1
            return entry.entity

    def put(self, path: Path, entity: T) -> None:
        """Store an entity in the cache with the current file mtime."""
        key = str(path)
        try:
            current_mtime = os.stat(path).st_mtime
        except OSError:
            return  # Don't cache if file doesn't exist

        with self._lock:
            # Remove existing entry if present
            self._cache.pop(key, None)

            # Evict LRU if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

            self._cache[key] = _CacheEntry(
                entity=entity,
                mtime=current_mtime,
                accessed_at=datetime.now(timezone.utc),
            )

    def invalidate(self, path: Path) -> None:
        """Remove a single entry from the cache."""
        key = str(path)
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> CacheStats:
        """Return current cache performance metrics."""
        with self._lock:
            total = self._hits + self._misses
            return CacheStats(
                size=len(self._cache),
                max_size=self._max_size,
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                hit_rate=self._hits / total if total > 0 else 0.0,
            )

    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        with self._lock:
            return len(self._cache)


class _CacheEntry:
    """Internal cache entry. NOT a Pydantic model for performance."""

    __slots__ = ("entity", "mtime", "accessed_at")

    def __init__(self, entity: Any, mtime: float, accessed_at: datetime):
        self.entity = entity
        self.mtime = mtime
        self.accessed_at = accessed_at
