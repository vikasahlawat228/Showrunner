"""Phase K: DAL schema validation tests.

Tests cover all 8 Pydantic models in schemas/dal.py:
  SyncMetadata, CacheEntry, CacheStats, ContextScope,
  ProjectSnapshot, UnitOfWorkEntry, DBHealthReport, ConsistencyIssue
"""

from datetime import datetime, timezone

import pytest

from showrunner_tool.schemas.dal import (
    CacheEntry,
    CacheStats,
    ConsistencyIssue,
    ContextScope,
    DBHealthReport,
    ProjectSnapshot,
    SyncMetadata,
    UnitOfWorkEntry,
)


# ═══════════════════════════════════════════════════════════════════
# SyncMetadata
# ═══════════════════════════════════════════════════════════════════


class TestSyncMetadata:
    def test_required_fields(self):
        m = SyncMetadata(
            yaml_path="/project/characters/zara.yaml",
            entity_id="char_01",
            entity_type="character",
            content_hash="abc123",
            mtime=1706000000.0,
            file_size=2048,
        )
        assert m.yaml_path == "/project/characters/zara.yaml"
        assert m.entity_type == "character"
        assert m.content_hash == "abc123"
        assert m.file_size == 2048

    def test_indexed_at_default(self):
        m = SyncMetadata(
            yaml_path="x.yaml", entity_id="e1", entity_type="scene",
            content_hash="h", mtime=0.0, file_size=0,
        )
        assert isinstance(m.indexed_at, datetime)

    def test_roundtrip(self):
        m = SyncMetadata(
            yaml_path="a.yaml", entity_id="e1", entity_type="world",
            content_hash="sha256", mtime=1.5, file_size=100,
        )
        data = m.model_dump(mode="json")
        m2 = SyncMetadata(**data)
        assert m2.yaml_path == m.yaml_path
        assert m2.entity_id == m.entity_id


# ═══════════════════════════════════════════════════════════════════
# CacheEntry / CacheStats
# ═══════════════════════════════════════════════════════════════════


class TestCacheEntry:
    def test_creation(self):
        entry = CacheEntry(entity={"name": "Zara"}, path="/x.yaml", mtime=1.0)
        assert entry.entity == {"name": "Zara"}
        assert entry.size_bytes == 0

    def test_generic_any(self):
        entry = CacheEntry(entity="a string", path="/a.yaml", mtime=2.0)
        assert entry.entity == "a string"


class TestCacheStats:
    def test_defaults(self):
        stats = CacheStats()
        assert stats.size == 0
        assert stats.max_size == 500
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.hit_rate == 0.0

    def test_custom_values(self):
        stats = CacheStats(size=10, hits=80, misses=20, hit_rate=0.8)
        assert stats.hit_rate == 0.8


# ═══════════════════════════════════════════════════════════════════
# ContextScope
# ═══════════════════════════════════════════════════════════════════


class TestContextScope:
    def test_minimal(self):
        scope = ContextScope(step="scene_writing")
        assert scope.step == "scene_writing"
        assert scope.access_level == "story"
        assert scope.token_budget == 100_000
        assert scope.output_format == "template"
        assert scope.include_relationships is True

    def test_full(self):
        scope = ContextScope(
            step="evaluation", access_level="author",
            chapter=3, scene=1, character_name="Zara",
            token_budget=50_000, output_format="structured",
            include_relationships=False, semantic_query="revenge arc",
        )
        assert scope.access_level == "author"
        assert scope.semantic_query == "revenge arc"

    def test_literal_validation(self):
        with pytest.raises(Exception):
            ContextScope(step="x", access_level="invalid")


# ═══════════════════════════════════════════════════════════════════
# ProjectSnapshot
# ═══════════════════════════════════════════════════════════════════


class TestProjectSnapshot:
    def test_empty_defaults(self):
        snap = ProjectSnapshot()
        assert snap.world is None
        assert snap.characters == []
        assert snap.scenes == []
        assert snap.load_time_ms == 0
        assert snap.cache_hits == 0

    def test_populated(self):
        snap = ProjectSnapshot(
            world={"name": "Aetheria"},
            characters=[{"name": "Zara"}, {"name": "Kael"}],
            entities_loaded=3,
            cache_hits=2,
            cache_misses=1,
        )
        assert len(snap.characters) == 2
        assert snap.entities_loaded == 3


# ═══════════════════════════════════════════════════════════════════
# UnitOfWorkEntry
# ═══════════════════════════════════════════════════════════════════


class TestUnitOfWorkEntry:
    def test_save_entry(self):
        entry = UnitOfWorkEntry(
            operation="save",
            entity_id="char_01",
            entity_type="character",
            yaml_path="characters/zara.yaml",
            data={"name": "Zara"},
            event_type="UPDATE",
            event_payload={"field": "backstory"},
        )
        assert entry.operation == "save"
        assert entry.branch_id == "main"

    def test_delete_entry(self):
        entry = UnitOfWorkEntry(
            operation="delete",
            entity_id="char_02",
            entity_type="character",
            yaml_path="characters/old.yaml",
        )
        assert entry.data is None
        assert entry.event_type is None

    def test_literal_validation(self):
        with pytest.raises(Exception):
            UnitOfWorkEntry(
                operation="update",  # invalid
                entity_id="x", entity_type="x", yaml_path="x.yaml",
            )


# ═══════════════════════════════════════════════════════════════════
# DBHealthReport / ConsistencyIssue
# ═══════════════════════════════════════════════════════════════════


class TestDBHealthReport:
    def test_defaults(self):
        report = DBHealthReport()
        assert report.entity_counts == {}
        assert report.total_yaml_files == 0
        assert report.orphaned_indexes == 0
        assert report.cache_stats is None

    def test_with_stats(self):
        report = DBHealthReport(
            entity_counts={"character": 5, "scene": 12},
            total_yaml_files=20,
            total_indexed=17,
            cache_stats=CacheStats(hits=100, misses=10, hit_rate=0.91),
        )
        assert report.entity_counts["character"] == 5
        assert report.cache_stats.hit_rate == 0.91


class TestConsistencyIssue:
    def test_orphaned_index(self):
        issue = ConsistencyIssue(
            issue_type="orphaned_index",
            entity_id="char_99",
            description="Entity in SQLite but YAML file missing",
        )
        assert issue.auto_fixable is True

    def test_all_types(self):
        for t in ("orphaned_index", "stale_file", "hash_mismatch", "missing_entity"):
            issue = ConsistencyIssue(issue_type=t, description=f"Test {t}")
            assert issue.issue_type == t

    def test_invalid_type(self):
        with pytest.raises(Exception):
            ConsistencyIssue(issue_type="bad_type", description="nope")
