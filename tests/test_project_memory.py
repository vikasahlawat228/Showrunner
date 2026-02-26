"""Tests for ProjectMemoryService — CRUD, scoped queries, auto-injection."""

from __future__ import annotations

import pytest

from showrunner_tool.schemas.project_memory import MemoryEntry, MemoryScope
from showrunner_tool.services.project_memory_service import ProjectMemoryService


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def svc(tmp_path):
    """ProjectMemoryService with a temp project path."""
    return ProjectMemoryService(tmp_path)


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestAddEntry:
    def test_add_returns_entry(self, svc):
        entry = svc.add_entry("tone", "Dark fantasy")
        assert isinstance(entry, MemoryEntry)
        assert entry.key == "tone"
        assert entry.value == "Dark fantasy"

    def test_add_persists_to_disk(self, svc, tmp_path):
        svc.add_entry("tone", "Dark fantasy")

        # Reload from scratch
        svc2 = ProjectMemoryService(tmp_path)
        entries = svc2.get_entries()
        assert len(entries) == 1
        assert entries[0].key == "tone"

    def test_add_with_scope(self, svc):
        entry = svc.add_entry(
            "villain_motivation", "Revenge",
            scope=MemoryScope.CHARACTER,
            scope_id="char_villain",
        )
        assert entry.scope == MemoryScope.CHARACTER
        assert entry.scope_id == "char_villain"

    def test_add_multiple_entries(self, svc):
        svc.add_entry("tone", "Dark")
        svc.add_entry("style", "Manhwa")
        svc.add_entry("pacing", "Fast")

        entries = svc.get_entries()
        assert len(entries) == 3


class TestGetEntries:
    def test_get_empty(self, svc):
        assert svc.get_entries() == []

    def test_filter_by_scope(self, svc):
        svc.add_entry("global_rule", "No info dumps", scope=MemoryScope.GLOBAL)
        svc.add_entry("ch1_tone", "Mysterious", scope=MemoryScope.CHAPTER, scope_id="ch1")
        svc.add_entry("ch2_tone", "Action", scope=MemoryScope.CHAPTER, scope_id="ch2")

        chapters = svc.get_entries(scope=MemoryScope.CHAPTER)
        assert len(chapters) == 2

        globals_ = svc.get_entries(scope=MemoryScope.GLOBAL)
        assert len(globals_) == 1

    def test_filter_by_scope_id(self, svc):
        svc.add_entry("ch1_tone", "Mysterious", scope=MemoryScope.CHAPTER, scope_id="ch1")
        svc.add_entry("ch2_tone", "Action", scope=MemoryScope.CHAPTER, scope_id="ch2")

        ch1 = svc.get_entries(scope_id="ch1")
        assert len(ch1) == 1
        assert ch1[0].value == "Mysterious"

    def test_auto_inject_only(self, svc):
        svc.add_entry("visible", "Show this", auto_inject=True)
        svc.add_entry("hidden", "Hide this", auto_inject=False)

        visible = svc.get_entries(auto_inject_only=True)
        assert len(visible) == 1
        assert visible[0].key == "visible"


class TestGetEntryByKey:
    def test_found(self, svc):
        svc.add_entry("tone", "Dark")
        entry = svc.get_entry_by_key("tone")
        assert entry is not None
        assert entry.value == "Dark"

    def test_not_found(self, svc):
        assert svc.get_entry_by_key("nonexistent") is None


class TestUpdateEntry:
    def test_update_existing(self, svc):
        svc.add_entry("tone", "Light")
        result = svc.update_entry("tone", "Dark")
        assert result is not None
        assert result.value == "Dark"

        # Verify persistence
        entry = svc.get_entry_by_key("tone")
        assert entry.value == "Dark"

    def test_update_nonexistent_returns_none(self, svc):
        result = svc.update_entry("ghost", "value")
        assert result is None


class TestDeleteEntry:
    def test_delete_existing(self, svc):
        svc.add_entry("tone", "Dark")
        assert svc.delete_entry("tone") is True
        assert svc.get_entry_by_key("tone") is None

    def test_delete_nonexistent(self, svc):
        assert svc.delete_entry("ghost") is False


class TestContextString:
    def test_empty_returns_empty_string(self, svc):
        assert svc.to_context_string() == ""

    def test_renders_auto_inject_entries(self, svc):
        svc.add_entry("tone", "Dark fantasy")
        svc.add_entry("pacing", "Fast")
        svc.add_entry("hidden", "Secret", auto_inject=False)

        ctx = svc.to_context_string()
        assert "Project Memory" in ctx
        assert "tone" in ctx
        assert "Dark fantasy" in ctx
        assert "pacing" in ctx
        assert "Secret" not in ctx

    def test_scope_label_included(self, svc):
        svc.add_entry("ch_tone", "Mysterious", scope=MemoryScope.CHAPTER)
        ctx = svc.to_context_string()
        assert "[chapter]" in ctx


class TestClearAll:
    def test_clear_all(self, svc):
        svc.add_entry("a", "1")
        svc.add_entry("b", "2")

        count = svc.clear_all()
        assert count == 2
        assert svc.get_entries() == []
