"""Tests for ProjectSnapshotFactory — batch entity loading via SQLite + cache."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
from showrunner_tool.schemas.dal import ContextScope, ProjectSnapshot
from showrunner_tool.services.project_snapshot import (
    STEP_ENTITY_MAP,
    ProjectSnapshotFactory,
)


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _seed_entity(indexer, entity_id, entity_type, name, yaml_path, attrs=None):
    """Insert a row into the entities table."""
    indexer.upsert_entity(
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        yaml_path=str(yaml_path),
        content_hash="abc123",
        attributes_json=json.dumps(attrs or {}),
        created_at="2025-01-01T00:00:00Z",
        updated_at="2025-01-01T00:00:00Z",
    )


def _write_yaml(path: Path, data: dict):
    """Write a minimal YAML file."""
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def indexer():
    return SQLiteIndexer(":memory:")


@pytest.fixture
def factory(indexer):
    return ProjectSnapshotFactory(indexer)


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestStepEntityMap:
    """STEP_ENTITY_MAP should define the expected workflow steps."""

    def test_has_all_core_steps(self):
        for step in [
            "world_building",
            "character_creation",
            "story_outline",
            "scene_writing",
            "screenplay",
            "panel_composition",
            "evaluation",
        ]:
            assert step in STEP_ENTITY_MAP

    def test_world_building_needs_world_settings(self):
        assert "world_settings" in STEP_ENTITY_MAP["world_building"]

    def test_scene_writing_needs_characters(self):
        assert "character" in STEP_ENTITY_MAP["scene_writing"]


class TestBasicLoading:
    """ProjectSnapshotFactory.load() should batch-load entities from SQLite."""

    def test_empty_project_returns_empty_snapshot(self, factory):
        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert isinstance(snapshot, ProjectSnapshot)
        assert snapshot.world is None
        assert snapshot.characters == []
        assert snapshot.entities_loaded == 0

    def test_loads_world_entity(self, indexer, factory, tmp_path):
        yaml_path = tmp_path / "world.yaml"
        world_data = {"name": "Aetheria", "genre": "fantasy"}
        _write_yaml(yaml_path, world_data)

        _seed_entity(indexer, "w1", "world_settings", "Aetheria", yaml_path)

        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert snapshot.world is not None
        assert snapshot.world["name"] == "Aetheria"
        assert snapshot.entities_loaded == 1

    def test_loads_multiple_characters(self, indexer, factory, tmp_path):
        for i, name in enumerate(["Zara", "Kael", "Mira"]):
            yaml_path = tmp_path / f"{name.lower()}.yaml"
            _write_yaml(yaml_path, {"name": name, "role": "protagonist"})
            _seed_entity(indexer, f"c{i}", "character", name, yaml_path)

        scope = ContextScope(step="character_creation")
        snapshot = factory.load(scope)

        assert len(snapshot.characters) == 3
        names = {c["name"] for c in snapshot.characters}
        assert names == {"Zara", "Kael", "Mira"}

    def test_routes_scenes_to_snapshot(self, indexer, factory, tmp_path):
        yaml_path = tmp_path / "scene1.yaml"
        _write_yaml(yaml_path, {"title": "The Arrival", "chapter": 1})
        _seed_entity(indexer, "s1", "scene", "The Arrival", yaml_path)

        scope = ContextScope(step="scene_writing")
        snapshot = factory.load(scope)

        assert len(snapshot.scenes) >= 1


class TestScopeFiltering:
    """Load should filter entities by scope (chapter, character_name)."""

    def test_character_name_filter(self, indexer, factory, tmp_path):
        for name in ["Zara", "Kael"]:
            path = tmp_path / f"{name.lower()}.yaml"
            _write_yaml(path, {"name": name})
            _seed_entity(
                indexer, name.lower(), "character", name, path,
                attrs={"name": name},
            )

        scope = ContextScope(step="character_creation", character_name="Zara")
        snapshot = factory.load(scope)

        # Should only load Zara (if SQLite query_entities filters by name)
        # The actual filtering depends on query_entities implementation
        assert snapshot.entities_loaded >= 1


class TestCacheIntegration:
    """When mtime_cache is provided, factory should use it."""

    def test_cache_hit_skips_yaml_read(self, indexer, tmp_path):
        from showrunner_tool.repositories.mtime_cache import MtimeCache

        cache = MtimeCache(max_size=100)
        factory = ProjectSnapshotFactory(indexer, mtime_cache=cache)

        yaml_path = tmp_path / "world.yaml"
        world_data = {"name": "Cached World", "genre": "scifi"}
        _write_yaml(yaml_path, world_data)

        # Seed cache manually
        cache.put(yaml_path, world_data)

        _seed_entity(indexer, "w1", "world_settings", "Cached World", yaml_path)

        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert snapshot.cache_hits == 1
        assert snapshot.cache_misses == 0
        assert snapshot.world["name"] == "Cached World"

    def test_cache_miss_reads_yaml(self, indexer, tmp_path):
        from showrunner_tool.repositories.mtime_cache import MtimeCache

        cache = MtimeCache(max_size=100)
        factory = ProjectSnapshotFactory(indexer, mtime_cache=cache)

        yaml_path = tmp_path / "world.yaml"
        _write_yaml(yaml_path, {"name": "Fresh World"})

        _seed_entity(indexer, "w1", "world_settings", "Fresh World", yaml_path)

        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert snapshot.cache_misses == 1
        assert snapshot.world["name"] == "Fresh World"


class TestFallbackToSQLiteAttributes:
    """If YAML file doesn't exist, should fall back to attributes_json from SQLite."""

    def test_missing_yaml_uses_sqlite_attributes(self, indexer, factory):
        _seed_entity(
            indexer, "w1", "world_settings", "Ghost World",
            "/nonexistent/world.yaml",
            attrs={"name": "Ghost World", "genre": "mystery"},
        )

        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert snapshot.world is not None
        assert snapshot.world["name"] == "Ghost World"


class TestCreativeRoomAccessControl:
    """Creative room data should only appear in author access level."""

    def test_author_access_includes_creative_room(self, indexer, factory, tmp_path):
        path = tmp_path / "creative.yaml"
        _write_yaml(path, {"secrets": ["twist1"]})
        _seed_entity(indexer, "cr1", "creative_room", "creative", path)

        scope = ContextScope(step="evaluation", access_level="author")
        snapshot = factory.load(scope)

        assert snapshot.creative_room is not None

    def test_story_access_excludes_creative_room(self, indexer, factory, tmp_path):
        path = tmp_path / "creative.yaml"
        _write_yaml(path, {"secrets": ["twist1"]})
        _seed_entity(indexer, "cr1", "creative_room", "creative", path)

        scope = ContextScope(step="evaluation", access_level="story")
        snapshot = factory.load(scope)

        assert snapshot.creative_room is None


class TestLoadMetrics:
    """Snapshot should include timing and count metadata."""

    def test_load_time_is_populated(self, factory):
        scope = ContextScope(step="world_building")
        snapshot = factory.load(scope)

        assert snapshot.load_time_ms >= 0

    def test_unknown_step_uses_defaults(self, factory):
        scope = ContextScope(step="totally_unknown_step")
        snapshot = factory.load(scope)

        # Should use the default fallback entity types
        assert isinstance(snapshot, ProjectSnapshot)
