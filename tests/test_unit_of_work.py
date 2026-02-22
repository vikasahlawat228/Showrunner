"""Phase K Session 4: UnitOfWork tests.

Tests cover:
  - Single save + commit (YAML file + SQLite entity)
  - Multi-save atomicity (3 saves, all succeed)
  - Delete + commit (file removed, entity removed)
  - Rollback on error (no temp files, no entities)
  - Context manager auto-commit on clean exit
  - Context manager auto-rollback on exception
  - EventService.append_event called for each operation
  - MtimeCache.invalidate called for each affected path
  - Empty commit returns 0
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.repositories.mtime_cache import MtimeCache
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.services.unit_of_work import UnitOfWork


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def indexer():
    """In-memory SQLiteIndexer for testing."""
    idx = SQLiteIndexer(":memory:")
    yield idx
    idx.close()


@pytest.fixture
def event_service():
    """In-memory EventService for testing."""
    svc = EventService(":memory:")
    yield svc
    svc.close()


@pytest.fixture
def cache():
    """MtimeCache instance for testing."""
    return MtimeCache(max_size=100)


@pytest.fixture
def uow(indexer, event_service, cache):
    """UnitOfWork wired to real in-memory SQLite + EventService + MtimeCache."""
    return UnitOfWork(
        sqlite_indexer=indexer,
        event_service=event_service,
        chroma_indexer=None,
        mtime_cache=cache,
    )


# ===================================================================
# Helpers
# ===================================================================


def _make_yaml_path(tmp_path: Path, name: str) -> str:
    """Return an absolute YAML path string inside tmp_path."""
    return str(tmp_path / f"{name}.yaml")


def _sample_data(name: str = "Hero") -> dict:
    """Return minimal entity data for testing."""
    return {"name": name, "role": "protagonist", "level": 1}


# ===================================================================
# test_save_and_commit
# ===================================================================


class TestSaveAndCommit:
    def test_save_and_commit(self, uow, indexer, tmp_path):
        """Buffer a save, commit, verify YAML file exists + entity in SQLite."""
        yaml_path = _make_yaml_path(tmp_path, "hero")
        data = _sample_data("Hero")

        uow.save(
            entity_id="ent-001",
            entity_type="character",
            name="Hero",
            yaml_path=yaml_path,
            data=data,
            event_type="CREATE",
        )

        count = uow.commit()

        # Verify commit count
        assert count == 1

        # Verify YAML file was written
        final_path = Path(yaml_path)
        assert final_path.exists(), "YAML file should exist after commit"

        # Verify no temp file lingering
        tmp_file = Path(yaml_path + ".tmp")
        assert not tmp_file.exists(), "Temp file should be cleaned up after commit"

        # Verify entity in SQLite
        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 1
        assert entities[0]["id"] == "ent-001"
        assert entities[0]["name"] == "Hero"

        # Verify sync_metadata
        sync = indexer.get_sync_metadata(yaml_path)
        assert len(sync) == 1
        assert sync[0]["entity_id"] == "ent-001"


# ===================================================================
# test_multi_save_atomic
# ===================================================================


class TestMultiSaveAtomic:
    def test_multi_save_atomic(self, uow, indexer, tmp_path):
        """Buffer 3 saves, commit, verify all 3 files + entities exist."""
        names = ["alpha", "beta", "gamma"]
        for i, name in enumerate(names):
            yaml_path = _make_yaml_path(tmp_path, name)
            uow.save(
                entity_id=f"ent-{i:03d}",
                entity_type="character",
                name=name.capitalize(),
                yaml_path=yaml_path,
                data=_sample_data(name.capitalize()),
                event_type="CREATE",
            )

        count = uow.commit()
        assert count == 3

        # All 3 YAML files exist
        for name in names:
            assert Path(_make_yaml_path(tmp_path, name)).exists()

        # All 3 entities in SQLite
        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 3
        entity_ids = {e["id"] for e in entities}
        assert entity_ids == {"ent-000", "ent-001", "ent-002"}


# ===================================================================
# test_delete_and_commit
# ===================================================================


class TestDeleteAndCommit:
    def test_delete_and_commit(self, uow, indexer, event_service, tmp_path):
        """Create a file, buffer a delete, commit, verify file + entity gone."""
        yaml_path = _make_yaml_path(tmp_path, "doomed")
        data = _sample_data("Doomed")

        # First: save and commit to create the file and entity
        uow.save(
            entity_id="ent-doomed",
            entity_type="character",
            name="Doomed",
            yaml_path=yaml_path,
            data=data,
            event_type="CREATE",
        )
        uow.commit()

        assert Path(yaml_path).exists()
        entities = indexer.query_entities(filters={"id": "ent-doomed"})
        assert len(entities) == 1

        # Second: create a new UoW and delete
        uow2 = UnitOfWork(
            sqlite_indexer=indexer,
            event_service=event_service,
            chroma_indexer=None,
            mtime_cache=None,
        )
        uow2.delete(
            entity_id="ent-doomed",
            entity_type="character",
            yaml_path=yaml_path,
        )
        count = uow2.commit()
        assert count == 1

        # File is gone
        assert not Path(yaml_path).exists(), "YAML file should be deleted"

        # Entity is gone from SQLite
        entities = indexer.query_entities(filters={"id": "ent-doomed"})
        assert len(entities) == 0

        # Sync metadata is gone
        sync = indexer.get_sync_metadata(yaml_path)
        assert len(sync) == 0


# ===================================================================
# test_rollback_on_error
# ===================================================================


class TestRollbackOnError:
    def test_rollback_on_error(self, indexer, event_service, tmp_path):
        """Mock a failure mid-commit, verify no temp files left, no entities in SQLite."""
        yaml_path = _make_yaml_path(tmp_path, "failed")

        uow = UnitOfWork(
            sqlite_indexer=indexer,
            event_service=event_service,
            chroma_indexer=None,
            mtime_cache=None,
        )
        uow.save(
            entity_id="ent-fail",
            entity_type="character",
            name="FailChar",
            yaml_path=yaml_path,
            data=_sample_data("FailChar"),
            event_type="CREATE",
        )

        # Patch the indexer to raise during upsert_entity (Step 2),
        # after temp files are written (Step 1).
        original_upsert = indexer.upsert_entity
        def failing_upsert(*args, **kwargs):
            raise RuntimeError("Simulated SQLite failure")

        indexer.upsert_entity = failing_upsert

        with pytest.raises(RuntimeError, match="Simulated SQLite failure"):
            uow.commit()

        # Restore original method
        indexer.upsert_entity = original_upsert

        # Temp files should be cleaned up by rollback
        tmp_file = Path(yaml_path + ".tmp")
        assert not tmp_file.exists(), "Temp file should be removed on rollback"

        # No entity in SQLite
        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 0

        # Pending buffer should be cleared
        assert len(uow._pending) == 0


# ===================================================================
# test_context_manager_auto_commit
# ===================================================================


class TestContextManagerAutoCommit:
    def test_context_manager_auto_commit(self, indexer, event_service, tmp_path):
        """Use `with` block, verify commit on clean exit."""
        yaml_path = _make_yaml_path(tmp_path, "auto_committed")

        with UnitOfWork(indexer, event_service) as uow:
            uow.save(
                entity_id="ent-auto",
                entity_type="scene",
                name="Opening",
                yaml_path=yaml_path,
                data={"title": "Opening Scene", "beats": []},
                event_type="CREATE",
            )

        # After exiting the context manager, file and entity should exist
        assert Path(yaml_path).exists()
        entities = indexer.query_entities(entity_type="scene")
        assert len(entities) == 1
        assert entities[0]["id"] == "ent-auto"


# ===================================================================
# test_context_manager_auto_rollback
# ===================================================================


class TestContextManagerAutoRollback:
    def test_context_manager_auto_rollback(self, indexer, event_service, tmp_path):
        """Use `with` block, raise exception, verify rollback."""
        yaml_path = _make_yaml_path(tmp_path, "rolled_back")

        with pytest.raises(ValueError, match="intentional"):
            with UnitOfWork(indexer, event_service) as uow:
                uow.save(
                    entity_id="ent-rb",
                    entity_type="character",
                    name="Ghost",
                    yaml_path=yaml_path,
                    data=_sample_data("Ghost"),
                    event_type="CREATE",
                )
                raise ValueError("intentional error")

        # File should NOT exist (rollback clears pending, no commit happened)
        assert not Path(yaml_path).exists()

        # No temp file
        assert not Path(yaml_path + ".tmp").exists()

        # No entity in SQLite
        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 0


# ===================================================================
# test_event_appended
# ===================================================================


class TestEventAppended:
    def test_event_appended(self, indexer, event_service, tmp_path):
        """Verify EventService.append_event() called for each save."""
        uow = UnitOfWork(indexer, event_service)

        for i in range(3):
            yaml_path = _make_yaml_path(tmp_path, f"evented_{i}")
            uow.save(
                entity_id=f"ent-ev-{i}",
                entity_type="character",
                name=f"Char{i}",
                yaml_path=yaml_path,
                data=_sample_data(f"Char{i}"),
                event_type="CREATE",
                branch_id="main",
            )

        uow.commit()

        # Check events were appended
        events = event_service.get_events_for_branch("main")
        assert len(events) == 3

        event_containers = {e["container_id"] for e in events}
        assert event_containers == {"ent-ev-0", "ent-ev-1", "ent-ev-2"}

        for ev in events:
            assert ev["event_type"] == "CREATE"

    def test_delete_event_appended(self, indexer, event_service, tmp_path):
        """Verify EventService.append_event() called for delete operations."""
        uow = UnitOfWork(indexer, event_service)

        yaml_path = _make_yaml_path(tmp_path, "to_delete")
        # First save
        uow.save(
            entity_id="ent-del",
            entity_type="character",
            name="Gone",
            yaml_path=yaml_path,
            data=_sample_data("Gone"),
            event_type="CREATE",
        )
        uow.commit()

        # Now delete
        uow2 = UnitOfWork(indexer, event_service)
        uow2.delete(
            entity_id="ent-del",
            entity_type="character",
            yaml_path=yaml_path,
        )
        uow2.commit()

        events = event_service.get_events_for_branch("main")
        assert len(events) == 2
        assert events[0]["event_type"] == "CREATE"
        assert events[1]["event_type"] == "DELETE"


# ===================================================================
# test_cache_invalidated
# ===================================================================


class TestCacheInvalidated:
    def test_cache_invalidated(self, indexer, event_service, tmp_path):
        """Verify MtimeCache.invalidate() called for each affected path."""
        mock_cache = MagicMock()
        uow = UnitOfWork(indexer, event_service, mtime_cache=mock_cache)

        paths = []
        for i in range(2):
            yaml_path = _make_yaml_path(tmp_path, f"cached_{i}")
            paths.append(yaml_path)
            uow.save(
                entity_id=f"ent-c-{i}",
                entity_type="character",
                name=f"Cached{i}",
                yaml_path=yaml_path,
                data=_sample_data(f"Cached{i}"),
                event_type="CREATE",
            )

        uow.commit()

        # invalidate() should be called once per entry
        assert mock_cache.invalidate.call_count == 2
        invalidated_paths = {
            str(call.args[0]) for call in mock_cache.invalidate.call_args_list
        }
        assert invalidated_paths == {str(Path(p)) for p in paths}

    def test_cache_invalidated_on_delete(self, indexer, event_service, tmp_path):
        """Verify MtimeCache.invalidate() called for delete operations too."""
        # First create the file
        uow1 = UnitOfWork(indexer, event_service)
        yaml_path = _make_yaml_path(tmp_path, "cache_del")
        uow1.save(
            entity_id="ent-cd",
            entity_type="character",
            name="CacheDel",
            yaml_path=yaml_path,
            data=_sample_data("CacheDel"),
            event_type="CREATE",
        )
        uow1.commit()

        # Now delete with cache
        mock_cache = MagicMock()
        uow2 = UnitOfWork(indexer, event_service, mtime_cache=mock_cache)
        uow2.delete(
            entity_id="ent-cd",
            entity_type="character",
            yaml_path=yaml_path,
        )
        uow2.commit()

        assert mock_cache.invalidate.call_count == 1

    def test_no_cache_no_error(self, indexer, event_service, tmp_path):
        """When mtime_cache is None, commit still succeeds without errors."""
        uow = UnitOfWork(indexer, event_service, mtime_cache=None)
        yaml_path = _make_yaml_path(tmp_path, "no_cache")
        uow.save(
            entity_id="ent-nc",
            entity_type="character",
            name="NoCache",
            yaml_path=yaml_path,
            data=_sample_data("NoCache"),
            event_type="CREATE",
        )
        count = uow.commit()
        assert count == 1
        assert Path(yaml_path).exists()


# ===================================================================
# test_empty_commit
# ===================================================================


class TestEmptyCommit:
    def test_empty_commit(self, uow):
        """Commit with no pending ops returns 0."""
        result = uow.commit()
        assert result == 0

    def test_double_commit(self, uow, tmp_path):
        """Second commit after first returns 0 (buffer is cleared)."""
        yaml_path = _make_yaml_path(tmp_path, "double")
        uow.save(
            entity_id="ent-dbl",
            entity_type="character",
            name="Double",
            yaml_path=yaml_path,
            data=_sample_data("Double"),
            event_type="CREATE",
        )
        first = uow.commit()
        assert first == 1

        second = uow.commit()
        assert second == 0
