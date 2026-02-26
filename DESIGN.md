# Showrunner -- Design Document

## 1. Project Overview

**Showrunner** is an agentic AI platform for creating manga, manhwa, and webtoon comics. It combines a Python CLI, a FastAPI backend, and a Next.js web studio to orchestrate a 7-step creative pipeline -- from world-building through character creation, story structure, scene writing, screenplay generation, panel division, to final image prompt generation.

### Vision

A single author (or a small team) can produce publication-quality visual storytelling by combining AI-driven content generation with a structured creative workflow. The AI handles the labor-intensive parts (consistent character rendering, panel composition, image prompts) while the human retains full creative control through decisions, evaluations, and a private creative room.

### Cost Model

| Component | Cost | Role |
|-----------|------|------|
| Claude Code | Free (subscription) | Orchestration, reasoning, content generation, evaluation |
| Gemini API | Paid (GEMINI_API_KEY) | Image generation only (Imagen 4) |
| Showrunner CLI | Free (local Python) | Context compilation, file management, no API calls |

---

## 2. Domain Model

### Entity Relationship Diagram

```
Project (root aggregate)
 |
 +-- WorldSettings (1)
 |    +-- Location[] (N)
 |    +-- WorldRule[] (N)        -- some hidden from reader
 |    +-- Faction[] (N)
 |    +-- HistoricalEvent[] (N)  -- some hidden from reader
 |
 +-- Character[] (N)
 |    +-- Personality
 |    +-- CharacterDNA           -- stable image tokens
 |    |    +-- FacialFeatures
 |    |    +-- HairDescription
 |    |    +-- BodyDescription
 |    |    +-- OutfitCanon[]
 |    +-- CharacterArc
 |    +-- Relationship[]         -- some hidden from reader
 |
 +-- StoryStructure (1)
 |    +-- StoryBeat[] (N)        -- save_the_cat / heros_journey / etc.
 |    +-- CharacterArcBeat[] (N)
 |    +-- SubArc[] (N)
 |
 +-- Chapter[] (N)
 |    +-- Scene[] (N per chapter)
 |    |    +-- SceneSetting
 |    |    +-- SceneCharacters
 |    |    +-- SceneNarrative
 |    |    +-- SceneConnections
 |    |    +-- CharacterState[] (per-scene snapshots)
 |    +-- Screenplay[] (N per chapter, 1:1 with scenes)
 |    |    +-- ScreenplayBeat[]
 |    +-- Panel[] (N per chapter)
 |         +-- PanelComposition (shot_type, camera_angle, panel_size)
 |         +-- PanelContent (characters, background, effects)
 |         +-- PanelText (dialogue_bubbles, sound_effects, narration)
 |         +-- ImageGeneration (prompt, negative_prompt, style_tokens)
 |
 +-- CreativeRoom (1, ISOLATED)
 |    +-- PlotTwist[] (N)
 |    +-- CharacterSecret[] (N)
 |    +-- ForeshadowingEntry[] (N)
 |    +-- TrueMechanic[] (N)
 |    +-- ReaderKnowledgeState[] (per-scene checkpoints)
 |    +-- ending_plans, thematic_threads, author_notes
 |
 +-- StyleGuides
 |    +-- VisualStyleGuide (1)   -- art style, colors, panel format
 |    +-- NarrativeStyleGuide (1) -- tone, POV, prose style
 |
 +-- DecisionLog                 -- cross-session author preferences
 |    +-- Decision[] (N, scoped to global/chapter/scene/character)
 |
 +-- SessionLog                  -- cross-session history
 |    +-- SessionEntry[] (N, one per working session)
 |
 +-- WorkflowState               -- pipeline progress tracker
      +-- StepState[] (7 steps)
```

### Schema Base Class

All domain entities inherit from `ShowrunnerBase`:
```
ShowrunnerBase
  id: str (ULID -- sortable, unique)
  schema_version: str ("1.0.0")
  created_at: datetime (UTC)
  updated_at: datetime (UTC)
  notes: Optional[str]
```

### Key Schema Files

| Schema | File | Primary Purpose |
|--------|------|-----------------|
| Character, CharacterDNA, Personality | `schemas/character.py` | Character with stable image generation tokens |
| WorldSettings, Location, Faction | `schemas/world.py` | World state with visibility filtering |
| StoryStructure, StoryBeat, SubArc | `schemas/story_structure.py` | Narrative structure templates |
| Scene, SceneSetting, SceneNarrative | `schemas/scene.py` | Scene content with branching support |
| Screenplay, ScreenplayBeat | `schemas/screenplay.py` | Visual screenplay beats |
| Panel, PanelComposition, DialogueBubble | `schemas/panel.py` | Panel layout and image generation |
| CreativeRoom, PlotTwist, CharacterSecret | `schemas/creative_room.py` | Author-only isolated data |
| ReaderKnowledgeState | `schemas/creative_room.py` | Positive-list knowledge tracking |
| Decision, DecisionScope, SessionEntry | `schemas/session.py` | Cross-session persistence |
| VisualStyleGuide, NarrativeStyleGuide | `schemas/style_guide.py` | Style configuration |
| GenrePreset | `schemas/genre.py` | Genre-specific defaults |
| EvaluationResult | `schemas/evaluation.py` | Quality assessment output |
| ContinuityReport, ContinuityIssue | `schemas/continuity.py` | Consistency validation |
| PacingReport, PacingMetrics | `schemas/pacing.py` | Rhythm analysis |
| Timeline, TimelineEvent | `schemas/timeline.py` | Story timeline tracking |
| AnalyticsReport | `schemas/analytics.py` | Project statistics |

---

## 3. Architecture

### Target Layered Architecture

```
+------------------------------------------------------------------+
|                       ENTRY POINTS                                |
|                                                                    |
|  CLI (Typer, 29 commands)  |  API (FastAPI)  |  Director Agent    |
|  Thin wrappers that call   |  REST routers   |  Task-based FSM    |
|  services and display      |  with DI        |  returns results   |
+------------------------------------------------------------------+
                               |
+------------------------------------------------------------------+
|                       SERVICE LAYER                               |
|                                                                    |
|  WorldService      | CharacterService  | StoryService            |
|  SceneService      | PanelService      | EvaluationService       |
|  SessionService    | CreativeRoomService| DirectorService         |
|                                                                    |
|  Each service: takes ServiceContext, returns typed results         |
|  No console output, no HTTP concerns -- pure business logic       |
+------------------------------------------------------------------+
                               |
+------------------------------------------------------------------+
|                       CORE LAYER                                  |
|                                                                    |
|  ContextCompiler   -- step-specific context assembly              |
|  TemplateEngine    -- Jinja2 rendering with user overrides        |
|  WorkflowState     -- pipeline step tracking                      |
|  CreativeRoomManager -- isolation enforcement + CRUD              |
|  BriefingGenerator -- ProjectBrief assembly                       |
|  Evaluator         -- evaluation prompt generation                |
|  ContinuityChecker -- cross-scene validation                      |
|  PacingAnalyzer    -- rhythm analysis                             |
+------------------------------------------------------------------+
                               |
+------------------------------------------------------------------+
|                     REPOSITORY LAYER                              |
|                                                                    |
|  YAMLRepository[T] -- generic base with load/save/list            |
|  CharacterRepository | WorldRepository | ChapterRepository       |
|  StoryRepository | StyleRepository | CreativeRoomRepository      |
|  SessionRepository (DecisionLog + SessionLog)                     |
|                                                                    |
|  All I/O goes through here. Project delegates to these.           |
+------------------------------------------------------------------+
                               |
+------------------------------------------------------------------+
|                     PERSISTENCE LAYER                             |
|                                                                    |
|  utils/io.py: read_yaml(), write_yaml()                          |
|  File system: project_dir/**/*.yaml                               |
+------------------------------------------------------------------+
                               |
+------------------------------------------------------------------+
|                     SCHEMA LAYER (Pydantic v2)                    |
|                                                                    |
|  19 domain models in schemas/                                     |
|  API request/response models in server/api_schemas.py             |
+------------------------------------------------------------------+
```

### Agent Layer

```
+------------------------------------------------------------------+
|                       AGENT LAYER                                 |
|                                                                    |
|  DirectorService                                                  |
|  +-- Plans next action based on WorkflowState                    |
|  +-- Executes via ContextCompiler -> TemplateEngine -> Writer     |
|  +-- Returns DirectorResult (status, files, next_step)            |
|                                                                    |
|  Writer                                                           |
|  +-- Wraps LLMClient with system prompt injection                 |
|  +-- generate(prompt, output_schema) -> validated model           |
|  +-- Streaming support via generate_stream()                      |
|                                                                    |
|  LLMClient                                                        |
|  +-- LiteLLM wrapper (supports Gemini, OpenAI, etc.)             |
|  +-- generate() / generate_stream()                               |
|                                                                    |
|  ImageProvider (abstract)                                         |
|  +-- GeminiImagenProvider (Imagen 4)                              |
|  +-- DalleProvider (DALL-E 3)                                     |
|  +-- StableDiffusionProvider (SD-XL)                              |
|  +-- FluxProvider (BFL Flux)                                      |
+------------------------------------------------------------------+
```

---

## 4. Context Isolation Rules

This is the **most critical architectural constraint**. The creative room contains author-level secrets (plot twists, character secrets, true world mechanics, ending plans) that must NEVER appear in story-level prompts. If they leak, the AI will write stories that prematurely reveal twists.

### Access Levels

| Level | Sees | Used By |
|-------|------|---------|
| `story` (default) | Characters (filtered), World (filtered), StoryStructure, Scenes, ReaderKnowledge | All story-writing commands: world, character, scene, screenplay, panel, image_prompt |
| `author` | Everything including CreativeRoom, unfiltered characters, hidden rules | evaluate commands, creative-room commands, consistency checks |

### Enforcement Points

1. **ContextCompiler.compile_for_step()** -- routes by `access_level` parameter. Story-level compilers never call `project.load_creative_room()`.

2. **Project.load_all_characters(filter_secrets=True)** -- removes relationships where `known_to_reader=False`.

3. **Project.load_world_rules(filter_hidden=True)** -- removes rules where `known_to_reader=False`.

4. **CreativeRoomManager.is_isolated()** -- checks `.showrunner-secret` marker file exists.

5. **ReaderKnowledgeState** -- positive-list filtering. Tracks what the reader KNOWS at each scene checkpoint. Scene prompts include this state so the AI only references known information.

### Data Flow with Isolation

```
Story-Level Prompt:
  ContextCompiler(access_level="story")
    -> load_world_settings()          [filtered: hidden rules removed]
    -> load_all_characters(filter=T)  [filtered: hidden relationships removed]
    -> load_story_structure()         [full]
    -> load_reader_knowledge()        [positive-list of what reader knows]
    -> inject_decisions()             [scoped to chapter/scene]
    !! NEVER: load_creative_room()

Author-Level Prompt:
  ContextCompiler(access_level="author")
    -> load_world_settings()          [UNFILTERED]
    -> load_all_characters(filter=F)  [UNFILTERED]
    -> load_creative_room()           [FULL ACCESS]
    -> load_reader_knowledge()        [for comparison]
```

---

## 5. User Flows

### 5.1 CLI Flow (Prompt Compilation Pipeline)

This is the primary user flow. Claude Code acts as the Director Agent, running CLI commands to compile prompts, then generating content itself.

```
User (via Claude Code)
  |
  v
showrunner <command> [args]
  |
  v
Typer CLI -> Command handler
  |
  v
Service Layer
  +-- Project.find()              # Walk up from cwd to find showrunner.yaml
  +-- ServiceContext.from_project()
  +-- service.compile_*_prompt()
  |     +-- ContextCompiler.compile_for_step()
  |     |     +-- Load relevant data from repositories
  |     |     +-- Apply access_level filtering
  |     |     +-- Inject applicable decisions
  |     +-- TemplateEngine.render()
  |     |     +-- Resolve template (user overrides > built-in)
  |     |     +-- Render Jinja2 with context
  |     +-- WorkflowState.mark_step_started()
  |     +-- Return PromptResult
  |
  v
Rich Console Output
  +-- Prompt displayed to Claude Code
  +-- Claude Code reads, reasons, generates YAML content
  +-- User saves YAML to project files
  |
  v
showrunner status  # Verify progress
```

### 5.2 Web Studio Flow (Target)

```
Browser (Next.js)
  |
  v
API Request (e.g., GET /api/v1/characters)
  |
  v
FastAPI Router
  +-- Depends(get_character_service)
  |     +-- Depends(get_service_context)
  |           +-- Depends(get_project)
  |
  v
Service Layer
  +-- CharacterService.list_all()
  |     +-- Repository.get_all()
  |
  v
JSON Response -> Browser renders UI
```

### 5.3 Director Flow (Target)

```
API: POST /api/v1/director/act
  OR
CLI: showrunner director action
  |
  v
DirectorService.act()
  +-- WorkflowState.get_current_step()
  +-- Route to handler (e.g., _handle_world_building)
  |     +-- Check if step already complete
  |     +-- ContextCompiler.compile_for_step()
  |     +-- TemplateEngine.render()
  |     +-- Writer.generate(prompt, output_schema)
  |     |     +-- LLMClient.generate_stream()
  |     |     +-- Parse YAML output
  |     |     +-- Validate against Pydantic schema
  |     +-- Repository.save(entity)
  |     +-- WorkflowState.mark_step_complete()
  |
  v
DirectorResult
  +-- step_executed: str
  +-- status: "success" | "skipped" | "error"
  +-- files_created: list[str]
  +-- next_step: str | None
  +-- message: str
```

### 5.4 Cross-Session Flow

```
Session N ends:
  showrunner session end "Built world and characters" --next "Write first scene"
    +-- SessionLog.save_session()
    +-- Records: summary, actions, decisions, next_steps

Session N+1 starts:
  showrunner brief show
    +-- BriefingGenerator.generate()
    |     +-- Scans: WorkflowState, characters, story structure
    |     +-- Loads: last SessionEntry, active Decisions
    |     +-- Computes: chapter summaries, progress stats
    +-- Returns ProjectBrief with:
    |     +-- Current step + position
    |     +-- Character names + count
    |     +-- Story beats progress (X/Y)
    |     +-- Active decisions in scope
    |     +-- Last session summary + next steps
    |     +-- Suggested next command
    |
  showrunner brief update
    +-- Writes briefing to CLAUDE.md between <!-- DYNAMIC:START --> and <!-- DYNAMIC:END -->
    +-- New Claude Code session reads CLAUDE.md automatically
```

---

## 6. Data Flow per Workflow Step

### Step 1: World Building

```
Command:   showrunner world build
Template:  world/build_setting.md.j2
Context:   project_name, project_variables, narrative_style, existing_world, author_decisions
Output:    WorldSettings YAML (name, genre, time_period, tone, locations, rules)
Saves to:  world/settings.yaml
```

### Step 2: Character Creation

```
Command:   showrunner character create "Name" --role protagonist
Template:  character/create_character.md.j2
Context:   project_name, world_summary, existing_characters, narrative_style, author_decisions
Output:    Character YAML (name, personality, backstory, arc)
Saves to:  characters/{slug}.yaml

Follow-up: showrunner character generate-dna "Name"
Template:  character/generate_dna_block.md.j2
Output:    CharacterDNA YAML (face, hair, body, outfits)
```

### Step 3: Story Structure

```
Command:   showrunner story outline --structure save_the_cat
Template:  story/outline_beats.md.j2
Context:   project_name, world_summary, characters (name, role, one_line), narrative_style, author_decisions
Output:    StoryStructure YAML (beats, character_arcs, act_summaries)
Saves to:  story/structure.yaml
```

### Step 4: Scene Writing

```
Command:   showrunner scene write --chapter 1 --scene 1
Template:  scene/write_scene.md.j2
Context:   project_name, world_summary, characters (FILTERED), story_structure, reader_knowledge,
           previous_scenes, narrative_style, author_decisions (scoped to chapter/scene)
Output:    Scene YAML (title, summary, setting, characters, narrative, connections)
Saves to:  chapters/chapter-01/scenes/scene-01.yaml

Auto-runs:  Knowledge extraction -> updates reader_knowledge state
```

### Step 5: Screenplay Writing

```
Command:   showrunner screenplay convert --chapter 1 --scene 1
Template:  screenplay/scene_to_screenplay.md.j2
Context:   project_name, scene (full), characters (with speech_patterns, verbal_tics),
           narrative_style, author_decisions
Output:    Screenplay YAML (beats with type, character, content, emotion)
Saves to:  chapters/chapter-01/screenplay/scene-01.yaml
```

### Step 6: Panel Division

```
Command:   showrunner panel divide --chapter 1 --scene 1
Template:  panel/divide_panels.md.j2
Context:   project_name, screenplay, character_dna_blocks, visual_style, author_decisions
Output:    Panel[] YAML (composition, content, text, image_generation hints)
Saves to:  chapters/chapter-01/panels/page-XX-panel-YY.yaml

Rules enforced by template:
  - Max 2 panels per screen section (webtoon)
  - Max 3 dialogue bubbles per panel
  - Full-width panels for reveals
  - Shot type variation (3-of-5 rule)
```

### Step 7: Image Prompt Generation

```
Command:   showrunner prompt generate --chapter 1
Template:  panel/panel_to_image_prompt.md.j2
Context:   panels, character_dna_blocks, visual_style
Output:    Updated Panel.image_generation (prompt, negative_prompt, style_tokens)
Saves to:  panel files updated in-place
```

---

## 7. Cross-Session Persistence

### Decision Log

```
File:       .showrunner/decisions.yaml
Schema:     Decision[]
Scoping:    Each decision has a DecisionScope:
              global    -- applies everywhere
              chapter   -- applies to specific chapter
              scene     -- applies to specific chapter + scene
              character -- applies to specific character everywhere

Injection:  ContextCompiler._inject_decisions() auto-adds matching decisions
            to every compiled context dict as "author_decisions" text block.

Example:
  - [tone] (global) Dark fantasy tone with moments of levity
  - [visual] (chapter 1) Heavy shadows, limited color palette
  - [character] (character: Hero) Always wears the amulet
```

### Session Log

```
Directory:  .showrunner/sessions/
Files:      session-{YYYY-MM-DD}-{seq}.yaml
Schema:     SessionEntry
Contains:   session_date, summary, workflow_step_start/end,
            actions[], decisions_made, next_steps

Actions track: command executed, files created/modified, timestamp
```

### Project Brief

```
Generator:  BriefingGenerator.generate() -> ProjectBrief
Contains:   project_name, one_line, current_step, current_chapter/scene,
            character_names, story_beats_filled, chapter_summaries[],
            active_decisions[], last_session_summary, suggested_next_action

Used for:   Dynamic CLAUDE.md injection between
            <!-- DYNAMIC:START --> and <!-- DYNAMIC:END -->
```

---

## 8. File System Layout

```
{project_name}/
+-- showrunner.yaml                    # Project manifest (name, version, template, structure)
+-- CLAUDE.md                           # Static instructions + dynamic state section
+-- .env                                # API keys (git-ignored)
|
+-- world/
|   +-- settings.yaml                   # WorldSettings
|   +-- rules.yaml                      # WorldRule[] (some hidden)
|   +-- history.yaml                    # HistoricalEvent[] (some hidden)
|   +-- factions/
|       +-- {faction_slug}.yaml         # Faction
|
+-- characters/
|   +-- {character_slug}.yaml           # Character (includes DNA, personality, arc)
|   +-- _template.yaml                  # Template for new characters
|
+-- story/
|   +-- structure.yaml                  # StoryStructure (beats, arcs)
|   +-- arcs/
|       +-- {arc_slug}.yaml             # SubArc details
|
+-- style_guide/
|   +-- visual.yaml                     # VisualStyleGuide
|   +-- narrative.yaml                  # NarrativeStyleGuide
|
+-- chapters/
|   +-- chapter-01/
|   |   +-- scenes/
|   |   |   +-- scene-01.yaml           # Scene
|   |   |   +-- scene-02.yaml
|   |   +-- screenplay/
|   |   |   +-- scene-01.yaml           # Screenplay (1:1 with scene)
|   |   +-- panels/
|   |       +-- page-01-panel-01.yaml   # Panel
|   |       +-- page-01-panel-02.yaml
|   +-- chapter-02/
|       +-- ...
|
+-- creative_room/                      # ISOLATED: author-only data
|   +-- .showrunner-secret             # Isolation marker file
|   +-- plot_twists.yaml                # PlotTwist[]
|   +-- character_secrets.yaml          # CharacterSecret[]
|   +-- foreshadowing_map.yaml          # ForeshadowingEntry[]
|   +-- true_mechanics.yaml             # TrueMechanic[]
|   +-- ending_plans.yaml               # Author's ending plans
|   +-- reader_knowledge/
|       +-- chapter-01-01.yaml          # ReaderKnowledgeState at Ch1 Sc1
|       +-- chapter-01-02.yaml          # ReaderKnowledgeState at Ch1 Sc2
|
+-- prompts/                            # User template overrides (optional)
|   +-- (mirrors built-in prompts/ structure)
|
+-- exports/                            # Generated output
|
+-- .showrunner/                       # Project metadata
    +-- workflow_state.yaml             # WorkflowState (7 steps)
    +-- decisions.yaml                  # Decision[]
    +-- sessions/
        +-- session-2026-02-19-001.yaml # SessionEntry
```

---

## 9. Prompt Assembly Pipeline

```
             +-------------------+
             |  ContextCompiler  |
             |                   |
             |  compile_for_step |
             |  (step, access,   |
             |   chapter, scene) |
             +--------+----------+
                      |
          +-----------+-----------+
          |                       |
    Load from Repos         Inject Decisions
    (filtered by             (scoped to
     access_level)            chapter/scene)
          |                       |
          +-------+-------+-------+
                  |
                  v
          +-------+-------+
          | context: dict  |
          | {              |
          |   world_summary|
          |   characters   |
          |   story_struct |
          |   reader_know  |
          |   decisions    |
          |   ...          |
          | }              |
          +-------+--------+
                  |
                  v
          +-------+--------+
          | TemplateEngine  |
          |                 |
          | render(template,|
          |   **context)    |
          |                 |
          | Resolution:     |
          | 1. user prompts/|
          | 2. built-in     |
          +-------+---------+
                  |
                  v
          +-------+---------+
          | Jinja2 .md.j2   |
          |                  |
          | Renders markdown |
          | with YAML output |
          | instructions     |
          +-------+----------+
                  |
                  v
          +-------+----------+
          | prompt_text: str  |
          | (ready for LLM    |
          |  or CLI display)  |
          +-------------------+
```

### Template Override System

Templates are resolved with a Jinja2 `ChoiceLoader`:
1. **User overrides** (`{project_path}/prompts/`) -- checked first
2. **Built-in templates** (`src/showrunner_tool/prompts/`) -- fallback

This allows per-project customization of any prompt without modifying the package.

### Custom Jinja2 Filters

- `| to_yaml` -- renders any value as YAML string (for embedding data in prompts)

---

## 10. API Design (Implemented)

### Resource Routes

| Method | Path | Description | Service |
|--------|------|-------------|---------|
| GET | `/api/v1/project/` | Project metadata + workflow step | ProjectRouter |
| GET | `/api/v1/project/health` | Health check | ProjectRouter |
| GET | `/api/v1/world/` | World settings | WorldService |
| POST | `/api/v1/world/build/prompt` | Compile world-building prompt | WorldService |
| GET | `/api/v1/characters/` | List all characters (summaries) | CharacterService |
| GET | `/api/v1/characters/{name}` | Character detail (full model) | CharacterService |
| POST | `/api/v1/characters/prompt` | Compile character creation prompt | CharacterService |
| POST | `/api/v1/characters/{name}/dna/prompt` | Compile DNA generation prompt | CharacterService |
| GET | `/api/v1/chapters/{num}/scenes` | List scenes for chapter (includes characters_present) | SceneService |
| GET | `/api/v1/chapters/{num}/scenes/{scene_num}` | Single scene detail | SceneService |
| PATCH | `/api/v1/chapters/{num}/scenes/{scene_num}` | Update scene (e.g. link characters) | SceneService |
| POST | `/api/v1/chapters/{num}/scenes/write/prompt` | Compile scene writing prompt | SceneService |
| POST | `/api/v1/chapters/{num}/screenplay/prompt` | Compile screenplay prompt | SceneService |
| GET | `/api/v1/chapters/{num}/panels` | List panels for chapter | PanelService |
| POST | `/api/v1/chapters/{num}/panels/divide/prompt` | Compile panel division prompt | PanelService |
| GET | `/api/v1/workflow/` | Current workflow state + step list | WorkflowService |
| POST | `/api/v1/director/act` | Director executes next task | DirectorService |
| GET | `/api/v1/director/status` | Current director step | DirectorService |

### Error Responses

All errors return:
```json
{
  "error": "Human-readable message",
  "error_type": "EntityNotFoundError",
  "context": {"entity_type": "Character", "identifier": "Hero"}
}
```

Status code mapping:
- 404: EntityNotFoundError
- 409: WorkflowError
- 403: ContextIsolationError
- 422: SchemaValidationError
- 500: ProjectError, PersistenceError

---

## 11. Knowledge Base

The project includes an embedded knowledge base at `src/showrunner_tool/knowledge/` with markdown articles organized by category:

| Category | Articles | Purpose |
|----------|----------|---------|
| `structures/` | save_the_cat, heros_journey, story_circle, kishotenketsu, sub_arcs | Story structure templates and guides |
| `writing/` | character_arcs, dialogue, pacing, scene_types, tension_conflict, show_dont_tell | Fiction craft reference |
| `image_prompts/` | character_dna, composition_prompts, style_tokens | Image generation guidance |
| `panel_composition/` | shot_types, camera_angles, panel_layouts, composition_rules | Visual storytelling reference |

Articles are indexed via `index.yaml` with metadata (title, tags, summary, use_in_steps). The `KnowledgeBase` class provides keyword search, step-based retrieval, and full article loading.

---

## 12. Genre Preset System

Genre presets provide a one-command setup for common genres. Each preset configures:

- **Narrative defaults**: tone, prose_style, dialogue_style, pacing_preference
- **Visual defaults**: art_style, color_palette, line_weight, shading_style
- **Genre-specific**: common_tropes, panel_style_hints, themes

Available presets: `dark_fantasy`, `shonen_action`, `romance`, `slice_of_life`, `sci_fi`, `horror`, `isekai`

Applied via: `showrunner init "Name" --genre dark_fantasy`

---

## 13. Web Studio Architecture (Implemented)

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16.1.6 |
| UI | React | 19.2.3 |
| Styling | Tailwind CSS | v4 |
| State | Zustand | 5.0.11 |
| Drag & Drop | @dnd-kit (core, sortable, utilities) | 6.x / 10.x |
| Icons | Lucide React | 0.575.0 |
| Utilities | clsx + tailwind-merge | 2.x / 3.x |

### Frontend Architecture

```
app/dashboard/page.tsx
  └── WorkbenchLayout (DndContext + DragOverlay)
       ├── Sidebar (w-72, collapsible)
       │    ├── Characters tab → SidebarItem[] (useDraggable)
       │    ├── Scenes tab → SidebarItem[] (useDraggable)
       │    └── World tab → WorldStatus
       ├── Canvas (flex-1)
       │    ├── DirectorControls (act button + result badge)
       │    ├── WorkflowBar (7-step indicators)
       │    ├── Characters grid → ContainerCard[]
       │    └── Scenes grid → ContainerCard[] (useDroppable)
       │         └── Chapter navigation (< Ch.N >)
       └── Inspector (w-80, conditional on selection)
            ├── CharacterInspector (identity, personality, DNA, arc, relationships)
            ├── SceneInspector (info, tension bar, linked characters with unlink)
            └── WorldInspector (locations, rules, factions)
```

### State Management (Zustand)

Single store in `lib/store.ts` with:

- **Data**: project, characters, scenes, workflow, world
- **UI**: loading, error, directorActing, lastDirectorResult
- **Sidebar**: sidebarCollapsed, sidebarTab (characters | scenes | world)
- **Chapter**: currentChapter (derived from workflow, user-overridable)
- **Inspector**: selectedItem, inspectorData, inspectorLoading
- **Actions**: fetchAll, directorAct, selectItem, clearSelection, setChapter, linkCharacterToScene, unlinkCharacterFromScene

Selection flow: click item → `selectItem()` → fetch detail from API → inspector opens.

### Drag-Drop Flow

```
SidebarItem (useDraggable, id: "sidebar-{id}", data: {type, name, id, source: "sidebar"})
  |  drag starts → DragOverlay renders ghost card
  |  drag over →
  v
ContainerCard (useDroppable, enabled for type="scene" only)
  |  drop →
  v
WorkbenchLayout.handleDragEnd()
  |  if activeData.type === "character" && overData.type === "scene"
  v
store.linkCharacterToScene(characterId, sceneId)
  |  → PATCH /api/v1/chapters/{ch}/scenes/{num} with updated characters_present
  |  → refresh scenes list
  |  → refresh inspector if affected scene selected
  v
Scene card shows updated character count, inspector shows linked characters
```

### Implementation Status

| Feature | Status |
|---------|--------|
| **Dashboard / Workbench** | |
| 3-pane layout (sidebar + canvas + inspector) | Done |
| Asset sidebar with 3 tabs | Done |
| Collapsible sidebar | Done |
| Character inspector (DNA, personality, arc) | Done |
| Scene inspector (tension bar, linked characters) | Done |
| World inspector (locations, rules, factions) | Done |
| Workflow progress bar | Done |
| Director act button + result display | Done |
| Character → scene drag-drop linking | Done |
| Chapter navigation | Done |
| DragOverlay ghost card | Done |
| Toast notifications (sonner) | Done |
| Loading skeletons (all views) | Done |
| Confirmation dialogs (destructive actions) | Done |
| Context Inspector / Glass Box UI | Done |
| **Zen Mode (/zen)** | |
| TipTap rich text editor | Done |
| @-mention entity detection | Done |
| /slash command palette | Done |
| Slash commands wired to agent dispatch | Done |
| Context sidebar with Glass Box | Done |
| Auto-save with debounce | Done |
| **Pipeline Builder (/pipelines)** | |
| Visual DAG editor (ReactFlow) | Done |
| Step library with categories | Done |
| Step config panels | Done |
| Template gallery (hardcoded stubs) | Done |
| Pipeline SSE streaming | Done |
| PromptReviewModal (Edit/Refine/Paste/Skip) | Done |
| Model selector per pipeline run | Done |
| **Storyboard (/storyboard)** | |
| Scene strip view with drag-reorder | Done |
| Semantic canvas view (ReactFlow) | Done |
| Panel generation via AI | Done |
| Panel CRUD + editor | Done |
| **Timeline (/timeline)** | |
| Real-time SSE event stream | Done |
| Event type visual differentiation | Done |
| Branch creation modal | Done |
| Story structure tree (basic) | Done |
| **Schema Builder (/schemas)** | |
| NL-to-schema wizard | Done |
| Field editor with type selector | Done |
| Schema preview | Done |
| **Command Center (/dashboard)** | |
| Project switcher | Done |
| Progress overview | Done |
| Model config panel | Done |
| **Agent System** | |
| Agent dispatcher with keyword routing | Done |
| ReAct loop execution | Done |
| 6 agent skill files | Done |
| Agent dispatch API + Glass Box metadata | Done |
| **Backend Infrastructure** | |
| Knowledge Graph (SQLite + ReactFlow) | Done |
| ChromaDB vector embeddings (RAG) | Done |
| Event sourcing (append-only + branching) | Done |
| File watcher (watchdog + SSE) | Done |
| Context Engine (token budgeting) | Done |
| Model cascade resolution | Done |
| 3-format export (MD, JSON, Fountain) | Done |
| **Analysis / Intelligence (Phase Next-B)** | |
| Emotional Arc Dashboard (recharts) | Done |
| Character Voice Scorecard (stylometric) | Done |
| Story Ribbons visualization (SVG) | Done |
| AnalysisService (3 analysis methods) | Done |
| Analysis API router (3 endpoints) | Done |
| **Panel Intelligence (Phase Next-C)** | |
| Panel Layout Intelligence (beat analysis → layout suggestion) | Done |
| LayoutSuggestionPanel.tsx (visual preview + Apply & Generate) | Done |
| Character Progressions (DNA timeline with deep-merge) | Done |
| CharacterProgressionTimeline.tsx (horizontal timeline in Inspector) | Done |
| Reader Scroll Simulation (heuristic pacing analysis) | Done |
| ReaderSimService + preview.py router (2 endpoints) | Done |
| `/preview` page (vertical scroll + pacing sidebar + auto-scroll) | Done |
| **Workflow Power (Phase Next-D)** | |
| Workflow Templates Library (5 wired end-to-end templates) | Done |
| TemplateGallery fetches from API (not hardcoded) | Done |
| Enhanced Approval Gate (temperature slider, context pinning, regenerate) | Done |
| Pipeline resume supports temperature_override + pinned_context_ids | Done |
| Research Agent UI Surface (`/research` page) | Done |
| ResearchDetailPanel.tsx + ResearchTopicCard.tsx | Done |
| **Spatial & Structural (Phase Next-E)** | |
| Containers CRUD router (`containers.py` — create/get/update/delete/reorder) | Done |
| ContainerRepository `get_by_id()` + `delete_by_id()` | Done |
| StoryStructureTree.tsx (add child/delete/open-in-Zen/reorder fix/status colors) | Done |
| Fix `getProjectStructure()` API URL mismatch | Done |
| EventService `get_branches()` + `get_events_for_branch()` + `compare_branches()` | Done |
| Timeline router extensions (branches, branch events, compare, SSE stream) | Done |
| BranchList.tsx (sidebar with event counts + active indicator) | Done |
| BranchComparison.tsx (two-column diff: additions/removals/changes) | Done |
| Spatial Brainstorming Canvas (`/brainstorm` page with ReactFlow) | Done |
| IdeaCardNode.tsx (editable cards with color coding + auto-save) | Done |
| SuggestionPanel.tsx (AI-suggested connections + new ideas) | Done |
| Brainstorm backend endpoints (suggest-connections, save/get/delete cards) | Done |
| Voice-to-Scene pipeline (`POST /storyboard/voice-to-scene`) | Done |
| VoiceToSceneButton.tsx (Web Speech API + fallback textarea + panel generation) | Done |
| Brainstorm nav link in Canvas.tsx | Done |
| **Intelligence Layer (Phase H)** | |
| ContinuityService (KG validation via `continuity_analyst` agent) | Done |
| Continuity endpoints (`POST /continuity-check`, scene check, issues list) | Done |
| ContinuityPanel.tsx (severity-coded issue cards in Zen sidebar) | Done |
| StyleService (prose evaluation via `style_enforcer` agent) | Done |
| Style endpoint (`POST /style-check`) | Done |
| StyleScorecard.tsx (score gauge + categorized issues in Zen sidebar) | Done |
| Style tab in PromptReviewModal (pipeline approval style check) | Done |
| `/check-style` slash command in Zen Mode | Done |
| ContextSidebar 4-tab system (Context / Continuity / Style / Translation) | Done |
| TranslationService (cultural adaptation via `translator_agent`) | Done |
| Translation router (`POST /translate`, glossary CRUD) | Done |
| TranslationPanel.tsx + `/translation` page (Translation Studio) | Done |
| InlineTranslation.tsx (compact Zen Mode translation widget) | Done |
| `/translate` slash command + Translation tab in ContextSidebar | Done |
| NLPipelineWizard.tsx (describe workflow → auto-generate DAG) | Done |
| "Create from Description" button on Pipelines page | Done |
| Semantic @mentions in Zen Mode (ChromaDB vector search) | Done |
| `GET /writing/semantic-search` endpoint | Done |
| Translation nav link in Canvas.tsx | Done |
| **Polish Layer (Phase I)** | |
| Persistent Navbar (`Navbar.tsx` — 9 page tabs, active state, Cmd+K trigger) | Not started |
| Command Palette (`CommandPalette.tsx` — cmdk library, page nav, actions, search) | Not started |
| Error Boundary (`ErrorBoundary.tsx` — crash recovery fallback UI) | Not started |
| Canvas.tsx cross-page nav cleanup (keep Graph/Timeline toggle only) | Not started |
| Export UI Modal (`ExportModal.tsx` — 4 formats, preview, download, print-to-PDF) | Not started |
| HTML export endpoint (`POST /export/html` + `POST /export/preview`) | Not started |
| Export trigger in ProgressOverview + `open:export` custom event | Not started |
| Zen Mode word count + character count + reading time in toolbar | Not started |
| Focus mode (Cmd+Shift+F — paragraph dimming, toolbar hide, floating status) | Not started |
| Session writing stats (+N words this session) | Not started |
| Keyboard shortcuts overlay (Cmd+/) | Not started |
| Backend word_count tracking on fragment saves | Not started |
| Zen page header simplification (remove redundant nav) | Not started |
| **Not Yet Started** | |
| Scene editing in canvas | Not started |
