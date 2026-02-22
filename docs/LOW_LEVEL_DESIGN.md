# Showrunner Low-Level Design Document
**Status:** Phase F–K Blueprint (supersedes Alpha v2.0)
**Last Updated:** 2026-02-22

---

## 1. Project Structure

### 1.1 Root Layout

```
writing_tool/
├── docs/                               # Documentation
│   ├── PRD.md                          # Product Requirements
│   ├── DESIGN.md                       # High-Level Architecture (Phase F–I)
│   ├── LOW_LEVEL_DESIGN.md             # This file
│   ├── ROADMAP_PHASE_D.md             # Phase D roadmap
│   ├── ROADMAP_PHASE_E.md             # Phase E roadmap
│   └── VISION.md                       # Product vision
├── agents/
│   ├── skills/                         # AI agent system prompts (12 total)
│   └── tasks/                          # Outsourced session prompts
├── schemas/                            # User-defined ContainerSchema YAMLs
├── characters/                         # Character instance YAMLs
├── src/
│   ├── antigravity_tool/               # Python backend
│   │   ├── schemas/                    # Pydantic model files
│   │   ├── services/                   # Service layer
│   │   ├── repositories/              # YAML, SQLite, Event Sourcing, ChromaDB repos
│   │   └── server/                     # FastAPI app + routers
│   └── web/                            # Next.js frontend
│       ├── src/app/                    # Route pages
│       ├── src/components/            # Component groups
│       └── src/lib/                    # API client + Zustand stores
├── antigravity.yaml                    # Project manifest + model config
└── CLAUDE.md                           # Agent briefing
```

### 1.2 Multi-Project Data Isolation (Phase F)

Each project lives in its own directory with fully self-contained persistence:

```
~/projects/midnight-chronicle/          # Project root
├── antigravity.yaml                    # Project manifest + model_overrides
├── schemas/                            # ContainerSchema YAML files
│   ├── character.yaml
│   ├── location.yaml
│   ├── season.yaml
│   ├── research_topic.yaml
│   └── ...
├── containers/                         # GenericContainer instances grouped by type
│   ├── character/
│   │   ├── zara.yaml
│   │   └── kael.yaml
│   ├── season/
│   │   └── season-1.yaml
│   ├── arc/
│   │   └── the-awakening.yaml
│   ├── chapter/
│   │   └── chapter-1.yaml
│   ├── scene/
│   │   └── scene-1.yaml
│   ├── research_topic/
│   │   └── railgun-physics.yaml
│   ├── fragment/
│   │   └── draft-fragment-01.yaml
│   ├── panel/
│   │   └── panel-1.yaml
│   └── pipeline/
│       └── scene-to-panels.yaml
├── characters/                         # Legacy character YAML (still read by CharacterService)
├── world/                              # Legacy world data
├── knowledge_graph.db                  # SQLite relational index
├── event_log.db                        # SQLite event sourcing DAG
├── .chroma/                            # ChromaDB vector embeddings (project-scoped)
├── .antigravity/                       # Internal state
│   ├── decisions.yaml                  # Cross-session decision log
│   └── sessions/                       # Session logs
└── agents/skills/                      # Agent system prompts
```

**Key rules:**
- `knowledge_graph.db`, `event_log.db`, and `.chroma/` are scoped per-project directory.
- `ContainerRepository` resolves paths relative to the project root: `{project_root}/containers/{container_type}/{slug}.yaml`.
- Multi-project switching requires `get_project(project_id)` to return a `Project` pointing at the correct root.

### 1.3 Frontend Route Structure

```
src/web/src/app/
├── layout.tsx                          # Root layout (Zustand provider)
├── page.tsx                            # Redirect → /dashboard
├── dashboard/page.tsx                  # KG Canvas + Command Center overview
├── schemas/page.tsx                    # Schema Builder UI
├── zen/page.tsx                        # Writing Desk (TipTap editor)
├── pipelines/page.tsx                  # Workflow Studio + Template Gallery
├── storyboard/page.tsx                 # Storyboard Canvas (Strip + Semantic)
├── timeline/page.tsx                   # Story Timeline (branch visualization + structure tree)
├── preview/page.tsx                    # Reader Scroll Simulation (Phase Next-C)
├── research/page.tsx                   # Research Library (Phase Next-D)
├── brainstorm/page.tsx                 # Spatial Brainstorming Canvas (Phase Next-E)
└── settings/page.tsx                   # Project settings + model config (Phase F)
```

---

## 2. Backend Modules

### 2.1 Pydantic Models (`schemas/`)

| File | Key Models | Notes | Phase |
|------|-----------|-------|:-----:|
| `base.py` | `AntigravityBase` | ULID `id`, `created_at`, `updated_at`, `schema_version` — base for all domain objects | Core |
| `container.py` | `FieldType` (8 variants), `FieldDefinition`, `ContainerSchema`, `GenericContainer` | Universal Bucket model — see §2.2 for Phase F additions | Core+F |
| `pipeline.py` | `PipelineState`, `PipelineRun`, `PipelineRunCreate`, `PipelineResume` | Pipeline execution state machine | Core |
| `pipeline_steps.py` | `StepType` (17 types), `StepCategory` (5 categories), `STEP_REGISTRY`, `PipelineStepDef`, `PipelineEdge`, `PipelineDefinition`, `PipelineDefinitionCreate`, `PipelineDefinitionResponse`, `StepRegistryEntry` | Composable pipeline DAG — see §2.3 for Phase G logic node additions | Core+B+G |
| `prompt_templates.py` | `PromptSlot`, `PromptTemplate`, `PromptTemplateCreate`, `PromptTemplateResponse` | Handlebars-style rendering with slot injection | B |
| `fragment.py` | `WritingFragment`, `FragmentCreateRequest`, `FragmentResponse`, `EntityDetectionRequest`, `EntityDetection`, `EntityDetectionResponse`, `ContainerContextResponse` | Zen Mode text chunks + entity detection | A |
| `storyboard.py` | `PanelType`, `CameraAngle`, `Panel`, `StoryboardPage`, `PanelCreate`, `PanelUpdate`, `PanelReorder`, `PanelResponse`, `GeneratePanelsRequest` | Storyboard panel CRUD models | C |
| `timeline.py` | `Timeline`, `TimelineUnit`, `TimelineEvent`, `TimelineIssue` | Event/branch models for Story Timeline | Core |
| `character.py` | `Character`, `CharacterDNA`, `CharacterRole`, `FacialFeatures`, `HairDescription`, `BodyDescription`, `OutfitCanon`, `Personality`, `CharacterArc`, `Relationship`, `RelationshipEdge`, `RelationshipGraph` | **DEPRECATED** — migrate instances to `GenericContainer` with `container_type: "character"` | Legacy |
| `world.py` | `WorldSettings`, `Location`, `WorldRule`, `Faction`, `HistoricalEvent` | **DEPRECATED** — migrate to `GenericContainer` buckets | Legacy |
| `scene.py` | `Scene`, `TimeOfDay`, `Weather`, `SceneType` | **DEPRECATED** — migrate to `GenericContainer` with `container_type: "scene"` | Legacy |
| `panel.py` | `Panel`, `ShotType`, `CameraAngle`, `PanelSize`, `PanelWidth` | Legacy panel model (superseded by `storyboard.py`) | Legacy |
| `screenplay.py` | `Screenplay`, `BeatType`, `ScreenplayBeat` | Screenplay beats | Core |
| `story_structure.py` | `StoryStructure`, `StructureType`, `StoryBeat`, `CharacterArcBeat`, `SubArc` | Story structure definitions | Core |
| `creative_room.py` | `CreativeRoom`, `PlotTwist`, `CharacterSecret`, `ForeshadowingEntry`, `TrueMechanic`, `ReaderKnowledgeState` | Context isolation: author-only data | Core |
| `pacing.py` | `PacingReport`, `PacingMetrics`, `PacingIssue` | Pacing analysis output | Core |
| `continuity.py` | `ContinuityReport`, `ContinuityIssue`, `DNADriftReport`, `DNADriftIssue`, `IssueSeverity` | Continuity validation results | Core |
| `evaluation.py` | `EvaluationResult`, `ScoreEntry` | AI output evaluation | Core |
| `session.py` | `SessionEntry`, `Decision`, `DecisionCategory`, `DecisionScope`, `SessionAction`, `ChapterSummary`, `ProjectBrief` | Cross-session persistence | Core |
| `analytics.py` | `AnalyticsReport`, `CharacterStats` | Reporting models | Core |
| `assets.py` | `ReferenceLibrary`, `ReferenceImage`, `ReferenceType` | Image reference library | Core |
| `style_guide.py` | `VisualStyleGuide`, `NarrativeStyleGuide` | Style guides | Core |
| `genre.py` | `GenrePreset` | Genre presets | Core |
| `chat.py` | `ChatMessage`, `ChatSession`, `ChatSessionSummary`, `ChatActionTrace`, `AgentInvocation`, `ChatArtifact`, `ChatCompactionResult`, `ChatEvent`, `ToolIntent`, `SessionState`, `AutonomyLevel`, `BackgroundTask` | Agentic Chat models — session, message, Glass Box trace, streaming events | J |
| `project_memory.py` | `ProjectMemory`, `MemoryEntry`, `MemoryScope` | Persistent project-level memory (decisions, world rules, style guide) — auto-injected into every chat context | J |
| `dal.py` | `SyncMetadata`, `CacheEntry`, `CacheStats`, `ContextScope`, `ProjectSnapshot`, `UnitOfWorkEntry`, `DBHealthReport` | Unified Data Access Layer models — caching, sync, batch loading, maintenance | K |

### 2.2 `GenericContainer` — Phase F Additions

The current `GenericContainer` in `src/antigravity_tool/schemas/container.py` has 4 fields: `container_type`, `name`, `attributes`, `relationships`. Phase F adds 6 new fields:

```python
# src/antigravity_tool/schemas/container.py — Phase F target state
class GenericContainer(AntigravityBase):
    """A polymorphic container instance that holds dynamic attributes."""

    container_type: str                       # References a ContainerSchema.name
    name: str                                 # Display name
    attributes: Dict[str, Any] = {}           # Dynamic EAV fields (JSON)
    relationships: List[Dict[str, Any]] = []  # Typed edges to other buckets

    # ── New in Phase F ──────────────────────────────────────────
    context_window: Optional[str] = None      # LLM-friendly auto-summary
    timeline_positions: List[str] = []        # Story positions: ["S1.Arc1.Act2.Ch3.Sc5"]
    tags: List[str] = []                      # Free-form labels: ["#act1", "#subplot-revenge"]
    model_preference: Optional[str] = None    # LiteLLM model override for this bucket
    parent_id: Optional[str] = None           # Hierarchical parent (e.g., Chapter → Act)
    sort_order: int = 0                       # Position among siblings
```

**What changes:**
- `parent_id` + `sort_order` enable the Season → Arc → Act → Chapter → Scene tree without separate models.
- `context_window` is an LLM-generated summary, auto-refreshed when attributes change.
- `timeline_positions` maps a container to its position(s) in the story timeline notation.
- `model_preference` feeds into the `ModelConfigRegistry` cascade.
- `tags` enable free-form filtering in the UI and pipeline gather steps.

**Legacy model deprecation strategy:**
- `character.py`, `world.py`, `scene.py` remain importable for backward compatibility but new data MUST use `GenericContainer`.
- `CharacterService` and `WorldService` become thin shims that read legacy YAML *and* new containers.

### 2.3 `PipelineStepDef` — Phase G Logic Node Additions

The current `StepType` enum in `src/antigravity_tool/schemas/pipeline_steps.py` has 11 step types across 4 categories. Phase G adds:

```python
# Added to StepType enum
class StepType(str, Enum):
    # ... existing 11 types ...

    # ── New in Phase G ──────────────────────────────────────────
    # Context nodes
    RESEARCH_LOOKUP = "research_lookup"        # Query Research Library

    # Human nodes
    SELECT_MODEL = "select_model"              # Writer changes model for next step

    # Execute nodes
    RESEARCH_DEEP_DIVE = "research_deep_dive"  # Invoke Research Agent

    # Logic nodes (NEW CATEGORY)
    IF_ELSE = "if_else"                        # Conditional branch on payload data
    LOOP = "loop"                              # Repeat subgraph N times or until condition
    MERGE_OUTPUTS = "merge_outputs"            # Combine outputs from parallel branches
```

```python
# Added to StepCategory enum
class StepCategory(str, Enum):
    CONTEXT = "context"
    TRANSFORM = "transform"
    HUMAN = "human"
    EXECUTE = "execute"
    LOGIC = "logic"                            # NEW
```

**Logic node execution:**
- `if_else`: Evaluates a JSONPath expression against the step payload. Routes to `true_target` or `false_target` edge based on result. Config: `{"condition": "$.payload.word_count > 500", "true_target": "step_5", "false_target": "step_6"}`.
- `loop`: Repeats connected subgraph. Config: `{"max_iterations": 3, "until_condition": "$.payload.approved == true"}`.
- `merge_outputs`: Collects outputs from multiple upstream edges into a single combined payload.

### 2.4 New Pydantic Models — Phase F–G

#### `ModelConfig` Classes (new file: `src/antigravity_tool/schemas/model_config.py`)

```python
class ModelConfig(BaseModel):
    """Configuration for a single model slot."""
    model: str                                # LiteLLM model string
    temperature: float = 0.7
    max_tokens: int = 2048
    fallback_model: Optional[str] = None      # Used if primary model fails

class ProjectModelConfig(BaseModel):
    """Project-level model configuration from antigravity.yaml."""
    default_model: str = "gemini/gemini-2.0-flash"
    model_overrides: Dict[str, ModelConfig] = {}  # Keyed by agent_id
```

#### `ContextResult` (existing: `src/antigravity_tool/services/context_engine.py`)

Already implemented as a dataclass:

```python
@dataclass
class ContextResult:
    text: str                     # The assembled context string
    token_estimate: int           # Estimated token count
    containers_included: int      # How many containers fit
    containers_truncated: int     # How many were cut for budget
    was_summarized: bool          # Whether LLM summarization was used
```

> **Phase F action:** Promote `ContextResult` from a dataclass to a Pydantic `BaseModel` in `schemas/` for API serialization, and add `source_container_ids: List[str]` for traceability.

### 2.5 Chat Pydantic Models — Phase J

#### Core Chat Models (`src/antigravity_tool/schemas/chat.py`)

```python
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel
from antigravity_tool.schemas.base import AntigravityBase


class SessionState(str, Enum):
    ACTIVE = "active"
    COMPACTED = "compacted"
    ENDED = "ended"


class AutonomyLevel(int, Enum):
    ASK = 0       # Propose every action, wait for approval
    SUGGEST = 1   # Propose and execute on "yes", explain on ambiguity
    EXECUTE = 2   # Act immediately for routine ops, pause for destructive actions


class ChatSession(AntigravityBase):
    """A chat conversation session within a project."""
    name: str                                    # User-provided or auto-generated name
    project_id: str                              # Project this session belongs to
    state: SessionState = SessionState.ACTIVE
    autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST
    message_ids: List[str] = []                  # Ordered message IDs (loaded on demand)
    context_budget: int = 100_000                # Max tokens for session context
    token_usage: int = 0                         # Current token usage
    digest: Optional[str] = None                 # Latest compaction digest
    compaction_count: int = 0                    # How many times /compact has been called
    background_tasks: List['BackgroundTask'] = []  # Running pipelines, research, etc.
    tags: List[str] = []                         # User-defined session tags


class ChatMessage(AntigravityBase):
    """A single message in a chat session."""
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str                                 # The text content
    action_traces: List['ChatActionTrace'] = []  # Glass Box traces for this message
    artifacts: List['ChatArtifact'] = []         # Generated content (prose, outlines, etc.)
    mentioned_entity_ids: List[str] = []         # Container IDs from @-mentions
    approval_state: Optional[Literal["pending", "approved", "rejected"]] = None


class ChatActionTrace(BaseModel):
    """Glass Box trace for a single agent/tool action within a message."""
    tool_name: str                               # WRITE, BRAINSTORM, PIPELINE, BUCKET, etc.
    agent_id: Optional[str] = None               # Which agent skill was invoked (if any)
    context_summary: str                         # Human-readable context description
    containers_used: List[str] = []              # Container IDs included in context
    model_used: str                              # LiteLLM model string (from cascade)
    duration_ms: int                             # Execution time
    token_usage_in: int = 0                      # Input tokens
    token_usage_out: int = 0                     # Output tokens
    result_preview: str = ""                     # Truncated result for display
    sub_invocations: List['AgentInvocation'] = []  # Agent-to-agent calls


class AgentInvocation(BaseModel):
    """Record of one agent invoking another agent."""
    caller_agent_id: str                         # Agent that initiated the call
    callee_agent_id: str                         # Agent that was invoked
    intent: str                                  # What the caller needed
    depth: int                                   # 0 = root, max 3
    trace: 'ChatActionTrace'                     # Full trace of the sub-invocation


class ChatArtifact(BaseModel):
    """Generated content that can be previewed in the Artifact Preview panel."""
    artifact_type: Literal["prose", "outline", "schema", "panel", "diff", "table", "yaml"]
    title: str
    content: str                                 # The generated content
    container_id: Optional[str] = None           # If saved as a container
    is_saved: bool = False


class ChatCompactionResult(BaseModel):
    """Result of a /compact operation."""
    digest: str                                  # LLM-generated summary (~2K tokens)
    original_message_count: int                  # Messages before compaction
    token_reduction: int                         # Tokens freed
    preserved_entities: List[str]                # Container IDs preserved in digest
    compaction_number: int                       # Which compaction this is (1, 2, 3...)


class ChatSessionSummary(BaseModel):
    """Lightweight session info for the SessionPicker."""
    id: str
    name: str
    state: SessionState
    message_count: int
    created_at: str
    updated_at: str
    tags: List[str] = []
    last_message_preview: str = ""


class BackgroundTask(BaseModel):
    """Tracks a background operation running within a chat session."""
    task_id: str
    task_type: Literal["pipeline", "research", "bulk_create", "analysis"]
    label: str                                   # Human-readable description
    pipeline_run_id: Optional[str] = None        # If task_type == "pipeline"
    progress: float = 0.0                        # 0.0 to 1.0
    state: Literal["running", "paused", "completed", "failed"] = "running"


class ToolIntent(BaseModel):
    """Classified intent from a user message."""
    tool: str                                    # Tool category (WRITE, PIPELINE, etc.)
    confidence: float                            # Classification confidence 0.0–1.0
    params: dict = {}                            # Extracted parameters
    requires_approval: bool = False              # Whether this action needs explicit approval


class ChatEvent(BaseModel):
    """SSE event streamed to the frontend during message processing."""
    event_type: Literal[
        "token",              # Partial response token
        "action_trace",       # Glass Box trace complete
        "artifact",           # Generated content ready for preview
        "approval_needed",    # Agent action needs writer approval
        "background_update",  # Background task progress
        "complete",           # Message processing finished
        "error",              # Error occurred
    ]
    data: dict                                   # Event-specific payload
```

#### Project Memory Models (`src/antigravity_tool/schemas/project_memory.py`)

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from antigravity_tool.schemas.base import AntigravityBase


class MemoryScope(str, Enum):
    GLOBAL = "global"          # Applies to entire project
    CHAPTER = "chapter"        # Applies to a specific chapter
    SCENE = "scene"            # Applies to a specific scene
    CHARACTER = "character"    # Applies to a specific character


class MemoryEntry(BaseModel):
    """A single persistent memory entry."""
    key: str                                     # Unique identifier (e.g., "tone", "pov-style")
    value: str                                   # The memory content
    scope: MemoryScope = MemoryScope.GLOBAL
    scope_id: Optional[str] = None               # Container ID for non-global scopes
    source: str = "user_decision"                # "user_decision", "agent_learned", "style_guide"
    auto_inject: bool = True                     # Include in every chat context?
    created_at: str = ""                         # ISO timestamp


class ProjectMemory(AntigravityBase):
    """Persistent project-level memory — auto-injected into every chat context."""
    entries: List[MemoryEntry] = []

    def get_auto_inject_entries(self, scope: Optional[MemoryScope] = None,
                                 scope_id: Optional[str] = None) -> List[MemoryEntry]:
        """Get all entries that should be auto-injected, optionally filtered by scope."""
        ...

    def to_context_string(self) -> str:
        """Render all auto-inject entries as a formatted context block."""
        ...
```

### 2.7 DAL Pydantic Models — Phase K

Located in `schemas/dal.py`. These models support the Unified Data Access Layer (§17 in DESIGN.md).

```python
"""Data Access Layer schemas — caching, sync, batch loading, maintenance."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Sync & Indexing ─────────────────────────────────────────────

class SyncMetadata(BaseModel):
    """Tracks the last-indexed state of a YAML file for incremental sync."""

    yaml_path: str                            # Absolute path to the YAML file
    entity_id: str                            # ID of the indexed entity
    entity_type: str                          # 'character', 'scene', 'container', etc.
    content_hash: str                         # SHA-256 of file content at index time
    mtime: float                              # os.stat().st_mtime at index time
    indexed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    file_size: int                            # Bytes — for quick change detection


# ── Caching ────────────────────────────────────────────────────

class CacheEntry(BaseModel, Generic[T]):
    """A single cached entity with mtime-based invalidation metadata."""

    entity: Any                               # The cached Pydantic model instance
    path: str                                 # Absolute YAML path
    mtime: float                              # File mtime when cached
    accessed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    size_bytes: int = 0                       # Approximate memory footprint


class CacheStats(BaseModel):
    """Cache performance metrics."""

    size: int = 0                             # Current entries in cache
    max_size: int = 500                       # Configured capacity
    hits: int = 0                             # Cache hit count
    misses: int = 0                           # Cache miss count
    evictions: int = 0                        # LRU eviction count
    hit_rate: float = 0.0                     # hits / (hits + misses)


# ── Context Assembly ────────────────────────────────────────────

class ContextScope(BaseModel):
    """Defines what context to assemble and how to render it."""

    step: str                                 # Workflow step: "scene_writing", "evaluation", etc.
    access_level: Literal["story", "author"] = "story"
    chapter: Optional[int] = None             # Scope to specific chapter
    scene: Optional[int] = None               # Scope to specific scene
    character_name: Optional[str] = None      # Scope to specific character
    token_budget: int = 100_000               # Max tokens for assembled context
    output_format: Literal["template", "structured", "raw"] = "template"
    include_relationships: bool = True        # Include 1-hop KG neighbors
    semantic_query: Optional[str] = None      # Optional semantic search query for RAG


class ProjectSnapshot(BaseModel):
    """Pre-loaded batch of entities for a given context scope.

    Assembled by ProjectSnapshotFactory.load() in a single pass
    through SQLite index + MtimeCache + YAML hydration.
    """

    world: Optional[Dict[str, Any]] = None
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    story_structure: Optional[Dict[str, Any]] = None
    scenes: List[Dict[str, Any]] = Field(default_factory=list)
    screenplays: List[Dict[str, Any]] = Field(default_factory=list)
    panels: List[Dict[str, Any]] = Field(default_factory=list)
    style_guides: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    reader_knowledge: Optional[Dict[str, Any]] = None
    creative_room: Optional[Dict[str, Any]] = None  # Only populated if access_level="author"

    # Load metrics (Glass Box)
    load_time_ms: int = 0
    entities_loaded: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


# ── Unit of Work ────────────────────────────────────────────────

class UnitOfWorkEntry(BaseModel):
    """A single buffered mutation in a UnitOfWork transaction."""

    operation: Literal["save", "delete"]
    entity_id: str
    entity_type: str
    yaml_path: str
    data: Optional[Dict[str, Any]] = None     # Serialized entity (for saves)
    event_type: Optional[Literal["CREATE", "UPDATE", "DELETE"]] = None
    event_payload: Optional[Dict[str, Any]] = None
    branch_id: str = "main"                    # Event sourcing branch


# ── DB Maintenance ──────────────────────────────────────────────

class DBHealthReport(BaseModel):
    """Comprehensive health check of the persistence layer."""

    entity_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Entity count by type: {'character': 5, 'scene': 12, ...}"
    )
    total_yaml_files: int = 0
    total_indexed: int = 0
    orphaned_indexes: int = 0                  # In SQLite but YAML file missing
    stale_entries: int = 0                     # On disk but not in SQLite
    mismatched_hashes: int = 0                 # YAML changed but index not updated
    disk_usage_bytes: int = 0                  # Total YAML file sizes
    index_size_bytes: int = 0                  # SQLite DB file size
    chroma_doc_count: int = 0                  # Documents in vector index
    event_count: int = 0                       # Events in event log
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    cache_stats: Optional[CacheStats] = None   # Current cache performance


class ConsistencyIssue(BaseModel):
    """A single YAML ↔ SQLite consistency issue found by db check."""

    issue_type: Literal["orphaned_index", "stale_file", "hash_mismatch", "missing_entity"]
    yaml_path: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    description: str
    auto_fixable: bool = True
```

---

## 3. Backend Modules: Repositories

### 3.1 Repository Inventory

| File | Class | Storage | Phase | Notes |
|------|-------|---------|:-----:|-------|
| `base.py` | `YAMLRepository[T]` | YAML files | Core | Generic base with `_on_save` / `_on_delete` callbacks |
| `container_repo.py` | `SchemaRepository` | YAML (`schemas/`) | Core | Stores `ContainerSchema` definitions |
| `container_repo.py` | `ContainerRepository` | YAML (`containers/{type}/`) | Core | **Primary write path** — all mutations flow through here |
| `sqlite_indexer.py` | `SQLiteIndexer` | `knowledge_graph.db` | Core | Two tables: `containers` (JSON1), `relationships` (graph edges) |
| `chroma_indexer.py` | `ChromaIndexer` | `.chroma/` directory | Core+H | Vector embeddings via `all-MiniLM-L6-v2`; RAG semantic search |
| `event_sourcing_repo.py` | `EventService` | `event_log.db` | Core | Append-only DAG: `events` + `branches` tables |
| `character_repo.py` | `CharacterRepository` | YAML (`characters/`) | Legacy | Thin wrapper; reads legacy character files |
| `world_repo.py` | `WorldRepository` | YAML (`world/`) | Legacy | Reads `settings.yaml`, `rules.yaml`, `history.yaml` |
| `story_repo.py` | `StoryRepository` | YAML | Legacy | Story structure data |
| `chapter_repo.py` | `ChapterRepository` | YAML | Legacy | Chapter/scene data |
| `style_repo.py` | `StyleRepository` | YAML | Legacy | Style guide persistence |
| `creative_room_repo.py` | `CreativeRoomRepository` | YAML | Core | Author-only creative room data |

### 3.2 The Death of In-Memory Storage

**Phase F mandate:** Every service that previously used `Dict[str, ...]` as its data store MUST migrate to YAML + SQLite event logging.

| Service | Alpha v2.0 Storage | Phase F Target Storage |
|---------|-------------------|----------------------|
| `PipelineService` | `_runs: Dict[str, PipelineRun]` (class-level) | Pipeline *definitions* → `ContainerRepository` (already done). Pipeline *runs* → ephemeral in-memory is acceptable for active runs, but completed runs MUST be persisted as containers. |
| `WritingService` | `ContainerRepository` + `EventService` | ✅ Already correct — saves `WritingFragment` as YAML containers + appends events. |
| `StoryboardService` | `ContainerRepository` + `EventService` | ✅ Already correct — converts `Panel` ↔ `GenericContainer` and persists to `containers/panel/`. |
| `KnowledgeGraphService` | `SQLiteIndexer` + `ChromaIndexer` | ✅ Already correct — maintains indexes with callbacks from `ContainerRepository`. |

**Remaining gap:** `PipelineService._runs` still uses class-level dicts for active pipeline run state. Active runs may remain in-memory for SSE streaming performance, but a `_persist_completed_run()` method must save the final `PipelineRun` as a `GenericContainer` with `container_type: "pipeline_run"`.

### 3.3 New Services

#### `ModelConfigRegistry` (new file: `src/antigravity_tool/services/model_config_registry.py`)

```python
class ModelConfigRegistry:
    """Resolves the correct model for any execution context via cascade."""

    def __init__(self, project_path: Path):
        self._project_config: ModelConfig    # From antigravity.yaml default_model
        self._agent_configs: Dict[str, ModelConfig]  # From antigravity.yaml model_overrides
        self._load_configs(project_path)

    def resolve(
        self,
        step_config: Optional[Dict[str, Any]] = None,    # Pipeline step's model field
        bucket: Optional[GenericContainer] = None,         # Target bucket
        agent_id: Optional[str] = None,                    # Active agent
    ) -> ModelConfig:
        """
        Cascade: Step > Bucket > Agent > Project.
        """
```

**Storage:** Reads `antigravity.yaml` at boot. No persistence — configuration changes go back to YAML via `PUT /api/v1/projects/{id}/model-config`.

### 3.4 Chat Session Repository (Phase J)

#### `ChatSessionRepository` (new file: `src/antigravity_tool/repositories/chat_session_repo.py`)

```python
class ChatSessionRepository:
    """YAML-based persistence for chat sessions and messages.

    Storage layout:
      .antigravity/sessions/{session_id}/
      ├── manifest.yaml         # ChatSession metadata
      ├── messages/
      │   ├── msg_{ulid}.yaml   # Individual ChatMessage files
      │   └── ...
      ├── digests/
      │   ├── compact_001.yaml  # Compaction summaries
      │   └── ...
      └── artifacts/
          └── artifact_{ulid}.yaml

    Design decisions:
    - Messages stored as individual files (not a single list) to support
      large sessions without loading all messages into memory
    - Manifest stores only metadata + ordered message IDs
    - Digests stored separately for efficient resume (load digest without messages)
    """

    def __init__(self, project_path: Path):
        self._sessions_dir = project_path / ".antigravity" / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    # ── Session CRUD ────────────────────────────────────────────

    def save_session(self, session: ChatSession) -> None:
        """Write session manifest to .antigravity/sessions/{id}/manifest.yaml."""
        ...

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load session manifest. Returns None if not found."""
        ...

    def list_sessions(self) -> List[ChatSessionSummary]:
        """List all sessions with lightweight summaries (no messages loaded)."""
        ...

    def delete_session(self, session_id: str) -> None:
        """Archive or delete a session directory."""
        ...

    # ── Message CRUD ────────────────────────────────────────────

    def save_message(self, session_id: str, message: ChatMessage) -> None:
        """Write individual message to messages/msg_{id}.yaml."""
        ...

    def load_messages(self, session_id: str,
                      offset: int = 0, limit: int = 50) -> List[ChatMessage]:
        """Load messages with pagination. Most recent first."""
        ...

    def load_message(self, session_id: str, message_id: str) -> Optional[ChatMessage]:
        """Load a single message by ID."""
        ...

    # ── Digest CRUD ─────────────────────────────────────────────

    def save_digest(self, session_id: str, digest: ChatCompactionResult) -> None:
        """Save compaction digest to digests/compact_{N}.yaml."""
        ...

    def load_latest_digest(self, session_id: str) -> Optional[ChatCompactionResult]:
        """Load the most recent compaction digest for resume."""
        ...

    # ── Artifact CRUD ───────────────────────────────────────────

    def save_artifact(self, session_id: str, artifact: ChatArtifact) -> None:
        """Save generated artifact to artifacts/artifact_{id}.yaml."""
        ...

    def load_artifacts(self, session_id: str) -> List[ChatArtifact]:
        """Load all artifacts for a session."""
        ...
```

#### `ProjectMemoryRepository` (new file: `src/antigravity_tool/repositories/project_memory_repo.py`)

```python
class ProjectMemoryRepository:
    """YAML persistence for project-level memory.

    Storage: .antigravity/project_memory.yaml
    """

    def __init__(self, project_path: Path):
        self._memory_file = project_path / ".antigravity" / "project_memory.yaml"

    def load(self) -> ProjectMemory:
        """Load project memory from YAML. Returns empty if file doesn't exist."""
        ...

    def save(self, memory: ProjectMemory) -> None:
        """Write project memory to YAML."""
        ...
```

### 3.5 Enhanced SQLite Schema (Phase K)

Phase K extends the current `containers` table into a universal `entities` table that indexes **all entity types** (characters, scenes, world settings, style guides, story structures, and containers). This eliminates the O(n) directory-scanning lookups in `ContainerRepository.get_by_id()`.

#### Full DDL

```sql
-- ══════════════════════════════════════════════════════════════
-- Universal Entity Index (replaces/extends 'containers' table)
-- ══════════════════════════════════════════════════════════════

CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,          -- 'character', 'scene', 'world_settings',
                                        -- 'story_structure', 'style_guide', 'container', etc.
    container_type TEXT,                 -- For GenericContainers only: sub-type
                                        -- ('fragment', 'research_topic', 'pipeline_def')
    name TEXT NOT NULL,
    yaml_path TEXT NOT NULL UNIQUE,      -- Absolute path → O(1) file resolution
    content_hash TEXT NOT NULL,          -- SHA-256 of YAML content
    attributes_json TEXT,                -- JSON1 support for attribute queries
    parent_id TEXT,                      -- Hierarchical: Season→Arc→Act→Chapter→Scene
    sort_order INTEGER DEFAULT 0,
    tags_json TEXT DEFAULT '[]',
    model_preference TEXT,               -- Phase F: per-entity model override
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES entities(id) ON DELETE SET NULL
);

-- Indexes for common query patterns
CREATE INDEX idx_entity_type ON entities(entity_type);
CREATE INDEX idx_entity_container_type ON entities(container_type);
CREATE INDEX idx_entity_parent ON entities(parent_id);
CREATE INDEX idx_entity_sort ON entities(sort_order);
CREATE INDEX idx_entity_yaml_path ON entities(yaml_path);
CREATE INDEX idx_entity_name ON entities(name);

-- ══════════════════════════════════════════════════════════════
-- Incremental Sync Metadata
-- ══════════════════════════════════════════════════════════════

CREATE TABLE sync_metadata (
    yaml_path TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,           -- SHA-256 at index time
    mtime REAL NOT NULL,                  -- os.stat().st_mtime at index time
    indexed_at TEXT NOT NULL,             -- ISO timestamp
    file_size INTEGER NOT NULL,           -- Bytes
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_sync_mtime ON sync_metadata(mtime);
CREATE INDEX idx_sync_entity_type ON sync_metadata(entity_type);

-- ══════════════════════════════════════════════════════════════
-- Relationships (unchanged from current schema)
-- ══════════════════════════════════════════════════════════════

CREATE TABLE relationships (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    metadata_json TEXT,
    PRIMARY KEY (source_id, target_id, rel_type),
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_rel_type ON relationships(rel_type);
CREATE INDEX idx_rel_source ON relationships(source_id);
CREATE INDEX idx_rel_target ON relationships(target_id);
```

#### Migration Strategy

```python
class SQLiteIndexer:
    def _migrate_to_entities(self) -> None:
        """Migrate Phase F 'containers' table → Phase K 'entities' table.

        1. Check if 'entities' table exists — skip if already migrated
        2. CREATE TABLE entities (...)
        3. INSERT INTO entities SELECT *, 'container' as entity_type FROM containers
        4. Create sync_metadata entries from existing containers
        5. DROP TABLE containers (after verification)
        """
```

#### Entity Type Registration

Typed repos register their entities into the universal index via existing `subscribe_save` / `subscribe_delete` callbacks on `YAMLRepository`:

```python
# In app lifespan — register typed repos with the indexer
character_repo.subscribe_save(lambda path, entity: indexer.upsert_entity(
    entity_id=entity.id,
    entity_type="character",
    name=entity.name,
    yaml_path=str(path),
    content_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
    attributes=entity.model_dump(mode="json"),
    created_at=entity.created_at.isoformat(),
    updated_at=entity.updated_at.isoformat(),
))

# Same pattern for WorldRepo, ChapterRepo, StoryRepo, StyleRepo, CreativeRoomRepo
```

### 3.6 MtimeCache Implementation (Phase K)

New file: `src/antigravity_tool/repositories/mtime_cache.py`

```python
"""Mtime-based LRU cache for YAML repository entities.

Uses file modification time for cache invalidation — a stat() syscall
(~0.01ms) determines if the cached version is still valid, avoiding
expensive YAML parse (~1-5ms per file).
"""

from __future__ import annotations

import os
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Generic, Optional, TypeVar

from antigravity_tool.schemas.dal import CacheStats

T = TypeVar("T")


class MtimeCache(Generic[T]):
    """Bounded LRU cache with file-modification-time invalidation.

    Thread-safety: NOT thread-safe. For FastAPI's async workers,
    this is fine since each worker is single-threaded. For
    multi-threaded access, wrap with threading.Lock.
    """

    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[T, float, datetime]] = OrderedDict()
        # Internal stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, path: Path) -> Optional[T]:
        """Return cached entity if file hasn't changed, else None.

        Steps:
        1. stat(path) → current_mtime
        2. Compare against cached mtime
        3. Return entity on match, None on mismatch or miss
        """
        key = str(path)
        if key not in self._cache:
            self._misses += 1
            return None

        entity, cached_mtime, _ = self._cache[key]
        try:
            current_mtime = os.stat(path).st_mtime
        except OSError:
            # File deleted or inaccessible — evict
            del self._cache[key]
            self._misses += 1
            return None

        if current_mtime == cached_mtime:
            # LRU touch: move to end
            self._cache.move_to_end(key)
            self._cache[key] = (entity, cached_mtime, datetime.now(timezone.utc))
            self._hits += 1
            return entity

        # Mtime changed — stale cache
        del self._cache[key]
        self._misses += 1
        return None

    def put(self, path: Path, entity: T) -> None:
        """Cache entity with current file mtime. Evicts LRU if at capacity."""
        key = str(path)
        try:
            mtime = os.stat(path).st_mtime
        except OSError:
            return  # Don't cache if we can't stat

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (entity, mtime, datetime.now(timezone.utc))

        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)  # Evict oldest
            self._evictions += 1

    def invalidate(self, path: Path) -> None:
        """Remove a specific entry (called by UnitOfWork on write)."""
        key = str(path)
        self._cache.pop(key, None)

    def invalidate_all(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()

    def stats(self) -> CacheStats:
        """Return current cache performance metrics."""
        total = self._hits + self._misses
        return CacheStats(
            size=len(self._cache),
            max_size=self.max_size,
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            hit_rate=self._hits / total if total > 0 else 0.0,
        )
```

**Integration with `YAMLRepository._load_file()`:**

```python
class YAMLRepository(Generic[T]):
    def __init__(self, base_dir: Path, model_class: Type[T],
                 cache: Optional[MtimeCache] = None):
        self.base_dir = base_dir
        self.model_class = model_class
        self._cache = cache  # Injected by DI; None for backward compat
        # ... existing fields ...

    def _load_file(self, path: Path) -> T:
        # 1. Try cache
        if self._cache:
            cached = self._cache.get(path)
            if cached is not None:
                return cached

        # 2. Read from disk (existing logic)
        data = read_yaml(path)
        entity = self.model_class(**data)

        # 3. Populate cache
        if self._cache:
            self._cache.put(path, entity)

        return entity

    def _save_file(self, path: Path, entity: T) -> Path:
        # ... existing write logic ...
        # After successful write, invalidate cache
        if self._cache:
            self._cache.invalidate(path)
        return path
```

---

## 4. Backend Modules: Services

### 4.1 Service Inventory

| File | Class | Dependencies | Storage | Phase |
|------|-------|-------------|---------|:-----:|
| `base.py` | `ServiceContext`, `PromptResult` | Project, ContextCompiler, TemplateEngine, WorkflowState | Stateless | Core |
| `knowledge_graph_service.py` | `KnowledgeGraphService` | ContainerRepository, SchemaRepository, SQLiteIndexer, ChromaIndexer | SQLite + ChromaDB | Core |
| `pipeline_service.py` | `PipelineService` | ContainerRepository, EventService, ContextEngine*, ModelConfigRegistry* | YAML (definitions) + In-Memory (active runs) + SQLite (events) | Core+B+F |
| `writing_service.py` | `WritingService` | ContainerRepository, KnowledgeGraphService, EventService | YAML + SQLite (events) | A |
| `storyboard_service.py` | `StoryboardService` | ContainerRepository, EventService | YAML + SQLite (events) | C |
| `director_service.py` | `DirectorService` | ServiceContext, ContextEngine | Stateless (returns result objects) | Core |
| `context_engine.py` | `ContextEngine` | KnowledgeGraphService, ContainerRepository | Stateless (assembles context on demand) | Core+F |
| `agent_dispatcher.py` | `AgentDispatcher` | Skill markdown files, ModelConfigRegistry*, ContextEngine* | In-memory skill registry + LiteLLM calls | Core+G |
| `file_watcher_service.py` | `FileWatcherService` | watchdog, KnowledgeGraphService, ContainerRepository | Background thread + SSE broadcast | E |
| `model_config_registry.py`* | `ModelConfigRegistry` | Project path (reads `antigravity.yaml`) | YAML config (read-only at runtime) | F |
| `character_service.py` | `CharacterService` | ServiceContext | YAML via project | Legacy |
| `world_service.py` | `WorldService` | ServiceContext | YAML via project | Legacy |
| `story_service.py` | `StoryService` | ServiceContext | YAML via project | Legacy |
| `scene_service.py` | `SceneService` | ServiceContext | YAML via project | Legacy |
| `panel_service.py` | `PanelService` | ServiceContext | YAML via project | Legacy |
| `evaluation_service.py` | `EvaluationService` | ServiceContext | YAML via project | Core |
| `session_service.py` | `SessionService` | ServiceContext | YAML (.antigravity/sessions/) | Core |
| `creative_room_service.py` | `CreativeRoomService` | ServiceContext | YAML via project | Core |
| `analysis_service.py` | `AnalysisService` | KnowledgeGraphService, ContainerRepository, ContextEngine | Stateless (LLM calls) | Next-B |
| `export_service.py` | `ExportService` | ContainerRepository, KnowledgeGraphService | Stateless | Core |
| `reader_sim_service.py` | `ReaderSimService` | ContainerRepository, StoryboardService | Stateless (heuristic computation) | Next-C |
| `research_service.py` | `ResearchService` | AgentDispatcher, ContainerRepository, KnowledgeGraphService | YAML + KG | G |

*Starred (`*`) dependencies are **Phase F additions** to existing services.

### 4.2 Key Service Contracts

#### `PipelineService` — Phase F Evolution

```python
class PipelineService:
    def __init__(
        self,
        container_repo: ContainerRepository,
        event_service: EventService,
        context_engine: ContextEngine,            # NEW: Phase F
        model_config_registry: ModelConfigRegistry,  # NEW: Phase F
    ): ...

    async def _run_composable_pipeline(self, run_id: str, definition: PipelineDefinition):
        """
        For each step in topological order:
        1. Resolve model → ModelConfigRegistry.resolve(step.config, bucket, agent_id)
        2. Build context → ContextEngine.assemble_context(query, container_ids)
        3. Dispatch to step handler
        4. If logic step (if_else/loop) → evaluate condition, branch DAG
        5. Emit event → EventService.append_event()
        6. Push SSE event
        """
```

#### `AgentDispatcher` — Phase G Evolution

```python
class AgentDispatcher:
    def __init__(self, skills_dir: Path):
        self.skills: dict[str, AgentSkill] = {}
        self._load_skills(skills_dir)

    def route(self, intent: str) -> Optional[AgentSkill]:
        """Keyword matching → skill. Returns None if ambiguous."""

    def route_with_llm(self, intent: str) -> Optional[AgentSkill]:
        """LLM classification fallback."""

    def execute(self, skill: AgentSkill, intent: str,
                context: dict | None = None) -> AgentResult:
        """Call LiteLLM with the skill's system prompt + context."""

    def route_and_execute(self, intent: str,
                         context: dict | None = None) -> Optional[AgentResult]:
        """Combined route + execute."""
```

**Phase G target:** Agents transition from static prompt files to **ReAct executors**:
1. **Reason** about the user's intent and available context
2. **Act** by invoking tools (KG queries, Research Library lookups, container CRUD)
3. **Observe** the results and iterate

The ReAct loop is implemented as a multi-turn LLM conversation within `execute()`.

### 4.3 Chat Services — Phase J

Four new services implement the Agentic Chat system. They follow existing patterns (constructor DI, async methods, YAML persistence) and integrate with all existing services.

#### `ChatOrchestrator` (new file: `src/antigravity_tool/services/chat_orchestrator.py`)

The central brain for all chat interactions. Routes user intents to tools/agents, manages the ReAct loop, and streams responses.

```python
from typing import AsyncGenerator, Dict, List, Optional
from antigravity_tool.schemas.chat import (
    ChatActionTrace, ChatEvent, ChatMessage, ChatSession,
    AgentInvocation, ToolIntent, BackgroundTask,
)

MAX_AGENT_DEPTH = 3


class ChatTool:
    """Base class for tools the orchestrator can invoke."""
    name: str
    description: str

    async def execute(self, params: dict, context: str,
                      session: ChatSession) -> ChatActionTrace:
        """Execute the tool and return a Glass Box trace."""
        ...


class ChatOrchestrator:
    """Central brain for chat interactions. Routes intents to tools/agents."""

    def __init__(
        self,
        agent_dispatcher: 'AgentDispatcher',
        context_engine: 'ContextEngine',
        pipeline_service: 'PipelineService',
        container_repo: 'ContainerRepository',
        kg_service: 'KnowledgeGraphService',
        model_config_registry: 'ModelConfigRegistry',
        event_service: 'EventService',
        project_memory_service: 'ProjectMemoryService',
    ):
        self._agent_dispatcher = agent_dispatcher
        self._context_engine = context_engine
        self._pipeline_service = pipeline_service
        self._container_repo = container_repo
        self._kg_service = kg_service
        self._model_config = model_config_registry
        self._event_service = event_service
        self._memory_service = project_memory_service
        self._tools: Dict[str, ChatTool] = {}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all 14 chat tools mapped to backend services.

        Tools registered:
          WRITE, BRAINSTORM, OUTLINE, RESEARCH, CONTINUITY, STYLE,
          TRANSLATE, STORYBOARD, PIPELINE, BUCKET, SEARCH, NAVIGATE,
          STATUS, MEMORY
        """
        ...

    async def process_message(
        self,
        session: ChatSession,
        message: str,
        mentioned_ids: List[str] = [],
        chat_context_manager: 'ChatContextManager' = None,
    ) -> AsyncGenerator[ChatEvent, None]:
        """
        Process a user message through the full pipeline:

        1. Build context (3-layer model via ChatContextManager)
        2. Classify intent (LLM-based classification)
        3. Check autonomy level — if Level 0, propose action and wait
        4. Execute tool (via tool registry)
        5. Collect ChatActionTrace (Glass Box)
        6. If agent-to-agent needed, invoke sub-agent with depth tracking
        7. Stream response tokens + traces + artifacts via ChatEvent
        8. Persist message via ChatSessionService

        Yields ChatEvent instances for SSE streaming.
        """
        # Step 1: Context assembly
        context = await chat_context_manager.build_context(
            session, message, mentioned_ids
        )

        # Step 2: Intent classification
        intent = await self._classify_intent(message, context.text)

        # Step 3: Autonomy check
        if session.autonomy_level == AutonomyLevel.ASK:
            yield ChatEvent(event_type="approval_needed", data={
                "proposed_action": intent.tool,
                "params": intent.params,
                "explanation": f"I'd like to use {intent.tool} to {intent.params}",
            })
            return  # Wait for approval message

        # Step 4–7: Execute and stream
        trace = await self._execute_tool(intent, session, context)
        yield ChatEvent(event_type="action_trace", data=trace.model_dump())
        ...

    async def _classify_intent(
        self, message: str, context: str,
    ) -> ToolIntent:
        """
        LLM classifies user intent into one of 14 tool categories.

        Uses a fast model (e.g., gemini-flash) with the tool descriptions
        as system prompt. Returns ToolIntent with extracted parameters.

        Fallback: if classification confidence < 0.5, ask user to clarify.
        """
        ...

    async def _execute_tool(
        self, intent: ToolIntent, session: ChatSession, context: 'ChatContext',
    ) -> ChatActionTrace:
        """
        Execute the resolved tool and collect a Glass Box trace.

        Records: tool_name, agent_id, context_summary, containers_used,
        model_used, duration_ms, token_usage, result_preview.
        """
        ...

    async def _invoke_agent(
        self,
        agent_id: str,
        intent: str,
        context: str,
        depth: int = 0,
        call_chain: Optional[List[str]] = None,
    ) -> AgentInvocation:
        """
        Invoke an agent with depth tracking for agent-to-agent composition.

        Rules:
        - Max depth: MAX_AGENT_DEPTH (3)
        - Circular detection: rejects if agent_id already in call_chain
        - Each invocation produces its own ChatActionTrace
        - Sub-agents inherit parent context but can request additional via @-mentions

        Example chain:
          Writing Agent (depth 0)
            → Continuity Analyst (depth 1)
              → Research Agent (depth 2) for fact verification
        """
        if depth > MAX_AGENT_DEPTH:
            raise AgentDepthExceeded(
                f"Agent chain exceeded {MAX_AGENT_DEPTH} levels: {call_chain}"
            )
        call_chain = call_chain or []
        if agent_id in call_chain:
            raise AgentCircularCall(
                f"Circular agent call detected: {call_chain} → {agent_id}"
            )
        call_chain.append(agent_id)

        # Dispatch to agent via AgentDispatcher
        skill = self._agent_dispatcher.route(agent_id)
        result = await self._agent_dispatcher.execute(skill, intent, {"text": context})

        # Build trace
        trace = ChatActionTrace(
            tool_name=agent_id,
            agent_id=agent_id,
            context_summary=f"Invoked by {call_chain[-2] if len(call_chain) > 1 else 'orchestrator'}",
            model_used=self._model_config.resolve(agent_id=agent_id).model,
            duration_ms=result.duration_ms,
            token_usage_in=result.tokens_in,
            token_usage_out=result.tokens_out,
            result_preview=result.content[:200],
        )

        return AgentInvocation(
            caller_agent_id=call_chain[-2] if len(call_chain) > 1 else "orchestrator",
            callee_agent_id=agent_id,
            intent=intent,
            depth=depth,
            trace=trace,
        )

    async def handle_pipeline_approval(
        self, session: ChatSession, run_id: str, user_response: str,
    ) -> None:
        """
        Translate a natural language chat response into a pipeline resume call.

        Parses user intent:
        - "approve" / "looks good" → resume with approved payload
        - "use option B" → resume with selection
        - "skip this step" → resume with skip flag
        - "change model to opus" → update model config, then resume
        - "pause" → pause the pipeline
        - "cancel" → cancel the pipeline
        """
        ...
```

#### `ChatSessionService` (new file: `src/antigravity_tool/services/chat_session_service.py`)

```python
class ChatSessionService:
    """Manages chat session lifecycle: create, messages, compact, end, resume."""

    def __init__(self, project_path: Path):
        self._repo = ChatSessionRepository(project_path)

    async def create_session(
        self, name: str, project_id: str,
        autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST,
    ) -> ChatSession:
        """Create a new chat session with initial Project Memory injection."""
        session = ChatSession(
            name=name,
            project_id=project_id,
            autonomy_level=autonomy_level,
        )
        self._repo.save_session(session)
        return session

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Persist a message and update session token usage."""
        session = self._repo.load_session(session_id)
        session.message_ids.append(message.id)
        session.token_usage += self._estimate_tokens(message.content)
        self._repo.save_message(session_id, message)
        self._repo.save_session(session)

    async def compact_session(self, session_id: str,
                               llm_summarize_fn) -> ChatCompactionResult:
        """
        Trigger /compact:
        1. Load all messages since last compaction
        2. Call LLM to summarize into ~2K token digest
        3. Preserve story-critical entities (mentioned container IDs)
        4. Save digest, update session state
        5. Reset token_usage to digest size
        """
        ...

    async def end_session(self, session_id: str, summary: str) -> ChatCompactionResult:
        """
        Trigger /end:
        1. Generate final digest (if not already compacted)
        2. Persist end summary and stats
        3. Set state to ENDED
        4. Suggest "next steps" based on session content
        """
        ...

    async def resume_session(self, session_id: str) -> ChatSession:
        """
        Resume a previously ended session:
        1. Load session manifest
        2. Load latest digest (not full messages)
        3. Set state back to ACTIVE
        4. Return session ready for new messages
        """
        ...

    async def list_sessions(self, project_id: str) -> List[ChatSessionSummary]:
        """List all sessions with lightweight summaries for SessionPicker."""
        return self._repo.list_sessions()

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Load full session metadata."""
        return self._repo.load_session(session_id)

    async def get_messages(self, session_id: str,
                            offset: int = 0, limit: int = 50) -> List[ChatMessage]:
        """Load paginated messages for a session."""
        return self._repo.load_messages(session_id, offset, limit)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (4 chars ≈ 1 token, matching ContextEngine)."""
        return len(text) // 4
```

#### `ProjectMemoryService` (new file: `src/antigravity_tool/services/project_memory_service.py`)

```python
class ProjectMemoryService:
    """Manages persistent project-level memory.

    This is the story's equivalent of CLAUDE.md — decisions, world rules,
    style preferences, and character DNA that persist across all sessions.
    """

    def __init__(self, project_path: Path):
        self._repo = ProjectMemoryRepository(project_path)

    async def get_memory(self) -> ProjectMemory:
        """Load project memory."""
        return self._repo.load()

    async def add_entry(
        self, key: str, value: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        source: str = "user_decision",
        auto_inject: bool = True,
    ) -> MemoryEntry:
        """
        Add or update a memory entry.

        Examples:
          "remember: always use present tense" → key="tense", value="present tense", scope=GLOBAL
          "remember for Zara: she never smiles" → key="zara-smile", scope=CHARACTER, scope_id="zara_id"
        """
        memory = self._repo.load()
        entry = MemoryEntry(
            key=key, value=value, scope=scope, scope_id=scope_id,
            source=source, auto_inject=auto_inject,
        )
        # Replace if key exists, otherwise append
        memory.entries = [e for e in memory.entries if e.key != key]
        memory.entries.append(entry)
        self._repo.save(memory)
        return entry

    async def remove_entry(self, key: str) -> bool:
        """Remove a memory entry by key. Returns True if found and removed."""
        memory = self._repo.load()
        original_count = len(memory.entries)
        memory.entries = [e for e in memory.entries if e.key != key]
        if len(memory.entries) < original_count:
            self._repo.save(memory)
            return True
        return False

    async def get_auto_inject_context(
        self,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> str:
        """
        Render all auto-inject entries as a formatted context block.

        Returns a string like:
          ## Project Memory
          - **Tone:** Dark fantasy, literary
          - **POV:** Close third-person, present tense
          - **World Rule:** Magic costs memories (Whisper Magic)
          - **Zara:** Never smiles (CHARACTER scope)
        """
        memory = self._repo.load()
        return memory.to_context_string()

    async def list_entries(
        self, scope: Optional[MemoryScope] = None,
    ) -> List[MemoryEntry]:
        """List memory entries, optionally filtered by scope."""
        memory = self._repo.load()
        if scope:
            return [e for e in memory.entries if e.scope == scope]
        return memory.entries
```

#### `ChatContextManager` (new file: `src/antigravity_tool/services/chat_context_manager.py`)

```python
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChatContext:
    """Assembled context for a chat message."""
    text: str                          # Full context string
    token_estimate: int                # Estimated token count
    layer1_tokens: int                 # Project Memory tokens
    layer2_tokens: int                 # Session History tokens
    layer3_tokens: int                 # On-Demand Retrieval tokens
    entity_ids_included: List[str]     # Container IDs in context


class ChatContextManager:
    """Assembles context for chat messages using the Three-Layer Model.

    Layer 1: Project Memory (always present, ~500–2K tokens)
    Layer 2: Session Context (conversation history, within budget)
    Layer 3: On-Demand Retrieval (@-mentioned entities, semantic search)
    """

    def __init__(
        self,
        session_service: ChatSessionService,
        memory_service: ProjectMemoryService,
        context_engine: 'ContextEngine',
    ):
        self._session_service = session_service
        self._memory_service = memory_service
        self._context_engine = context_engine

    async def build_context(
        self,
        session: ChatSession,
        message: str,
        mentioned_ids: List[str] = [],
    ) -> ChatContext:
        """
        Assemble the three-layer context:

        1. Layer 1 — Project Memory:
           memory_service.get_auto_inject_context()
           Always included. ~500–2K tokens.

        2. Layer 2 — Session History:
           Load recent messages from session (within token budget).
           If session has a digest, include digest instead of full history.
           Budget = session.context_budget - layer1_tokens - estimated_layer3

        3. Layer 3 — On-Demand Retrieval:
           For each mentioned_id: load full container data via ContextEngine
           If no explicit @-mentions: run semantic search on message text
           to auto-detect relevant entities.

        Total must fit within session.context_budget.
        """
        ...

    async def compact(self, session: ChatSession) -> ChatCompactionResult:
        """
        Summarize conversation into a ~2K token digest.

        Uses LLM (fast model via ModelConfigRegistry) to:
        1. Read all messages since last compaction
        2. Extract: key decisions, entity states, pending actions, writer preferences
        3. Produce a structured digest preserving story-critical info
        4. Discard routine exchanges (greetings, minor edits, etc.)

        The digest replaces the full history in Layer 2 for future messages.
        """
        ...

    def _should_suggest_compact(self, session: ChatSession) -> bool:
        """Returns True if token usage exceeds 80% of budget."""
        return session.token_usage > (session.context_budget * 0.8)
```

### 4.4 UnitOfWork Service (Phase K)

New file: `src/antigravity_tool/services/unit_of_work.py`

The `UnitOfWork` enforces atomic writes across YAML, SQLite index, and EventService. Services buffer mutations, then commit them in a single transaction.

```python
"""Atomic write coordinator for YAML + SQLite + EventService.

Ensures the 'Key Invariant' from §12 (End-to-End Mutation) is
structurally enforced, not left to convention.
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.repositories.mtime_cache import MtimeCache
from antigravity_tool.schemas.dal import UnitOfWorkEntry
from antigravity_tool.utils.io import write_yaml

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Ensures YAML + SQLite + EventService writes are atomic.

    Usage:
        async with UnitOfWork(indexer, event_service, chroma, cache) as uow:
            uow.save("char_01", "character", "/path/to/hero.yaml",
                      data=hero.model_dump(mode="json"))
            uow.save("scene_01", "scene", "/path/to/scene.yaml",
                      data=scene.model_dump(mode="json"))
            # commit() is called automatically on exit
            # rollback() is called automatically on exception
    """

    def __init__(
        self,
        indexer: SQLiteIndexer,
        event_service: EventService,
        chroma_indexer: Optional[Any] = None,
        cache: Optional[MtimeCache] = None,
    ):
        self._indexer = indexer
        self._event_service = event_service
        self._chroma = chroma_indexer
        self._cache = cache
        self._entries: List[UnitOfWorkEntry] = []
        self._temp_files: List[tuple[str, str]] = []  # (temp_path, final_path)

    def save(
        self,
        entity_id: str,
        entity_type: str,
        yaml_path: str,
        data: Dict[str, Any],
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
        event_type: str = "CREATE",
        branch_id: str = "main",
    ) -> None:
        """Buffer a save operation."""
        self._entries.append(UnitOfWorkEntry(
            operation="save",
            entity_id=entity_id,
            entity_type=entity_type,
            yaml_path=yaml_path,
            data=data,
            event_type=event_type,
            event_payload=data,
            branch_id=branch_id,
        ))

    def delete(
        self,
        entity_id: str,
        yaml_path: str,
        branch_id: str = "main",
    ) -> None:
        """Buffer a delete operation."""
        self._entries.append(UnitOfWorkEntry(
            operation="delete",
            entity_id=entity_id,
            entity_type="",
            yaml_path=yaml_path,
            event_type="DELETE",
            event_payload={"id": entity_id},
            branch_id=branch_id,
        ))

    def commit(self) -> None:
        """Execute all buffered operations atomically.

        Commit sequence:
        1. Write YAML to temp files (.tmp suffix)
        2. BEGIN SQLite transaction
        3. Upsert entities + sync_metadata into SQLite
        4. Append events to EventService
        5. Atomic rename: temp → final for each YAML file
        6. COMMIT SQLite transaction
        7. Invalidate MtimeCache for affected paths
        8. Async ChromaDB upsert (non-fatal)

        On failure at any step: temp files deleted, SQLite auto-rollback,
        original YAML files untouched.
        """
        if not self._entries:
            return

        try:
            # Step 1: Write temps
            for entry in self._entries:
                if entry.operation == "save" and entry.data:
                    temp_path = entry.yaml_path + ".tmp"
                    Path(temp_path).parent.mkdir(parents=True, exist_ok=True)
                    write_yaml(Path(temp_path), entry.data)
                    self._temp_files.append((temp_path, entry.yaml_path))

            # Steps 2-4: SQLite transaction + events
            with self._indexer.conn:  # SQLite context manager = transaction
                for entry in self._entries:
                    if entry.operation == "save" and entry.data:
                        content_hash = hashlib.sha256(
                            Path(entry.yaml_path + ".tmp").read_bytes()
                        ).hexdigest()
                        self._indexer.upsert_container(
                            container_id=entry.entity_id,
                            container_type=entry.entity_type,
                            name=entry.data.get("name", entry.entity_id),
                            yaml_path=entry.yaml_path,
                            attributes=entry.data,
                            created_at=entry.data.get("created_at", ""),
                            updated_at=entry.data.get("updated_at", ""),
                            parent_id=entry.data.get("parent_id"),
                        )
                    elif entry.operation == "delete":
                        self._indexer.delete_container(entry.entity_id)

                    # Append event
                    if entry.event_type and entry.event_payload:
                        self._event_service.append_event(
                            parent_event_id=None,
                            branch_id=entry.branch_id,
                            event_type=entry.event_type,
                            container_id=entry.entity_id,
                            payload=entry.event_payload,
                        )

            # Step 5: Atomic rename
            for temp_path, final_path in self._temp_files:
                os.rename(temp_path, final_path)

            # Step 6: SQLite already committed (context manager)

            # Step 7: Invalidate cache
            if self._cache:
                for entry in self._entries:
                    self._cache.invalidate(Path(entry.yaml_path))

            # Step 8: Async ChromaDB (non-fatal)
            if self._chroma:
                for entry in self._entries:
                    if entry.operation == "save" and entry.data:
                        try:
                            text = f"{entry.data.get('name', '')} {entry.data}"
                            self._chroma.upsert(entry.entity_id, text[:2000])
                        except Exception as exc:
                            logger.warning("ChromaDB upsert failed for %s: %s",
                                           entry.entity_id, exc)

        except Exception:
            # Cleanup temp files on failure
            for temp_path, _ in self._temp_files:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise
        finally:
            self._entries.clear()
            self._temp_files.clear()

    def rollback(self) -> None:
        """Discard all buffered operations without writing."""
        self._entries.clear()
        self._temp_files.clear()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False  # Don't suppress exceptions
```

### 4.5 ProjectSnapshotFactory (Phase K)

New file: `src/antigravity_tool/services/project_snapshot.py`

Batch-loads all project data needed for a context scope in a single pass through the SQLite index + MtimeCache.

```python
"""Batch loader for context assembly — replaces N individual YAML reads
with a single SQLite query + cached hydration pass.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.repositories.mtime_cache import MtimeCache
from antigravity_tool.schemas.dal import ContextScope, ProjectSnapshot
from antigravity_tool.utils.io import read_yaml


# Maps workflow steps to the entity types needed
STEP_ENTITY_MAP: Dict[str, List[str]] = {
    "world_building": ["world_settings"],
    "character_creation": ["world_settings", "character", "style_guide"],
    "story_structure": ["world_settings", "character", "story_structure"],
    "scene_writing": [
        "world_settings", "character", "story_structure",
        "scene", "style_guide", "decision",
    ],
    "screenplay_writing": ["scene", "character", "style_guide"],
    "panel_division": ["screenplay", "style_guide", "character"],
    "image_prompt_generation": ["panel", "style_guide", "character"],
    "evaluation": [
        "world_settings", "character", "story_structure",
        "scene", "creative_room", "style_guide", "decision",
    ],
    "creative_room": ["creative_room"],
}


class ProjectSnapshotFactory:
    """Batch-loads project data for a given context scope in a single pass.

    Algorithm:
    1. Look up required entity types from STEP_ENTITY_MAP
    2. Query SQLite for matching entities (with scope filters)
    3. For each entity: check MtimeCache
    4. Hydrate from YAML only on cache miss
    5. Return pre-loaded ProjectSnapshot
    """

    def __init__(
        self,
        indexer: SQLiteIndexer,
        cache: MtimeCache,
    ):
        self._indexer = indexer
        self._cache = cache

    def load(self, scope: ContextScope) -> ProjectSnapshot:
        """Batch-load all entities needed for the given context scope."""
        start = time.monotonic()
        snapshot = ProjectSnapshot()
        hits = 0
        misses = 0

        # Determine which entity types to load
        entity_types = STEP_ENTITY_MAP.get(scope.step, [])

        # Filter by scope
        for etype in entity_types:
            # Skip creative_room unless author access
            if etype == "creative_room" and scope.access_level != "author":
                continue

            # Query SQLite index
            filters: Dict[str, Any] = {}
            if scope.chapter is not None and etype in ("scene", "screenplay", "panel"):
                filters["parent_id"] = f"chapter-{scope.chapter:02d}"

            rows = self._indexer.query_containers(
                container_type=etype, filters=filters if filters else None
            )

            # Hydrate each entity
            for row in rows:
                yaml_path = Path(row["yaml_path"])

                # Try cache first
                cached = self._cache.get(yaml_path)
                if cached is not None:
                    entity_data = cached if isinstance(cached, dict) else cached.model_dump(mode="json")
                    hits += 1
                else:
                    # Cache miss — read from disk
                    entity_data = read_yaml(yaml_path)
                    self._cache.put(yaml_path, entity_data)
                    misses += 1

                # Route into snapshot fields
                self._route_entity(snapshot, etype, entity_data)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        snapshot.load_time_ms = elapsed_ms
        snapshot.entities_loaded = hits + misses
        snapshot.cache_hits = hits
        snapshot.cache_misses = misses
        return snapshot

    def _route_entity(
        self, snapshot: ProjectSnapshot, etype: str, data: Dict[str, Any]
    ) -> None:
        """Route a loaded entity into the correct snapshot field."""
        if etype == "world_settings":
            snapshot.world = data
        elif etype == "character":
            snapshot.characters.append(data)
        elif etype == "story_structure":
            snapshot.story_structure = data
        elif etype == "scene":
            snapshot.scenes.append(data)
        elif etype == "screenplay":
            snapshot.screenplays.append(data)
        elif etype == "panel":
            snapshot.panels.append(data)
        elif etype == "style_guide":
            snapshot.style_guides[data.get("name", "default")] = data
        elif etype == "decision":
            snapshot.decisions.append(data)
        elif etype == "creative_room":
            snapshot.creative_room = data
```

### 4.6 Unified ContextAssembler (Phase K)

New file: `src/antigravity_tool/services/context_assembler.py`

Merges the CLI's `ContextCompiler` (Jinja2 templates, no token budget) and the Web's `ContextEngine` (token budget, Glass Box, no templates) into a single service.

```python
"""Unified context assembly for CLI, Web, and Chat paths.

Replaces the dual-pipeline problem where ContextCompiler (CLI) and
ContextEngine (Web) had completely different implementations for the
same task — assembling context for LLM prompts.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.schemas.dal import ContextScope, ProjectSnapshot
from antigravity_tool.services.context_engine import ContextResult, ContextBucketInfo
from antigravity_tool.services.project_snapshot import ProjectSnapshotFactory

logger = logging.getLogger(__name__)


# Maps workflow steps to their Jinja2 template (for "template" output_format)
STEP_TEMPLATE_MAP: Dict[str, str] = {
    "world_building": "world/build_setting.md.j2",
    "character_creation": "character/create_character.md.j2",
    "story_structure": "story/outline_beats.md.j2",
    "scene_writing": "scene/write_scene.md.j2",
    "screenplay_writing": "screenplay/scene_to_screenplay.md.j2",
    "panel_division": "panel/divide_panels.md.j2",
    "image_prompt_generation": "panel/panel_to_image_prompt.md.j2",
    "evaluation": "evaluate/evaluate_scene.md.j2",
    "creative_room": "creative_room/extract_knowledge.md.j2",
}


class ContextAssembler:
    """Unified context assembly for CLI, Web, and Chat paths.

    Pipeline:
    1. ProjectSnapshotFactory.load(scope) — batch-load from SQLite + cache
    2. Apply creative room isolation (access_level check)
    3. Inject decisions (scoped to current context)
    4. Apply token budget (rank by relevance, drop least relevant)
    5. Render output (Jinja2 | structured text | raw dict)
    6. Collect Glass Box metadata
    """

    def __init__(
        self,
        snapshot_factory: ProjectSnapshotFactory,
        template_engine: TemplateEngine,
        decision_log: Any,  # DecisionLog from session_manager
        kg_service: Any,    # KnowledgeGraphService for relationship traversal
    ):
        self._snapshot_factory = snapshot_factory
        self._template_engine = template_engine
        self._decision_log = decision_log
        self._kg_service = kg_service

    def compile(self, scope: ContextScope, **extra_context) -> ContextResult:
        """Assemble context for any consumer path.

        Args:
            scope: What to assemble and how to render it
            **extra_context: Additional template variables (e.g., new_character_name)

        Returns:
            ContextResult with assembled text, token estimate, and Glass Box metadata
        """
        # Step 1: Batch-load project data
        snapshot = self._snapshot_factory.load(scope)

        # Step 2: Build context dict from snapshot
        context = self._build_context_dict(snapshot, scope)
        context.update(extra_context)

        # Step 3: Inject decisions
        if self._decision_log:
            decisions_text = self._decision_log.format_for_prompt(
                chapter=scope.chapter,
                scene=scope.scene,
                character=scope.character_name,
            )
            if decisions_text:
                context["author_decisions"] = decisions_text

        # Step 4: Collect Glass Box metadata
        buckets = self._collect_buckets(snapshot)

        # Step 5: Apply token budget
        context_text = self._render_context(context, scope)
        token_estimate = len(context_text) // 4

        containers_truncated = 0
        if token_estimate > scope.token_budget:
            context_text, containers_truncated = self._apply_token_budget(
                context_text, scope.token_budget
            )
            token_estimate = len(context_text) // 4

        return ContextResult(
            text=context_text,
            token_estimate=token_estimate,
            containers_included=snapshot.entities_loaded,
            containers_truncated=containers_truncated,
            was_summarized=False,
            buckets=buckets,
        )

    def _build_context_dict(
        self, snapshot: ProjectSnapshot, scope: ContextScope
    ) -> Dict[str, Any]:
        """Convert ProjectSnapshot into the context dict expected by templates."""
        ctx: Dict[str, Any] = {}

        if snapshot.world:
            ctx["world_summary"] = snapshot.world
        if snapshot.characters:
            ctx["characters"] = snapshot.characters
        if snapshot.story_structure:
            ctx["story_structure"] = snapshot.story_structure
        if snapshot.scenes:
            ctx["scenes"] = snapshot.scenes
            ctx["previous_scenes"] = snapshot.scenes  # For scene writing
        if snapshot.screenplays:
            ctx["screenplays"] = snapshot.screenplays
        if snapshot.panels:
            ctx["panels"] = snapshot.panels
        if snapshot.style_guides:
            ctx["visual_style"] = snapshot.style_guides.get("visual", {})
            ctx["narrative_style"] = snapshot.style_guides.get("narrative", {})
        if snapshot.creative_room and scope.access_level == "author":
            ctx["creative_room"] = snapshot.creative_room
        if snapshot.reader_knowledge:
            ctx["reader_knowledge"] = snapshot.reader_knowledge

        return ctx

    def _render_context(
        self, context: Dict[str, Any], scope: ContextScope
    ) -> str:
        """Render context in the requested output format."""
        if scope.output_format == "template":
            template = STEP_TEMPLATE_MAP.get(scope.step)
            if template and self._template_engine.template_exists(template):
                return self._template_engine.render(template, **context)
            # Fall back to structured if no template
            return self._render_structured(context)

        elif scope.output_format == "structured":
            return self._render_structured(context)

        else:  # "raw"
            return json.dumps(context, indent=2, default=str)

    def _render_structured(self, context: Dict[str, Any]) -> str:
        """Render context as structured text with markdown headers."""
        sections = []
        for key, value in context.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                items = "\n".join(f"- {json.dumps(v, default=str)[:200]}" for v in value[:20])
                sections.append(f"## {key}\n{items}")
            elif isinstance(value, dict):
                items = "\n".join(f"- **{k}**: {str(v)[:200]}" for k, v in value.items())
                sections.append(f"## {key}\n{items}")
            elif isinstance(value, str):
                sections.append(f"## {key}\n{value}")
        return "\n\n---\n\n".join(sections)

    def _collect_buckets(self, snapshot: ProjectSnapshot) -> List[ContextBucketInfo]:
        """Collect Glass Box metadata from the snapshot."""
        buckets = []
        if snapshot.world:
            buckets.append(ContextBucketInfo(
                id=snapshot.world.get("id", "world"),
                name="World Settings",
                container_type="world_settings",
                summary=str(snapshot.world.get("description", ""))[:120],
            ))
        for char in snapshot.characters:
            buckets.append(ContextBucketInfo(
                id=char.get("id", ""),
                name=char.get("name", "Unknown"),
                container_type="character",
                summary=str(char.get("role", ""))[:120],
            ))
        for scene in snapshot.scenes:
            buckets.append(ContextBucketInfo(
                id=scene.get("id", ""),
                name=scene.get("title", scene.get("name", "Scene")),
                container_type="scene",
                summary=str(scene.get("setting", ""))[:120],
            ))
        return buckets

    def _apply_token_budget(
        self, text: str, budget: int
    ) -> tuple[str, int]:
        """Truncate text to fit within token budget."""
        max_chars = budget * 4
        if len(text) <= max_chars:
            return text, 0
        truncated = text[:max_chars]
        truncated += "\n\n[...context truncated to fit token budget]"
        # Estimate how many containers were dropped (rough)
        lines_dropped = text[max_chars:].count("\n## ")
        return truncated, lines_dropped
```

---

## 5. Backend Modules: FastAPI Routers & Dependency Injection

### 5.1 Router Inventory

| Router File | Prefix | Key Endpoints | Phase |
|-------------|--------|--------------|:-----:|
| `project.py` | `/api/v1/project` | `GET /` (project info), `GET /health`, `GET /events` (SSE stream) | Core |
| `projects.py`* | `/api/v1/projects` | `GET /` (list projects), `POST /` (create project), `GET /{id}/structure` (hierarchy tree), `PUT /{id}/settings`, `PUT /{id}/model-config` | F |
| `characters.py` | `/api/v1/characters` | `GET /`, `GET /{name}`, `POST /prompt` | Legacy |
| `world.py` | `/api/v1/world` | `GET /`, `POST /build/prompt` | Legacy |
| `chapters.py` | `/api/v1/chapters` | `GET /{ch}/scenes`, `GET /{ch}/scenes/{id}`, `PUT /{ch}/scenes/{id}`, scene write/screenplay/panel prompts | Legacy |
| `workflow.py` | `/api/v1/workflow` | `GET /` (workflow progress) | Core |
| `director.py` | `/api/v1/director` | `POST /act`, `GET /status`, `POST /dispatch` (agent dispatch), `GET /skills`, `POST /brainstorm/suggest-connections`, `POST /brainstorm/save-card`, `GET /brainstorm/cards`, `DELETE /brainstorm/cards/{id}` | Core+Next-E |
| `schemas_router.py` | `/api/v1/schemas` | `GET /`, `GET /{name}`, `POST /`, `PUT /{name}`, `DELETE /{name}`, `POST /validate`, `POST /generate`, `POST /nl-schema` | Core |
| `graph.py` | `/api/v1/graph` | `GET /` (full KG as React Flow JSON), `GET /search?q=&limit=` (semantic search) | Core |
| `timeline.py` | `/api/v1/timeline` | `GET /events`, `POST /checkout`, `POST /branch`, `GET /branches`, `GET /branch/{id}/events`, `GET /compare`, `GET /stream` (SSE) | Core+Next-E |
| `pipeline.py` | `/api/pipeline` | `GET /steps/registry`, `GET /definitions`, `POST /definitions`, `GET /definitions/{id}`, `PUT /definitions/{id}`, `DELETE /definitions/{id}`, `POST /runs`, `GET /runs/{id}`, `POST /runs/{id}/resume`, `GET /runs/{id}/stream` (SSE) | Core+B |
| `writing.py` | `/api/v1/writing` | `POST /fragments`, `POST /detect-entities`, `GET /fragments/{id}/context`, `GET /semantic-search` | A+H |
| `storyboard.py` | `/api/v1/storyboard` | `GET /scenes/{id}/panels`, `POST /scenes/{id}/panels`, `GET /scenes/{id}/panels/{pid}`, `PUT /scenes/{id}/panels/{pid}`, `POST /scenes/{id}/panels/reorder`, `POST /scenes/{id}/panels/generate`, `POST /voice-to-scene` | C+Next-E |
| `models.py`* | `/api/v1/models` | `GET /available` (list LiteLLM models), `GET /config` (current project config), `PUT /config` (update) | F |
| `agents.py`* | `/api/v1/agents` | `GET /` (list all agent skills + status), `PUT /{name}/model-config` (override model for agent) | F |
| `research.py`* | `/api/v1/research` | `POST /query` (trigger Research Agent), `GET /library` (list research topics), `GET /topic/{id}` (get topic detail) | G |
| `analysis.py` | `/api/v1/analysis` | `GET /emotional-arc`, `GET /voice-scorecard`, `GET /ribbons`, `POST /continuity-check`, `POST /continuity-check/scene/{id}`, `GET /continuity-issues`, `POST /style-check` | Next-B+H |
| `preview.py` | `/api/v1/preview` | `GET /scene/{scene_id}` (reading sim), `GET /chapter/{chapter}` (chapter sim) | Next-C |
| `export.py` | `/api/v1/export` | `GET /markdown`, `GET /json`, `GET /fountain` | Core |
| `containers.py` | `/api/v1/containers` | `POST /` (create), `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /reorder` | Next-E |
| `translation.py` | `/api/v1/translation` | `POST /translate`, `GET /glossary`, `POST /glossary` | H |

*Starred routers are **new files** created in Phase F/G. All routers above are implemented.

### 5.2 Router Registration (`server/app.py`)

Current registration order in `src/antigravity_tool/server/app.py`:

```python
app.include_router(project.router)               # /api/v1/project
app.include_router(characters.router)             # /api/v1/characters
app.include_router(world.router)                  # /api/v1/world
app.include_router(chapters.router)               # /api/v1/chapters
app.include_router(workflow.router)               # /api/v1/workflow
app.include_router(director.router)               # /api/v1/director
app.include_router(pipeline.router, prefix="/api") # /api/pipeline (no /v1)
app.include_router(schemas_router.router)         # /api/v1/schemas
app.include_router(graph.router)                  # /api/v1/graph
app.include_router(timeline.router)               # /api/v1/timeline
app.include_router(writing.router)                # /api/v1/writing
app.include_router(storyboard.router)             # /api/v1/storyboard

# Phase F additions:
app.include_router(projects.router)               # /api/v1/projects
app.include_router(models.router)                 # /api/v1/models
app.include_router(agents.router)                 # /api/v1/agents

# Phase G additions:
app.include_router(research.router)               # /api/v1/research

# Phase Next-B additions:
app.include_router(analysis.router)               # /api/v1/analysis

# Phase Next-C additions:
app.include_router(preview.router)                # /api/v1/preview

# Phase Next-E additions:
app.include_router(containers.router)             # /api/v1/containers

# Phase H additions:
app.include_router(translation.router)            # /api/v1/translation

# Phase J additions:
app.include_router(chat.router)                   # /api/v1/chat
```

### 5.3 Dependency Injection (`server/deps.py`)

**Current DI graph** (from `src/antigravity_tool/server/deps.py`):

```
get_project()                    → Project (LRU cached singleton via Project.find(Path.cwd()))
├── get_service_context(project) → ServiceContext (per-request)
│   ├── get_world_service(ctx)       → WorldService
│   ├── get_character_service(ctx)   → CharacterService
│   ├── get_story_service(ctx)       → StoryService
│   ├── get_scene_service(ctx)       → SceneService
│   ├── get_panel_service(ctx)       → PanelService
│   ├── get_evaluation_service(ctx)  → EvaluationService
│   ├── get_session_service(ctx)     → SessionService
│   └── get_director_service(ctx)    → DirectorService
├── get_schema_repo(project)         → SchemaRepository
├── get_container_repo(project)      → ContainerRepository
├── get_event_service(project)       → EventService
└── (Lifespan singletons on app.state)
    ├── KnowledgeGraphService        (container_repo + schema_repo + sqlite_indexer + chroma_indexer)
    ├── SQLiteIndexer                (knowledge_graph.db)
    ├── ChromaIndexer                (.chroma/)
    └── FileWatcherService           (watchdog thread + SSE broadcast)
```

**Composite service providers:**
```python
get_knowledge_graph_service(request) → app.state.kg_service (lifespan singleton)
get_writing_service(project, container_repo, kg_service, event_service) → WritingService
get_storyboard_service(container_repo, event_service) → StoryboardService
get_pipeline_service(container_repo, event_service) → PipelineService
get_context_engine(kg_service, container_repo) → ContextEngine
get_agent_dispatcher() → AgentDispatcher (LRU cached)
get_analysis_service(kg_service, container_repo, context_engine) → AnalysisService
get_reader_sim_service(container_repo, storyboard_service) → ReaderSimService
get_continuity_service(kg_service, context_engine, event_service, agent_dispatcher) → ContinuityService
get_style_service(container_repo, context_engine, agent_dispatcher) → StyleService
get_translation_service(kg_service, container_repo, agent_dispatcher) → TranslationService
```

**Phase F additions to `deps.py`:**

```python
@lru_cache()
def get_model_config_registry(
    project: Project = Depends(get_project),
) -> ModelConfigRegistry:
    """LRU cached model config registry, loaded from antigravity.yaml."""
    return ModelConfigRegistry(project.path)

def get_context_engine(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
) -> ContextEngine:
    """Context assembly with token budgeting and relevance scoring."""
    return ContextEngine(kg_service, container_repo)

@lru_cache()
def get_agent_dispatcher() -> AgentDispatcher:
    """Cached AgentDispatcher that loads skills from agents/skills/."""
    skills_dir = Path(__file__).resolve().parent.parent.parent.parent / "agents" / "skills"
    return AgentDispatcher(skills_dir)

# Updated PipelineService provider (Phase F):
def get_pipeline_service(
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    model_config_registry: ModelConfigRegistry = Depends(get_model_config_registry),
) -> PipelineService:
    return PipelineService(container_repo, event_service, context_engine, model_config_registry)
```

**Updated DI graph (Phase F target):**

```
get_project()
├── get_service_context(project) → ServiceContext
│   └── ... (legacy services unchanged)
├── get_schema_repo(project) → SchemaRepository
├── get_container_repo(project) → ContainerRepository
├── get_event_service(project) → EventService
├── get_model_config_registry(project) → ModelConfigRegistry [NEW, LRU cached]
│
├── Lifespan singletons (app.state):
│   ├── KnowledgeGraphService
│   ├── SQLiteIndexer
│   ├── ChromaIndexer
│   └── FileWatcherService
│
├── Composite providers:
│   ├── get_context_engine(kg_service, container_repo) → ContextEngine
│   ├── get_writing_service(project, container_repo, kg_service, event_service) → WritingService
│   ├── get_storyboard_service(container_repo, event_service) → StoryboardService
│   ├── get_pipeline_service(container_repo, event_service, context_engine, model_config_registry) → PipelineService [UPDATED]
│   └── get_agent_dispatcher() → AgentDispatcher [LRU cached]
│
├── model_config_registry → AgentDispatcher (injected for model resolution)
│   model_config_registry → PipelineService (injected for model resolution)
│   context_engine → PipelineService (injected for context assembly)
│
└── Phase J Chat providers:
    ├── get_chat_session_service(project) → ChatSessionService
    ├── get_project_memory_service(project) → ProjectMemoryService
    ├── get_chat_context_manager(session_service, memory_service, context_engine) → ChatContextManager
    └── get_chat_orchestrator(agent_dispatcher, context_engine, pipeline_service,
                              container_repo, kg_service, model_config_registry,
                              event_service, memory_service) → ChatOrchestrator
```

**Phase J additions to `deps.py`:**

```python
def get_chat_session_service(
    project: Project = Depends(get_project),
) -> ChatSessionService:
    """Chat session lifecycle: create, compact, end, resume."""
    return ChatSessionService(project.path)

def get_project_memory_service(
    project: Project = Depends(get_project),
) -> ProjectMemoryService:
    """Persistent project-level memory (decisions, world rules, style guide)."""
    return ProjectMemoryService(project.path)

def get_chat_context_manager(
    session_service: ChatSessionService = Depends(get_chat_session_service),
    memory_service: ProjectMemoryService = Depends(get_project_memory_service),
    context_engine: ContextEngine = Depends(get_context_engine),
) -> ChatContextManager:
    """Three-layer context assembly for chat messages."""
    return ChatContextManager(session_service, memory_service, context_engine)

def get_chat_orchestrator(
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
    context_engine: ContextEngine = Depends(get_context_engine),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    model_config_registry: ModelConfigRegistry = Depends(get_model_config_registry),
    event_service: EventService = Depends(get_event_service),
    memory_service: ProjectMemoryService = Depends(get_project_memory_service),
) -> ChatOrchestrator:
    """Central brain for chat interactions."""
    return ChatOrchestrator(
        agent_dispatcher, context_engine, pipeline_service,
        container_repo, kg_service, model_config_registry,
        event_service, memory_service,
    )

# ── Phase K additions — Unified Data Access Layer ─────────────

@lru_cache()
def get_mtime_cache() -> MtimeCache:
    """Singleton LRU cache with 500-entry capacity."""
    return MtimeCache(max_size=500)

def get_unit_of_work(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    event_service: EventService = Depends(get_event_service),
    cache: MtimeCache = Depends(get_mtime_cache),
) -> UnitOfWork:
    """Per-request UnitOfWork for atomic YAML + SQLite + Event writes."""
    chroma = getattr(kg_service, 'chroma_indexer', None)
    return UnitOfWork(kg_service.indexer, event_service, chroma, cache)

@lru_cache()
def get_project_snapshot_factory(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    cache: MtimeCache = Depends(get_mtime_cache),
) -> ProjectSnapshotFactory:
    """Singleton batch loader for context assembly."""
    return ProjectSnapshotFactory(kg_service.indexer, cache)

def get_context_assembler(
    factory: ProjectSnapshotFactory = Depends(get_project_snapshot_factory),
    ctx: ServiceContext = Depends(get_service_context),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
) -> ContextAssembler:
    """Unified context assembly for CLI, Web, and Chat."""
    return ContextAssembler(factory, ctx.engine, ctx.compiler.decision_log, kg_service)
```

### 5.4 New Endpoint Details

#### Projects Router (`/api/v1/projects`) — Phase F

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `GET` | `/` | — | `List[ProjectSummary]` | List all projects in the workspace |
| `POST` | `/` | `ProjectCreate` | `ProjectSummary` | Create new project directory + `antigravity.yaml` |
| `GET` | `/{id}/structure` | — | `StructureTree` | Walk `parent_id` chains to build Season→Scene tree |
| `PUT` | `/{id}/settings` | `ProjectSettingsUpdate` | `ProjectSettings` | Update project metadata |
| `PUT` | `/{id}/model-config` | `ProjectModelConfig` | `ProjectModelConfig` | Update `model_overrides` in `antigravity.yaml` |

#### Models Router (`/api/v1/models`) — Phase F

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `GET` | `/available` | — | `List[str]` | List available LiteLLM model identifiers |
| `GET` | `/config` | — | `ProjectModelConfig` | Current model cascade configuration |
| `PUT` | `/config` | `ProjectModelConfig` | `ProjectModelConfig` | Update model overrides |

#### Research Router (`/api/v1/research`) — Phase G

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `POST` | `/query` | `ResearchQuery` | `ResearchResult` | Trigger Research Agent deep-dive |
| `GET` | `/library` | — | `List[GenericContainer]` | List all `container_type: "research_topic"` buckets |
| `GET` | `/topic/{id}` | — | `GenericContainer` | Get single research topic detail |

#### Timeline Router Additions — Phase F

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `POST` | `/branch` | `BranchCreate` | `BranchResponse` | Create new alternate timeline branch |
| `GET` | `/stream` | — | SSE | Stream new event sourcing events |

#### Chat Router (`/api/v1/chat`) — Phase J

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `POST` | `/sessions` | `ChatSessionCreate` | `ChatSession` | Create a new chat session |
| `GET` | `/sessions` | — | `List[ChatSessionSummary]` | List all sessions for current project |
| `GET` | `/sessions/{id}` | — | `ChatSession` | Get session with metadata (no messages) |
| `DELETE` | `/sessions/{id}` | — | `204` | End/archive a session |
| `POST` | `/sessions/{id}/messages` | `ChatMessageCreate` | SSE stream of `ChatEvent` | Send message; response streams via SSE |
| `GET` | `/sessions/{id}/messages` | `?offset=0&limit=50` | `List[ChatMessage]` | Get paginated message history |
| `GET` | `/sessions/{id}/stream` | — | SSE | Persistent SSE stream for real-time updates (background tasks, pipeline events) |
| `POST` | `/sessions/{id}/compact` | — | `ChatCompactionResult` | Trigger context compaction |
| `POST` | `/sessions/{id}/resume` | — | `ChatSession` | Resume an ended session |
| `GET` | `/memory` | — | `ProjectMemory` | Get all project memory entries |
| `POST` | `/memory` | `MemoryEntryCreate` | `MemoryEntry` | Add or update a memory entry |
| `DELETE` | `/memory/{key}` | — | `204` | Remove a memory entry |
| `POST` | `/sessions/{id}/messages/{mid}/approve` | `ApprovalPayload` | `ChatMessage` | Approve a pending agent action |
| `POST` | `/sessions/{id}/messages/{mid}/reject` | `RejectionPayload` | `ChatMessage` | Reject a pending agent action |

**Request/Response models:**

```python
class ChatSessionCreate(BaseModel):
    name: str = ""                               # Auto-generated if empty
    autonomy_level: AutonomyLevel = AutonomyLevel.SUGGEST
    tags: List[str] = []

class ChatMessageCreate(BaseModel):
    content: str                                 # User message text
    mentioned_entity_ids: List[str] = []         # Container IDs from @-mentions

class MemoryEntryCreate(BaseModel):
    key: str
    value: str
    scope: MemoryScope = MemoryScope.GLOBAL
    scope_id: Optional[str] = None
    auto_inject: bool = True

class ApprovalPayload(BaseModel):
    action: Literal["approve", "approve_with_edit"]
    edited_content: Optional[str] = None         # If the writer edited before approving

class RejectionPayload(BaseModel):
    reason: Optional[str] = None                 # Optional rejection reason
```

**SSE streaming for messages:** The `POST /sessions/{id}/messages` endpoint returns an `EventSourceResponse` that streams `ChatEvent` objects as the `ChatOrchestrator` processes the message. This enables:
- Progressive token streaming (response appears word-by-word)
- Real-time `ChatActionTrace` delivery (Glass Box blocks appear as actions complete)
- Artifact delivery (preview panel updates when content is generated)
- Error handling (errors stream as `ChatEvent(event_type="error")`)

#### DB Maintenance Router (`/api/v1/db`) — Phase K

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `GET` | `/health` | — | `DBHealthReport` | Entity counts, index health, cache stats, disk usage |
| `POST` | `/reindex` | `ReindexRequest` | SSE stream of `ReindexEvent` | Full rebuild of SQLite + ChromaDB indexes from YAML files |
| `POST` | `/check` | — | `ConsistencyReport` | Verify YAML ↔ SQLite consistency (mismatches, orphans, stale entries) |
| `GET` | `/stats` | — | `DBStatsResponse` | Detailed entity counts by type, cache hit rates, sync timestamps |

**Request/Response models:**

```python
class ReindexRequest(BaseModel):
    """Controls reindex scope."""
    full: bool = True                          # True = full rebuild, False = incremental only
    include_chroma: bool = True                # Whether to rebuild ChromaDB vectors too
    entity_types: Optional[List[str]] = None   # If set, only reindex these types

class ReindexEvent(BaseModel):
    """SSE event emitted during reindex progress."""
    phase: str                                 # "scanning", "indexing", "vectors", "cleanup", "complete"
    processed: int                             # Files processed so far
    total: int                                 # Total files to process
    current_file: Optional[str] = None         # Currently processing
    errors: List[str] = []                     # Non-fatal errors encountered

class ConsistencyReport(BaseModel):
    """Result of a YAML ↔ SQLite consistency check."""
    checked_at: datetime
    total_yaml_files: int
    total_indexed: int
    issues: List[ConsistencyIssue]             # From dal.py schema
    is_consistent: bool                        # True if zero issues

class DBStatsResponse(BaseModel):
    """Detailed database statistics."""
    entity_counts: Dict[str, int]              # {"character": 12, "scene": 45, ...}
    total_entities: int
    total_yaml_files: int
    index_size_bytes: int
    chroma_doc_count: int
    cache_stats: Optional[CacheStats] = None   # From MtimeCache.stats()
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    sync_metadata_entries: int
    orphaned_indexes: int                      # In SQLite but not on disk
    stale_entries: int                         # On disk but not indexed
```

**SSE streaming for reindex:** The `POST /reindex` endpoint returns an `EventSourceResponse` that streams `ReindexEvent` objects as the rebuild progresses. The frontend renders a progress bar (`processed / total`) with the current file being indexed. Non-fatal errors (e.g., malformed YAML) are collected and returned in the final `complete` event without halting the reindex.

**Implementation notes:**
- `GET /health` is fast (single SQLite query + cache stats read) — safe for polling
- `POST /reindex` acquires a global lock to prevent concurrent reindexes; returns `409 Conflict` if already running
- `POST /check` does NOT modify any data — read-only comparison between disk and index
- All endpoints use the `get_unit_of_work` / `get_mtime_cache` DI providers from §5.3

---

## 6. Frontend Modules

### 6.1 Zustand Store Slices

**Main store:** `useStudioStore` in `src/web/src/lib/store.ts` — composes all slices via Zustand's slice pattern.

| Slice | File | Responsibility | Key State | Phase |
|-------|------|---------------|-----------|:-----:|
| `graphDataSlice` | `graphDataSlice.ts` | Project data, characters, scenes, workflow, world, pipeline trigger | `project`, `characters`, `scenes`, `workflow`, `world`, `loading`, `pipelineRunId` | Core |
| `reactFlowSlice` | `reactFlowSlice.ts` | React Flow nodes/edges, `buildGraph()` with hybrid fallback, link/unlink | `nodes`, `edges` | Core |
| `canvasUISlice` | `canvasUISlice.ts` | Sidebar state, view toggle, selected item, inspector | `mainView`, `sidebarCollapsed`, `sidebarTab`, `selectedItem`, `inspectorData` | Core |
| `storyboardSlice` | `storyboardSlice.ts` | Scenes, panels map, selection, view mode, CRUD + generate | `scenes`, `panelsByScene`, `selectedPanelId`, `viewMode`, `isGenerating` | C |
| `projectSlice`* | `projectSlice.ts` | **Multi-project state**, active project, structure tree | `projects`, `activeProjectId`, `structureTree`, `isLoading` | F |
| `modelConfigSlice`* | `modelConfigSlice.ts` | **Model cascade config**, available models, overrides | `availableModels`, `projectConfig`, `agentConfigs` | F |
| `researchSlice`* | `researchSlice.ts` | **Research Library** state, topic CRUD | `topics`, `isResearching`, `currentQuery` | G |

**Separate stores (independent from main):**

| Store | File | Responsibility | Key State | Phase |
|-------|------|---------------|-----------|:-----:|
| `useZenStore` | `zenSlice.ts` | Fragments, entities, auto-save, AI commands | `currentFragmentId`, `isSaving`, `detectedEntities`, `contextEntries`, `searchResults` | A |
| `usePipelineBuilderStore` | `pipelineBuilderSlice.ts` | Step registry, definitions, RF nodes/edges, config | `stepRegistry`, `definitions`, `nodes`, `edges`, `selectedStepId`, `activeRunId` | B |
| `useChatStore`* | `chatSlice.ts` | **Agentic Chat** — sessions, messages, streaming, traces, artifacts, @-mentions | `sessions`, `activeSessionId`, `messages`, `isStreaming`, `streamingContent`, `actionTraces`, `activeArtifact`, `mentionSuggestions`, `backgroundTasks` | J |

*Starred slices are **new** for Phase F+.

### 6.2 Component Groups

| Group | Directory | Key Components | Phase |
|-------|-----------|---------------|:-----:|
| `command-center/`* | `components/command-center/` | `ProjectSwitcher.tsx`, `ProgressOverview.tsx`, `PendingApprovals.tsx`, `ModelConfigPanel.tsx` | I |
| `canvas/` | `components/canvas/` | `InfiniteCanvas.tsx`, `nodes/GenericNode.tsx` | Core |
| `pipeline/` | `components/pipeline/` | `usePipelineStream.ts` (SSE hook), `PromptReviewModal.tsx` (Edit/Chat/Paste/Skip/ChangeModel) | Core |
| `pipeline-builder/` | `components/pipeline-builder/` | `PipelineBuilder.tsx`, `StepNode.tsx`, `StepLibrary.tsx`, `StepConfigPanel.tsx`, `TemplateGallery.tsx`* | B+G |
| `zen/` | `components/zen/` | `ZenEditor.tsx`, `MentionList.tsx`, `SlashCommandList.tsx`, `ContextSidebar.tsx` (4-tab: Context/Continuity/Style/Translation), `StoryboardStrip.tsx`, `ContinuityPanel.tsx`, `StyleScorecard.tsx`, `InlineTranslation.tsx` | A+H |
| `storyboard/` | `components/storyboard/` | `PanelCard.tsx`, `SceneStrip.tsx`, `PanelEditor.tsx`, `SemanticCanvas.tsx`, `LayoutSuggestionPanel.tsx`, `VoiceToSceneButton.tsx` | C+Next-C+Next-E |
| `schema-builder/` | `components/schema-builder/` | `SchemaBuilderPanel.tsx`, `SchemaEditor.tsx`, `NLWizardInput.tsx`, `FieldRow.tsx`, `FieldTypeSelector.tsx`, `SchemaPreview.tsx` | Core |
| `timeline/` | `components/timeline/` | `TimelineView.tsx`, `TimelinePanel.tsx`, `TimelineEventNode.tsx`, `StoryStructureTree.tsx`, `BranchList.tsx`, `BranchComparison.tsx`, `useInterval.ts` | Core+Next-E |
| `research/` | `components/research/` | `ResearchDetailPanel.tsx`, `ResearchTopicCard.tsx` | Next-D |
| `brainstorm/` | `components/brainstorm/` | `IdeaCardNode.tsx`, `SuggestionPanel.tsx` | Next-E |
| `workbench/` | `components/workbench/` | `WorkbenchLayout.tsx`, `Canvas.tsx`, `Sidebar.tsx`, `SidebarItem.tsx`, `Inspector.tsx`, `CharacterInspector.tsx`, `CharacterProgressionTimeline.tsx`, `CharacterVoiceScorecard.tsx`, `SceneInspector.tsx`, `WorldStatus.tsx`, `WorkflowBar.tsx`, `DirectorControls.tsx` | Core+Next-B+Next-C |
| `chat/`* | `components/chat/` | `ChatSidebar.tsx`, `ChatInput.tsx`, `ChatMessageList.tsx`, `ChatMessage.tsx`, `ActionTraceBlock.tsx`, `ArtifactPreview.tsx`, `SessionPicker.tsx`, `MentionPopover.tsx`, `BackgroundTaskIndicator.tsx`, `useChatStream.ts` | J |

*Starred components are **new** for Phase F+.

**Phase G additions to `pipeline-builder/`:**

| Component | Purpose |
|-----------|---------|
| `TemplateGallery.tsx` | Browse and 1-click launch pre-built workflow templates |
| `LogicStepNode.tsx`* | Specialized React Flow node for if/else/loop steps with condition editor |

**Phase J `chat/` component details:**

| Component | Purpose | Key Props / State |
|-----------|---------|-------------------|
| `ChatSidebar.tsx` | Global collapsible sidebar on the right side of every page. Contains SessionPicker, ChatMessageList, ChatInput, and ArtifactPreview. Rendered in root `layout.tsx`. | `isOpen`, `width` (resizable), mounted on every route |
| `ChatInput.tsx` | Message input with @-mention autocomplete and /command detection. Uses TipTap (shared with ZenEditor) for rich text input. | `onSubmit(content, mentionedIds)`, `isStreaming` (disabled during response) |
| `ChatMessageList.tsx` | Virtualized scrolling message list (react-window). Auto-scrolls to bottom on new messages. Supports infinite scroll for history. | `messages[]`, `isStreaming`, `streamingContent` |
| `ChatMessage.tsx` | Single message bubble with role-based styling. Contains nested ActionTraceBlock(s) and artifact links. | `message: ChatMessage`, `isStreaming` |
| `ActionTraceBlock.tsx` | Collapsible Glass Box action block. Shows tool name, model, duration as header. Expands to show full context, containers, token counts. Nested sub-invocations render recursively. | `trace: ChatActionTrace`, `defaultExpanded: false` |
| `ArtifactPreview.tsx` | Split-pane preview panel for generated content. Supports prose, outlines, schemas, panels, diffs. Shows alongside the chat when an artifact is active. | `artifact: ChatArtifact`, `onSave()`, `onRevise()`, `onRegenerate()` |
| `SessionPicker.tsx` | Dropdown/modal for session management. Lists sessions with name, date, message count, tags. Supports create, resume, and end actions. | `sessions[]`, `activeSessionId`, `onSwitch(id)`, `onCreate()` |
| `MentionPopover.tsx` | @-mention autocomplete popover. Queries KG for matching containers by type. Shows icon + name + type for each suggestion. | `query: string`, `onSelect(containerId)`, keyboard navigation |
| `BackgroundTaskIndicator.tsx` | Compact progress indicator for background tasks (pipelines, research). Shown inline in the chat when tasks are running. | `task: BackgroundTask`, `onApprove()`, `onPause()` |
| `useChatStream.ts` | Custom hook for SSE streaming. Connects to `GET /sessions/{id}/stream` and `POST /sessions/{id}/messages`. Demultiplexes ChatEvent types. | `useChatStream(sessionId)` → `{ streamingContent, actionTraces, artifact, isStreaming }` |

### 6.3 API Client (`lib/api.ts`)

**Current methods** in `src/web/src/lib/api.ts`:

| Category | Methods | Phase |
|----------|---------|:-----:|
| **Project** | `getProject()`, `getHealth()` | Core |
| **Characters** | `getCharacters()`, `getCharacter(name)` | Core |
| **World** | `getWorld()` | Core |
| **Chapters/Scenes** | `getScenes(ch)`, `getScene(ch, num)`, `updateScene(...)`, `getPanels(ch)` | Core |
| **Workflow** | `getWorkflow()` | Core |
| **Director** | `directorAct(req?)`, `getDirectorStatus()` | Core |
| **Schemas** | `getSchemas()`, `getSchema(id)`, `createSchema()`, `updateSchema()`, `deleteSchema()`, `generateFields()` | Core |
| **Graph** | `getGraph()` | Core |
| **Pipeline Execution** | `startPipeline(payload?, definitionId?)`, `resumePipeline(runId, payload)` | Core |
| **Pipeline Definitions** | `getPipelineStepRegistry()`, `getPipelineDefinitions()`, `getPipelineDefinition(id)`, `createPipelineDefinition()`, `updatePipelineDefinition()`, `deletePipelineDefinition()` | B |
| **Timeline** | `getTimelineEvents()`, `checkoutEvent(eventId, branchName?)` | Core |
| **Writing** | `saveFragment(data)`, `detectEntities(text)`, `getContainerContext(containerId)`, `searchContainers(q, limit)` | A |
| **Storyboard** | `getStoryboardPanels(sceneId)`, `createStoryboardPanel()`, `updateStoryboardPanel()`, `deleteStoryboardPanel()`, `reorderStoryboardPanels()`, `generateStoryboardPanels()` | C |

**Phase F–G additions:**

| Category | Methods | Phase |
|----------|---------|:-----:|
| **Projects** | `listProjects()`, `createProject(body)`, `getProjectStructure(id)`, `updateProjectSettings(id, body)`, `updateProjectModelConfig(id, body)` | F |
| **Models** | `getAvailableModels()`, `getModelConfig()`, `updateModelConfig(body)` | F |
| **Agents** | `listAgents()`, `updateAgentModelConfig(name, body)` | F |
| **Timeline (additions)** | `createBranch(body)`, `subscribeTimeline()` (SSE) | F |
| **Research** | `queryResearch(body)`, `getResearchLibrary()`, `getResearchTopic(id)` | G |
| **Analysis** | `getEmotionalArc(chapter?)`, `getVoiceScorecard(characterIds?)`, `getCharacterRibbons(chapter?)` | Next-B |
| **Storyboard (additions)** | `suggestLayout(sceneId)` | Next-C |
| **Characters (additions)** | `getCharacterProgressions(id)`, `addCharacterProgression(id, body)`, `updateCharacterProgression(id, progId, body)`, `deleteCharacterProgression(id, progId)`, `getDNAAtChapter(id, chapter)` | Next-C |
| **Preview** | `getReadingSimScene(sceneId)`, `getReadingSimChapter(chapter)` | Next-C |
| **Workflow Templates** | `getWorkflowTemplates()`, `createFromTemplate(templateId)` | Next-D |
| **Containers** | `createContainer(body)`, `getContainer(id)`, `updateContainer(id, body)`, `deleteContainer(id)`, `reorderContainers(body)` | Next-E |
| **Timeline (Next-E)** | `getBranches()`, `getBranchEvents(branchId)`, `compareBranches(a, b)`, `streamTimeline()` (SSE) | Next-E |
| **Brainstorm** | `getBrainstormCards()`, `saveBrainstormCard(body)`, `deleteBrainstormCard(id)`, `suggestBrainstormConnections(body)` | Next-E |
| **Voice-to-Scene** | `voiceToScene(body)` | Next-E |
| **Continuity** | `checkContinuity(body)`, `checkSceneContinuity(sceneId)`, `getContinuityIssues(scope?, scopeId?)` | H |
| **Style** | `checkStyle(body)` | H |
| **Translation** | `translate(body)`, `getGlossary()`, `addGlossaryTerm(body)` | H |
| **Writing (additions)** | `semanticSearchContainers(query, limit?)` | H |
| **Pipeline (additions)** | `generatePipelineFromNL(description)` | H |
| **Chat Sessions** | `createChatSession(body)`, `listChatSessions()`, `getChatSession(id)`, `endChatSession(id)` | J |
| **Chat Messages** | `sendChatMessage(sessionId, body)` → EventSource, `getChatMessages(sessionId, page?)` | J |
| **Chat Lifecycle** | `compactSession(sessionId)`, `resumeSession(sessionId)` | J |
| **Chat Actions** | `approveChatAction(sessionId, messageId, body)`, `rejectChatAction(sessionId, messageId, body)` | J |
| **Project Memory** | `getProjectMemory()`, `addMemoryEntry(body)`, `removeMemoryEntry(key)` | J |
| **Chat Stream** | `subscribeChatStream(sessionId)` → EventSource (persistent SSE for background tasks) | J |

**Phase K additions:**

| Category | Methods | Phase |
|----------|---------|:-----:|
| **DB Health** | `getDBHealth()` → `DBHealthReport` | K |
| **DB Reindex** | `triggerReindex(body?)` → EventSource of `ReindexEvent` | K |
| **DB Check** | `runConsistencyCheck()` → `ConsistencyReport` | K |
| **DB Stats** | `getDBStats()` → `DBStatsResponse` | K |

---

## 7. Data Flow Diagrams

### 7.1 The Unified Mutation Flow

**Scenario:** The frontend saves a new Scene text fragment from the Writing Desk (Zen Mode).

```
1. USER ACTION
   Writer types in ZenEditor (TipTap) at /zen
   Auto-save debounces (2 seconds)

2. FRONTEND → API
   zenSlice.saveFragment(data) fires
   POST /api/v1/writing/fragments
     Body: { scene_id, text, title }

3. API ROUTER
   src/antigravity_tool/server/routers/writing.py
     @router.post("/fragments")
     async def save_fragment(req: FragmentCreateRequest,
                             writing_service: WritingService = Depends(get_writing_service))
       → writing_service.save_fragment(req)

4. WRITING SERVICE → CONTAINER REPOSITORY (YAML Write)
   src/antigravity_tool/services/writing_service.py
     WritingService.save_fragment():
       a. Build GenericContainer:
            container_type = "fragment"
            name = req.title
            attributes = { "text": req.text, "scene_id": req.scene_id }
            relationships = [{ "target_id": req.scene_id, "type": "belongs_to" }]
       b. self.container_repo.save_container(container)

5. CONTAINER REPOSITORY → YAML ON DISK
   src/antigravity_tool/repositories/container_repo.py
     ContainerRepository.save_container():
       a. _save_file() → writes containers/fragment/{slug}.yaml
       b. Fires _on_save callback chain:

6. SQLITE INDEXER (Knowledge Graph Update)
   src/antigravity_tool/repositories/sqlite_indexer.py
     Callback: SQLiteIndexer.upsert_container(container)
       → INSERT OR REPLACE INTO containers (id, container_type, name, attributes_json, ...)
       → INSERT OR REPLACE INTO relationships (source_id, target_id, rel_type, ...)
       → knowledge_graph.db updated

7. CHROMA INDEXER (Vector Embedding Update)
   src/antigravity_tool/repositories/chroma_indexer.py
     Callback: ChromaIndexer.upsert_embedding(container)
       → Encode container text via all-MiniLM-L6-v2
       → Upsert into .chroma/ collection

8. WRITING SERVICE → EVENT SERVICE (Event Log)
   src/antigravity_tool/repositories/event_sourcing_repo.py
     WritingService.save_fragment() continues:
       self.event_service.append_event(
           branch_id = "main",
           event_type = "CONTAINER_CREATED",
           container_id = container.id,
           payload_json = { "container_type": "fragment", "name": container.name, ... }
       )
       → INSERT INTO events (id, parent_event_id, branch_id, event_type, container_id, payload_json)
       → UPDATE branches SET head_event_id = new_event.id WHERE id = "main"
       → event_log.db updated

9. RESPONSE → FRONTEND
   Router returns FragmentResponse { id, text, scene_id, ... }
   zenSlice updates currentFragmentId, lastSavedAt

10. SSE BROADCAST (Asynchronous)
    FileWatcherService detects containers/fragment/{slug}.yaml change
      → Debounce 500ms
      → KnowledgeGraphService.sync_all() or incremental upsert
      → SSE broadcast to all connected frontends via GET /api/v1/project/events
      → graphDataSlice receives update → React Flow rebuilds nodes/edges
```

### 7.2 The Context Generation & Model Resolution Flow

**Scenario:** A pipeline step needs to generate prose for a scene. The system assembles context from the Knowledge Graph and resolves the correct LLM model.

```
1. PIPELINE STEP REACHED: llm_generate (step_5 in a "Outline → Draft" workflow)
   src/antigravity_tool/services/pipeline_service.py
     PipelineService._run_composable_pipeline():
       current_step = PipelineStepDef(
           step_type = "llm_generate",
           config = { "model": "", "temperature": 0.8, "max_tokens": 4096 }
       )
       upstream_payload = { "text": "Scene outline...", "scene_id": "abc123" }

2. CONTEXT ASSEMBLY
   PipelineService calls ContextEngine.assemble_context():
     src/antigravity_tool/services/context_engine.py
       a. _resolve_containers():
            → KnowledgeGraphService.find_containers(container_type="character")
            → KnowledgeGraphService.find_containers(container_type="scene")
            → Also fetches scene's relationships to get linked characters
       b. For each container, _format_container():
            → Build structured text: "## Zara (character)\n- role: protagonist\n- ..."
       c. If include_relationships:
            → KnowledgeGraphService.get_neighbors(container_id) for each
            → Append "Related: Kael (character), Obsidian Blade (weapon)"
       d. _relevance_score(query, entry_text):
            → Simple keyword-overlap scoring vs. the scene outline
       e. Sort by relevance, apply token budget (max_tokens=4000):
            → Include highest-scoring containers first
            → Truncate when cumulative tokens exceed budget
       f. Return ContextResult:
            text = "## Zara (character)\n...\n---\n## The Market (location)\n..."
            token_estimate = 3200
            containers_included = 8
            containers_truncated = 3
            was_summarized = False

3. MODEL RESOLUTION
   PipelineService calls ModelConfigRegistry.resolve():
     src/antigravity_tool/services/model_config_registry.py
       a. Check step_config["model"] → "" (empty, skip)
       b. Check bucket.model_preference → None (no bucket override, skip)
       c. Check agent_configs["writing_agent"] → ModelConfig(model="anthropic/claude-3.5-sonnet")
       d. Return: ModelConfig(model="anthropic/claude-3.5-sonnet", temperature=0.7, max_tokens=2048)

4. PROMPT COMPILATION
   PipelineService builds the final prompt:
       system_prompt = "You are a prose writer. Write the scene based on this context..."
       user_prompt = context_result.text + "\n\n---\nScene outline:\n" + upstream_payload["text"]

5. HUMAN CHECKPOINT (if preceding step is review_prompt)
   If the pipeline has a review_prompt step before llm_generate:
       → PipelineRun.state = PAUSED_FOR_USER
       → SSE push to frontend
       → PromptReviewModal opens
       → Writer can: ✏️ Edit / 💬 Chat / 🔧 Change model / 📋 Paste / ⏭️ Skip / ✅ Approve
       → POST /api/pipeline/runs/{id}/resume with edited payload
       → PipelineService._resume_events[run_id].set()

6. LLM EXECUTION
   PipelineService calls LiteLLM:
       from litellm import completion
       response = completion(
           model = "anthropic/claude-3.5-sonnet",   # From ModelConfigRegistry
           messages = [
               {"role": "system", "content": system_prompt},
               {"role": "user", "content": user_prompt},
           ],
           temperature = 0.8,    # From step config (overrides model default)
           max_tokens = 4096,    # From step config
       )
       result_text = response.choices[0].message.content

7. POST-EXECUTION
   → SSE push: step_5 COMPLETED with result preview
   → Next step in topological order begins
   → If save_to_bucket step follows → ContainerRepository.save_container()
   → EventService.append_event("PIPELINE_STEP_COMPLETED", ...)
```

### 7.3 The Alternate Timeline Branching Flow

**Scenario:** The writer is viewing the Story Timeline at `/timeline` and clicks "Branch" on a historical event to create an alternate timeline ("What if Zara survived?").

```
1. USER ACTION
   Writer views TimelineView at /timeline
   Clicks an event node (e.g., "Scene 5 — Zara's Death" in Act 2)
   Clicks "Branch from here" button

2. FRONTEND → API
   POST /api/v1/timeline/branch
     Body: {
       source_branch_id: "main",
       new_branch_name: "what-if-zara-survived",
       checkout_event_id: "evt_01HXYZ..."    # The event BEFORE Zara's death
     }

3. API ROUTER
   src/antigravity_tool/server/routers/timeline.py
     @router.post("/branch")
     async def create_branch(req: BranchCreate,
                             event_service: EventService = Depends(get_event_service))
       → event_service.branch(req.source_branch_id, req.new_branch_name, req.checkout_event_id)

4. EVENT SERVICE — BRANCH CREATION
   src/antigravity_tool/repositories/event_sourcing_repo.py
     EventService.branch():
       a. Validate checkout_event_id exists on source_branch_id
       b. Generate new branch_id (ULID)
       c. INSERT INTO branches (id, head_event_id) VALUES (new_id, checkout_event_id)
          → The new branch's HEAD points at the fork event
          → All events AFTER checkout_event_id on the source branch are NOT included
       d. Return new branch_id

5. STATE PROJECTION
   EventService.project_state(new_branch_id):
       a. Recursive CTE walks parent_event_id chain from HEAD to root:
          WITH RECURSIVE event_chain AS (
            SELECT * FROM events WHERE id = (SELECT head_event_id FROM branches WHERE id = ?)
            UNION ALL
            SELECT e.* FROM events e JOIN event_chain ec ON e.id = ec.parent_event_id
          )
       b. Apply JSON payloads forward (earliest → latest) to reconstruct container state
       c. Return Dict[container_id, container_state]
          → This state reflects the world AS IF events after the fork never happened

6. RESPONSE → FRONTEND
   Return: { branch_id, branch_name, head_event_id, event_count }

7. FRONTEND STATE UPDATE
   TimelineView receives the new branch
     → Renders a second branch line in the Git-style DAG visualization
     → TimelineEventNode for the fork point shows a branch icon
     → StoryStructureTree (Phase F) refreshes to show the alternate Act 2'

8. SUBSEQUENT WRITES ON NEW BRANCH
   When the writer edits a scene while on the new branch:
     → WritingService.save_fragment() → ContainerRepository.save_container()
     → EventService.append_event(branch_id="what-if-zara-survived", ...)
     → New events accumulate independently on this branch
     → The "main" branch is unaffected

9. CONTINUITY VALIDATION (Phase H, Automatic)
   Continuity Analyst agent auto-validates the new branch:
     → Checks relationships against World Bible containers
     → Flags: "Zara is now alive but is still referenced as dead in Chapter 7 summary"
     → Surfaces warning in PendingApprovals queue on Command Center
```

### 7.4 The Research Agent Flow

**Scenario:** The writer is drafting a scene about a railgun fight in low gravity. The system detects a real-world concept and the Research Agent creates a persistent knowledge bucket.

```
1. CONCEPT DETECTION (Automatic — Phase H)
   Writer types in ZenEditor: "The railgun projectile curves slightly in the low gravity..."
   Auto-save fires → POST /api/v1/writing/detect-entities

   WritingService.detect_entities():
     a. Calls KnowledgeGraphService.get_all_container_names()
        → Returns: ["Zara", "Obsidian Blade", "Whispering Market", ...]
     b. Calls LLM (Gemini Flash) with known names + text
        → LLM returns: { entities: ["Zara"], unresolved: ["railgun", "low gravity"] }
     c. For unresolved terms, check if they match Research Library:
        → KG query: find_containers(container_type="research_topic", name LIKE "railgun%")
        → No match found

   OR: Manual trigger
   Writer clicks "Research" button or types /research in the Writing Desk
     → Opens Research query input
     → Writer types: "How would a railgun work in low gravity?"

2. FRONTEND → API
   POST /api/v1/research/query
     Body: { query: "How would a railgun work in low gravity?", auto_link_scene_id: "scene_5" }

3. RESEARCH AGENT EXECUTION
   src/antigravity_tool/server/routers/research.py
     @router.post("/query")
     → Gets AgentDispatcher via Depends(get_agent_dispatcher)
     → Gets ContextEngine via Depends(get_context_engine)

   AgentDispatcher.route_and_execute():
     a. route("research: How would a railgun...") → matches "research_agent" skill
     b. ContextEngine.assemble_context(query="railgun low gravity",
                                        container_types=["research_topic", "scene"])
        → Gathers existing context about the scene and any related research
     c. ModelConfigRegistry.resolve(agent_id="research_agent")
        → Returns ModelConfig(model="gemini/gemini-2.0-pro") (deep reasoning)
     d. Build prompt:
        system: agents/skills/research_agent.md (system prompt)
        user: assembled_context + "\n\nResearch query: How would a railgun work in low gravity?"
     e. LiteLLM completion with gemini/gemini-2.0-pro
     f. Parse structured response:
        {
          "topic": "Railgun Physics in Low Gravity",
          "category": "Physics / Weapons",
          "summary": "In low gravity environments, railgun projectiles...",
          "key_facts": [
            "Projectile velocity unaffected by gravity",
            "Trajectory curves less than in 1G",
            "Recoil force identical (Newton's 3rd law)"
          ],
          "constraints": [
            "Shooter would be pushed backward more noticeably",
            "No atmospheric drag means infinite range"
          ],
          "story_implications": [
            "Combat would be at longer ranges",
            "Cover becomes less useful — penetration depth unchanged"
          ],
          "confidence": "high"
        }

4. APPROVAL GATE (⏸️)
   If triggered via pipeline or manual "Research" command:
     → PromptReviewModal opens showing the LLM's findings
     → Writer reviews: ✅ Approve / ✏️ Edit facts / ⏭️ Skip

5. KNOWLEDGE BUCKET CREATION
   On approval, research.py router calls:
     a. Build GenericContainer:
          container_type = "research_topic"
          name = "Railgun Physics in Low Gravity"
          attributes = {
            "category": "Physics / Weapons",
            "summary": "In low gravity environments...",
            "key_facts": ["Projectile velocity unaffected by gravity", ...],
            "constraints": ["Shooter would be pushed backward...", ...],
            "story_implications": ["Combat would be at longer ranges", ...],
            "sources": [],
            "confidence": "high"
          }

     b. ContainerRepository.save_container(container)
        → YAML: containers/research_topic/railgun-physics-in-low-gravity.yaml
        → SQLiteIndexer.upsert_container() → knowledge_graph.db
        → ChromaIndexer.upsert_embedding() → .chroma/

     c. EventService.append_event(
          branch_id = "main",
          event_type = "CONTAINER_CREATED",
          container_id = container.id,
          payload_json = { ... }
        )

6. AUTO-LINKING
   After bucket creation:
     a. If auto_link_scene_id was provided:
        → Load scene container
        → Append to scene.relationships: { "target_id": research_bucket.id, "type": "references" }
        → ContainerRepository.save_container(scene)  → updates scene YAML
        → EventService.append_event("CONTAINER_UPDATED", scene.id, ...)

     b. KnowledgeGraphService picks up the new relationship
        → SQLiteIndexer indexes the edge
        → React Flow canvas shows new connection: Scene 5 → "Railgun Physics"

7. FUTURE CONTEXT INJECTION
   On subsequent AI calls involving Scene 5:
     a. ContextEngine.assemble_context(container_ids=[scene_5.id])
        → Resolves scene relationships → finds "Railgun Physics" research topic
        → Includes research summary in the context block
     b. Any AI-generated prose about railguns now has factual grounding
     c. The writer sees "Context included: Railgun Physics in Low Gravity" in the glass box UI
```

### 7.5 The Agentic Chat Message Flow

**Scenario:** The writer types "write a scene where Zara enters the market" with @Zara and @The Market mentions in the Chat Sidebar.

```
1. USER ACTION
   Writer types in ChatInput at any page (chat sidebar is global)
   Types: "write a scene where Zara enters the market"
   @-mentions: [@Zara, @The Market] resolved to container IDs

2. FRONTEND → API
   chatSlice.sendMessage(sessionId, content, mentionedIds) fires
   POST /api/v1/chat/sessions/{sessionId}/messages
     Body: { content: "write a scene where Zara enters the market",
             mentioned_entity_ids: ["ulid_zara", "ulid_market"] }
   Response: SSE EventSourceResponse (streaming)

3. CHAT ROUTER → CHAT ORCHESTRATOR
   src/antigravity_tool/server/routers/chat.py
     @router.post("/sessions/{id}/messages")
     async def send_message(req: ChatMessageCreate,
                            orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
                            context_manager: ChatContextManager = Depends(get_chat_context_manager)):
       → Save user message via ChatSessionService
       → Return EventSourceResponse(orchestrator.process_message(...))

4. CONTEXT ASSEMBLY (Three-Layer Model)
   ChatContextManager.build_context(session, message, mentioned_ids):
     a. Layer 1 — Project Memory:
          ProjectMemoryService.get_auto_inject_context()
          → "## Project Memory\n- Tone: Dark fantasy\n- POV: Close third, present tense\n- World Rule: Magic costs memories"
          → ~800 tokens

     b. Layer 2 — Session History:
          Load recent messages from ChatSessionRepository (within token budget)
          → Last 5 messages from this session (or digest if compacted)
          → ~2,400 tokens

     c. Layer 3 — On-Demand Retrieval:
          For each mentioned_id:
            ContextEngine.assemble_context(container_ids=["ulid_zara", "ulid_market"])
            → Load Zara's full character DNA, The Market location details
            → Load relationships: Zara → Cursed Blade, Market → Chapter 1
          → ~1,800 tokens

     d. Total context: ~5,000 tokens (well within 100K budget)

5. INTENT CLASSIFICATION
   ChatOrchestrator._classify_intent(message, context):
     → LLM (fast model, e.g. gemini-flash) classifies:
       ToolIntent{
         tool: "WRITE",
         confidence: 0.95,
         params: { "action": "draft_scene", "scene_context": "Zara enters the market" },
         requires_approval: false  (autonomy_level == SUGGEST)
       }

6. TOOL EXECUTION — Writing Agent
   ChatOrchestrator._execute_tool(intent, session, context):
     a. Resolve tool: self._tools["WRITE"] → WriteTool
     b. WriteTool wraps AgentDispatcher.execute("writing_agent", ...)
     c. AgentDispatcher:
          → Route: "writing_agent" skill
          → ModelConfigRegistry.resolve(agent_id="writing_agent")
            → anthropic/claude-3.5-sonnet
          → Build prompt: system prompt + assembled context + user intent
          → LiteLLM completion (streaming)

     d. AGENT-TO-AGENT: Writing Agent decides to verify continuity
        ChatOrchestrator._invoke_agent("continuity_analyst", intent, context, depth=1):
          → Continuity Analyst checks Zara's state, market details
          → No issues found
          → Returns AgentInvocation record (nested in parent trace)

     e. Build ChatActionTrace:
          tool_name: "WRITE"
          agent_id: "writing_agent"
          context_summary: "Project Memory (800t) + Session (2,400t) + @Zara + @The Market (1,800t)"
          containers_used: ["ulid_zara", "ulid_market", "ulid_cursed_blade"]
          model_used: "anthropic/claude-3.5-sonnet"
          duration_ms: 3200
          token_usage_in: 5000, token_usage_out: 847
          sub_invocations: [AgentInvocation(continuity_analyst, depth=1)]

7. SSE STREAMING TO FRONTEND
   ChatOrchestrator yields ChatEvent sequence:
     a. ChatEvent(event_type="token", data={"text": "The rain fell..."})    → partial response
     b. ChatEvent(event_type="token", data={"text": " in sheets..."})       → continues
     ... (many token events)
     c. ChatEvent(event_type="action_trace", data={...trace...})             → Glass Box block
     d. ChatEvent(event_type="artifact", data={                              → Artifact preview
          "artifact_type": "prose",
          "title": "Scene: Zara Enters the Market",
          "content": "The rain fell in sheets as Zara stepped into..."
        })
     e. ChatEvent(event_type="complete", data={                              → Done
          "message_id": "msg_ulid",
          "token_usage": 5847
        })

8. MESSAGE PERSISTENCE
   ChatSessionService.add_message(session_id, ChatMessage{
     role: "assistant",
     content: "The rain fell in sheets as Zara...",
     action_traces: [trace],
     artifacts: [artifact],
     mentioned_entity_ids: ["ulid_zara", "ulid_market"],
   })
   → ChatSessionRepository.save_message(session_id, message)
   → Update session.token_usage += 5847
   → ChatSessionRepository.save_session(session)

9. FRONTEND STATE UPDATE
   useChatStream hook demultiplexes events:
     → "token" events → chatSlice.streamingContent appends
     → "action_trace" → chatSlice.actionTraces.push(trace)
       → ChatMessage renders ActionTraceBlock (collapsed by default)
     → "artifact" → chatSlice.activeArtifact = artifact
       → ArtifactPreview panel opens alongside chat
       → Shows: [✅ Save to Ch.3]  [✏️ Revise]  [🔄 Regenerate]
     → "complete" → chatSlice.isStreaming = false
       → Final message added to chatSlice.messages

10. ARTIFACT SAVE (Optional — if writer clicks "Save to Ch.3")
    Writer clicks "Save to Ch.3" in ArtifactPreview
    → chatSlice.saveArtifact(artifactId, targetContainerId)
    → POST /api/v1/writing/fragments { scene_id, text, title }
    → Standard Unified Mutation Flow (§7.1) takes over:
      WritingService → ContainerRepository → YAML → SQLite → Chroma → EventService
    → Chat confirms: "✅ Scene saved to Ch.3, Scene 1"
    → KG canvas updates via SSE (if visible behind chat sidebar)
```

### 7.6 The Chat-Initiated Pipeline Flow

**Scenario:** The writer types "run Scene→Panels on Ch.3 Sc.1" in the Chat Sidebar while working in Zen Mode.

```
1. USER ACTION
   Writer is in Zen Mode (/zen), chat sidebar open on right
   Types: "run Scene→Panels on Ch.3 Sc.1"

2. INTENT CLASSIFICATION
   ChatOrchestrator._classify_intent():
     → ToolIntent{tool: "PIPELINE", params: {
           "pipeline_name": "Scene→Panels",
           "target": "Ch.3 Sc.1",
           "action": "run"
       }}

3. PIPELINE RESOLUTION
   ChatOrchestrator → PipelineService.find_definition_by_name("Scene→Panels"):
     → Returns PipelineDefinition (8 steps)
   ChatOrchestrator → Resolve target container:
     → KnowledgeGraphService.find_containers(type="scene", chapter=3, scene=1)
     → Returns scene container ID

4. PREVIEW (Before Launch)
   ChatEvent(event_type="artifact", data={
     "artifact_type": "table",
     "title": "Scene→Panels Pipeline — Execution Plan",
     "content": "1. 🧠 Brainstorm (3 variations)\n2. ⏸️ Pick Variation...\n..."
   })
   → ArtifactPreview shows execution plan
   → Writer responds: "start it"

5. PIPELINE LAUNCH (Background)
   ChatOrchestrator → PipelineService.start_pipeline(definition_id, payload={
     "scene_id": scene_container_id,
     "concept": "Ch.3 Sc.1 content",
   })
   → Returns run_id
   → Add to session.background_tasks:
     BackgroundTask(task_id=run_id, task_type="pipeline",
                    label="Scene→Panels on Ch.3 Sc.1", pipeline_run_id=run_id)

6. SSE MULTIPLEXING
   PipelineService pushes events to _events[run_id] queue
   ChatOrchestrator multiplexes pipeline events into chat SSE stream:
     → ChatEvent(event_type="background_update", data={
         "task_id": run_id,
         "step": "brainstorm",
         "state": "running",
         "progress": 0.125  (1/8)
       })
   → BackgroundTaskIndicator renders in chat
   → Writer can continue chatting about other topics

7. APPROVAL GATE (Inline in Chat)
   PipelineService reaches Step 2: approve_output (pick brainstorm variation)
   → Pipeline pauses (PAUSED_FOR_USER)
   → ChatEvent(event_type="approval_needed", data={
       "task_id": run_id,
       "step": "pick_variation",
       "options": ["[A] Zara discovers...", "[B] Kael reveals...", "[C] The blade..."],
     })
   → Chat renders inline: "Pick a variation: [A] [B] [C]"
   → Writer types: "use B"

8. CHAT → PIPELINE RESUME
   ChatOrchestrator.handle_pipeline_approval(session, run_id, "use B"):
     → Parse "use B" → selected option index 1
     → PipelineService.resume(run_id, payload={"selected": "B"})
     → Pipeline continues execution

9. PIPELINE COMPLETION
   All steps complete:
   → ChatEvent(event_type="background_update", data={
       "task_id": run_id,
       "state": "completed",
       "progress": 1.0,
       "result_summary": "Scene saved to Ch.3, Scene 1. 847 words."
     })
   → BackgroundTaskIndicator shows ✅
   → Chat notification: "Pipeline complete! Scene saved."
   → Remove from session.background_tasks

10. ERROR HANDLING
    If any step fails:
    → ChatEvent(event_type="error", data={
        "task_id": run_id,
        "step": "llm_generate",
        "error": "LiteLLM timeout after 30s",
        "suggestion": "Try again with a different model, or skip this step"
      })
    → Chat shows error inline with suggested actions
    → Writer can: "retry with gemini-pro" or "skip and save what we have"
```

### 7.7 The Unified Write Path (Phase K)

**Scenario:** Any service saves a modified character entity through the Unit of Work.

```
1. SERVICE MUTATION
   WritingService / ChatOrchestrator / PipelineService calls:
     uow.save(entity_id="char_01JABC", entity_type="character",
              yaml_path="characters/zara.yaml",
              data=character.model_dump(),
              event_payload={"field": "backstory", "action": "update"})
   → UoW buffers the operation in _pending: List[UnitOfWorkEntry]
   → No disk I/O yet — caller can buffer multiple saves before commit

2. COMMIT — TEMP FILE WRITE
   uow.commit() begins:
   → For each buffered save:
     Write serialized YAML to temp file: characters/zara.yaml.tmp
     Compute content_hash = SHA-256(file_content)
   → If any temp write fails: immediate rollback (delete all .tmp files), raise

3. COMMIT — SQLITE TRANSACTION
   → BEGIN TRANSACTION on SQLite
   → For each buffered save:
     UPSERT INTO entities (id, entity_type, name, yaml_path, content_hash,
                           attributes_json, updated_at)
     UPSERT INTO sync_metadata (yaml_path, entity_id, entity_type,
                                content_hash, mtime=now(), indexed_at=now(),
                                file_size=len(content))
   → If SQL fails: ROLLBACK, delete all .tmp files, raise

4. COMMIT — EVENT APPEND
   → For each buffered save with event_payload:
     EventService.append_event(
       event_type="UPDATE", container_id="char_01JABC",
       branch_id="main", payload=event_payload)
   → Events are append-only (no rollback needed for events on failure,
     but the entry includes a "pending" flag cleared on step 6)

5. COMMIT — ATOMIC RENAME
   → For each buffered save:
     os.rename("characters/zara.yaml.tmp", "characters/zara.yaml")
   → This is the point of no return: YAML files now reflect new state
   → atomic on POSIX (same filesystem), near-atomic on macOS APFS

6. COMMIT — FINALIZE
   → COMMIT SQLite transaction
   → For each affected path: MtimeCache.invalidate(path)
   → Async (fire-and-forget): ChromaDB upsert for semantic index
   → Clear _pending buffer

7. ROLLBACK (if any step 2-5 fails)
   → Delete all .tmp files (glob project_path for *.yaml.tmp)
   → SQLite transaction auto-rolls back (no COMMIT was issued)
   → MtimeCache unchanged (old cached data still valid)
   → ChromaDB unchanged
   → Raise original exception to caller

8. DOWNSTREAM EFFECTS
   → FileWatcher detects YAML modification → but checks content_hash
     against sync_metadata → hash matches → skips re-index (no duplicate work)
   → SSE broadcasts container_updated event to connected frontends
   → MtimeCache will re-cache on next read (lazy population)
```

### 7.8 The Unified Read Path — Context Assembly (Phase K)

**Scenario:** The Chat Orchestrator or CLI ContextCompiler needs full context for scene writing in Chapter 3.

```
1. CONTEXT REQUEST
   Consumer calls:
     assembler.compile(ContextScope(
       step="scene_writing", chapter=3, scene=1,
       access_level="story", token_budget=100_000,
       output_format="structured"  # Chat path
     ))

2. SNAPSHOT FACTORY — ENTITY RESOLUTION
   ProjectSnapshotFactory.load(scope):
   → Consult STEP_ENTITY_MAP["scene_writing"]:
     Required types: ["world_settings", "character", "story_structure",
                      "scene", "style_guide"]
   → Query SQLite:
     SELECT id, entity_type, yaml_path, content_hash
     FROM entities
     WHERE entity_type IN ('world_settings', 'character', 'story_structure',
                           'style_guide')
        OR (entity_type = 'scene' AND
            json_extract(attributes_json, '$.chapter') = 3
            AND json_extract(attributes_json, '$.scene_number') = 1)
   → Returns: ~15-25 rows with yaml_paths (no YAML read yet)

3. BATCH CACHE CHECK
   For each entity row from SQLite:
   → MtimeCache.get(yaml_path):
     a) os.stat(yaml_path) → current_mtime
     b) Compare current_mtime vs cached_mtime
     c) If match AND path in cache: CACHE HIT → return cached entity
     d) If mismatch or not cached: CACHE MISS → continue to step 4
   → Typical result: 80-95% cache hits after first request

4. YAML HYDRATION (cache misses only)
   For each cache miss:
   → Read YAML file from disk
   → Parse into Pydantic model (type determined by entity_type)
   → MtimeCache.put(path, entity)  # store for future reads
   → Typical: 1-3 files read on warm cache vs 15-25 on cold start

5. SNAPSHOT ASSEMBLY
   Route loaded entities into ProjectSnapshot fields:
   → snapshot.world = world_settings entity dict
   → snapshot.characters = [character dicts...]
   → snapshot.story_structure = story structure dict
   → snapshot.scenes = [matching scene dicts...]
   → snapshot.style_guides = style guide dict
   → snapshot.load_time_ms = elapsed
   → snapshot.cache_hits / cache_misses = tracked counts

6. CONTEXT DICT CONSTRUCTION
   ContextAssembler builds step-specific context:
   → context = {
       "world": snapshot.world,
       "characters": snapshot.characters,
       "story_structure": snapshot.story_structure,
       "current_scene": snapshot.scenes[0],
       "style_guide": snapshot.style_guides,
     }
   → Inject decisions: DecisionLog.get_decisions(chapter=3, scene=1)
   → If scope.include_relationships:
       KnowledgeGraphService.get_neighbors(scene_id) → add related entities

7. TOKEN BUDGET APPLICATION
   → Estimate tokens per context bucket (chars / 4 heuristic)
   → If total > scope.token_budget:
     a) Rank buckets by step-specific priority
        (for scene_writing: current_scene > characters > world > style > decisions)
     b) Truncate lowest-priority buckets first
     c) Track truncation in Glass Box metadata

8. OUTPUT RENDERING
   Based on scope.output_format:
   → "template": Jinja2 render via TemplateEngine (CLI path)
   → "structured": Markdown-formatted text with headers (Chat/Web path)
   → "raw": Dict of loaded entities (API consumers)

9. RETURN
   → ContextResult(
       text=rendered_output,          # Final assembled prompt context
       snapshot=snapshot,              # For inspection/debugging
       glass_box=GlassBoxMetadata(
         buckets=[ContextBucketInfo(name="world", tokens=2400, truncated=False), ...],
         total_tokens=48_200,
         budget=100_000,
         cache_hit_rate=0.87,
         load_time_ms=12
       )
     )
```

### 7.9 The Incremental Sync on Startup (Phase K)

**Scenario:** The Antigravity server starts up. Instead of `sync_all()` (which crawls every YAML file), the DAL performs an incremental sync.

```
1. STARTUP — LOAD SYNC METADATA
   App lifespan begins:
   → SQLiteIndexer loads sync_metadata table into memory:
     known_files: Dict[str, SyncMetadata] = {
       "characters/zara.yaml": SyncMetadata(mtime=1706000000.0, content_hash="abc123..."),
       "characters/kael.yaml": SyncMetadata(mtime=1706000100.0, content_hash="def456..."),
       "world/settings.yaml": SyncMetadata(mtime=1705999000.0, content_hash="789abc..."),
       ... (N entries)
     }

2. DISK SCAN — STRUCTURED GLOB
   → Instead of rglob("*.yaml") across entire project:
     Scan known directories only:
       characters/*.yaml
       world/*.yaml
       story_structure/*.yaml
       scenes/**/*.yaml
       creative_room/*.yaml
       containers/**/*.yaml
       schemas/*.yaml
   → Result: disk_files: Dict[str, float] = {path: mtime for each found file}
   → O(known_dirs) glob operations, not recursive full-tree walk

3. CLASSIFY FILES INTO THREE BUCKETS

   a) UNCHANGED: disk_files[path].mtime == known_files[path].mtime
      → Skip entirely (no read, no index update)
      → This is the fast path — typically 90%+ of files

   b) CHANGED: path exists in both, but disk mtime > known mtime
      → Must re-read YAML, re-compute content_hash, update index
      → Caused by: user edited file externally, git pull, Claude Code edit

   c) NEW: path exists on disk but not in known_files
      → Must read YAML, compute content_hash, insert into index
      → Caused by: new entity created outside the server

   d) DELETED: path exists in known_files but not on disk
      → Must remove from entities table + sync_metadata
      → Caused by: user deleted file, git checkout to different branch

4. PROCESS CHANGED FILES (bucket b)
   For each changed file:
   → Read YAML content from disk
   → Parse into appropriate entity type (inferred from directory or YAML content)
   → Compute content_hash = SHA-256(raw_content)
   → If content_hash == known_files[path].content_hash:
       Touch only (mtime updated but content identical — e.g., git checkout)
       UPDATE sync_metadata SET mtime = disk_mtime WHERE yaml_path = path
   → Else (actual content change):
       UPSERT entities row with new attributes_json, content_hash, updated_at
       UPDATE sync_metadata with new content_hash, mtime, indexed_at
       Async: ChromaDB upsert for semantic index
       MtimeCache.invalidate(path)  # force re-read on next access

5. PROCESS NEW FILES (bucket c)
   For each new file:
   → Read YAML, parse, compute content_hash
   → INSERT INTO entities (...)
   → INSERT INTO sync_metadata (...)
   → Async: ChromaDB insert

6. PROCESS DELETED FILES (bucket d)
   For each deleted file:
   → DELETE FROM entities WHERE yaml_path = path
   → DELETE FROM sync_metadata WHERE yaml_path = path
   → Async: ChromaDB delete by entity_id
   → MtimeCache.invalidate(path)

7. FINALIZE
   → Log summary:
     "Incremental sync complete: 142 unchanged, 3 changed, 1 new, 0 deleted (12ms)"
   → Compare to sync_all():
     "Full sync would have processed 146 files (~2.1s). Saved ~2.1s."
   → Update last_incremental_sync timestamp in app state
   → Server ready to accept requests

FALLBACK — FULL RESYNC
   Triggered by: `antigravity db reindex` CLI command or `POST /api/v1/db/reindex`
   → Drop all sync_metadata rows
   → Process ALL disk files as "new" (bucket c)
   → Rebuild entities table from scratch
   → Rebuild ChromaDB vectors
   → Invalidate entire MtimeCache
   → This is the nuclear option — only needed after schema migrations or corruption
```

---

## 8. SSE Streaming Endpoints

| Endpoint | Purpose | Consumer | Event Format |
|----------|---------|----------|--------------|
| `GET /api/pipeline/{id}/stream` | Pipeline step/state transitions | `usePipelineStream` hook | `PipelineRun.model_dump_json()` on every state change |
| `GET /api/v1/project/events` | File watcher changes, KG updates | `graphDataSlice` | `{ "type": "container_updated", "container_id": "...", ... }` |
| `GET /api/v1/timeline/stream`* | New event sourcing events | `TimelineView` | `{ "type": "event_appended", "event": {...} }` |
| `POST /api/v1/chat/sessions/{id}/messages`* | Chat message response streaming | `useChatStream` hook | `ChatEvent` (token, action_trace, artifact, approval_needed, complete, error) |
| `GET /api/v1/chat/sessions/{id}/stream`* | Persistent SSE for background task updates | `useChatStream` hook | `ChatEvent` (background_update only) |

*Phase J additions. The chat message endpoint uses POST (not GET) because it sends the user's message in the request body and returns the streamed response via SSE — this is a combined send-and-stream pattern similar to Claude API's streaming response.

---

## 9. Known Limitations & Phase F–I Remediation Plan

| Area | Current State | Target | Severity | Phase |
|------|--------------|--------|:--------:|:-----:|
| **Event Sourcing** | `WritingService` calls `append_event()`; `StoryboardService` calls it; `PipelineService` does not | ALL services call `append_event()` on every mutation | 🔴 | F |
| **GenericContainer fields** | Missing `parent_id`, `context_window`, `timeline_positions`, `tags`, `model_preference`, `sort_order` | Add all 6 fields to `GenericContainer` | 🔴 | F |
| **Story Structure** | No hierarchy — only flat containers | Season → Arc → Act → Chapter → Scene via `parent_id` chain + `sort_order` | 🔴 | F |
| **Model Selection** | Hardcoded to `gemini/gemini-2.0-flash` in step configs | `ModelConfigRegistry` cascade: Step > Bucket > Agent > Project | 🟠 | F |
| **Context Engineering** | `ContextEngine` exists but not injected into `PipelineService` | Inject `ContextEngine` into every agent invocation and pipeline step | 🟠 | F |
| **Multi-Project** | Single project in `Path.cwd()` | Project directory isolation, project-scoped `get_project(project_id)` | 🟠 | F |
| **Pipeline Run Persistence** | Active runs in `_runs: Dict[str, PipelineRun]` (lost on restart) | Persist completed runs as `GenericContainer` with `container_type: "pipeline_run"` | 🟠 | F |
| **Research Library** | Does not exist | Research Agent + persistent `research_topic` buckets + auto-injection into context | 🟠 | G |
| **Logic Steps** | Pipeline supports only linear/DAG with 11 step types | Add `if_else`, `loop`, `merge_outputs` step types (total: 17) | 🟡 | G |
| **Workflow Templates** | Does not exist | Pre-built `PipelineDefinition` YAML files + `TemplateGallery.tsx` UI | 🟡 | G |
| **Agent Skills** | 5 static markdown files, keyword routing | 10+ agents, ReAct executors, model-specific routing | 🟡 | G+H |
| **RAG** | ChromaDB indexer exists but not widely used | Vector search integrated into `ContextEngine.assemble_context()` | 🟡 | H |
| **Continuity Auto-check** | Manual only | Auto-run `Continuity Analyst` on every scene save | 🟡 | H |
| **Command Center** | Dashboard shows only KG canvas | Multi-project launcher, progress overview, pending approvals, model config | 🟡 | I |
| **Auth** | None (local-only) | User auth for cloud deploy | 🟡 | I |

---

## 10. Phase Next-B: Emotional Intelligence — Detailed Design

Phase Next-B adds three analytical features that give writers superpowers no competitor offers. These are parallelizable into two independent work streams.

### 10.1 New Backend Service: `AnalysisService`

**File:** `src/antigravity_tool/services/analysis_service.py`

```python
from dataclasses import dataclass, field

@dataclass
class EmotionalScore:
    """Per-scene emotional analysis result."""
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    hope: float          # 0.0–1.0
    conflict: float      # 0.0–1.0
    tension: float       # 0.0–1.0
    sadness: float       # 0.0–1.0
    joy: float           # 0.0–1.0
    dominant_emotion: str # "tension", "hope", etc.
    summary: str         # 1-line explanation

@dataclass
class EmotionalArcResult:
    """Full emotional arc analysis across scenes."""
    scores: list[EmotionalScore]
    flat_zones: list[dict]    # { start_scene, end_scene, reason }
    peak_moments: list[dict]  # { scene_id, emotion, intensity }
    pacing_grade: str         # "A", "B", "C", "D", "F"
    recommendations: list[str]

@dataclass
class VoiceProfile:
    """Per-character voice analysis."""
    character_id: str
    character_name: str
    avg_sentence_length: float
    vocabulary_diversity: float  # unique words / total words
    formality_score: float       # 0.0 (casual) – 1.0 (formal)
    top_phrases: list[str]       # Most distinctive phrases
    dialogue_sample_count: int

@dataclass
class VoiceScorecardResult:
    """Comparison of character voices across the story."""
    profiles: list[VoiceProfile]
    similarity_matrix: list[dict]  # pairs with similarity > 0.7
    warnings: list[str]            # "Zara and Kael sound 82% similar"

@dataclass
class CharacterRibbon:
    """Per-scene character presence data for ribbon visualization."""
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    characters: list[dict]  # { character_id, character_name, prominence: 0.0–1.0 }


class AnalysisService:
    """Analyzes story content for emotional arcs, character voices, and ribbons."""

    def __init__(self, kg_service, container_repo, context_engine):
        self.kg_service = kg_service
        self.container_repo = container_repo
        self.context_engine = context_engine

    async def analyze_emotional_arc(self, chapter: int | None = None) -> EmotionalArcResult:
        """
        Score each scene for emotional valence using LLM analysis.
        If chapter is None, analyze all chapters.
        Returns scores + flat zones + recommendations.
        """
        ...

    async def analyze_character_voices(self, character_ids: list[str] | None = None) -> VoiceScorecardResult:
        """
        Extract dialogue per character, compute voice metrics.
        If character_ids is None, analyze all characters with dialogue.
        Returns profiles + similarity warnings.
        """
        ...

    def compute_character_ribbons(self, chapter: int | None = None) -> list[CharacterRibbon]:
        """
        Derive character presence + prominence per scene from KG relationships.
        No LLM call — pure KG query + heuristic scoring.
        Returns ribbon data for SVG visualization.
        """
        ...
```

### 10.2 New API Endpoints

**Router:** `src/antigravity_tool/server/routers/analysis.py`

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| `GET` | `/api/v1/analysis/emotional-arc` | Query: `?chapter=N` (optional) | `EmotionalArcResponse` | LLM-scored emotional valence per scene |
| `GET` | `/api/v1/analysis/voice-scorecard` | Query: `?character_ids=a,b,c` (optional) | `VoiceScorecardResponse` | Character voice analysis + similarity |
| `GET` | `/api/v1/analysis/ribbons` | Query: `?chapter=N` (optional) | `list[CharacterRibbonResponse]` | Character presence per scene for SVG |

**Pydantic response models** in `api_schemas.py`:

```python
class EmotionalScoreResponse(BaseModel):
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    hope: float
    conflict: float
    tension: float
    sadness: float
    joy: float
    dominant_emotion: str
    summary: str

class EmotionalArcResponse(BaseModel):
    scores: list[EmotionalScoreResponse]
    flat_zones: list[dict]
    peak_moments: list[dict]
    pacing_grade: str
    recommendations: list[str]

class VoiceProfileResponse(BaseModel):
    character_id: str
    character_name: str
    avg_sentence_length: float
    vocabulary_diversity: float
    formality_score: float
    top_phrases: list[str]
    dialogue_sample_count: int

class VoiceScorecardResponse(BaseModel):
    profiles: list[VoiceProfileResponse]
    similarity_matrix: list[dict]
    warnings: list[str]

class CharacterRibbonResponse(BaseModel):
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    characters: list[dict]
```

### 10.3 New Frontend Components

#### Emotional Arc Dashboard (`EmotionalArcChart.tsx`)

**File:** `src/web/src/components/timeline/EmotionalArcChart.tsx`

```
┌─────────────────────────────────────────────────────────┐
│ Emotional Arc                              [Analyze] 🔄 │
├─────────────────────────────────────────────────────────┤
│ 1.0 ┤                                                   │
│     │      ╱╲        ╱╲                                 │
│ 0.5 ┤   ╱╱  ╲╲   ╱╱  ╲╲____╱╲                         │
│     │ ╱╱      ╲╲╱╱              ╲╲                      │
│ 0.0 ┤──────────────────────────────╲╲                   │
│     Sc1  Sc2  Sc3  Sc4  Sc5  Sc6  Sc7  Sc8             │
│                                                          │
│  Legend: ─ Hope  ─ Tension  ─ Conflict  ─ Joy           │
│                                                          │
│ ⚠ Flat Zone: Scenes 3–5 (no tension peaks)              │
│ ⭐ Peak Moment: Scene 2 (tension: 0.95)                  │
│ Pacing Grade: B                                          │
│ Rec: "Consider adding a minor conflict in the Sc3-5 run"│
└─────────────────────────────────────────────────────────┘
```

- **Charting library:** `recharts` (already lightweight, React-native)
- **Interaction:** Click a scene data point → selects it in the workbench inspector
- **State:** Lives on the Timeline page, fetches from `/api/v1/analysis/emotional-arc`

#### Story Ribbons (`StoryRibbons.tsx`)

**File:** `src/web/src/components/timeline/StoryRibbons.tsx`

```
┌─────────────────────────────────────────────────────────┐
│ Story Ribbons                                           │
├─────────────────────────────────────────────────────────┤
│ Zara:  ████████░░████████████████████░░████████████     │
│ Kael:  ░░░░████████████░░░░░░████████████████████░     │
│ Lira:  ░░░░░░░░████░░░░░░░░░░░░░░████░░░░░░████░     │
│        Sc1  Sc2  Sc3  Sc4  Sc5  Sc6  Sc7  Sc8         │
│                                                         │
│ Legend: █ = Present  ░ = Absent  Width = Prominence     │
└─────────────────────────────────────────────────────────┘
```

- **Rendering:** Pure SVG with `<rect>` elements per character per scene
- **Color:** Each character gets a consistent color from a palette
- **Thickness:** Maps to `prominence` value (0.0–1.0)
- **Interaction:** Hover shows tooltip with character name + scene + prominence %
- **State:** Fetches from `/api/v1/analysis/ribbons`, lives on Timeline page

#### Character Voice Scorecard (`CharacterVoiceScorecard.tsx`)

**File:** `src/web/src/components/workbench/CharacterVoiceScorecard.tsx`

```
┌─────────────────────────────────────────────────────────┐
│ Voice Analysis                             [Analyze] 🔄 │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┬────────┬─────────┬──────────┬────────────┐ │
│ │ Name    │ AvgLen │ Vocab   │ Formality│ Phrases    │ │
│ ├─────────┼────────┼─────────┼──────────┼────────────┤ │
│ │ Zara    │ 12.3   │ 0.78    │ 0.45     │ "damn it", │ │
│ │         │        │         │          │ "let's go" │ │
│ │ Kael    │ 18.7   │ 0.62    │ 0.82     │ "Indeed",  │ │
│ │         │        │         │          │ "observe"  │ │
│ └─────────┴────────┴─────────┴──────────┴────────────┘ │
│                                                          │
│ ⚠ Warning: Lira and Kael sound 82% similar              │
│   Suggestion: Give Lira shorter, more abrupt sentences   │
└─────────────────────────────────────────────────────────┘
```

- **Location:** Rendered inside `CharacterInspector.tsx` when viewing a character
- **Also accessible:** From a dedicated "Voice Analysis" section on the Timeline page for cross-character comparison
- **State:** Fetches from `/api/v1/analysis/voice-scorecard`

### 10.4 DI Wiring

Add to `server/deps.py`:

```python
def get_analysis_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    context_engine: ContextEngine = Depends(get_context_engine),
) -> AnalysisService:
    return AnalysisService(kg_service, container_repo, context_engine)
```

### 10.5 API Client Additions

Add to `src/web/src/lib/api.ts`:

```typescript
// Analysis
getEmotionalArc: (chapter?: number) =>
  request<EmotionalArcResponse>(
    chapter ? `/api/v1/analysis/emotional-arc?chapter=${chapter}` : "/api/v1/analysis/emotional-arc"
  ),
getVoiceScorecard: (characterIds?: string[]) =>
  request<VoiceScorecardResponse>(
    characterIds
      ? `/api/v1/analysis/voice-scorecard?character_ids=${characterIds.join(",")}`
      : "/api/v1/analysis/voice-scorecard"
  ),
getCharacterRibbons: (chapter?: number) =>
  request<CharacterRibbonResponse[]>(
    chapter ? `/api/v1/analysis/ribbons?chapter=${chapter}` : "/api/v1/analysis/ribbons"
  ),
```

### 10.6 Parallelization Strategy

Phase Next-B splits cleanly into two independent work streams:

| Session | Features | Touches | Dependencies |
|---------|----------|---------|--------------|
| **Session A** | Emotional Arc Dashboard + Story Ribbons | Timeline page, `AnalysisService` (emotional_arc + ribbons methods), `analysis.py` router (2 endpoints), 2 new frontend components | Existing KG + scene data |
| **Session B** | Character Voice Scorecard | CharacterInspector, `AnalysisService` (voice methods), `analysis.py` router (1 endpoint), 1 new frontend component | Existing character + fragment data |

Both sessions create the same `AnalysisService` file but implement different methods. Session A creates the file; Session B adds to it (or they merge afterward).

---

## 11. Phase Next-C: Panel Intelligence — Detailed Design

### 11.1 Panel Layout Intelligence

**Backend:** Add `suggest_layout(scene_id, scene_text, scene_name) -> dict` to `StoryboardService`. Uses LLM to analyze narrative beat type (action/dialogue/reveal/transition/montage/emotional) and suggest panel count, sizes, camera angles, and composition notes.

**API:** `POST /api/v1/storyboard/scenes/{scene_id}/suggest-layout` → `LayoutSuggestionResponse`

**Frontend:** `LayoutSuggestionPanel.tsx` — Visual preview of suggested panel sizes/types with "Apply & Generate" button. Integrated into `SceneStrip.tsx` as "Suggest Layout" button.

### 11.2 Character Progressions

**Backend:** Store visual DNA evolution as `attributes.progressions` array on character containers. CRUD endpoints at `/api/v1/characters/{id}/progressions`. `GET /dna-at-chapter/{chapter}` resolves DNA by deep-merging base + all progressions up to that chapter.

**Frontend:** `CharacterProgressionTimeline.tsx` — Horizontal timeline with nodes at each progression chapter. Inline editing, add/delete stages. Integrated into `CharacterInspector.tsx`.

### 11.3 Reader Scroll Simulation

**Backend:** New `ReaderSimService` with `simulate_reading(scene_id)` — heuristic-based (no LLM). Estimates per-panel reading time, text density, info-dense flags, pacing dead zones, engagement score.

**API:** `GET /api/v1/preview/scene/{scene_id}`, `GET /api/v1/preview/chapter/{chapter}`

**Frontend:** New `/preview` route with vertical panel scroll (70%) + pacing sidebar (30%). Auto-scroll player with speed control. Info-dense panel warnings, dead zone highlights, engagement percentage.

### 11.4 Parallelization Strategy

| Session | Features | Touches |
|---------|----------|---------|
| **Session 22** | Panel Layout Intelligence + Enhanced Approval Gate | StoryboardService, SceneStrip, PromptReviewModal, pipeline_service |
| **Session 23** | Character Progressions + Reader Scroll Sim | CharacterInspector, new /preview route, new ReaderSimService |
| **Session 24** | Workflow Templates + Research UI | PipelineService, TemplateGallery, new /research page |

---

## 12. Phase Next-D: Workflow Power — Detailed Design

### 12.1 Workflow Templates Library

**Backend:** New `src/antigravity_tool/templates/workflow_templates.py` with 5 templates as PipelineDefinition data:
1. Scene → Panels (gather → prompt → review → generate → save)
2. Concept → Outline (input → brainstorm → review → architect → approve → save)
3. Outline → Draft (gather → prompt → review → draft → save)
4. Topic → Research (input → research_deep_dive → review → save)
5. Draft → Polish (gather → style_check → review → final_edit → approve → save)

**API:** `GET /api/pipeline/templates`, `POST /api/pipeline/templates/{id}/create`

**Frontend:** Update `TemplateGallery.tsx` to fetch templates from API instead of hardcoded data. "Use Template" creates a definition and opens it in the builder.

### 12.2 Enhanced Approval Gate

**Backend:** Extend `_handle_llm_generate` in `pipeline_service.py` to support `temperature_override` and `pinned_context_ids` from the resume payload.

**Frontend:** Add to `PromptReviewModal.tsx`:
- Temperature slider (0–2, step 0.1) in header
- Pin/unpin toggle per context bucket in Glass Box
- "Regenerate" button (amber) in footer that re-runs with changed parameters

### 12.3 Research Agent UI Surface

**Backend:** Already exists (`research_service.py` + `research.py` router). No backend changes needed.

**Frontend:** New `/research` page with:
- Left panel: Research topic list with search/filter + confidence indicators
- Right panel: Structured topic detail (summary, key_facts, constraints, story_implications)
- Bottom: New research query input triggering agent execution
- "Link to Scene" dropdown for relationship creation
- `ResearchTopicCard.tsx` + `ResearchDetailPanel.tsx` components

---

## 13. Phase Next-E: Spatial & Structural — Implementation Summary ✅

### 13.1 Story Structure Visual Editor ✅

**Backend (implemented):**
- `src/antigravity_tool/server/routers/containers.py` (131 lines) with prefix `/api/v1/containers`:
  - `POST /` — Create container (type-validated: season/arc/act/chapter/scene)
  - `GET /{id}` — Get container by ID
  - `PUT /{id}` — Update container (name, sort_order, parent_id, attributes)
  - `DELETE /{id}` — Delete container + remove from KG + emit event
  - `POST /reorder` — Bulk update sort_order for siblings
- `ContainerRepository` extended with `get_by_id()` and `delete_by_id()` (81 lines total)
- Fixed `getProjectStructure()` API URL mismatch in `projectSlice.ts`

**Frontend (implemented in `StoryStructureTree.tsx`, 479 lines):**
- "Add Child" button per node (Season→Arc, Arc→Act, Act→Chapter, Chapter→Scene)
- Delete button with confirmation dialog
- "Open in Zen" for scene nodes → `router.push('/zen?scene_id=...')`
- Drag reorder wired to bulk `POST /containers/reorder`
- Completion status color-coding (green/amber/blue left border)

### 13.2 Alternate Timeline Browser ✅

**Backend (implemented):**
- `EventService` extended (256 lines total) with `get_branches()`, `get_events_for_branch()`, `compare_branches()` (recursive CTE state projection diff)
- Timeline router expanded (111 lines total):
  - `GET /branches` — List branches with event counts
  - `POST /branch` — Create branch from historical event
  - `GET /branch/{id}/events` — Events filtered per branch
  - `GET /compare?branch_a=X&branch_b=Y` — Side-by-side state diff
  - `GET /stream` — SSE real-time event streaming

**Frontend (implemented):**
- `BranchList.tsx` (96 lines) — Sidebar with event counts + active indicator
- `BranchComparison.tsx` (161 lines) — Two-column diff: additions (green), removals (red), changes (amber)
- Integrated into `timeline/page.tsx` (147 lines) left panel below `StoryStructureTree`

### 13.3 Spatial Brainstorming Canvas ✅

**Backend (implemented in `director.py`, 194 lines total):**
- `POST /brainstorm/suggest-connections` — AI-suggested edges/new cards/themes via `brainstorm_agent` skill
- `POST /brainstorm/save-card` — Persist idea card as `GenericContainer` with `container_type: "idea_card"`
- `GET /brainstorm/cards` — List all idea cards
- `DELETE /brainstorm/cards/{id}` — Delete card

**Frontend (implemented):**
- `/brainstorm` page with ReactFlow infinite canvas (`@xyflow/react` v12)
- `IdeaCardNode.tsx` (116 lines) — Editable text, color coding, auto-save on drag-end/blur, delete button
- `SuggestionPanel.tsx` (189 lines) — AI suggestions with accept/dismiss, theme clusters
- Auto-save card positions, load on mount, minimap navigation
- "Suggest" button triggers `brainstorm_agent` analysis
- Brainstorm nav link added to `Canvas.tsx` (200 lines)

### 13.4 Voice-to-Scene ✅

**Backend (implemented in `storyboard.py`, 193 lines total):**
- `POST /api/v1/storyboard/voice-to-scene` — Receives transcribed text, orchestrates `suggest_layout()` → `generate_panels_for_scene()`, returns layout suggestion + generated panels

**Frontend (implemented):**
- `VoiceToSceneButton.tsx` — Browser-native Web Speech API with three states (idle/recording/processing)
- Live transcript + editable textarea review + scene selector + panel count config
- Generated panel preview with "Apply to Scene" / "Discard"
- Integrated into `storyboard/page.tsx` (138 lines) header next to Strip/Canvas toggle
- Textarea fallback for browsers without speech support

### 13.5 Execution Summary

Both sessions completed successfully with zero file conflicts:

| Session | Features | Files Created/Modified |
|---------|----------|----------------------|
| **Session 25** ✅ | Story Structure Editor + Alternate Timeline Browser | `containers.py` (new, 131L), `container_repo.py` (81L), `event_sourcing_repo.py` (256L), `timeline.py` (111L), `StoryStructureTree.tsx` (479L), `timeline/page.tsx` (147L), `BranchList.tsx` (new, 96L), `BranchComparison.tsx` (new, 161L), `api.ts` (822L) |
| **Session 26** ✅ | Spatial Brainstorm Canvas + Voice-to-Scene | `director.py` (194L), `storyboard.py` (193L), `brainstorm/page.tsx` (new), `IdeaCardNode.tsx` (new, 116L), `SuggestionPanel.tsx` (new, 189L), `VoiceToSceneButton.tsx` (new), `storyboard/page.tsx` (138L), `Canvas.tsx` (200L), `api.ts` (822L) |

TypeScript validation: 0 errors across entire `src/web/` directory. Next.js build: successful.

---

## 14. Phase H: Intelligence Layer — Implementation Summary ✅

All 5 features completed across 3 sessions (27–29). 21 files created/modified.

### 14.1 Continuity Auto-Check ✅
- `ContinuityService` (208 lines) — `check_continuity()`, `check_scene_continuity()`, `get_recent_issues()`. Gathers KG context + future dependencies, routes through `continuity_analyst` skill. Returns ContinuityVerdict (status, reasoning, suggestions, affected_entities, severity).
- 3 endpoints on `analysis.py`: `POST /continuity-check`, `POST /continuity-check/scene/{id}`, `GET /continuity-issues`
- `ContinuityPanel.tsx` (117 lines) — Severity-coded issue cards (error/warning/info) in ContextSidebar "Continuity" tab

### 14.2 Style Enforcer ✅
- `StyleService` (145 lines) — `evaluate_style(text, scene_id?)`. Loads `NarrativeStyleGuide` from containers, routes through `style_enforcer` skill. Returns StyleEvaluation (status, overall_score, issues[], strengths[], summary).
- Endpoint: `POST /style-check` on `analysis.py`
- `StyleScorecard.tsx` (155 lines) — Score gauge + categorized issues + strengths in ContextSidebar "Style" tab
- Style tab added to `PromptReviewModal.tsx` (425 lines total)
- `/check-style` slash command wired in `SlashCommandList.tsx`

### 14.3 Translation Agent UI ✅
- `TranslationService` (207 lines) — `translate()` with glossary, character profiles, cultural adaptation. Routes through `translator_agent` skill. Returns (translated_text, adaptation_notes, cultural_flags, glossary_applied, confidence).
- `translation.py` router (83 lines): `POST /translate`, `GET /glossary`, `POST /glossary`
- `TranslationPanel.tsx` (351 lines) — Two-column source/target with adaptation notes
- `/translation` page (Translation Studio, 26 lines)
- `InlineTranslation.tsx` (257 lines) — Compact widget in ContextSidebar "Translation" tab with Replace/Insert Below actions
- `/translate` slash command wired in `SlashCommandList.tsx`

### 14.4 NL → Workflow Generation ✅
- Backend: Already existed (`PipelineService.generate_pipeline_from_nl()` + `POST /api/pipeline/definitions/generate`)
- `NLPipelineWizard.tsx` (206 lines) — Modal with textarea, example prompts, "Open in Builder" action
- "Create from Description" button integrated into `pipelines/page.tsx` (210 lines)

### 14.5 Semantic @Mentions in Zen Mode ✅
- `GET /api/v1/writing/semantic-search` endpoint on `writing.py` (95 lines total) using `kg_service.semantic_search()` via ChromaDB
- `ZenEditor.tsx` (432 lines) — @mention suggestions upgraded from keyword to semantic vector search
- `MentionList.tsx` — Relevance indicator in dropdown

### 14.6 Execution Summary

| Session | Features | Status |
|---------|----------|--------|
| **Session 27** | Continuity Auto-Check + Style Enforcer | ✅ Complete |
| **Session 28** | Translation Agent UI + NL Pipeline Wizard | ✅ Complete |
| **Session 29** | Semantic @Mentions + /translate Slash + Integration | ✅ Complete |

Parallelization strategy (27 ∥ 28, then 29) executed cleanly with zero file conflicts.

## 15. Phase I: Polish — Detailed Design

### 15.1 Persistent Navbar + Command Palette + Error Boundary (Session 30)

**New components:**
- `Navbar.tsx` — Sticky top navbar with route-aware active tabs (9 pages), logo, Cmd+K trigger
- `CommandPalette.tsx` — cmdk-powered overlay with page navigation, actions, search
- `ErrorBoundary.tsx` — React class component with crash recovery fallback UI

**Modifications:**
- `layout.tsx` — Add Navbar + ErrorBoundary wrapping children
- `Canvas.tsx` — Remove cross-page nav links (keep Graph/Timeline toggle + DirectorControls)

### 15.2 Export UI + HTML/PDF Export (Session 31)

**Backend:**
- `export_service.py` — Add `export_html()` method generating styled, print-friendly HTML document
- `export.py` — Add `POST /html` (download) and `POST /preview` (inline) endpoints

**Frontend:**
- `ExportModal.tsx` — Format selector (Markdown/JSON/Fountain/HTML), preview area, download + print-to-PDF
- `ProgressOverview.tsx` — Export trigger button + custom event listener (`open:export`)
- `api.ts` — 5 export methods (exportManuscript, exportBundle, exportScreenplay, exportHTML, exportPreview)

### 15.3 Zen Mode Polish (Session 32)

**Frontend:**
- `ZenEditor.tsx` — Real-time word/char/reading-time count, focus mode (Cmd+Shift+F), session writing stats, keyboard shortcuts overlay (Cmd+/)
- `zenSlice.ts` — Session stats state (sessionStartWordCount, sessionWordsWritten, sessionStartTime)
- `zen/page.tsx` — Simplified header (remove redundant nav links)
- `globals.css` — Focus mode paragraph dimming CSS

**Backend:**
- `writing_service.py` — Compute word_count on fragment save
- `writing.py` — Include word_count in response
- `api_schemas.py` — Add word_count to FragmentResponse

### 15.4 Parallelization Strategy

| Session | Features | Parallel? |
|---------|----------|-----------|
| **Session 30** | Navbar + Command Palette + Error Boundary | ✅ Parallel with 31 |
| **Session 31** | Export UI + HTML Export | ✅ Parallel with 30 |
| **Session 32** | Zen Mode Polish | ⏳ Sequential (after 30+31, touches api.ts) |

Sessions 30 and 31 have zero file overlap. Session 32 touches api.ts (also modified by 31) so runs after both complete.

---

## 16. Phase J: Testing & Evaluation Strategy for Agentic Chat

### 16.1 Test Infrastructure Setup

**Backend:**
- Framework: `pytest` + `pytest-asyncio` (existing)
- New shared fixtures in `tests/conftest.py` (currently missing — create as part of Phase J)

```python
# tests/conftest.py — Phase J additions

@pytest.fixture
def project_path(tmp_path):
    """Create a temporary project directory with required structure."""
    (tmp_path / ".antigravity" / "sessions").mkdir(parents=True)
    (tmp_path / "containers").mkdir()
    (tmp_path / "schemas").mkdir()
    (tmp_path / "antigravity.yaml").write_text("name: test-project\n")
    return tmp_path

@pytest.fixture
def chat_session_repo(project_path):
    """ChatSessionRepository with temporary storage."""
    return ChatSessionRepository(project_path)

@pytest.fixture
def project_memory_repo(project_path):
    """ProjectMemoryRepository with temporary storage."""
    return ProjectMemoryRepository(project_path)

@pytest.fixture
def mock_llm():
    """AsyncMock for LiteLLM completion calls."""
    mock = AsyncMock()
    mock.return_value = _make_llm_response("Mock LLM response")
    return mock

@pytest.fixture
def mock_agent_dispatcher():
    """AgentDispatcher with mocked skills and LLM calls."""
    dispatcher = AsyncMock(spec=AgentDispatcher)
    dispatcher.route.return_value = AgentSkill(name="writing_agent", system_prompt="...")
    dispatcher.execute.return_value = AgentResult(content="Generated content", tokens_in=100, tokens_out=50)
    return dispatcher

@pytest.fixture
def chat_session_service(project_path):
    """ChatSessionService with temporary storage."""
    return ChatSessionService(project_path)

@pytest.fixture
def project_memory_service(project_path):
    """ProjectMemoryService with temporary storage."""
    return ProjectMemoryService(project_path)

def _make_llm_response(content: str):
    """Helper to create a mock LiteLLM response."""
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])
```

**Frontend:**
- Framework: Vitest + React Testing Library (new — add to `src/web/package.json`)
- E2E: Playwright (new — add to project root)

### 16.2 Unit Tests — Backend

#### `tests/test_chat_orchestrator.py`

```python
class TestChatOrchestrator:
    """Test the central chat brain."""

    async def test_classify_intent_write(self, mock_llm):
        """User message about writing → WRITE tool intent."""
        orchestrator = ChatOrchestrator(...)
        intent = await orchestrator._classify_intent(
            "write a scene where Zara enters the market", ""
        )
        assert intent.tool == "WRITE"
        assert intent.confidence > 0.8

    async def test_classify_intent_pipeline(self, mock_llm):
        """User message about running pipeline → PIPELINE tool intent."""
        intent = await orchestrator._classify_intent(
            "run Scene→Panels on Ch.3 Sc.1", ""
        )
        assert intent.tool == "PIPELINE"

    async def test_classify_intent_ambiguous(self, mock_llm):
        """Ambiguous message → low confidence, asks for clarification."""
        intent = await orchestrator._classify_intent("help me", "")
        assert intent.confidence < 0.5

    async def test_tool_execution_produces_trace(self, mock_agent_dispatcher):
        """Every tool execution must produce a ChatActionTrace."""
        trace = await orchestrator._execute_tool(
            ToolIntent(tool="WRITE", params={...}), session, context
        )
        assert isinstance(trace, ChatActionTrace)
        assert trace.tool_name == "WRITE"
        assert trace.model_used != ""
        assert trace.duration_ms > 0

    async def test_agent_to_agent_depth_limit(self, mock_agent_dispatcher):
        """Agent invocation respects MAX_AGENT_DEPTH."""
        with pytest.raises(AgentDepthExceeded):
            await orchestrator._invoke_agent("writing_agent", "test", "", depth=4)

    async def test_agent_to_agent_circular_detection(self, mock_agent_dispatcher):
        """Circular agent calls are rejected."""
        with pytest.raises(AgentCircularCall):
            await orchestrator._invoke_agent(
                "writing_agent", "test", "", depth=1,
                call_chain=["writing_agent"]
            )

    async def test_agent_to_agent_records_sub_invocation(self, mock_agent_dispatcher):
        """Sub-agent invocation recorded in parent trace."""
        invocation = await orchestrator._invoke_agent(
            "continuity_analyst", "check consistency", "", depth=1,
            call_chain=["writing_agent"]
        )
        assert invocation.caller_agent_id == "writing_agent"
        assert invocation.callee_agent_id == "continuity_analyst"
        assert invocation.depth == 1

    async def test_process_message_streams_events(self, mock_agent_dispatcher):
        """process_message yields correct ChatEvent sequence."""
        events = []
        async for event in orchestrator.process_message(session, "write a scene", []):
            events.append(event)
        event_types = [e.event_type for e in events]
        assert "token" in event_types or "action_trace" in event_types
        assert event_types[-1] == "complete"

    async def test_autonomy_level_ask_pauses(self):
        """Level 0 (ASK) yields approval_needed before executing."""
        session.autonomy_level = AutonomyLevel.ASK
        events = [e async for e in orchestrator.process_message(session, "create a character", [])]
        assert events[0].event_type == "approval_needed"
```

#### `tests/test_chat_session_service.py`

```python
class TestChatSessionService:
    """Test session lifecycle: create, messages, compact, end, resume."""

    async def test_create_session(self, chat_session_service):
        session = await chat_session_service.create_session("worldbuilding", "proj_1")
        assert session.name == "worldbuilding"
        assert session.state == SessionState.ACTIVE
        assert session.token_usage == 0

    async def test_add_message_updates_token_usage(self, chat_session_service):
        session = await chat_session_service.create_session("test", "proj_1")
        msg = ChatMessage(session_id=session.id, role="user", content="Hello " * 100)
        await chat_session_service.add_message(session.id, msg)
        updated = await chat_session_service.get_session(session.id)
        assert updated.token_usage > 0
        assert msg.id in updated.message_ids

    async def test_compact_session_reduces_tokens(self, chat_session_service, mock_llm):
        """Compaction reduces token usage and produces a digest."""
        session = await chat_session_service.create_session("test", "proj_1")
        # Add many messages to simulate high token usage
        for i in range(20):
            msg = ChatMessage(session_id=session.id, role="user", content=f"Message {i} " * 50)
            await chat_session_service.add_message(session.id, msg)
        result = await chat_session_service.compact_session(session.id, mock_llm)
        assert result.token_reduction > 0
        assert result.digest != ""
        assert result.compaction_number == 1

    async def test_end_session_sets_state(self, chat_session_service):
        session = await chat_session_service.create_session("test", "proj_1")
        await chat_session_service.end_session(session.id, "Finished worldbuilding")
        ended = await chat_session_service.get_session(session.id)
        assert ended.state == SessionState.ENDED

    async def test_resume_session_restores_active(self, chat_session_service):
        session = await chat_session_service.create_session("test", "proj_1")
        await chat_session_service.end_session(session.id, "Done")
        resumed = await chat_session_service.resume_session(session.id)
        assert resumed.state == SessionState.ACTIVE

    async def test_list_sessions(self, chat_session_service):
        await chat_session_service.create_session("session1", "proj_1")
        await chat_session_service.create_session("session2", "proj_1")
        sessions = await chat_session_service.list_sessions("proj_1")
        assert len(sessions) == 2

    async def test_get_messages_paginated(self, chat_session_service):
        session = await chat_session_service.create_session("test", "proj_1")
        for i in range(10):
            msg = ChatMessage(session_id=session.id, role="user", content=f"Msg {i}")
            await chat_session_service.add_message(session.id, msg)
        page1 = await chat_session_service.get_messages(session.id, offset=0, limit=5)
        assert len(page1) == 5
```

#### `tests/test_project_memory_service.py`

```python
class TestProjectMemoryService:
    """Test persistent project memory CRUD and context injection."""

    async def test_add_entry(self, project_memory_service):
        entry = await project_memory_service.add_entry("tone", "Dark fantasy, literary")
        assert entry.key == "tone"
        assert entry.scope == MemoryScope.GLOBAL
        assert entry.auto_inject == True

    async def test_add_entry_replaces_existing(self, project_memory_service):
        await project_memory_service.add_entry("tone", "Dark fantasy")
        await project_memory_service.add_entry("tone", "Light comedy")
        entries = await project_memory_service.list_entries()
        assert len(entries) == 1
        assert entries[0].value == "Light comedy"

    async def test_remove_entry(self, project_memory_service):
        await project_memory_service.add_entry("tone", "Dark fantasy")
        removed = await project_memory_service.remove_entry("tone")
        assert removed == True
        entries = await project_memory_service.list_entries()
        assert len(entries) == 0

    async def test_auto_inject_context(self, project_memory_service):
        await project_memory_service.add_entry("tone", "Dark fantasy")
        await project_memory_service.add_entry("pov", "Close third-person")
        await project_memory_service.add_entry("debug_note", "test only",
                                                auto_inject=False)
        context = await project_memory_service.get_auto_inject_context()
        assert "Dark fantasy" in context
        assert "Close third-person" in context
        assert "test only" not in context

    async def test_scoped_entries(self, project_memory_service):
        await project_memory_service.add_entry("tone", "Dark fantasy", scope=MemoryScope.GLOBAL)
        await project_memory_service.add_entry("mood", "Tense", scope=MemoryScope.CHAPTER, scope_id="ch5")
        global_entries = await project_memory_service.list_entries(scope=MemoryScope.GLOBAL)
        assert len(global_entries) == 1
```

#### `tests/test_chat_context_manager.py`

```python
class TestChatContextManager:
    """Test three-layer context assembly and token budget enforcement."""

    async def test_build_context_includes_all_layers(self, ...):
        """Context includes project memory, session history, and @-mentioned entities."""
        context = await context_manager.build_context(session, "test message", ["entity_1"])
        assert context.layer1_tokens > 0  # Project Memory
        assert context.layer2_tokens > 0  # Session History
        assert context.layer3_tokens > 0  # @-mentioned entity
        assert "entity_1" in context.entity_ids_included

    async def test_token_budget_enforced(self, ...):
        """Context assembly stays within session.context_budget."""
        session.context_budget = 1000  # Very small budget
        context = await context_manager.build_context(session, "test", [])
        assert context.token_estimate <= 1000

    async def test_compact_produces_digest(self, ...):
        """Compaction summarizes conversation to ~2K tokens."""
        result = await context_manager.compact(session)
        assert result.digest != ""
        assert len(result.digest) // 4 < 3000  # ~2K tokens

    async def test_should_suggest_compact(self, ...):
        """Suggests compaction when usage > 80% of budget."""
        session.context_budget = 10000
        session.token_usage = 8500
        assert context_manager._should_suggest_compact(session) == True
        session.token_usage = 5000
        assert context_manager._should_suggest_compact(session) == False
```

#### `tests/test_agent_composition.py`

```python
class TestAgentComposition:
    """Test agent-to-agent calling, depth limits, and circular prevention."""

    async def test_single_agent_invocation(self, mock_agent_dispatcher):
        invocation = await orchestrator._invoke_agent(
            "research_agent", "research railguns", "", depth=0
        )
        assert invocation.depth == 0
        assert invocation.callee_agent_id == "research_agent"

    async def test_nested_invocation(self, mock_agent_dispatcher):
        """Agent at depth 0 can invoke agent at depth 1."""
        invocation = await orchestrator._invoke_agent(
            "continuity_analyst", "check plot", "", depth=1,
            call_chain=["writing_agent"]
        )
        assert invocation.depth == 1

    async def test_max_depth_exceeded(self, mock_agent_dispatcher):
        with pytest.raises(AgentDepthExceeded):
            await orchestrator._invoke_agent("agent_a", "", "", depth=4)

    async def test_circular_call_detected(self, mock_agent_dispatcher):
        with pytest.raises(AgentCircularCall):
            await orchestrator._invoke_agent(
                "writing_agent", "", "", depth=2,
                call_chain=["writing_agent", "continuity_analyst"]
            )

    async def test_trace_nesting(self, mock_agent_dispatcher):
        """Sub-invocations produce nested traces."""
        # Mock: writing_agent invokes continuity_analyst
        invocation = await orchestrator._invoke_agent(
            "continuity_analyst", "verify", "", depth=1,
            call_chain=["writing_agent"]
        )
        assert invocation.trace.agent_id == "continuity_analyst"
        assert "writing_agent" in invocation.trace.context_summary
```

### 16.3 Integration Tests — Backend

#### `tests/test_chat_api.py`

```python
class TestChatAPI:
    """Full router integration tests using TestClient."""

    def test_create_session(self, client):
        resp = client.post("/api/v1/chat/sessions", json={"name": "test"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "test"
        assert resp.json()["state"] == "active"

    def test_list_sessions(self, client):
        client.post("/api/v1/chat/sessions", json={"name": "s1"})
        client.post("/api/v1/chat/sessions", json={"name": "s2"})
        resp = client.get("/api/v1/chat/sessions")
        assert len(resp.json()) == 2

    def test_send_message_streams_sse(self, client):
        session = client.post("/api/v1/chat/sessions", json={"name": "test"}).json()
        # Note: SSE testing requires special handling with TestClient
        resp = client.post(
            f"/api/v1/chat/sessions/{session['id']}/messages",
            json={"content": "hello"},
        )
        assert resp.status_code == 200

    def test_compact_session(self, client):
        session = client.post("/api/v1/chat/sessions", json={"name": "test"}).json()
        resp = client.post(f"/api/v1/chat/sessions/{session['id']}/compact")
        assert resp.status_code == 200
        assert "digest" in resp.json()

    def test_project_memory_crud(self, client):
        # Create
        resp = client.post("/api/v1/chat/memory",
                          json={"key": "tone", "value": "Dark fantasy"})
        assert resp.status_code == 200
        # Read
        resp = client.get("/api/v1/chat/memory")
        assert len(resp.json()["entries"]) == 1
        # Delete
        resp = client.delete("/api/v1/chat/memory/tone")
        assert resp.status_code == 204
```

#### `tests/test_chat_session_lifecycle.py`

```python
class TestChatSessionLifecycle:
    """End-to-end session lifecycle: create → messages → compact → end → resume."""

    async def test_full_lifecycle(self, chat_session_service, project_memory_service):
        # 1. Create session
        session = await chat_session_service.create_session("worldbuilding", "proj_1")

        # 2. Add messages
        for i in range(5):
            msg = ChatMessage(session_id=session.id, role="user", content=f"Build world part {i}")
            await chat_session_service.add_message(session.id, msg)

        # 3. Compact
        result = await chat_session_service.compact_session(session.id, mock_summarize)
        assert result.original_message_count == 5

        # 4. Add more messages after compaction
        msg = ChatMessage(session_id=session.id, role="user", content="Continue building")
        await chat_session_service.add_message(session.id, msg)

        # 5. End session
        await chat_session_service.end_session(session.id, "Finished worldbuilding")
        ended = await chat_session_service.get_session(session.id)
        assert ended.state == SessionState.ENDED
        assert ended.digest is not None

        # 6. Resume session
        resumed = await chat_session_service.resume_session(session.id)
        assert resumed.state == SessionState.ACTIVE
        # Digest preserved from end
        assert resumed.digest is not None
```

### 16.4 Evaluation Framework

Extend the existing `evaluator.py` / `evaluation_service.py` pattern to evaluate chat quality:

| Evaluation Dimension | Metric | Method | Target |
|---------------------|--------|--------|--------|
| **Intent Classification** | Accuracy on labeled test set | 100+ user messages with expected tool labels; measure precision/recall per tool | 90%+ accuracy |
| **Context Relevance** | Precision@K for included entities | For each @-mention, verify the correct container data is included in context | 95%+ precision |
| **Action Correctness** | Match rate against expected service calls | Given intent + context, verify the correct service method is called with correct params | 85%+ match |
| **Session Continuity** | Information retention after compact | After compact + resume, verify key decisions and entity states are preserved in digest | 90%+ retention |
| **Glass Box Completeness** | Trace coverage | Every agent action produces a valid `ChatActionTrace` with all required fields | 100% coverage |
| **Response Quality** | Human evaluation (1-5 scale) | Writers rate chat responses on helpfulness, accuracy, and creativity | 4.0+ average |
| **Latency** | P50/P95 response time | Measure time from message send to first token | P50 < 1s, P95 < 3s |

**Evaluation test set creation:**
- Curate 100+ labeled user messages spanning all 14 tool categories
- Include edge cases: ambiguous messages, multi-intent messages, messages with and without @-mentions
- Store as `tests/fixtures/chat_eval_dataset.yaml`

### 16.5 Frontend Tests

**Setup:** Add Vitest + React Testing Library to `src/web/`:

```json
// src/web/package.json (devDependencies additions)
{
  "vitest": "^3.0.0",
  "@testing-library/react": "^16.0.0",
  "@testing-library/jest-dom": "^6.0.0",
  "@testing-library/user-event": "^14.0.0",
  "jsdom": "^25.0.0"
}
```

#### `src/web/src/components/chat/__tests__/ChatSidebar.test.tsx`

```typescript
describe('ChatSidebar', () => {
  it('renders collapsed by default', () => {
    render(<ChatSidebar />);
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('expands when toggle clicked', async () => {
    render(<ChatSidebar />);
    await userEvent.click(screen.getByRole('button', { name: /open chat/i }));
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('shows session picker on session button click', async () => {
    render(<ChatSidebar />);
    // ... expand sidebar first
    await userEvent.click(screen.getByRole('button', { name: /sessions/i }));
    expect(screen.getByText(/create new session/i)).toBeInTheDocument();
  });
});
```

#### `src/web/src/components/chat/__tests__/ActionTraceBlock.test.tsx`

```typescript
describe('ActionTraceBlock', () => {
  const mockTrace: ChatActionTrace = {
    tool_name: 'WRITE',
    agent_id: 'writing_agent',
    context_summary: 'Project Memory (800t) + @Zara (500t)',
    containers_used: ['ulid_zara'],
    model_used: 'anthropic/claude-3.5-sonnet',
    duration_ms: 3200,
    token_usage_in: 1300,
    token_usage_out: 847,
    result_preview: 'The rain fell in sheets...',
    sub_invocations: [],
  };

  it('renders collapsed by default showing summary', () => {
    render(<ActionTraceBlock trace={mockTrace} />);
    expect(screen.getByText('WRITE')).toBeInTheDocument();
    expect(screen.getByText('3.2s')).toBeInTheDocument();
    expect(screen.queryByText('anthropic/claude-3.5-sonnet')).not.toBeInTheDocument();
  });

  it('expands to show full details on click', async () => {
    render(<ActionTraceBlock trace={mockTrace} />);
    await userEvent.click(screen.getByText('WRITE'));
    expect(screen.getByText('anthropic/claude-3.5-sonnet')).toBeInTheDocument();
    expect(screen.getByText('1,300 in / 847 out')).toBeInTheDocument();
  });

  it('renders nested sub-invocations', () => {
    const traceWithSub = {
      ...mockTrace,
      sub_invocations: [{
        caller_agent_id: 'writing_agent',
        callee_agent_id: 'continuity_analyst',
        intent: 'verify consistency',
        depth: 1,
        trace: { ...mockTrace, tool_name: 'CONTINUITY', agent_id: 'continuity_analyst' },
      }],
    };
    render(<ActionTraceBlock trace={traceWithSub} />);
    // Expand parent
    // Verify sub-invocation is rendered
  });
});
```

#### `src/web/src/components/chat/__tests__/ChatInput.test.tsx`

```typescript
describe('ChatInput', () => {
  it('triggers @-mention popover on @ character', async () => {
    render(<ChatInput onSubmit={vi.fn()} />);
    await userEvent.type(screen.getByRole('textbox'), '@');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
  });

  it('submits message on Enter', async () => {
    const onSubmit = vi.fn();
    render(<ChatInput onSubmit={onSubmit} />);
    await userEvent.type(screen.getByRole('textbox'), 'hello{enter}');
    expect(onSubmit).toHaveBeenCalledWith('hello', []);
  });

  it('disables input during streaming', () => {
    render(<ChatInput onSubmit={vi.fn()} isStreaming={true} />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
});
```

### 16.6 End-to-End Smoke Tests (Playwright)

```typescript
// e2e/chat.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agentic Chat E2E', () => {
  test('complete chat interaction flow', async ({ page }) => {
    await page.goto('/dashboard');

    // 1. Open chat sidebar
    await page.click('[data-testid="chat-toggle"]');
    await expect(page.locator('[data-testid="chat-sidebar"]')).toBeVisible();

    // 2. Create a session
    await page.click('[data-testid="new-session"]');
    await page.fill('[data-testid="session-name"]', 'E2E Test');
    await page.click('[data-testid="create-session"]');

    // 3. Send a message
    await page.fill('[data-testid="chat-input"]', 'Hello, tell me about this project');
    await page.press('[data-testid="chat-input"]', 'Enter');

    // 4. Verify response streams
    await expect(page.locator('[data-testid="chat-message"][data-role="assistant"]')).toBeVisible({
      timeout: 10000,
    });

    // 5. Verify action traces appear
    await expect(page.locator('[data-testid="action-trace"]')).toBeVisible();

    // 6. Verify session appears in picker
    await page.click('[data-testid="session-picker"]');
    await expect(page.locator('text=E2E Test')).toBeVisible();
  });
});
```

### 16.7 CI/CD Considerations (Future)

When CI/CD is added, the chat test suite should include:
- **Pre-commit:** Unit tests only (fast, no LLM calls)
- **PR gate:** Unit + integration tests with mocked LLM
- **Nightly:** Full evaluation suite with real LLM calls (uses test project fixtures)
- **Weekly:** E2E Playwright suite against running dev server

---

## 17. Phase L: Cloud Sync & Remote History — Detailed Design

### 17.1 Sync Data Models

**`schemas/sync.py`**
```python
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel
from antigravity_tool.schemas.base import AntigravityBase

class SyncStatus(str, Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    OFFLINE = "offline"

class DriveConfig(BaseModel):
    """Google Drive Sync Configuration."""
    enabled: bool = False
    folder_id: Optional[str] = None           # Root folder ID in Google Drive
    last_sync: Optional[str] = None           # ISO Timestamp

class RevisionHistory(BaseModel):
    """A Google Drive File Revision."""
    revision_id: str
    modified_time: str
    size: int
    user_name: str
    keep_forever: bool = False

class ProjectSnapshot(BaseModel):
    """Point-in-time manifest for aggregate rollback."""
    snapshot_id: str
    timestamp: str
    manifest: Dict[str, str]                  # yaml_path -> drive_revision_id
```

### 17.2 Backend Services

**`services/cloud_sync_service.py`**
Manages upload queues, tracking, and orchestrates syncs. Features exponential backoff, dead-letter recovery, and soft-deletes.
```python
class CloudSyncService:
    def __init__(self, drive_adapter: 'GoogleDriveAdapter', db_path: str):
        self.adapter = drive_adapter
        self.db = Database(db_path) # Tracks local yaml_path -> drive_file_id

    async def enqueue_upload(self, yaml_path: str, raw_content: bytes):
        """Called by UoW after a local save to queue file for sync."""
        pass

    async def enqueue_delete(self, yaml_path: str):
        """Moves remote file to Drive Trash for 30-day recovery."""
        pass

    async def process_queue(self):
        """Background worker loop uploading queued files via adapter."""
        pass
        
    async def revert_file(self, yaml_path: str, revision_id: str, uow_factory):
        """Downloads revision, processes via UnitOfWork to maintain KG and Event Log."""
        pass
```

**`services/google_drive_adapter.py`**
Wrapper around Google Drive API v3. Handles structured folders and quota-aware ratelimiting.
```python
class GoogleDriveAdapter:
    async def upload_file(self, content: bytes, filename: str, folder_id: Optional[str], drive_file_id: Optional[str] = None, keep_forever: bool = False) -> str:
        """Creates or updates a file (creating a new revision), returns drive_file_id."""
        pass
        
    async def trash_file(self, drive_file_id: str) -> None:
        """Marks file as trashed rather than permanent deletion."""
        pass

    async def list_revisions(self, drive_file_id: str) -> List[RevisionHistory]:
        """Calls drive.revisions().list()"""
        pass
        
    async def download_revision(self, drive_file_id: str, revision_id: str) -> bytes:
        """Downloads the file content for a specific revision."""
        pass
```

### 17.3 API Endpoints (FastAPI Router)

**`routers/sync.py`**
*   `GET /api/v1/sync/status` -> Returns current `SyncStatus`.
*   `POST /api/v1/sync/auth` -> Handles OAuth2 code exchange for Google Drive.
*   `GET /api/v1/sync/revisions?yaml_path=...` -> Returns `List[RevisionHistory]`.
*   `POST /api/v1/sync/revert` -> Payload `{yaml_path: str, revision_id: str}`, triggers revert via explicit UoW routing.
*   `POST /api/v1/sync/restore-project` -> Point-in-time full rollback utilizing a `ProjectSnapshot`.
