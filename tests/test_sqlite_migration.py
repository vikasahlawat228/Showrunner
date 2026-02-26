"""Phase K: SQLite entity index and sync metadata tests.

Tests cover the Phase K additions to SQLiteIndexer:
  - entities table CRUD (upsert, query, delete)
  - sync_metadata CRUD
  - get_entity_by_path O(1) lookup
  - get_entity_count_by_type aggregation
  - migrate_containers_to_entities one-time migration
"""

import json

import pytest

from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def indexer():
    """Create an in-memory SQLiteIndexer for testing."""
    idx = SQLiteIndexer(":memory:")
    return idx


def _upsert_sample_entity(indexer, entity_id="char_01", entity_type="character",
                          name="Zara", yaml_path="characters/zara.yaml"):
    """Helper to upsert a sample entity."""
    indexer.upsert_entity(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        yaml_path=yaml_path,
        content_hash="abc123def456",
        attributes_json=json.dumps({"role": "protagonist", "chapter": 1}),
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T12:00:00Z",
        container_type=None,
        parent_id=None,
        sort_order=0,
        tags=["hero", "main"],
    )


# ═══════════════════════════════════════════════════════════════════
# Entity CRUD
# ═══════════════════════════════════════════════════════════════════


class TestEntityCRUD:
    def test_upsert_and_query(self, indexer):
        _upsert_sample_entity(indexer)
        results = indexer.query_entities(entity_type="character")
        assert len(results) == 1
        assert results[0]["name"] == "Zara"
        assert results[0]["content_hash"] == "abc123def456"

    def test_upsert_replaces_existing(self, indexer):
        _upsert_sample_entity(indexer)
        indexer.upsert_entity(
            entity_id="char_01", entity_type="character", name="Zara Updated",
            yaml_path="characters/zara.yaml", content_hash="new_hash",
            attributes_json="{}", created_at="2025-01-01T00:00:00Z",
            updated_at="2025-02-01T00:00:00Z",
        )
        results = indexer.query_entities(entity_type="character")
        assert len(results) == 1
        assert results[0]["name"] == "Zara Updated"
        assert results[0]["content_hash"] == "new_hash"

    def test_delete_entity(self, indexer):
        _upsert_sample_entity(indexer)
        indexer.delete_entity("char_01")
        results = indexer.query_entities(entity_type="character")
        assert len(results) == 0

    def test_delete_nonexistent_is_safe(self, indexer):
        indexer.delete_entity("nonexistent_id")  # should not raise

    def test_query_with_filters(self, indexer):
        _upsert_sample_entity(indexer, "char_01", "character", "Zara", "chars/zara.yaml")
        _upsert_sample_entity(indexer, "char_02", "character", "Kael", "chars/kael.yaml")
        _upsert_sample_entity(indexer, "scene_01", "scene", "Battle", "scenes/battle.yaml")

        # Type filter
        chars = indexer.query_entities(entity_type="character")
        assert len(chars) == 2

        scenes = indexer.query_entities(entity_type="scene")
        assert len(scenes) == 1

        # All entities
        all_ents = indexer.query_entities()
        assert len(all_ents) == 3

    def test_query_with_json_attribute_filter(self, indexer):
        _upsert_sample_entity(indexer)
        results = indexer.query_entities(
            entity_type="character",
            filters={"role": "protagonist"},
        )
        assert len(results) == 1
        assert results[0]["name"] == "Zara"

        results = indexer.query_entities(
            entity_type="character",
            filters={"role": "antagonist"},
        )
        assert len(results) == 0

    def test_query_with_container_type(self, indexer):
        indexer.upsert_entity(
            entity_id="c1", entity_type="container", name="Fragment",
            yaml_path="containers/frag.yaml", content_hash="h1",
            attributes_json="{}", created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z", container_type="fragment",
        )
        indexer.upsert_entity(
            entity_id="c2", entity_type="container", name="Research",
            yaml_path="containers/res.yaml", content_hash="h2",
            attributes_json="{}", created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z", container_type="research_topic",
        )
        frags = indexer.query_entities(container_type="fragment")
        assert len(frags) == 1
        assert frags[0]["name"] == "Fragment"


# ═══════════════════════════════════════════════════════════════════
# Entity by Path
# ═══════════════════════════════════════════════════════════════════


class TestEntityByPath:
    def test_get_entity_by_path(self, indexer):
        _upsert_sample_entity(indexer)
        entity = indexer.get_entity_by_path("characters/zara.yaml")
        assert entity is not None
        assert entity["id"] == "char_01"
        assert entity["name"] == "Zara"

    def test_get_entity_by_path_not_found(self, indexer):
        result = indexer.get_entity_by_path("nonexistent.yaml")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# Sync Metadata CRUD
# ═══════════════════════════════════════════════════════════════════


class TestSyncMetadata:
    def test_upsert_and_get(self, indexer):
        indexer.upsert_sync_metadata(
            yaml_path="characters/zara.yaml",
            entity_id="char_01",
            entity_type="character",
            content_hash="sha256_abc",
            mtime=1706000000.0,
            file_size=2048,
        )
        results = indexer.get_sync_metadata("characters/zara.yaml")
        assert len(results) == 1
        assert results[0]["content_hash"] == "sha256_abc"
        assert results[0]["mtime"] == 1706000000.0
        assert results[0]["file_size"] == 2048

    def test_get_all(self, indexer):
        indexer.upsert_sync_metadata("a.yaml", "e1", "character", "h1", 1.0, 100)
        indexer.upsert_sync_metadata("b.yaml", "e2", "scene", "h2", 2.0, 200)
        all_meta = indexer.get_sync_metadata()
        assert len(all_meta) == 2

    def test_upsert_replaces(self, indexer):
        indexer.upsert_sync_metadata("a.yaml", "e1", "character", "h1", 1.0, 100)
        indexer.upsert_sync_metadata("a.yaml", "e1", "character", "h2_updated", 2.0, 150)
        results = indexer.get_sync_metadata("a.yaml")
        assert len(results) == 1
        assert results[0]["content_hash"] == "h2_updated"
        assert results[0]["mtime"] == 2.0

    def test_delete_sync_metadata(self, indexer):
        indexer.upsert_sync_metadata("a.yaml", "e1", "character", "h1", 1.0, 100)
        indexer.delete_sync_metadata("a.yaml")
        results = indexer.get_sync_metadata("a.yaml")
        assert len(results) == 0


# ═══════════════════════════════════════════════════════════════════
# Aggregation
# ═══════════════════════════════════════════════════════════════════


class TestEntityCountByType:
    def test_empty(self, indexer):
        counts = indexer.get_entity_count_by_type()
        assert counts == {}

    def test_counts(self, indexer):
        _upsert_sample_entity(indexer, "c1", "character", "A", "a.yaml")
        _upsert_sample_entity(indexer, "c2", "character", "B", "b.yaml")
        _upsert_sample_entity(indexer, "s1", "scene", "S", "s.yaml")
        counts = indexer.get_entity_count_by_type()
        assert counts["character"] == 2
        assert counts["scene"] == 1


# ═══════════════════════════════════════════════════════════════════
# Container → Entity Migration
# ═══════════════════════════════════════════════════════════════════


class TestMigrateContainersToEntities:
    def test_migration(self, indexer):
        # Insert a container using the legacy method
        indexer.upsert_container(
            container_id="legacy_01",
            container_type="fragment",
            name="Old Fragment",
            yaml_path="containers/old.yaml",
            attributes={"text": "some content"},
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        indexer.upsert_container(
            container_id="legacy_02",
            container_type="scene",
            name="Old Scene",
            yaml_path="scenes/old.yaml",
            attributes={"chapter": 1},
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )

        # Run migration
        count = indexer.migrate_containers_to_entities()
        assert count == 2

        # Verify entities table has the data
        entities = indexer.query_entities()
        assert len(entities) == 2

        # Verify by path
        entity = indexer.get_entity_by_path("containers/old.yaml")
        assert entity is not None
        assert entity["id"] == "legacy_01"
        assert entity["name"] == "Old Fragment"
        assert entity["content_hash"] == "migrated"  # placeholder hash

    def test_migration_empty(self, indexer):
        count = indexer.migrate_containers_to_entities()
        assert count == 0


# ═══════════════════════════════════════════════════════════════════
# Table Coexistence
# ═══════════════════════════════════════════════════════════════════


class TestTableCoexistence:
    """Verify the legacy containers table and new entities table work independently."""

    def test_both_tables_exist(self, indexer):
        cursor = indexer.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row["name"] for row in cursor.fetchall()]
        assert "containers" in tables
        assert "entities" in tables
        assert "sync_metadata" in tables
        assert "relationships" in tables

    def test_container_ops_still_work(self, indexer):
        indexer.upsert_container(
            container_id="c1", container_type="fragment", name="F1",
            yaml_path="f.yaml", attributes={"x": 1},
            created_at="2025-01-01T00:00:00Z", updated_at="2025-01-01T00:00:00Z",
        )
        results = indexer.query_containers(container_type="fragment")
        assert len(results) == 1
        indexer.delete_container("c1")
        results = indexer.query_containers(container_type="fragment")
        assert len(results) == 0
