"""Phase K: MtimeCache tests.

Tests cover:
  - Cache miss on empty cache
  - Put then get (cache hit)
  - Mtime invalidation (file modified)
  - File deletion invalidation
  - Explicit invalidate / invalidate_all
  - LRU eviction
  - Stats tracking
  - Thread safety
"""

import os
import threading
import time
from pathlib import Path

import pytest

from showrunner_tool.repositories.mtime_cache import MtimeCache


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _write_yaml(path: Path, content: str = "name: test\n") -> None:
    """Write a minimal YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ═══════════════════════════════════════════════════════════════════
# Basic Operations
# ═══════════════════════════════════════════════════════════════════


class TestBasicOperations:
    def test_cache_miss_on_empty(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "missing.yaml"
        _write_yaml(path)
        assert cache.get(path) is None
        assert cache.stats().misses == 1

    def test_put_and_get(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "char.yaml"
        _write_yaml(path, "name: Zara\n")
        entity = {"name": "Zara", "role": "protagonist"}

        cache.put(path, entity)
        result = cache.get(path)
        assert result == entity
        assert cache.stats().hits == 1
        assert cache.stats().misses == 0

    def test_put_nonexistent_file_is_ignored(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "ghost.yaml"  # Does not exist
        cache.put(path, {"name": "ghost"})
        assert cache.size == 0


# ═══════════════════════════════════════════════════════════════════
# Invalidation
# ═══════════════════════════════════════════════════════════════════


class TestInvalidation:
    def test_mtime_invalidation(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "entity.yaml"
        _write_yaml(path, "v1")
        cache.put(path, "version_1")

        # Ensure mtime changes (some filesystems have 1s granularity)
        time.sleep(0.05)
        _write_yaml(path, "v2")

        result = cache.get(path)
        assert result is None  # mtime changed
        assert cache.stats().misses == 1

    def test_file_deletion_invalidation(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "temp.yaml"
        _write_yaml(path, "temp")
        cache.put(path, "temp_entity")

        os.unlink(path)
        result = cache.get(path)
        assert result is None
        assert cache.size == 0

    def test_explicit_invalidate(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "char.yaml"
        _write_yaml(path, "test")
        cache.put(path, "entity")
        assert cache.size == 1

        cache.invalidate(path)
        assert cache.size == 0
        assert cache.get(path) is None

    def test_invalidate_nonexistent_key(self, tmp_path):
        cache = MtimeCache(max_size=10)
        path = tmp_path / "nope.yaml"
        cache.invalidate(path)  # should not raise

    def test_invalidate_all(self, tmp_path):
        cache = MtimeCache(max_size=10)
        for i in range(5):
            path = tmp_path / f"entity_{i}.yaml"
            _write_yaml(path, f"entity {i}")
            cache.put(path, f"entity_{i}")

        assert cache.size == 5
        cache.invalidate_all()
        assert cache.size == 0


# ═══════════════════════════════════════════════════════════════════
# LRU Eviction
# ═══════════════════════════════════════════════════════════════════


class TestLRUEviction:
    def test_evicts_lru_at_capacity(self, tmp_path):
        cache = MtimeCache(max_size=3)

        paths = []
        for i in range(4):
            p = tmp_path / f"e{i}.yaml"
            _write_yaml(p, f"entity {i}")
            paths.append(p)
            cache.put(p, f"entity_{i}")

        # Cache holds max 3 — oldest (e0) should be evicted
        assert cache.size == 3
        assert cache.get(paths[0]) is None  # evicted
        assert cache.get(paths[3]) == "entity_3"  # still there
        assert cache.stats().evictions >= 1

    def test_access_refreshes_lru_order(self, tmp_path):
        cache = MtimeCache(max_size=3)

        paths = []
        for i in range(3):
            p = tmp_path / f"e{i}.yaml"
            _write_yaml(p, f"entity {i}")
            paths.append(p)
            cache.put(p, f"entity_{i}")

        # Access e0, making it the most recently used
        cache.get(paths[0])

        # Add e3 — should evict e1 (now the LRU), not e0
        p3 = tmp_path / "e3.yaml"
        _write_yaml(p3, "entity 3")
        cache.put(p3, "entity_3")

        assert cache.get(paths[0]) == "entity_0"  # refreshed, not evicted
        assert cache.get(paths[1]) is None  # evicted (was LRU)


# ═══════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════


class TestStats:
    def test_stats_tracking(self, tmp_path):
        cache = MtimeCache(max_size=2)
        p1 = tmp_path / "a.yaml"
        p2 = tmp_path / "b.yaml"
        _write_yaml(p1)
        _write_yaml(p2)

        cache.get(p1)  # miss
        cache.put(p1, "a")
        cache.get(p1)  # hit
        cache.get(p2)  # miss
        cache.put(p2, "b")

        stats = cache.stats()
        assert stats.hits == 1
        assert stats.misses == 2
        assert stats.size == 2
        assert stats.max_size == 2
        assert stats.hit_rate == pytest.approx(1 / 3)

    def test_eviction_count(self, tmp_path):
        cache = MtimeCache(max_size=1)
        for i in range(5):
            p = tmp_path / f"e{i}.yaml"
            _write_yaml(p)
            cache.put(p, f"entity_{i}")

        assert cache.stats().evictions == 4  # first doesn't evict, 4 more do


# ═══════════════════════════════════════════════════════════════════
# Thread Safety
# ═══════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_put_get(self, tmp_path):
        cache = MtimeCache(max_size=100)
        errors = []

        def worker(worker_id):
            try:
                for i in range(20):
                    p = tmp_path / f"w{worker_id}_e{i}.yaml"
                    _write_yaml(p, f"worker {worker_id} entity {i}")
                    cache.put(p, f"w{worker_id}_e{i}")
                    cache.get(p)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(w,)) for w in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread safety errors: {errors}"
        stats = cache.stats()
        assert stats.hits + stats.misses > 0
