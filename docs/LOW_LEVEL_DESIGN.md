# Showrunner Low-Level Design Document
**Status:** Phase F–I Blueprint (supersedes Alpha v2.0)
**Last Updated:** 2026-02-21

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
└── model_config_registry → AgentDispatcher (injected for model resolution)
    model_config_registry → PipelineService (injected for model resolution)
    context_engine → PipelineService (injected for context assembly)
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

*Starred components are **new** for Phase F+.

**Phase G additions to `pipeline-builder/`:**

| Component | Purpose |
|-----------|---------|
| `TemplateGallery.tsx` | Browse and 1-click launch pre-built workflow templates |
| `LogicStepNode.tsx`* | Specialized React Flow node for if/else/loop steps with condition editor |

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

---

## 8. SSE Streaming Endpoints

| Endpoint | Purpose | Consumer | Event Format |
|----------|---------|----------|--------------|
| `GET /api/pipeline/{id}/stream` | Pipeline step/state transitions | `usePipelineStream` hook | `PipelineRun.model_dump_json()` on every state change |
| `GET /api/v1/project/events` | File watcher changes, KG updates | `graphDataSlice` | `{ "type": "container_updated", "container_id": "...", ... }` |
| `GET /api/v1/timeline/stream`* | New event sourcing events | `TimelineView` | `{ "type": "event_appended", "event": {...} }` |

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
