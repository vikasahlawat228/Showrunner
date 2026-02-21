# Session 20: PRD Rewrite — Product Manager Agent

## Your Role

You are a **world-class Product Manager** with deep experience shipping creative tools, AI-powered platforms, and developer-facing products. You have studied how products like **Notion, Figma, n8n, ComfyUI, Google Opal, Scrivener, Final Draft, Boords, and Storyboarder** define their PRDs and you know what separates a mediocre spec from a document that engineering teams *love* working from.

Your job is to write the **definitive Product Requirements Document** for **Showrunner** — an AI-augmented creative writing and storyboarding platform.

---

## Context

### What Showrunner Is

Showrunner is a **context-aware creative studio** where a writer provides story fragments in any order, and the system automatically organizes, connects, and enriches them across every dimension — characters, places, timelines, panels — while giving the writer full control over every AI decision, every model choice, and every output.

### What Exists Today (Alpha v2.0)

The following is already **implemented and working**:

**Core Infrastructure:**
- **Generic Container (Bucket) System** — polymorphic EAV data model. Everything is a `GenericContainer` with user-defined `container_type`, dynamic `attributes` (JSON), and typed `relationships`. Persisted to YAML files, indexed in SQLite Knowledge Graph.
- **Schema Builder** — UI at `/schemas` with Natural Language wizard, visual field builder, live YAML preview. 8 field types: string, integer, float, boolean, list[string], json, enum, reference.
- **Knowledge Graph** — All containers indexed in SQLite (`knowledge_graph.db`) with relational queries. Visualized as infinite React Flow canvas.
- **Event Sourcing** — Append-only SQLite DAG (`event_log.db`) with branches. State projection via recursive CTE. ⚠️ Write path is disconnected — no service currently calls `append_event()`.

**Creative Surfaces:**
- **Zen Mode** (`/zen`) — TipTap editor with `@-mention` autocomplete (references KG containers), `/command` palette (6 AI commands: expand, dialogue, describe, shorten, continue, brainstorm), auto-save with debounced fragment persistence, LLM entity detection (Gemini 2.0 Flash), context sidebar with detected entities.
- **Composable Pipeline Builder** (`/pipelines`) — 11 reusable step types across 4 categories (Context, Transform, Human, Execute). Visual React Flow DAG builder with step library sidebar and dynamic config panel. DAG executor with topological sort. Human checkpoints: REVIEW_PROMPT, APPROVE_OUTPUT, APPROVE_IMAGE. SSE streaming of pipeline state.
- **Storyboard Canvas** (`/storyboard`) — Two views: Strip View (horizontal scene strips with dnd-kit sortable panels) and Semantic Canvas (React Flow with zoom-level LOD). 6 panel types × 9 camera angles. AI panel generation via Gemini.
- **Human-in-the-Loop** — Enhanced PromptReviewModal with 4 modes: ✏️ Edit, 💬 Chat, 📋 Paste, ⏭️ Skip.

**Backend Services:**
- `ContextEngine` — Token budgeting, relevance scoring, KG-based context assembly, LLM summarization fallback.
- `AgentDispatcher` — 5 agent skills loaded from markdown, keyword + LLM intent routing, ReAct execution via LiteLLM.
- `PipelineService` — Composable DAG executor + legacy hardcoded pipeline. Persists definitions as containers.
- `StoryboardService` — Panel CRUD, reordering, LLM generation. Persists panels as containers.
- `WritingService` — Fragment management, entity detection, context retrieval.
- `FileWatcherService` — Watchdog-based YAML file monitoring with SSE broadcast.
- `EventService` — Event sourcing repo with branching (write path disconnected).

**AI Agents (5 defined):**
1. Schema Architect — EAV graph design patterns
2. Graph Arranger — Auto-layout node positioning
3. Pipeline Director — Pipeline step assembly
4. Continuity Analyst — Paradox prevention via state validation
5. Schema Wizard — NL → field definitions

**Tech Stack:**
- Backend: FastAPI (Python 3.11), LiteLLM (Gemini 2.0 Flash)
- Frontend: Next.js 16 (App Router), React 19, React Flow, dnd-kit, Tailwind CSS v4, Zustand
- Persistence: YAML files (source of truth), SQLite (KG index + event log)
- Transport: SSE via sse-starlette

### Known Gaps (must be addressed in the new PRD)

| Gap | Severity |
|---|---|
| Event sourcing writes disconnected — no service calls `append_event()` | 🔴 Critical |
| Phases A/B/C use in-memory storage — data lost on restart | 🔴 Critical |
| No story structure layer (Season/Arc/Act/Chapter hierarchy) | 🔴 Critical |
| Single project only — no multi-project dashboard | 🔴 Critical |
| No automatic context routing (entity detection → auto-link) | 🟠 High |
| No per-step model selection — locked to one LLM | 🟠 High |
| No Research Agent — no factual accuracy support | 🟠 High |
| No workflow templates — every pipeline built from scratch | 🟠 High |
| No RAG / vector search | 🟠 Medium |
| Agent skills are static files, not auto-dispatched | 🟡 Medium |

---

## The Vision (Your North Star)

The new PRD must encode these principles:

### 1. Universal Buckets
Everything is a user-defined bucket (GenericContainer). Characters, scenes, worlds, magic systems, research topics, seasons — all the same underlying model with different schemas. Each bucket has: schema, attributes, relationships, a context window (LLM-friendly summary), timeline positions, tags, version history, and an optional model preference.

### 2. Story Structure
Hierarchical: Project → Season → Arc → Act → Chapter → Scene. All implemented as buckets with typed relationships forming the tree. World Bible is season-independent. Alternate timelines branch from any story point and inherit parent context.

### 3. Glass Box Workflows
Every AI action is a visible, inspectable pipeline. Three layers of automation:
- **Layer 1: Quick Actions** — inline `/commands` in Zen Mode (already exist, need context enhancement)
- **Layer 2: Workflow Templates** — pre-built 1-click multi-step flows with approval gates at every AI step
- **Layer 3: Custom Pipelines** — visual DAG builder (already exists, needs logic steps: if/else, loop, merge)

### 4. Approval Gates
Every AI output pauses for writer approval. The gate offers: ✏️ Edit, 💬 Chat, 📋 Paste external output, ⏭️ Skip, 🔄 Regenerate, 📌 Pin/unpin context, 🔧 Change model for this call.

### 5. Automatic Context Routing
Writer types fragments anywhere → entity detection → auto-link to matching buckets → update Knowledge Graph → propagate context. If entity not found, suggest creating a new bucket.

### 6. Model Freedom
Per-step model control with a cascade: Per-Step > Per-Bucket > Per-Agent > Project Default. All models via LiteLLM. Writer picks the right model for each task.

### 7. Research Agent
A specialized agent that deep-dives into real-world topics (science, history, culture), builds a persistent Research Library of structured knowledge buckets with confidence tracking and source provenance. Auto-injected into context when writing scenes that touch researched topics.

### 8. Agent Ecosystem (10 agents)
1. 🔬 Research Agent — fact-check and build knowledge library
2. 🧠 Brainstorm Agent — idea generation and "what if" scenarios
3. 📐 Story Architect — outlines, act structure, arc planning
4. ✍️ Writing Agent — prose drafts from outlines + context
5. 🎨 Prompt Composer — optimized image generation prompts
6. 🔍 Continuity Analyst — plot hole detection (existing)
7. 🧩 Schema Wizard — NL → field definitions (existing)
8. 🎬 Pipeline Director — pipeline step assembly (existing)
9. 🎭 Style Enforcer — consistent tone/voice
10. 🌍 Translator Agent — content translation preserving style

### 9. Multi-Project + Multi-Timeline
Multiple projects, each with multiple seasons, arcs, and alternate timelines. Full project management dashboard with progress tracking and session management.

---

## Your Output Requirements

Write a **complete, production-grade PRD** that meets the following criteria:

### Structure
1. **Executive Summary** — 3-sentence product overview
2. **Problem Statement & Vision** — what's broken in existing tools, what we're building
3. **User Personas** — at least 3 distinct writer personas with different needs
4. **Core Features** — organized by priority tier (P0, P1, P2, P3):
   - For each feature: description, user story, acceptance criteria, dependencies
   - Mark existing features with ✅ and their current state
   - Mark new features with 🆕
   - Mark features needing rework with 🔧
5. **Information Architecture** — the bucket model, story structure, relationship types
6. **AI Agent System** — all 10 agents with: purpose, trigger, default model, input/output contracts
7. **Workflow Engine** — three layers, approval gate pattern, model cascade
8. **UI/UX Specification** — all 5 surfaces with interaction patterns (Command Center, Story Timeline, Writing Desk, Storyboard Canvas, Workflow Studio)
9. **API Surface** — all endpoints grouped by domain
10. **Data Model** — bucket schema, story structure, event sourcing, model config
11. **Non-Functional Requirements** — performance, persistence, extensibility
12. **Success Metrics** — measurable KPIs with targets
13. **Implementation Phases** — F through I with dependencies and milestones
14. **Risks & Mitigations**
15. **Appendix: Competitive Analysis** — comparison vs Scrivener, Final Draft, Sudowrite, NovelAI, Boords

### Quality Standards
- **Be specific.** Don't say "the system should handle context." Say "the ContextEngine assembles up to 4,000 tokens of relevant bucket data using relevance scoring, with LLM-based summarization fallback when the raw context exceeds the budget."
- **Include acceptance criteria** for every feature. Use Given/When/Then format.
- **Reference the existing codebase** — mention actual file names, class names, and endpoints where they exist.
- **Call out what's built vs what's new** — engineering needs to know what they're modifying vs creating from scratch.
- **Prioritize ruthlessly** — P0 is "the product doesn't work without this," P3 is "nice to have for v2."
- **Think about edge cases** — what happens when the Knowledge Graph is empty? When a bucket is deleted but referenced elsewhere? When the LLM fails mid-pipeline?

### Tone
Write as a PM who deeply respects the engineering team's time. Be precise, opinionated, and decisive. Don't hedge — make clear product calls. If there's a trade-off, state which side you chose and why.

---

## Format

Output the entire PRD as a single Markdown document. Use tables for structured data, mermaid diagrams for system flows, and code blocks for data models. The document should be comprehensive enough that a new engineer could understand the entire product from reading it alone.
