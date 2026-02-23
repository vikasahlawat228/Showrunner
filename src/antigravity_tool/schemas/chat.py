"""Chat system schemas for the Agentic Chat System (Phase J)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from antigravity_tool.schemas.base import AntigravityBase


# ── Enums ──────────────────────────────────────────────────────

class SessionState(str, Enum):
    """Chat session lifecycle states."""
    ACTIVE = "active"
    COMPACTED = "compacted"
    ENDED = "ended"


class AutonomyLevel(int, Enum):
    """How much freedom the chat agent has to act."""
    ASK = 0       # Propose every action, wait for approval
    SUGGEST = 1   # Propose and execute on "yes", explain on ambiguity
    EXECUTE = 2   # Act immediately for routine ops, pause for destructive actions


# ── Core Chat Models ───────────────────────────────────────────

class ChatSession(AntigravityBase):
    """A chat conversation session within a project."""
    name: str = ""
    project_id: str = ""
    state: SessionState = SessionState.ACTIVE
    autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST
    message_ids: List[str] = Field(default_factory=list)
    context_budget: int = 100_000
    token_usage: int = 0
    digest: Optional[str] = None
    compaction_count: int = 0
    background_tasks: List["BackgroundTask"] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ChatMessage(AntigravityBase):
    """A single message in a chat session."""
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    action_traces: List["ChatActionTrace"] = Field(default_factory=list)
    artifacts: List["ChatArtifact"] = Field(default_factory=list)
    mentioned_entity_ids: List[str] = Field(default_factory=list)
    approval_state: Optional[Literal["pending", "approved", "rejected"]] = None


class ChatSessionSummary(BaseModel):
    """Lightweight session info for the SessionPicker."""
    id: str
    name: str
    state: SessionState
    message_count: int
    context_budget: int = 100_000
    created_at: str
    updated_at: str
    tags: List[str] = Field(default_factory=list)
    last_message_preview: str = ""


# ── Glass Box Transparency ────────────────────────────────────

class ChatActionTrace(BaseModel):
    """Glass Box trace for a single agent/tool action within a message."""
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    parent_id: Optional[str] = None
    tool_name: str
    agent_id: Optional[str] = None
    context_summary: str = ""
    containers_used: List[str] = Field(default_factory=list)
    model_used: str = ""
    duration_ms: int = 0
    token_usage_in: int = 0
    token_usage_out: int = 0
    result_preview: str = ""
    prompt: Optional[str] = None
    raw_json: Optional[str] = None
    sub_invocations: List["AgentInvocation"] = Field(default_factory=list)


class AgentInvocation(BaseModel):
    """Record of one agent invoking another agent."""
    caller_agent_id: str
    callee_agent_id: str
    intent: str = ""
    depth: int = 0
    trace: Optional[ChatActionTrace] = None


# ── Artifacts ──────────────────────────────────────────────────

class ChatArtifact(BaseModel):
    """Generated content that can be previewed in the Artifact Preview panel."""
    artifact_type: Literal["prose", "outline", "schema", "panel", "diff", "table", "yaml", "pipeline_run"]
    title: str
    content: str
    container_id: Optional[str] = None
    is_saved: bool = False


# ── Compaction ─────────────────────────────────────────────────

class ChatCompactionResult(BaseModel):
    """Result of a /compact operation."""
    digest: str
    original_message_count: int
    token_reduction: int
    preserved_entities: List[str] = Field(default_factory=list)
    compaction_number: int


# ── Background Tasks ──────────────────────────────────────────

class BackgroundTask(BaseModel):
    """Tracks a background operation running within a chat session."""
    task_id: str
    task_type: Literal["pipeline", "research", "bulk_create", "analysis"]
    label: str
    pipeline_run_id: Optional[str] = None
    progress: float = 0.0
    state: Literal["running", "paused", "completed", "failed"] = "running"


# ── Intent Classification ─────────────────────────────────────

class ToolIntent(BaseModel):
    """Classified intent from a user message."""
    tool: str
    confidence: float = 0.0
    params: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


# ── SSE Events ─────────────────────────────────────────────────

class ChatEvent(BaseModel):
    """SSE event streamed to the frontend during message processing."""
    event_type: Literal[
        "token",
        "action_trace",
        "artifact",
        "approval_needed",
        "background_update",
        "complete",
        "error",
    ]
    data: Dict[str, Any] = Field(default_factory=dict)


# Pydantic model rebuild for forward references
ChatSession.model_rebuild()
ChatMessage.model_rebuild()
ChatActionTrace.model_rebuild()
