# Session 21: High-Level Architecture Update — System Architect Agent

## Your Role

You are a **Staff-Level System Architect** specializing in Python (FastAPI), React (Next.js), and Agentic AI orchestrations. You have a deep understanding of Event Sourcing, Entity-Attribute-Value (EAV) data modeling, DAG-based workflow engines, and LLM context engineering.

Your job is to rewrite the **High-Level Design Document (`DESIGN.md`)** for **Showrunner** to align with the newly updated Product Requirements Document (PRD).

---

## Context

Showrunner is transitioning from a rigid CLI tool to a "Glass Box" visual co-writer platform. The PRD has just been fully rewritten to introduce several massive architectural shifts:

1. **The Universal Bucket Model** — Everything (Characters, Scenes, Seasons, Research Topics) is a `GenericContainer`.
2. **Story Structure Hierarchy** — Project → Season → Arc → Act → Chapter → Scene.
3. **The Research Agent & Library** — A dedicated agent for factual deep-dives that stores results in persistent knowledge buckets.
4. **Automatic Context Routing** — Entity detection that auto-links buckets to scenes as the user types.
5. **Model Configuration Cascade** — LiteLLM model selection at the Step > Bucket > Agent > Project level.
6. **Multi-Project & Multi-Timeline Support** — Isolating data and expanding the event-sourcing branch model.

### What Exists Today (Alpha v2.0)

*(You must map your new architecture onto this existing reality. Do not invent new frameworks; extend what is here.)*

- **Backend:** FastAPI (Python 3.11), `sse-starlette` for streaming, `pydantic` for dynamic schemas.
- **Frontend:** Next.js 16 (App Router), React 19, React Flow, Zustand slices (`graphDataSlice`, `reactFlowSlice`, `zenSlice`, etc.).
- **Storage:** Local YAML files (via `ContainerRepository`), SQLite JSON1 for Knowledge Graph (`knowledge_graph.db`), SQLite DAG for Event Sourcing (`event_log.db`).
- **Pipeline Engine:** `PipelineService` with 11 step types, DAG topological sorting, and human checkpoint pausing (REVIEW_PROMPT, APPROVE_OUTPUT).
- **Agent Dispatcher:** Keyword + LLM intent routing executing static markdown skills via LiteLLM.
- **Context Engine:** Token budgeting, relevance scoring, LLM summarization fallback.

### The Problem

The current `DESIGN.md` reflects an older "Alpha v2.0" state where:
- Story structure doesn't exist (only characters/world/scenes).
- Model selection is hardcoded to `gemini-2.0-flash`.
- Pipelines are manual-only, with no "Workflow Templates" concept.
- Event Sourcing writes are completely disconnected from the rest of the app.
- Context routing is entirely manual.
- There is no concept of a "Research Library".
- Agents are just 5 static markdown files.

---

## Your Output Requirements

Rewrite `docs/DESIGN.md` completely. Make it the definitive high-level architectural blueprint for Phase F through I.

### Required Sections & Architectural Decisions You Must Document:

#### 1. System Overview (with Mermaid Diagram)
Update the architecture diagram to show the new multi-project isolation, the Research Library, the Model Config Registry, and the 10-agent ecosystem communicating via the Agent Dispatcher.

#### 2. Core Architecture: The Universal Bucket Model
Explain how `GenericContainer` handles hierarchical story structures (Season -> Act -> Scene) and how it stores the new properties (`context_window`, `timeline_positions`, `tags`, `model_preference`).

#### 3. Core Architecture: Event Sourcing & Branching
Explain how ALL mutations will now flow: REST API → Domain Service → `EventService.append_event()` → `ContainerRepository.save()` → `SQLiteIndexer.upsert()`. Explain how branches will work for Alternate Timelines.

#### 4. Core Architecture: Model Configuration Cascade
Design the configuration system. How does the backend resolve which model to pull from LiteLLM when a pipeline step executes? Explain the hierarchy: Step Definition > Bucket Preference > Agent Default > Project Default.

#### 5. Core Architecture: Automatic Context Routing & Research
Design the flow for when a user types in Zen Mode: Entity detection (Gemini) → KG lookup → Auto-linking → Context Sidebar update. Explain how the Research Agent persists knowledge as buckets and auto-injects them via the `ContextEngine`.

#### 6. The Glass Box Pipeline System
Explain the 3 layers (Quick Actions, Workflow Templates, Custom Pipelines). Detail the Approval Gate pattern (`PromptReviewModal` states: Edit, Chat, Paste, Skip, Change Model).

#### 7. AI Agent Ecosystem
List all 10 agents. Explain how `AgentDispatcher` is evolving from static markdown files into dynamic React (Reason+Act) executors.

#### 8. API Surface & Dependency Injection
Update the REST router list to include `/projects/`, `/models/`, and hierarchical scene routing. Update the FastApi `deps.py` diagram to include `ContextEngine` and `AgentDispatcher` singletons.

#### 9. Frontend Architecture
Update the Zustand slice architecture and component layout to account for the new Command Center, multi-project context, and enhanced Workflow Studio nodes.

### Quality Standards

- **Code Snippets:** Use Python/Pydantic snippets to illustrate the updated `GenericContainer` and Model Config structures. Use Mermaid for data flows.
- **Pragmatism:** Hook new concepts into existing services (`PipelineService`, `WritingService`) rather than inventing 10 new microservices. Stay true to the local-first, YAML+SQLite architecture.
- **Clarity:** This document is for engineers implementing the system. Tell them exactly *how* the generic concepts in the PRD translate into Python classes, DB tables, and React state.
- **Formatting:** Use standard Markdown. No HTML tags.

Output the entire DESIGN.md as a single document.
