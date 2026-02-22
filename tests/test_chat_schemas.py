"""Phase J: Chat and Project Memory schema validation tests.

Tests cover all models in schemas/chat.py and schemas/project_memory.py.
"""

import pytest

from antigravity_tool.schemas.chat import (
    AgentInvocation,
    AutonomyLevel,
    BackgroundTask,
    ChatActionTrace,
    ChatArtifact,
    ChatCompactionResult,
    ChatEvent,
    ChatMessage,
    ChatSession,
    ChatSessionSummary,
    SessionState,
    ToolIntent,
)
from antigravity_tool.schemas.project_memory import (
    MemoryEntry,
    MemoryScope,
    ProjectMemory,
)


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestEnums:
    def test_session_state_values(self):
        assert SessionState.ACTIVE == "active"
        assert SessionState.COMPACTED == "compacted"
        assert SessionState.ENDED == "ended"

    def test_autonomy_level_values(self):
        assert AutonomyLevel.ASK == 0
        assert AutonomyLevel.SUGGEST == 1
        assert AutonomyLevel.EXECUTE == 2

    def test_memory_scope_values(self):
        assert MemoryScope.GLOBAL == "global"
        assert MemoryScope.CHAPTER == "chapter"
        assert MemoryScope.SCENE == "scene"
        assert MemoryScope.CHARACTER == "character"


# ═══════════════════════════════════════════════════════════════════
# ChatSession
# ═══════════════════════════════════════════════════════════════════


class TestChatSession:
    def test_defaults(self):
        session = ChatSession()
        assert session.name == ""
        assert session.state == SessionState.ACTIVE
        assert session.autonomy_level == AutonomyLevel.SUGGEST
        assert session.message_ids == []
        assert session.context_budget == 100_000
        assert session.token_usage == 0
        assert session.digest is None
        assert session.compaction_count == 0
        assert session.tags == []
        # From AntigravityBase
        assert session.id is not None
        assert session.created_at is not None

    def test_custom_values(self):
        session = ChatSession(
            name="Writing Ch.3",
            project_id="proj_01",
            autonomy_level=AutonomyLevel.EXECUTE,
            tags=["chapter3", "action"],
        )
        assert session.name == "Writing Ch.3"
        assert session.autonomy_level == AutonomyLevel.EXECUTE

    def test_roundtrip(self):
        session = ChatSession(name="Test", project_id="p1")
        data = session.model_dump(mode="json")
        restored = ChatSession(**data)
        assert restored.name == session.name
        assert restored.id == session.id


# ═══════════════════════════════════════════════════════════════════
# ChatMessage
# ═══════════════════════════════════════════════════════════════════


class TestChatMessage:
    def test_required_fields(self):
        msg = ChatMessage(session_id="s1", role="user", content="Hello!")
        assert msg.session_id == "s1"
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert msg.action_traces == []
        assert msg.artifacts == []
        assert msg.approval_state is None

    def test_assistant_message(self):
        msg = ChatMessage(
            session_id="s1", role="assistant",
            content="Here's the scene...",
            mentioned_entity_ids=["char_01", "scene_05"],
        )
        assert msg.role == "assistant"
        assert len(msg.mentioned_entity_ids) == 2

    def test_invalid_role(self):
        with pytest.raises(Exception):
            ChatMessage(session_id="s1", role="invalid", content="nope")

    def test_approval_states(self):
        for state in ("pending", "approved", "rejected"):
            msg = ChatMessage(
                session_id="s1", role="assistant", content="x",
                approval_state=state,
            )
            assert msg.approval_state == state


# ═══════════════════════════════════════════════════════════════════
# ChatSessionSummary
# ═══════════════════════════════════════════════════════════════════


class TestChatSessionSummary:
    def test_creation(self):
        summary = ChatSessionSummary(
            id="s1", name="Session 1", state=SessionState.ACTIVE,
            message_count=42, created_at="2025-01-01", updated_at="2025-01-02",
            last_message_preview="What about the...",
        )
        assert summary.message_count == 42
        assert summary.last_message_preview == "What about the..."


# ═══════════════════════════════════════════════════════════════════
# Glass Box: ChatActionTrace + AgentInvocation
# ═══════════════════════════════════════════════════════════════════


class TestChatActionTrace:
    def test_simple_trace(self):
        trace = ChatActionTrace(
            tool_name="WRITE",
            context_summary="Writing scene 3 with character context",
            model_used="gemini/gemini-2.0-flash",
            duration_ms=1200,
            token_usage_in=5000,
            token_usage_out=800,
        )
        assert trace.tool_name == "WRITE"
        assert trace.duration_ms == 1200

    def test_with_sub_invocations(self):
        sub = AgentInvocation(
            caller_agent_id="continuity",
            callee_agent_id="search",
            intent="Find previous mentions of the artifact",
            depth=1,
        )
        trace = ChatActionTrace(
            tool_name="EVALUATE",
            sub_invocations=[sub],
        )
        assert len(trace.sub_invocations) == 1
        assert trace.sub_invocations[0].depth == 1

    def test_nested_trace(self):
        inner_trace = ChatActionTrace(tool_name="SEARCH", duration_ms=50)
        invocation = AgentInvocation(
            caller_agent_id="writer", callee_agent_id="search",
            depth=1, trace=inner_trace,
        )
        assert invocation.trace.tool_name == "SEARCH"


# ═══════════════════════════════════════════════════════════════════
# ChatArtifact
# ═══════════════════════════════════════════════════════════════════


class TestChatArtifact:
    def test_all_types(self):
        for art_type in ("prose", "outline", "schema", "panel", "diff", "table", "yaml"):
            artifact = ChatArtifact(
                artifact_type=art_type, title=f"Test {art_type}",
                content="sample content",
            )
            assert artifact.artifact_type == art_type
            assert artifact.is_saved is False

    def test_saved_artifact(self):
        artifact = ChatArtifact(
            artifact_type="prose", title="Scene 3", content="...",
            container_id="scene_03", is_saved=True,
        )
        assert artifact.is_saved is True
        assert artifact.container_id == "scene_03"


# ═══════════════════════════════════════════════════════════════════
# ChatCompactionResult
# ═══════════════════════════════════════════════════════════════════


class TestChatCompactionResult:
    def test_creation(self):
        result = ChatCompactionResult(
            digest="Summary of 50 messages...",
            original_message_count=50,
            token_reduction=40000,
            preserved_entities=["char_01", "scene_05"],
            compaction_number=1,
        )
        assert result.token_reduction == 40000
        assert len(result.preserved_entities) == 2


# ═══════════════════════════════════════════════════════════════════
# BackgroundTask
# ═══════════════════════════════════════════════════════════════════


class TestBackgroundTask:
    def test_defaults(self):
        task = BackgroundTask(
            task_id="run_01", task_type="pipeline", label="Scene→Panels",
        )
        assert task.progress == 0.0
        assert task.state == "running"
        assert task.pipeline_run_id is None

    def test_all_task_types(self):
        for tt in ("pipeline", "research", "bulk_create", "analysis"):
            task = BackgroundTask(task_id="t1", task_type=tt, label="Test")
            assert task.task_type == tt

    def test_all_states(self):
        for st in ("running", "paused", "completed", "failed"):
            task = BackgroundTask(
                task_id="t1", task_type="pipeline", label="x", state=st,
            )
            assert task.state == st


# ═══════════════════════════════════════════════════════════════════
# ToolIntent
# ═══════════════════════════════════════════════════════════════════


class TestToolIntent:
    def test_defaults(self):
        intent = ToolIntent(tool="SEARCH")
        assert intent.confidence == 0.0
        assert intent.params == {}
        assert intent.requires_approval is False

    def test_with_params(self):
        intent = ToolIntent(
            tool="PIPELINE", confidence=0.95,
            params={"pipeline_name": "Scene→Panels", "target": "Ch.3 Sc.1"},
            requires_approval=True,
        )
        assert intent.confidence == 0.95
        assert intent.requires_approval is True


# ═══════════════════════════════════════════════════════════════════
# ChatEvent
# ═══════════════════════════════════════════════════════════════════


class TestChatEvent:
    def test_all_event_types(self):
        for et in ("token", "action_trace", "artifact", "approval_needed",
                    "background_update", "complete", "error"):
            event = ChatEvent(event_type=et, data={"key": "value"})
            assert event.event_type == et

    def test_invalid_event_type(self):
        with pytest.raises(Exception):
            ChatEvent(event_type="invalid_type")


# ═══════════════════════════════════════════════════════════════════
# MemoryEntry
# ═══════════════════════════════════════════════════════════════════


class TestMemoryEntry:
    def test_defaults(self):
        entry = MemoryEntry(key="tone", value="Dark fantasy, bleak")
        assert entry.scope == MemoryScope.GLOBAL
        assert entry.scope_id is None
        assert entry.source == "user_decision"
        assert entry.auto_inject is True
        assert entry.created_at != ""

    def test_scoped_entry(self):
        entry = MemoryEntry(
            key="pov", value="First person",
            scope=MemoryScope.CHAPTER, scope_id="ch_03",
        )
        assert entry.scope == MemoryScope.CHAPTER
        assert entry.scope_id == "ch_03"


# ═══════════════════════════════════════════════════════════════════
# ProjectMemory
# ═══════════════════════════════════════════════════════════════════


class TestProjectMemory:
    def _make_memory(self):
        return ProjectMemory(entries=[
            MemoryEntry(key="tone", value="Dark fantasy"),
            MemoryEntry(key="pov", value="Third person limited", auto_inject=True),
            MemoryEntry(key="draft_note", value="Fix later", auto_inject=False),
            MemoryEntry(key="ch3_rule", value="No flashbacks",
                        scope=MemoryScope.CHAPTER, scope_id="ch_03"),
        ])

    def test_get_auto_inject_entries(self):
        mem = self._make_memory()
        auto = mem.get_auto_inject_entries()
        assert len(auto) == 3  # tone, pov, ch3_rule (all auto_inject=True)
        keys = [e.key for e in auto]
        assert "draft_note" not in keys

    def test_get_auto_inject_filtered_by_scope(self):
        mem = self._make_memory()
        chapter = mem.get_auto_inject_entries(scope=MemoryScope.CHAPTER)
        assert len(chapter) == 1
        assert chapter[0].key == "ch3_rule"

    def test_get_auto_inject_filtered_by_scope_id(self):
        mem = self._make_memory()
        results = mem.get_auto_inject_entries(scope_id="ch_03")
        assert len(results) == 1

    def test_to_context_string(self):
        mem = self._make_memory()
        ctx = mem.to_context_string()
        assert "## Project Memory" in ctx
        assert "**tone**" in ctx
        assert "**pov**" in ctx
        assert "draft_note" not in ctx  # auto_inject=False

    def test_to_context_string_empty(self):
        mem = ProjectMemory(entries=[])
        assert mem.to_context_string() == ""

    def test_roundtrip(self):
        mem = self._make_memory()
        data = mem.model_dump(mode="json")
        restored = ProjectMemory(**data)
        assert len(restored.entries) == 4
        assert restored.entries[0].key == "tone"
