"""Phase F automated tests — Foundation Rework.

Tests cover the three tracks:
  1. Universal Buckets & Multi-Project (GenericContainer, SQLiteIndexer, StructureTree)
  2. Unified Mutation Path (ContainerRepository + EventService integration)
  3. Model Configuration Cascade (ModelConfigRegistry.resolve())
"""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.schemas.model_config import ModelConfig, ProjectModelConfig
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.model_config_registry import (
    AGENT_DEFAULT_MODELS,
    ModelConfigRegistry,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory with antigravity.yaml."""
    (tmp_path / "schemas").mkdir()
    (tmp_path / "antigravity.yaml").write_text(
        "name: Test Project\n"
        "version: 0.1.0\n"
        "default_model: gemini/gemini-2.0-flash\n"
        "model_overrides:\n"
        "  writing_agent: anthropic/claude-3.5-sonnet\n"
        "  research_agent:\n"
        "    model: gemini/gemini-2.0-pro\n"
        "    temperature: 0.3\n"
        "    max_tokens: 4096\n"
    )
    return tmp_path


@pytest.fixture
def indexer() -> SQLiteIndexer:
    """In-memory SQLite indexer."""
    return SQLiteIndexer(":memory:")


@pytest.fixture
def container_repo(tmp_path: Path) -> ContainerRepository:
    """Container repo pointing at a temp dir."""
    return ContainerRepository(tmp_path)


@pytest.fixture
def event_service() -> EventService:
    """In-memory event service."""
    return EventService(":memory:")


# ═══════════════════════════════════════════════════════════════════
# Track 1: Universal Buckets & Multi-Project Isolation
# ═══════════════════════════════════════════════════════════════════


class TestGenericContainerPhaseF:
    """Verify the new Phase F fields on GenericContainer."""

    def test_default_values(self):
        """New Phase F fields should have sensible defaults."""
        c = GenericContainer(container_type="character", name="Test")
        assert c.context_window is None
        assert c.timeline_positions == []
        assert c.tags == []
        assert c.model_preference is None
        assert c.parent_id is None
        assert c.sort_order == 0

    def test_explicit_values(self):
        """Phase F fields accept explicit values."""
        c = GenericContainer(
            container_type="scene",
            name="Battle Scene",
            parent_id="chapter_01",
            sort_order=3,
            tags=["#act2", "#climax"],
            model_preference="anthropic/claude-3.5-sonnet",
            context_window="A battle scene in the desert.",
            timeline_positions=["S1.Arc1.Act2.Ch3.Sc5"],
        )
        assert c.parent_id == "chapter_01"
        assert c.sort_order == 3
        assert c.tags == ["#act2", "#climax"]
        assert c.model_preference == "anthropic/claude-3.5-sonnet"
        assert c.context_window == "A battle scene in the desert."
        assert "S1.Arc1.Act2.Ch3.Sc5" in c.timeline_positions

    def test_serialization_roundtrip(self):
        """Phase F fields survive JSON serialization roundtrip."""
        c = GenericContainer(
            container_type="chapter",
            name="Chapter 1",
            parent_id="act_01",
            sort_order=1,
            tags=["#intro"],
        )
        data = c.model_dump(mode="json")
        restored = GenericContainer(**data)
        assert restored.parent_id == "act_01"
        assert restored.sort_order == 1
        assert restored.tags == ["#intro"]


class TestSQLiteIndexerPhaseF:
    """Verify SQLiteIndexer handles Phase F columns."""

    def test_upsert_with_phase_f_fields(self, indexer: SQLiteIndexer):
        """Phase F columns are stored and retrievable."""
        indexer.upsert_container(
            container_id="c1",
            container_type="scene",
            name="Scene 1",
            yaml_path="/path/scene_1.yaml",
            attributes={"text": "hello"},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id="ch1",
            sort_order=2,
            tags=["#act1"],
            model_preference="openai/gpt-4o",
        )

        rows = indexer.query_containers(container_type="scene")
        assert len(rows) == 1
        row = rows[0]
        assert row["parent_id"] == "ch1"
        assert row["sort_order"] == 2
        assert json.loads(row["tags_json"]) == ["#act1"]
        assert row["model_preference"] == "openai/gpt-4o"

    def test_get_children(self, indexer: SQLiteIndexer):
        """get_children returns containers with the given parent_id, sorted."""
        for i, name in enumerate(["Scene C", "Scene A", "Scene B"]):
            indexer.upsert_container(
                container_id=f"s{i}",
                container_type="scene",
                name=name,
                yaml_path=f"/path/{name}.yaml",
                attributes={},
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
                parent_id="ch1",
                sort_order=i,
            )

        children = indexer.get_children("ch1")
        assert len(children) == 3
        assert children[0]["name"] == "Scene C"  # sort_order=0
        assert children[1]["name"] == "Scene A"  # sort_order=1
        assert children[2]["name"] == "Scene B"  # sort_order=2

    def test_get_roots(self, indexer: SQLiteIndexer):
        """get_roots returns containers with NULL parent_id."""
        indexer.upsert_container(
            container_id="s1",
            container_type="season",
            name="Season 1",
            yaml_path="/path/s1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id=None,
            sort_order=0,
        )
        indexer.upsert_container(
            container_id="ch1",
            container_type="chapter",
            name="Chapter 1",
            yaml_path="/path/ch1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id="s1",
            sort_order=0,
        )

        roots = indexer.get_roots(container_types=["season"])
        assert len(roots) == 1
        assert roots[0]["name"] == "Season 1"

    def test_filter_by_parent_id(self, indexer: SQLiteIndexer):
        """query_containers respects direct parent_id filter."""
        indexer.upsert_container(
            container_id="ch1",
            container_type="chapter",
            name="Chapter 1",
            yaml_path="/path/ch1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id="act_01",
        )
        results = indexer.query_containers(filters={"parent_id": "act_01"})
        assert len(results) == 1
        assert results[0]["name"] == "Chapter 1"

    def test_migration_adds_columns_idempotently(self):
        """_migrate_phase_f_columns can run multiple times safely."""
        idx = SQLiteIndexer(":memory:")
        # Running migration again should not raise
        idx._migrate_phase_f_columns()
        idx.close()


class TestStructureTree:
    """Verify the hierarchical structure tree queries."""

    def test_three_level_hierarchy(self, indexer: SQLiteIndexer):
        """Season → Chapter → Scene tree is built correctly."""
        indexer.upsert_container(
            container_id="season_1",
            container_type="season",
            name="Season 1",
            yaml_path="/s1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id=None,
            sort_order=0,
        )
        indexer.upsert_container(
            container_id="ch_1",
            container_type="chapter",
            name="Chapter 1",
            yaml_path="/ch1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id="season_1",
            sort_order=0,
        )
        indexer.upsert_container(
            container_id="sc_1",
            container_type="scene",
            name="Scene 1",
            yaml_path="/sc1.yaml",
            attributes={},
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            parent_id="ch_1",
            sort_order=0,
        )

        # Build tree manually (mimicking KnowledgeGraphService.get_structure_tree)
        structural_types = ["season", "chapter", "scene"]
        roots = indexer.get_roots(container_types=structural_types)
        assert len(roots) == 1
        assert roots[0]["name"] == "Season 1"

        children = indexer.get_children("season_1")
        assert len(children) == 1
        assert children[0]["name"] == "Chapter 1"

        grandchildren = indexer.get_children("ch_1")
        assert len(grandchildren) == 1
        assert grandchildren[0]["name"] == "Scene 1"


# ═══════════════════════════════════════════════════════════════════
# Track 2: Unified Mutation Path
# ═══════════════════════════════════════════════════════════════════


class TestUnifiedMutationPath:
    """Verify that saves go through ContainerRepository + EventService."""

    def test_save_creates_yaml_and_events(
        self,
        container_repo: ContainerRepository,
        event_service: EventService,
    ):
        """Saving a container + emitting an event creates both artifacts."""
        container = GenericContainer(
            id="test_01",
            container_type="fragment",
            name="Test Fragment",
            attributes={"text": "Hello world"},
        )

        # 1. Save to YAML
        path = container_repo.save_container(container)
        assert path.exists()

        # 2. Emit event
        event_id = event_service.append_event(
            parent_event_id=None,
            branch_id="main",
            event_type="CREATE",
            container_id="test_01",
            payload=container.attributes,
        )
        assert event_id is not None

        # 3. Verify event_log has exactly one event
        events = event_service.get_all_events()
        assert len(events) == 1
        assert events[0]["container_id"] == "test_01"
        assert events[0]["event_type"] == "CREATE"

    def test_indexer_syncs_on_save(self, tmp_path: Path):
        """ContainerRepository callbacks trigger SQLiteIndexer upsert."""
        from antigravity_tool.repositories.container_repo import (
            ContainerRepository,
            SchemaRepository,
        )
        from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

        container_repo = ContainerRepository(tmp_path)
        schema_repo = SchemaRepository(tmp_path / "schemas")
        indexer = SQLiteIndexer(":memory:")
        kg_service = KnowledgeGraphService(container_repo, schema_repo, indexer)

        container = GenericContainer(
            id="indexed_01",
            container_type="character",
            name="Zara",
            attributes={"role": "protagonist"},
            parent_id="act_01",
            tags=["#hero"],
        )

        container_repo.save_container(container)

        # Verify the indexer has the container with Phase F fields
        rows = indexer.query_containers(container_type="character")
        assert len(rows) == 1
        assert rows[0]["parent_id"] == "act_01"
        assert json.loads(rows[0]["tags_json"]) == ["#hero"]

    def test_event_service_branch_creation(self, event_service: EventService):
        """Branching creates a new branch pointing at a specific event."""
        # Create some events on main
        e1 = event_service.append_event(None, "main", "CREATE", "c1", {"v": 1})
        e2 = event_service.append_event(None, "main", "UPDATE", "c1", {"v": 2})

        # Branch from event 1
        event_service.branch("main", "alt-timeline", e1)

        # The alt branch should have state from only event 1
        state = event_service.project_state("alt-timeline")
        assert "c1" in state
        assert state["c1"]["v"] == 1  # Only first event applied


# ═══════════════════════════════════════════════════════════════════
# Track 3: Model Configuration Cascade
# ═══════════════════════════════════════════════════════════════════


class TestModelConfigRegistry:
    """Verify the 4-level model resolution cascade."""

    def test_project_default(self, tmp_project: Path):
        """When nothing else is configured, use the project default."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve()
        assert result.model == "gemini/gemini-2.0-flash"

    def test_agent_default_from_yaml(self, tmp_project: Path):
        """Agent override in antigravity.yaml takes priority over built-in."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(agent_id="writing_agent")
        # The YAML has writing_agent: anthropic/claude-3.5-sonnet
        assert result.model == "anthropic/claude-3.5-sonnet"

    def test_agent_default_with_full_config(self, tmp_project: Path):
        """Agent override with temperature and max_tokens."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(agent_id="research_agent")
        assert result.model == "gemini/gemini-2.0-pro"
        assert result.temperature == 0.3
        assert result.max_tokens == 4096

    def test_builtin_agent_default(self, tmp_project: Path):
        """Agents not overridden in YAML use built-in defaults."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(agent_id="brainstorm_agent")
        assert result.model == AGENT_DEFAULT_MODELS["brainstorm_agent"]

    def test_bucket_overrides_agent(self, tmp_project: Path):
        """Per-bucket model_preference overrides agent config."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(
            bucket_model_preference="openai/gpt-4o-mini",
            agent_id="writing_agent",
        )
        assert result.model == "openai/gpt-4o-mini"

    def test_step_overrides_everything(self, tmp_project: Path):
        """Per-step config has highest priority."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(
            step_config={"model": "anthropic/claude-3-haiku", "temperature": 0.2},
            bucket_model_preference="openai/gpt-4o-mini",
            agent_id="writing_agent",
        )
        assert result.model == "anthropic/claude-3-haiku"
        assert result.temperature == 0.2

    def test_empty_step_model_falls_through(self, tmp_project: Path):
        """Step config with empty model string falls through to next level."""
        registry = ModelConfigRegistry(tmp_project)
        result = registry.resolve(
            step_config={"model": "", "temperature": 0.9},
            agent_id="writing_agent",
        )
        # Empty model → fall through to agent level
        assert result.model == "anthropic/claude-3.5-sonnet"

    def test_cascade_priority_order(self, tmp_project: Path):
        """Full cascade: Step > Bucket > Agent > Project."""
        registry = ModelConfigRegistry(tmp_project)

        # Project default
        r1 = registry.resolve()
        assert r1.model == "gemini/gemini-2.0-flash"

        # Agent overrides project
        r2 = registry.resolve(agent_id="writing_agent")
        assert r2.model == "anthropic/claude-3.5-sonnet"

        # Bucket overrides agent
        r3 = registry.resolve(
            bucket_model_preference="openai/gpt-4o",
            agent_id="writing_agent",
        )
        assert r3.model == "openai/gpt-4o"

        # Step overrides bucket
        r4 = registry.resolve(
            step_config={"model": "anthropic/claude-3-haiku"},
            bucket_model_preference="openai/gpt-4o",
            agent_id="writing_agent",
        )
        assert r4.model == "anthropic/claude-3-haiku"

    def test_update_config_persists(self, tmp_project: Path):
        """update_config writes to YAML and reloads."""
        registry = ModelConfigRegistry(tmp_project)

        registry.update_config(
            default_model="openai/gpt-4o",
            model_overrides={"writing_agent": {"model": "openai/gpt-4o-mini"}},
        )

        # Re-read from disk
        registry2 = ModelConfigRegistry(tmp_project)
        assert registry2.project_config.default_model == "openai/gpt-4o"
        result = registry2.resolve(agent_id="writing_agent")
        assert result.model == "openai/gpt-4o-mini"

    def test_missing_yaml_uses_defaults(self, tmp_path: Path):
        """When no antigravity.yaml exists, use built-in defaults."""
        registry = ModelConfigRegistry(tmp_path)
        result = registry.resolve()
        assert result.model == "gemini/gemini-2.0-flash"

        result2 = registry.resolve(agent_id="writing_agent")
        assert result2.model == "anthropic/claude-3.5-sonnet"  # Built-in default
