"""Tests for the EntityIndexBridge service.

Verifies that save/delete callbacks on typed YAMLRepositories propagate
entity mutations to the SQLite ``entities`` table via the bridge.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from showrunner_tool.repositories.base import YAMLRepository
from showrunner_tool.repositories.sqlite_indexer import SQLiteIndexer
from showrunner_tool.services.entity_index_bridge import EntityIndexBridge


# ═══════════════════════════════════════════════════════════════════
# Minimal test model (avoids importing the full Character schema)
# ═══════════════════════════════════════════════════════════════════


class SimpleCharacter(BaseModel):
    """Minimal stand-in for Character with the fields the bridge inspects."""

    id: str = "char_001"
    name: str = "Test Hero"
    created_at: str = "2025-06-01T00:00:00Z"
    updated_at: str = "2025-06-01T12:00:00Z"
    tags: list[str] = Field(default_factory=list)


class _FakeCharacterRepo(YAMLRepository[SimpleCharacter]):
    """A concrete YAMLRepository subclass whose class name is CharacterRepository.

    We give it a predictable class name so the bridge resolves the entity
    type via REPO_ENTITY_TYPE_MAP.
    """

    def __init__(self, base_dir: Path):
        super().__init__(base_dir, SimpleCharacter)


# Rename at the class level so REPO_ENTITY_TYPE_MAP lookup works
_FakeCharacterRepo.__name__ = "CharacterRepository"
_FakeCharacterRepo.__qualname__ = "CharacterRepository"


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def indexer():
    """In-memory SQLiteIndexer."""
    return SQLiteIndexer(":memory:")


@pytest.fixture
def char_repo(tmp_path):
    """CharacterRepository backed by a temp directory."""
    characters_dir = tmp_path / "characters"
    characters_dir.mkdir()
    return _FakeCharacterRepo(characters_dir)


@pytest.fixture
def bridge(indexer):
    return EntityIndexBridge(indexer)


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestSaveTriggersEntityUpsert:
    """When a typed repo saves an entity the bridge should upsert into SQLite."""

    def test_save_triggers_entity_upsert(self, indexer, char_repo, bridge):
        bridge.register(char_repo, "character")

        hero = SimpleCharacter(id="hero_01", name="Zara", tags=["protagonist"])
        path = char_repo.base_dir / "zara.yaml"
        char_repo._save_file(path, hero)

        # Verify entity is now in the entities table
        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 1
        entity = entities[0]
        assert entity["id"] == "hero_01"
        assert entity["name"] == "Zara"
        assert entity["entity_type"] == "character"
        assert entity["yaml_path"] == str(path)
        # content_hash should be a sha256 hex string (64 chars)
        assert len(entity["content_hash"]) == 64

        # Verify attributes_json roundtrips
        attrs = json.loads(entity["attributes_json"])
        assert attrs["name"] == "Zara"
        assert attrs["id"] == "hero_01"

    def test_save_updates_existing_entity(self, indexer, char_repo, bridge):
        """Saving the same entity twice should update (not duplicate) the row."""
        bridge.register(char_repo, "character")

        hero = SimpleCharacter(id="hero_01", name="Zara")
        path = char_repo.base_dir / "zara.yaml"
        char_repo._save_file(path, hero)

        # Update the name and save again
        hero_v2 = SimpleCharacter(id="hero_01", name="Zara the Bold")
        char_repo._save_file(path, hero_v2)

        entities = indexer.query_entities(entity_type="character")
        assert len(entities) == 1
        assert entities[0]["name"] == "Zara the Bold"


class TestDeleteTriggersEntityRemoval:
    """When a typed repo deletes an entity the bridge should remove from SQLite."""

    def test_delete_triggers_entity_removal(self, indexer, char_repo, bridge):
        bridge.register(char_repo, "character")

        hero = SimpleCharacter(id="zara", name="Zara")
        path = char_repo.base_dir / "zara.yaml"
        char_repo._save_file(path, hero)

        # Confirm it is present
        assert len(indexer.query_entities(entity_type="character")) == 1

        # Delete via the repo
        char_repo.delete("zara")

        # Confirm it has been removed from the index
        assert len(indexer.query_entities(entity_type="character")) == 0


class TestRegisterAll:
    """register_all should wire up multiple repos in one call."""

    def test_register_all(self, indexer, tmp_path, bridge):
        repo_a = _FakeCharacterRepo(tmp_path / "a")
        (tmp_path / "a").mkdir()
        repo_b = _FakeCharacterRepo(tmp_path / "b")
        (tmp_path / "b").mkdir()

        bridge.register_all([
            (repo_a, "character"),
            (repo_b, "character_alt"),
        ])

        assert len(bridge.registered_types) == 2
        assert "character (CharacterRepository)" in bridge.registered_types
        assert "character_alt (CharacterRepository)" in bridge.registered_types

        # Save through both repos and verify both show up
        hero_a = SimpleCharacter(id="a_01", name="Alpha")
        repo_a._save_file(repo_a.base_dir / "alpha.yaml", hero_a)

        hero_b = SimpleCharacter(id="b_01", name="Beta")
        repo_b._save_file(repo_b.base_dir / "beta.yaml", hero_b)

        all_entities = indexer.query_entities()
        assert len(all_entities) == 2
        names = {e["name"] for e in all_entities}
        assert names == {"Alpha", "Beta"}


class TestCallbackFailureDoesNotBreakSave:
    """If the indexer raises inside a callback the repo save must still succeed."""

    def test_callback_failure_does_not_break_save(self, char_repo, tmp_path):
        # Create a mock indexer whose upsert_entity always raises
        broken_indexer = MagicMock()
        broken_indexer.upsert_entity.side_effect = RuntimeError("db exploded")
        broken_indexer.delete_entity.side_effect = RuntimeError("db exploded")

        bridge = EntityIndexBridge(broken_indexer)
        bridge.register(char_repo, "character")

        hero = SimpleCharacter(id="hero_01", name="Safe Hero")
        path = char_repo.base_dir / "safe_hero.yaml"

        # Save should succeed even though the bridge callback raises
        result_path = char_repo._save_file(path, hero)
        assert result_path.exists()

        # The YAML file should be readable and correct
        import yaml

        with open(result_path) as f:
            data = yaml.safe_load(f)
        assert data["name"] == "Safe Hero"

    def test_delete_callback_failure_does_not_break_delete(self, char_repo, tmp_path):
        """Delete should succeed even if the bridge callback raises."""
        broken_indexer = MagicMock()
        broken_indexer.upsert_entity.side_effect = RuntimeError("db exploded")
        broken_indexer.delete_entity.side_effect = RuntimeError("db exploded")

        bridge = EntityIndexBridge(broken_indexer)
        bridge.register(char_repo, "character")

        hero = SimpleCharacter(id="doomed", name="Doomed")
        path = char_repo.base_dir / "doomed.yaml"
        char_repo._save_file(path, hero)
        assert path.exists()

        # Delete should succeed despite bridge failure
        char_repo.delete("doomed")
        assert not path.exists()


class TestEntityTypeInference:
    """The bridge should infer entity_type from the repo class name."""

    def test_inferred_entity_type(self, indexer, char_repo):
        bridge = EntityIndexBridge(indexer)
        bridge.register(char_repo)  # no explicit entity_type

        assert len(bridge.registered_types) == 1
        # Should have inferred "character" from "CharacterRepository"
        assert "character (CharacterRepository)" in bridge.registered_types

    def test_fallback_for_unknown_repo(self, indexer, tmp_path):
        """Repos not in REPO_ENTITY_TYPE_MAP get a lowercased class name."""

        class CustomThingRepository(YAMLRepository[SimpleCharacter]):
            pass

        repo = CustomThingRepository(tmp_path, SimpleCharacter)
        bridge = EntityIndexBridge(indexer)
        bridge.register(repo)

        assert "customthingrepository (CustomThingRepository)" in bridge.registered_types


class TestSkipsReposWithoutCallbackAPI:
    """Repos that lack subscribe_save/subscribe_delete are silently skipped."""

    def test_skip_non_yaml_repo(self, indexer):
        class PlainRepo:
            """Does not extend YAMLRepository and has no subscribe hooks."""
            pass

        bridge = EntityIndexBridge(indexer)
        bridge.register(PlainRepo(), "some_type")

        assert len(bridge.registered_types) == 0
