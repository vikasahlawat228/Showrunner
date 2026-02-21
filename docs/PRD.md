# Product Requirements Document (PRD): Showrunner
**Status:** Alpha v2.0 (Evolution Plan)  
**Last Updated:** 2026-02-21

---

## 1. Executive Summary

**Showrunner** is a context-aware creative studio where a writer provides story fragments in any order, and the system automatically organizes, connects, and enriches them across every dimension — characters, places, timelines, and panels. By replacing the opaque "generate and pray" paradigm of existing tools with a transparent, "glass box" workflow engine, Showrunner ensures the writer maintains total control over every AI decision, prompt, and model choice. Driven by a universal "Bucket" data model, a robust agent ecosystem, and persistent event-sourced timelines, it stands as the ultimate extensible co-writer.

---

## 2. Problem Statement & Vision

**The Broken Paradigm:** Current AI writing tools (such as Sudowrite or NovelAI) treat AI as a black box. Writers provide a prompt, hit "generate," and receive a wall of text. If the text is inaccurate, the user has no visibility into *why* the AI made that decision, what context it utilized, or how to fix it beyond blindly regenerating. Furthermore, these tools enforce rigid schemas (e.g., standard "Character" or "Location" forms) that constrain worldbuilding, lock users into a single model, and lack the ability to research or verify real-world facts.

**The Vision:** Build the **"Ultimate Extensible Co-Writer."**
1. **Total Structural Freedom (Universal Buckets):** Everything is a generic, customizable "Container." Characters, magic systems, research topics, or whole seasons — the user defines the schema.
2. **Glass Box Workflows:** Every AI action is a visible, inspectable pipeline (inspired by n8n or ComfyUI). The writer sees the gathered context, the compiled prompt, and can intervene at any approval gate.
3. **Model Freedom:** At every step, the writer chooses the model (via LiteLLM). Pick Claude 3.5 Sonnet for prose and GPT-4o for image prompts.
4. **Automatic Context Routing:** The system detects entities as you type, automatically linking and retrieving context from the Knowledge Graph and persistent Research Library.

---

## 3. User Personas

1. **The Architect:** A meticulous planner deeply invested in worldbuilding and story structure before writing prose. Needs robust schema building, timeline branching, visual relationship mapping (Knowledge Graph), and hierarchical story structuring.
2. **The Discovery Writer (Pantser):** Writes linearly or in scattered fragments, letting the story unfold naturally. Needs distraction-free writing (Zen Mode), automatic entity detection, context routing, and on-demand quick AI actions.
3. **The Visual Storyteller / Director:** Thinks in terms of scenes, camera angles, and storyboards. Needs the Storyboard Canvas and Prompt Composer to visualize panels before moving to production or external image generators.

---

## 4. Core Features

| Feature | Description | User Story | Acceptance Criteria | State | Priority |
|---|---|---|---|:---:|:---:|
| **Everything is a Container (Bucket)** | Polymorphic EAV data model persisted in YAML. | As an Architect, I want to define custom data types (e.g., "Spell") so my worldbuilding fits my story constraints. | Given a new custom schema, When I create an instance, Then it is saved as a YAML file and indexed in the KG. | ✅ | P0 |
| **Knowledge Graph** | SQLite index of all buckets and typed relationships. Visual React Flow canvas. | As a writer, I want to visually see the relationships mapping my characters to locations. | Given existing buckets, When I open `/dashboard`, Then I see nodes and edges representing their relationships. | ✅ | P0 |
| **Schema Builder** | UI at `/schemas` to define custom bucket types via NL Wizard. | As an Architect, I want an AI to help me build a schema framework without writing JSON/YAML. | Given a natural language prompt, When submitted to Schema Wizard, Then it generates valid `FieldDefinition` objects. | ✅ | P1 |
| **Event Sourcing & Branching** | Immutable append-only SQLite log (`event_log.db`). | As a Pantser, I want to explore alternate story branches without breaking my main draft. | Given a state change, When saved, Then an event is appended and state projection is updated. | 🔧 | P0 |
| **Zen Mode Writing Engine** | `/zen` TipTap editor with `@-mention` and `/command` palette. | As a Discovery Writer, I want a distraction-free space that connects to my world Bible. | Given I type `@Zara`, When I select it, Then it links to the Zara bucket. | ✅ | P1 |
| **Context Routing (Entity Detection)** | Automatic linking of typed text to buckets + incremental KG updates. | As a writer, I want the system to know when I mention a character so it groups context automatically. | Given text mentioning "Zara", When I stop typing, Then the system detects the entity and auto-links it. | 🔧 | P0 |
| **Storyboard Canvas** | `/storyboard` Strip view and Semantic Canvas (React Flow). | As a Director, I want to map out scene panels before generating images. | Given a scene text, When I click "Generate Panels", Then Gemini creates panels with camera angles. | ✅ | P2 |
| **Workflow Engine (Pipelines)** | Visual DAG builder (`/pipelines`) + Composable templates. | As a power user, I want to compose my own AI steps to format outputs exactly how I like. | Given a custom DAG, When I run it, Then it executes steps topologically and pauses at human checkpoints. | ✅ | P1 |
| **Human-in-the-Loop Gates** | Interception at `PromptReviewModal` (Edit, Chat, Paste, Skip). | As a writer, I want to refine the AI's prompt before it generates the response. | Given an AI step reaches a human checkpoint, When I click "Chat", Then I can refine the prompt intent. | ✅ | P0 |
| **Story Structure Layer** | Hierarchical buckets: Season -> Arc -> Act -> Chapter -> Scene. | As an Architect, I want to organize my novel into manageable acts and chapters. | Given a Season bucket, When I view the tree, Then I see its nested sequential hierarchy. | 🆕 | P0 |
| **Multi-Project & Multi-Timeline** | Dashboard supporting multiple project silos and parallel history branches. | As an author of multiple series, I need separate project environments. | Given I am on the dashboard, When I click "New Project", Then a separate environment is initialized. | 🆕 | P0 |
| **Model Configuration Cascade** | Pick LLMs at Per-Step > Per-Bucket > Per-Agent > Project level. | As a power user, I want Claude 3.5 Sonnet for prose and GPT-4o for image prompts. | Given the Pipeline Builder, When I select a model, Then the `llm_generate` step uses that model via LiteLLM. | 🆕 | P1 |
| **Research Agent & Library** | Agent for factual deep-dives, stored in a persistent bucket library. | As a sci-fi writer, I want to ensure my orbital mechanics are accurate. | Given a real-world concept, When researched, Then a knowledge bucket is created with confidence scores. | 🆕 | P1 |
| **RAG / Vector Search** | Embedding store for semantic retrieval of buckets. | As a writer with a huge world bible, I want the AI to find relevant lore without manual linking. | Given a query, When the ContextEngine runs, Then it retrieves semantically similar buckets. | 🆕 | P2 |
| **Context Engine** | Service managing token budgeting and relevance scoring. | As a writer, I never want to exceed my context window. | Given too much context, When retrieving, Then the engine summarizes data to fit the token budget. | 🆕 | P1 |

*Legend: ✅ Implemented | 🆕 New | 🔧 Needs Rework*

---

## 5. Information Architecture

Everything in Showrunner descends from the `GenericContainer` (Bucket) model.

**The Bucket Model:**
- **Attributes:** `id`, `container_type` (schema reference), `name` (Display name), `attributes` (Dynamic EAV fields JSON), `relationships` (typed edges to other buckets), `context_window` (LLM-friendly auto-summary), `timeline_positions`, `tags`, `model_preference`.

**Story Structure Hierarchy:**
- Projects exist as isolating boundaries.
- The structure forms a directed relationship tree: **Season → Arc → Act → Chapter → Scene**.
- **World Bible:** Season-independent buckets (Characters, Magic Systems, Factions).
- **Research Library:** Persistent factual knowledge buckets with confidence tracking.
- **Alternate Timelines:** Divergent branches stored in `event_log.db` inheriting the parent chain state up to the fork.

---

## 6. AI Agent System

Every AI agent follows a universal invocation pattern: *Gather Context → Select Model → Build Prompt → ⏸️ Show to User → Execute → ⏸️ Show Output → Save → Emit Event → Index KG.*

| Agent | Purpose | Default Model | Trigger | Input/Output Contract |
|---|---|---|---|---|
| **🔬 Research Agent** | Deep-dives into real-world topics for facts, builds Research Library. | `gemini-2.0-pro` | Manual "Research" click or auto-detected real-world term. | **In:** Query string. **Out:** Structured Knowledge Bucket. |
| **🧠 Brainstorm Agent** | Generates ideas and "what if" scenarios. | `gemini-2.0-flash` | Manual "Brainstorm" command. | **In:** Scene Context. **Out:** Array of concepts. |
| **📐 Story Architect** | Builds outlines, act structures, and arc planning. | `gemini-2.0-flash` | "Outline from concept" button. | **In:** Logline. **Out:** Hierarchical structural buckets. |
| **✍️ Writing Agent** | Drafts prose from outlines and context. | `claude-3.5-sonnet` | "Draft scene" command. | **In:** Outline+Context. **Out:** Prose fragment. |
| **🎨 Prompt Composer** | Builds optimized prompts for image generation. | `gpt-4o` | Pipeline image generation step. | **In:** Panel metadata. **Out:** External Image API prompt. |
| **🔍 Continuity Analyst** | Detects plot holes and paradoxes. | `gemini-2.0-flash` | Auto-runs on scene save. | **In:** State diff. **Out:** Validation warnings/report. |
| **🧩 Schema Wizard**| NL to custom type formulation. | `gemini-2.0-flash` | Schema Builder NL wizard. | **In:** NL String. **Out:** `FieldDefinition` list. |
| **🎬 Pipeline Director** | Assembles pipeline steps dynamically. | `gemini-2.0-flash` | Pipeline builder assist. | **In:** NL workflow request. **Out:** DAG definition JSON. |
| **🎭 Style Enforcer** | Ensures consistent tone/voice across scenes. | Configurable | Optional workflow step. | **In:** Draft + Style Guide. **Out:** Revised text. |
| **🌍 Translator Agent**| Translates content preserving style. | Configurable | Optional workflow step. | **In:** Source language text. **Out:** Target text. |

---

## 7. Workflow Engine

The engine features three layers of automation:
1. **Layer 1: Quick Actions:** Inline `/commands` in Zen Mode (expand, brainstorm, research). Inherently injects the immediate visual context.
2. **Layer 2: Workflow Templates:** 1-Click pre-built flows (e.g., "Outline -> Draft"). Features approval gates (`⏸️`) at major steps.
3. **Layer 3: Custom Pipelines:** Full visual DAG Builder (`/pipelines`). Implements execution steps (Context, Transform, Human, Execute) and logical control flow (If/Else, Loop, Merge).

**Approval Gates Pattern:**
At every checkpoint step (`REVIEW_PROMPT`, `APPROVE_OUTPUT`, `APPROVE_IMAGE`), the engine pauses execution. The user opens the `PromptReviewModal` to:
- ✏️ Edit the text
- 💬 Chat to dynamically refine intent
- 🔧 Change the LiteLLM model
- 📋 Paste an output from an external tool
- ⏭️ Skip the step entirely
- ✅ Approve

**Model Cascade Optimization:**
When triggering LLM execution, the utilized model relies on a strict override cascade:
`Per-Step (Pipeline Definition) > Per-Bucket Preference > Per-Agent Default > Project Default`.

---

## 8. UI/UX Specification

- **Command Center (`/dashboard`):** Multi-project launchpad. Displays active project progress (Act 1: 80%), pending human-in-the-loop checkpoints, quick Model Config dropdowns, and the interactive Knowledge Graph.
- **Story Timeline (`/timeline`):** Git-style branching visualization tool. Renders Seasons and Chapters across alternate timelines to let writers visually explore parallel histories.
- **Writing Desk (`/zen`):** The enhanced TipTap editor interface. Features floating Context Sidebar for entity summaries, explicit inline `@-mentioning`, `/commands` for swift Agent triggers, and an expandable Storyboard Strip at the bottom.
- **Storyboard Canvas (`/storyboard`):** Two-mode visualizer. `Strip View` offers `dnd-kit` powered horizontal scene strips. `Semantic Canvas` leverages React Flow to provide zoom-level LOD for managing panel grids and camera angles visually.
- **Workflow Studio (`/pipelines`):** Visual DAG builder. Features categorized node library, drag-and-drop wiring, multi-variant transformation templates, and per-node model override configuration panels.

---

## 9. API Surface

The API acts as a gateway proxy to FastAPI on port 8000:

- **Projects:** `GET /POST /api/v1/projects/`, `GET /{id}/structure`, `PUT /{id}/settings`, `PUT /{id}/model-config`
- **Buckets/Containers:** Domain-merged CRUD routines referencing YAML backend via `ContainerRepository`.
- **Schemas:** `GET/POST /api/v1/schemas/`, `POST /generate`, `POST /validate`
- **Knowledge Graph:** `GET /api/v1/graph/`
- **Timeline/Events:** `GET /api/v1/timeline/events`, `POST /checkout`, `POST /branch`
- **Pipelines:** `POST /api/pipeline/run`, `GET /{id}/stream` (SSE), `POST /{id}/resume`, `/definitions`
- **Writing Engine:** `POST /api/v1/writing/fragments`, `/detect`, `/context`, `/search`
- **Storyboard:** CRUD `panels`, `POST /scene/{id}/generate`, `POST /panels/reorder`

---

## 10. Data Model

- **GenericContainer:** Standardized Pydantic structure generated safely via runtime compilation (`ContainerSchema.to_pydantic_model()`). Persisted solely in `.yaml` files as the source of truth.
- **Knowledge Graph Index:** Denormalized SQLite (`knowledge_graph.db`) synchronizing the `.yaml` structures on boot and incrementally updating to support highly relational queries.
- **Event Sourcing:** `event_log.db` holding the immutable tables:
  - `events`: (id, parent_event_id, branch_id, timestamp, event_type, container_id, payload_json)
  - `branches`: (id, head_event_id)
- **Model Configs:** Lightweight hierarchical dictionaries nested within project and bucket metadata.

---

## 11. Non-Functional Requirements

- **Performance Constraints:** 
  - LLM Entity detection (`/detect`) must debounce exactly 2s post-typing. 
  - Graph rendering must process >1000 nodes maintaining 60FPS using React Flow hybrid rendering fallbacks.
- **Persistence Guarantees:** 
  - ALL state mutators must be fully persisted. `PipelineService`, `WritingService`, and `StoryboardService` MUST stop utilizing in-memory dictionaries and route wholly through `ContainerRepository`.
- **System Extensibility:** 
  - Integrating new LLMs relies purely on updating LiteLLM string identifiers. 
  - Modifying the AI workflow behavior should require zero coding, relying exclusively on node manipulation in Workflow Studio.

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| **Context Transparency** | 100% of LLM prompts and retrieved context are visible, editable, and copyable. |
| **Model Flexibility** | 100% of pipeline LLM execution steps offer localized model configuration overrides. |
| **Undo Safety** | 100% of write-paths emit to `EventService`, eliminating all irreversible state overwrites. |
| **Architecture Robustness** | 0 instances of unrecoverable data loss upon backend restart (`ContainerRepository` integration). |
| **Agent Autonomy** | Research Agent handles 100% of factual context augmentation automatically if enabled. |

---

## 13. Implementation Phases

### Completed Phases

- **Phase A–E: Foundation + UI Build** ✅
  - Full 3-pane workbench layout with drag-drop, inspectors, chapter navigation
  - Zen Mode writing engine with TipTap, @mentions, /slash commands, auto-save
  - Pipeline Builder with visual DAG editor, SSE streaming, PromptReviewModal
  - Storyboard Canvas with strip + semantic canvas views, panel CRUD + generation
  - Timeline with real-time SSE, event type styling, branch creation
  - Schema Builder with NL wizard, field editor, preview
  - Knowledge Graph (SQLite + ReactFlow canvas), ChromaDB RAG, Event Sourcing
  - Agent Dispatcher with ReAct loops, 6 skill files, keyword + LLM routing
  - Context Engine with token budgeting, relevance scoring
  - Model cascade resolution (Step > Bucket > Agent > Project)
  - File watcher (watchdog + SSE broadcast)
  - 3-format export (Markdown, JSON, Fountain)
  - Toast notifications (sonner), loading skeletons, confirmation dialogs
  - Context Inspector / Glass Box UI (shows AI context, model, agent per operation)

- **Phase F: Foundation Rework** 🔧 (Partially Complete)
  - ✅ Context Engine with token budgeting
  - ✅ Model cascade resolution via ModelConfigRegistry
  - ✅ Multi-project listing + structure tree endpoints
  - 🔧 Wire `EventService.append_event()` across ALL remaining mutation paths
  - 🔧 Full YAML persistence for pipeline runs (ditch in-memory dictionaries)
  - 🔧 Complete multi-project isolation & structural bucketing (Season→Scene)

- **Phase G: Workflow & Agents Enhancement** 🔧 (Partially Complete)
  - ✅ Agent Dispatcher with keyword routing + LLM classification fallback
  - ✅ ReAct loop execution in AgentDispatcher
  - ✅ PromptReviewModal with Edit/Refine/Paste/Skip + model selector
  - 🔧 Logic control nodes (if/else, merge, loop) in pipeline builder
  - 🔧 1-Click Workflow Templates (wired end-to-end)
  - 🔧 Research Agent UI surface

### Upcoming Phases

- **Phase Next-A: Writer's Daily Experience** ✅ (Complete)
  - Toast notification system (sonner)
  - Zen Mode slash commands wired to agents
  - Confirmation dialogs for destructive actions
  - Loading skeletons across all views
  - Context Inspector / Glass Box transparency panel

- **Phase Next-B: Emotional Intelligence** ✅ (Complete)
  - **Emotional Arc Dashboard / Pacing Heatmap**: Analyze each scene/chapter for emotional valence (hope/conflict/tension). Visualize as a line chart overlaid on the timeline. Flag flat zones with no tension peaks. Backend: new `analysis_service.py` using LLM to score scenes. Frontend: new `EmotionalArcChart.tsx` on Timeline page.
  - **Character Voice Scorecard**: Analyze dialogue per character across scenes. Score vocabulary diversity, avg sentence length, formality level, unique phrases. Alert when two characters sound identical. Backend: new endpoint in `writing.py` router. Frontend: new panel in CharacterInspector.
  - **Story Ribbons Visualization**: Character presence + significance per scene as colored ribbons. Thickness = how prominent a character is in that scene. Backend: derive from Knowledge Graph relationships. Frontend: SVG visualization in Timeline page.

- **Phase Next-C: Panel Intelligence** ✅ (Complete)
  - **Panel Layout Intelligence**: AI analyzes narrative beat type (action/dialogue/reveal/transition/montage/emotional) and suggests panel count, sizes, camera angles. `suggest_layout()` in StoryboardService + `LayoutSuggestionPanel.tsx` with visual preview and "Apply & Generate" button.
  - **Character Progressions (Visual DNA Timeline)**: Character DNA evolves over chapters via `attributes.progressions` array with deep-merge resolution. CRUD endpoints + `dna-at-chapter/{chapter}` resolution. `CharacterProgressionTimeline.tsx` horizontal timeline in CharacterInspector.
  - **Reader Scroll Simulation**: `/preview` page simulating webtoon reading experience. `ReaderSimService` computes per-panel reading times, text density, pacing dead zones, engagement score. Auto-scroll player with speed control + pacing sidebar.

- **Phase Next-D: Workflow Power** ✅ (Complete)
  - **Workflow Templates Library**: 5 ready-to-use templates wired end-to-end in `templates/workflow_templates.py` (Scene→Panels, Concept→Outline, Outline→Draft, Topic→Research, Draft→Polish). `GET /api/pipeline/templates` + `POST /templates/{id}/create`. TemplateGallery fetches from API.
  - **Enhanced Approval Gate**: Temperature slider (0–2), pin/unpin context buckets per Glass Box entry, "Regenerate" button. Pipeline resume supports `temperature_override` + `pinned_context_ids` in `_handle_llm_generate`.
  - **Research Agent UI Surface**: `/research` page with topic list + search, structured detail panel (summary, key_facts, constraints, story_implications), new query input, link-to-scene support. `ResearchDetailPanel.tsx` + `ResearchTopicCard.tsx`.

- **Phase Next-E: Spatial & Structural** ✅ (Complete)
  - **Story Structure Visual Editor**: New `containers.py` router with full CRUD + bulk reorder for structural containers (season/arc/act/chapter/scene). `ContainerRepository` extended with `get_by_id()` and `delete_by_id()`. `StoryStructureTree.tsx` enhanced with "Add Child" per node, delete with confirmation, "Open in Zen" for scenes, drag-reorder wired to `POST /containers/reorder`, completion status color-coding (green/amber/blue left border). Fixed `getProjectStructure()` API URL mismatch.
  - **Alternate Timeline Browser**: `EventService` extended with `get_branches()`, `get_events_for_branch()`, `compare_branches()` (state projection diff). Timeline router expanded with `GET /branches`, `POST /branch`, `GET /branch/{id}/events`, `GET /compare?branch_a=X&branch_b=Y`, `GET /stream` (SSE). `BranchList.tsx` sidebar with event counts + active indicator. `BranchComparison.tsx` two-column diff view with color-coded additions/removals/changes. Integrated into `timeline/page.tsx`.
  - **Spatial Brainstorming Canvas**: New `/brainstorm` page with ReactFlow infinite canvas. `IdeaCardNode.tsx` custom node with editable text, color coding, auto-save on drag-end/blur. `SuggestionPanel.tsx` shows AI-suggested connections/new ideas with accept/dismiss. Backend: 4 brainstorm endpoints on `director.py` (suggest-connections via `brainstorm_agent`, save-card, get-cards, delete-card). Cards persisted as `GenericContainer` with `container_type: "idea_card"`.
  - **Voice-to-Scene**: `POST /api/v1/storyboard/voice-to-scene` endpoint orchestrating `suggest_layout()` → `generate_panels_for_scene()` pipeline. `VoiceToSceneButton.tsx` using browser-native Web Speech API with three states (idle/recording/processing), editable transcript review, scene selector, panel count config. Textarea fallback for unsupported browsers. Integrated into Storyboard page header.

- **Phase H: Intelligence Layer** ✅ (Complete)
  - **Continuity Auto-Check**: `ContinuityService` wiring `continuity_analyst` agent skill. Validates story changes against KG + future dependencies. 3 endpoints on `analysis.py` (`POST /continuity-check`, `POST /continuity-check/scene/{id}`, `GET /continuity-issues`). `ContinuityPanel.tsx` in Zen ContextSidebar "Continuity" tab with severity-coded issue cards.
  - **Style Enforcer**: `StyleService` wiring `style_enforcer` agent skill. Evaluates prose against `NarrativeStyleGuide`. `POST /style-check` on `analysis.py`. `StyleScorecard.tsx` in ContextSidebar "Style" tab + Style tab in PromptReviewModal. `/check-style` slash command in Zen Mode.
  - **Translation Agent UI**: `TranslationService` wiring `translator_agent` skill with glossary support. New `translation.py` router (`POST /translate`, `GET /glossary`, `POST /glossary`). `TranslationPanel.tsx` + `/translation` page (Translation Studio). `InlineTranslation.tsx` widget in Zen ContextSidebar "Translation" tab. `/translate` slash command.
  - **NL → Workflow Generation**: Backend already existed (`PipelineService.generate_pipeline_from_nl()`). `NLPipelineWizard.tsx` modal on Pipelines page with textarea, example prompts, and "Open in Builder" action.
  - **Semantic @Mentions in Zen Mode**: `GET /api/v1/writing/semantic-search` endpoint using ChromaDB vector search. ZenEditor @mentions upgraded from keyword to semantic search. Relevance indicator in MentionList dropdown.

- **Phase I: Polish** 🆕 (In Progress — 3 Sessions Designed)
  - **Persistent Navbar + Command Palette**: Sticky top navigation across all 10 pages. `cmdk`-powered Cmd+K command palette for page navigation, actions, search. React error boundary with crash recovery fallback.
  - **Export UI + HTML/PDF**: Export modal with 4 format cards (Markdown/JSON/Fountain/HTML), preview area, download + browser Print-to-PDF. New `export_html()` backend with print-friendly CSS. Export trigger on Dashboard ProgressOverview.
  - **Zen Mode Polish**: Real-time word/character/reading-time counter. Focus mode (Cmd+Shift+F) that dims non-active paragraphs. Session writing stats (+N words this session). Keyboard shortcuts overlay (Cmd+/). Backend word_count tracking on fragment saves.

---

## 14. Risks & Mitigations

- **Context Size Limit Exceeded:** Aggregating character graphs easily eclipses max token allowances.
  *Mitigation:* `ContextEngine` must proactively summarize peripheral variables and strictly adhere to LLM-aware token budgets before building the final prompt.
- **Event Sourcing Storage Bloat:** Writing a JSON blob to SQLite on every keystroke fragment will inflate the datastore.
  *Mitigation:* `WritingService` uses aggressive debouncing and stores only snapshot diffs instead of continuous strokes.
- **Relational Paradoxes on Branch Restores:** Checking out an old story branch could conflict with a globally updated World Bible relationship.
  *Mitigation:* `Continuity Analyst` conducts immediate verification on branch resolution, flagging unresolvable relationships to the human.
- **In-Memory Volatility:** Existing prototypes risk data wipe.
  *Mitigation:* Phase F exclusively addresses routing all service state through `ContainerRepository` as the highest technical priority.

---

## 15. Appendix: Competitive Analysis

| Competitor | Their Flaw | The Showrunner Answer |
|---|---|---|
| **Scrivener** | Exceptional at organizational trees but possesses zero internal AI tooling. Completely manual drafting. | Mimics the robust deep structural depth of Scrivener but acts natively as an extensible node within AI pipelines. |
| **Final Draft** | Iron-clad industry standard formatting, but functionally inflexible for mixed-media projects. | Abstractions allow scripts, panels, and novels to exist concurrently as universally formatted buckets. |
| **Sudowrite / NovelAI** | Promotes "black box" text blasting. No true concept of cross-linking robust knowledge bases or real-world fact-checking. | Enforces "glass box" transparent prompt composition. User dictates exact models, context, and logic steps before generation. |
| **Boords** | Top-tier storyboard management, but isolated completely from the prose document or character bibles. | natively bridges the writing interface (`/zen`) with the storyboard canvas, leveraging AI to automatically extract physical descriptions to panels. |
