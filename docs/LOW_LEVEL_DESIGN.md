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
├── research/page.tsx                   # Research Library (Phase G)
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
| `director.py` | `/api/v1/director` | `POST /act`, `GET /status`, `POST /dispatch` (agent dispatch), `GET /skills` | Core |
| `schemas_router.py` | `/api/v1/schemas` | `GET /`, `GET /{name}`, `POST /`, `PUT /{name}`, `DELETE /{name}`, `POST /validate`, `POST /generate`, `POST /nl-schema` | Core |
| `graph.py` | `/api/v1/graph` | `GET /` (full KG as React Flow JSON), `GET /search?q=&limit=` (semantic search) | Core |
| `timeline.py` | `/api/v1/timeline` | `GET /events`, `POST /checkout`, `POST /branch`*, `GET /stream`* (SSE) | Core+F |
| `pipeline.py` | `/api/pipeline` | `GET /steps/registry`, `GET /definitions`, `POST /definitions`, `GET /definitions/{id}`, `PUT /definitions/{id}`, `DELETE /definitions/{id}`, `POST /runs`, `GET /runs/{id}`, `POST /runs/{id}/resume`, `GET /runs/{id}/stream` (SSE) | Core+B |
| `writing.py` | `/api/v1/writing` | `POST /fragments`, `POST /detect-entities`, `GET /fragments/{id}/context` | A |
| `storyboard.py` | `/api/v1/storyboard` | `GET /scenes/{id}/panels`, `POST /scenes/{id}/panels`, `GET /scenes/{id}/panels/{pid}`, `PUT /scenes/{id}/panels/{pid}`, `POST /scenes/{id}/panels/reorder`, `POST /scenes/{id}/panels/generate` | C |
| `models.py`* | `/api/v1/models` | `GET /available` (list LiteLLM models), `GET /config` (current project config), `PUT /config` (update) | F |
| `agents.py`* | `/api/v1/agents` | `GET /` (list all agent skills + status), `PUT /{name}/model-config` (override model for agent) | F |
| `research.py`* | `/api/v1/research` | `POST /query` (trigger Research Agent), `GET /library` (list research topics), `GET /topic/{id}` (get topic detail) | G |

*Starred routers are **new files** to be created.

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
| `zen/` | `components/zen/` | `ZenEditor.tsx`, `MentionList.tsx`, `SlashCommandList.tsx`, `ContextSidebar.tsx`, `StoryboardStrip.tsx` | A |
| `storyboard/` | `components/storyboard/` | `PanelCard.tsx`, `SceneStrip.tsx`, `PanelEditor.tsx`, `SemanticCanvas.tsx` | C |
| `schema-builder/` | `components/schema-builder/` | `SchemaBuilderPanel.tsx`, `SchemaEditor.tsx`, `NLWizardInput.tsx`, `FieldRow.tsx`, `FieldTypeSelector.tsx`, `SchemaPreview.tsx` | Core |
| `timeline/` | `components/timeline/` | `TimelineView.tsx`, `TimelinePanel.tsx`, `TimelineEventNode.tsx`, `StoryStructureTree.tsx`*, `useInterval.ts` | Core+F |
| `research/`* | `components/research/` | `ResearchPanel.tsx`, `ResearchCard.tsx` | G |
| `workbench/` | `components/workbench/` | `WorkbenchLayout.tsx`, `Canvas.tsx`, `Sidebar.tsx`, `SidebarItem.tsx`, `Inspector.tsx`, `CharacterInspector.tsx`, `SceneInspector.tsx`, `WorldStatus.tsx`, `WorkflowBar.tsx`, `DirectorControls.tsx` | Core |

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
