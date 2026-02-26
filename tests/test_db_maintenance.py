"""Tests for DB maintenance (Phase K-5) — consistency checks and reindexing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from showrunner_tool.commands.db import _find_consistency_issues
from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
from showrunner_tool.schemas.dal import ConsistencyIssue


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def indexer():
    return SQLiteIndexer(":memory:")


def _seed_entity(indexer, entity_id, entity_type, name, yaml_path, content_hash="abc"):
    indexer.upsert_entity(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        yaml_path=str(yaml_path),
        content_hash=content_hash,
        attributes_json=json.dumps({"name": name}),
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


def _write_yaml(path: Path, data: dict):
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestConsistencyCheck:
    """_find_consistency_issues should detect YAML <-> SQLite mismatches."""

    def test_no_issues_when_consistent(self, indexer, tmp_path):
        yaml_path = tmp_path / "hero.yaml"
        _write_yaml(yaml_path, {"name": "Hero"})
        _seed_entity(indexer, "c1", "character", "Hero", yaml_path)

        issues = _find_consistency_issues(tmp_path, indexer)
        assert len(issues) == 0

    def test_orphaned_index_detected(self, indexer, tmp_path):
        # Entity in SQLite but YAML file doesn't exist
        fake_path = tmp_path / "nonexistent.yaml"
        _seed_entity(indexer, "c1", "character", "Ghost", fake_path)

        issues = _find_consistency_issues(tmp_path, indexer)
        orphans = [i for i in issues if i.issue_type == "orphaned_index"]
        assert len(orphans) == 1
        assert orphans[0].entity_id == "c1"
        assert orphans[0].auto_fixable is True

    def test_stale_sync_metadata_detected(self, indexer, tmp_path):
        # Sync metadata for a missing file
        indexer.upsert_sync_metadata(
            yaml_path=str(tmp_path / "gone.yaml"),
            entity_id="s1",
            entity_type="scene",
            content_hash="abc",
            mtime=0.0,
            file_size=0,
        )

        issues = _find_consistency_issues(tmp_path, indexer)
        stale = [i for i in issues if i.issue_type == "stale_file"]
        assert len(stale) == 1

    def test_multiple_issues_found(self, indexer, tmp_path):
        # Two orphaned entities + one stale sync
        _seed_entity(indexer, "c1", "character", "A", tmp_path / "a.yaml")
        _seed_entity(indexer, "c2", "character", "B", tmp_path / "b.yaml")
        indexer.upsert_sync_metadata(
            yaml_path=str(tmp_path / "c.yaml"),
            entity_id="c3",
            entity_type="world",
            content_hash="xyz",
            mtime=0.0,
            file_size=0,
        )

        issues = _find_consistency_issues(tmp_path, indexer)
        assert len(issues) == 3

    def test_empty_database_no_issues(self, indexer, tmp_path):
        issues = _find_consistency_issues(tmp_path, indexer)
        assert issues == []


class TestEntityCountByType:
    """get_entity_count_by_type should return correct counts."""

    def test_counts_by_type(self, indexer, tmp_path):
        for i in range(3):
            yaml_path = tmp_path / f"char{i}.yaml"
            _write_yaml(yaml_path, {"name": f"Char{i}"})
            _seed_entity(indexer, f"c{i}", "character", f"Char{i}", yaml_path)

        yaml_path = tmp_path / "world.yaml"
        _write_yaml(yaml_path, {"name": "World"})
        _seed_entity(indexer, "w1", "world_settings", "World", yaml_path)

        counts = indexer.get_entity_count_by_type()
        assert counts["character"] == 3
        assert counts["world_settings"] == 1


class TestMigrateContainersToEntities:
    """migrate_containers_to_entities should copy containers to entities table."""

    def test_migration_creates_entities(self, indexer):
        # Add a container via the legacy API
        indexer.upsert_container(
            "c1", "character", "Hero", "/path/to/hero.yaml",
            attributes={"name": "Hero"},
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )

        migrated = indexer.migrate_containers_to_entities()
        assert migrated == 1

        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 1
        assert entities[0]["name"] == "Hero"
