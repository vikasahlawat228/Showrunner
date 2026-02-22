"""Tests for ContextAssembler — unified context compilation pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from antigravity_tool.schemas.dal import ContextScope, ProjectSnapshot
from antigravity_tool.services.context_assembler import (
    STEP_TEMPLATE_MAP,
    ContextAssembler,
    ContextResult,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


def _make_snapshot(**overrides) -> ProjectSnapshot:
    """Create a ProjectSnapshot with sensible defaults."""
    defaults = {
        "world": {"name": "Aetheria", "genre": "fantasy"},
        "characters": [
            {"name": "Zara", "role": "protagonist"},
            {"name": "Kael", "role": "antagonist"},
        ],
        "story_structure": {"type": "three_act", "acts": 3},
        "scenes": [{"title": "The Arrival", "chapter": 1}],
        "load_time_ms": 42,
        "entities_loaded": 5,
        "cache_hits": 3,
        "cache_misses": 2,
    }
    defaults.update(overrides)
    return ProjectSnapshot(**defaults)


@pytest.fixture
def mock_snapshot_factory():
    """Factory that returns a pre-built snapshot."""
    factory = MagicMock()
    factory.load.return_value = _make_snapshot()
    return factory


@pytest.fixture
def assembler(mock_snapshot_factory):
    return ContextAssembler(mock_snapshot_factory)


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestStepTemplateMap:
    """STEP_TEMPLATE_MAP should cover the key workflow steps."""

    def test_has_core_steps(self):
        for step in ["world_building", "scene_writing", "panel_composition"]:
            assert step in STEP_TEMPLATE_MAP

    def test_templates_are_jinja2(self):
        for template_path in STEP_TEMPLATE_MAP.values():
            assert template_path.endswith(".md.j2")


class TestStructuredOutput:
    """Default output format is 'structured' markdown."""

    def test_compile_returns_context_result(self, assembler):
        scope = ContextScope(step="scene_writing", output_format="structured")
        result = assembler.compile(scope)

        assert isinstance(result, ContextResult)
        assert result.text
        assert result.token_estimate > 0

    def test_structured_includes_section_headers(self, assembler):
        scope = ContextScope(step="scene_writing", output_format="structured")
        result = assembler.compile(scope)

        # Should have markdown headers for each context bucket
        assert "# Context for" in result.text
        assert "World" in result.text
        assert "Characters" in result.text

    def test_structured_includes_character_names(self, assembler):
        scope = ContextScope(step="scene_writing", output_format="structured")
        result = assembler.compile(scope)

        assert "Zara" in result.text
        assert "Kael" in result.text


class TestRawOutput:
    """raw output format should produce JSON."""

    def test_raw_output_is_json(self, assembler):
        scope = ContextScope(step="scene_writing", output_format="raw")
        result = assembler.compile(scope)

        import json
        data = json.loads(result.text)
        assert "world" in data
        assert "characters" in data


class TestTemplateOutput:
    """template output falls back to structured when no template engine."""

    def test_template_without_engine_falls_back_to_structured(self, assembler):
        scope = ContextScope(step="scene_writing", output_format="template")
        result = assembler.compile(scope)

        # Without template engine, should fall back to structured
        assert "# Context for" in result.text

    def test_template_with_engine_renders(self, mock_snapshot_factory):
        engine = MagicMock()
        engine.render.return_value = "# Rendered Template\nHello world"

        assembler = ContextAssembler(mock_snapshot_factory, template_engine=engine)
        scope = ContextScope(step="scene_writing", output_format="template")
        result = assembler.compile(scope)

        assert "Rendered Template" in result.text
        engine.render.assert_called_once()


class TestTokenBudget:
    """Token budget should limit context size."""

    def test_large_budget_includes_everything(self, assembler):
        scope = ContextScope(step="scene_writing", token_budget=1_000_000)
        result = assembler.compile(scope)

        assert "World" in result.text
        assert "Characters" in result.text

    def test_tiny_budget_truncates(self, mock_snapshot_factory):
        # Create a snapshot with lots of content
        snapshot = _make_snapshot(
            world={"name": "Aetheria", "description": "A" * 2000},
            characters=[{"name": f"Char{i}", "bio": "B" * 1000} for i in range(10)],
        )
        mock_snapshot_factory.load.return_value = snapshot

        assembler = ContextAssembler(mock_snapshot_factory)
        scope = ContextScope(step="scene_writing", token_budget=100)
        result = assembler.compile(scope)

        # Should have glass box entries showing truncation
        assert len(result.glass_box) > 0


class TestGlassBoxMetadata:
    """ContextResult should include Glass Box transparency info."""

    def test_glass_box_has_entries(self, assembler):
        scope = ContextScope(step="scene_writing")
        result = assembler.compile(scope)

        assert len(result.glass_box) > 0
        bucket = result.glass_box[0]
        assert bucket.name
        assert bucket.tokens > 0

    def test_cache_hit_rate_propagated(self, assembler):
        scope = ContextScope(step="scene_writing")
        result = assembler.compile(scope)

        # 3 hits / 5 total = 0.6
        assert result.cache_hit_rate == pytest.approx(0.6)

    def test_load_time_propagated(self, assembler):
        scope = ContextScope(step="scene_writing")
        result = assembler.compile(scope)

        assert result.load_time_ms == 42


class TestDecisionInjection:
    """Decisions from DecisionLog should be injected into context."""

    def test_decisions_included_when_decision_log_present(self, mock_snapshot_factory):
        decision_log = MagicMock()
        decision_obj = MagicMock()
        decision_obj.decision = "Dark fantasy tone"
        decision_log.query.return_value = [decision_obj]

        assembler = ContextAssembler(mock_snapshot_factory, decision_log=decision_log)
        scope = ContextScope(step="scene_writing", output_format="structured")
        result = assembler.compile(scope)

        assert "Dark fantasy tone" in result.text

    def test_no_decisions_when_log_returns_empty(self, mock_snapshot_factory):
        decision_log = MagicMock()
        decision_log.query.return_value = []

        assembler = ContextAssembler(mock_snapshot_factory, decision_log=decision_log)
        scope = ContextScope(step="scene_writing")
        result = assembler.compile(scope)

        # Should still work fine, just no decisions section
        assert isinstance(result, ContextResult)

    def test_decision_log_failure_is_graceful(self, mock_snapshot_factory):
        decision_log = MagicMock()
        decision_log.query.side_effect = RuntimeError("DB down")

        assembler = ContextAssembler(mock_snapshot_factory, decision_log=decision_log)
        scope = ContextScope(step="scene_writing")
        result = assembler.compile(scope)

        # Should not crash
        assert isinstance(result, ContextResult)


class TestContextIsolation:
    """Creative room data should respect access level."""

    def test_creative_room_excluded_at_story_level(self, mock_snapshot_factory):
        snapshot = _make_snapshot(
            creative_room={"secrets": ["the villain is the hero's father"]},
        )
        mock_snapshot_factory.load.return_value = snapshot

        assembler = ContextAssembler(mock_snapshot_factory)
        scope = ContextScope(step="scene_writing", access_level="story")
        result = assembler.compile(scope)

        # creative_room should not appear in story-level context
        assert "villain is the hero" not in result.text

    def test_creative_room_included_at_author_level(self, mock_snapshot_factory):
        snapshot = _make_snapshot(
            creative_room={"secrets": ["the villain is the hero's father"]},
        )
        mock_snapshot_factory.load.return_value = snapshot

        assembler = ContextAssembler(mock_snapshot_factory)
        scope = ContextScope(step="evaluation", access_level="author")
        result = assembler.compile(scope)

        assert "villain" in result.text


class TestTokenEstimation:
    """Token estimation should be reasonable (~4 chars per token)."""

    def test_empty_text_zero_tokens(self, assembler):
        assert assembler._estimate_tokens("") == 0

    def test_reasonable_estimate(self, assembler):
        text = "Hello, world!" * 100  # 1300 chars
        estimate = assembler._estimate_tokens(text)
        assert 300 <= estimate <= 400  # ~325 expected
