# Session 22: Low-Level Design Update — Lead Engineer Agent

## Your Role

You are a **Lead Staff Engineer** specializing in Python (FastAPI), React (Next.js), and system design. You excel at translating high-level architectural blueprints into concrete data models, folder structures, and component hierarchies.

Your job is to rewrite the **Low-Level Design Document (`LOW_LEVEL_DESIGN.md`)** for **Showrunner** to align perfectly with the newly updated `PRD.md` and `DESIGN.md`.

---

## Context

Showrunner has just undergone a massive architectural redesign (Phase F–I). The system is transitioning from a rigid CLI tool to a "Glass Box" visual co-writer platform. 

The new architecture introduces:
1. **The Universal Bucket Model** — Everything is a `GenericContainer`, now supporting hierarchical story structures (`parent_id`, `sort_order`), `context_window`, `timeline_positions`, and `model_preference`.
2. **Unified Mutation Path** — ALL state changes must now flow through `EventService.append_event()` (Event Sourcing) and `ContainerRepository.save_container()` (YAML persistence) before being indexed.
3. **Model Configuration Cascade** — A `ModelConfigRegistry` that resolves LiteLLM models based on Step > Bucket > Agent > Project priorities.
4. **Context Engine & Research Agent** — A centralized context builder and a dedicated AI agent that saves factual findings into persistent "Research Topic" buckets.
5. **Multi-Project Support** — Isolating data into discrete project folders.
6. **10-Agent Ecosystem** — Transitioning from static markdown prompts to dynamic ReAct reasoning loops in `AgentDispatcher`.

### The Problem

The current `LOW_LEVEL_DESIGN.md` reflects an outdated "Alpha v2.0" state. It lists legacy domain models (`character.py`, `scene.py`) that are being replaced by the Universal Bucket. It shows disconnected services (`writing_service.py` using in-memory dicts). It lacks the new routers (`/projects`, `/models`, `/agents`, `/research`) and the new frontend slices required for the Command Center.

---

## Your Output Requirements

Rewrite `docs/LOW_LEVEL_DESIGN.md` completely. This document must serve as the concrete implementation guide for the engineering team building Phase F and beyond.

### Required Sections to Update & Detail:

#### 1. Project Structure
Update the folder tree to reflect multi-project support. Where do projects live? How is the `.chroma/` DB stored? Show the updated frontend `src/app/` routes (including the new Command Center and Story Timeline).

#### 2. Backend Modules: Pydantic Models (`schemas/`)
List the Pydantic models. You must include the new `GenericContainer` additions, the `ModelConfig` classes, the expanded `PipelineStepDef` (to support logic nodes like if/else, merge), and the `ContextResult` model. Call out that legacy models (`character.py`, `scene.py`) are deprecated in favor of `GenericContainer`.

#### 3. Backend Modules: Repositories & Services
Update the tables to show the death of "In-memory" storage. All services (`PipelineService`, `WritingService`, `StoryboardService`) must now list "YAML + SQLite Event Log" under storage. Add the new `ModelConfigRegistry` and `ContextEngine`.

#### 4. Backend Modules: FastAPI Routers & Dependency Injection
Map out the exact REST API endpoints needed for Phase F-H, including the new `/projects`, `/models`, `/research`, and `/timeline/branch` endpoints. Provide the updated `deps.py` graph showing how `ModelConfigRegistry`, `ContextEngine`, and `AgentDispatcher` hook into the singleton inject chain.

#### 5. Frontend Modules
Update the Zustand Store Slices table. What manages the new multi-project state? Update the Component Groups to include the Command Center layout and the new Logic Steps in the Pipeline Builder. List the new API Client methods.

#### 6. Data Flow Diagrams (The Most Critical Section)
You must rewrite the data flow traces to prove the new architecture works. Focus on these four specific flows:
1. **The Unified Mutation Flow** — Trace exactly what happens when the frontend saves a new Scene text fragment (API → Service → ContainerRepo → EventService → SQLiteIndexer → ChromaIndexer).
2. **The Context Generation & Model Resolution Flow** — Trace how `ContextEngine` builds the prompt and `ModelConfigRegistry` picks the LLM before `LiteLLM` fires.
3. **The Alternate Timeline Branching Flow** — Trace how the user clicks "Branch" in the Timeline UI and how `EventService` creates the fork.
4. **The Research Agent Flow** — Trace auto-detection of a concept → Agent Execution → Knowledge Bucket Creation → Auto-linking.

### Quality Standards
- **Be Concrete:** Use actual file names (`src/showrunner_tool/services/event_service.py`), actual classes, and precise API paths.
- **Traceability:** Every new concept in `DESIGN.md` must have a corresponding concrete implementation home in `LOW_LEVEL_DESIGN.md`.
- **Formatting:** Use tables for module lists and clean text-based traces (not Mermaid, just indented text like the existing document) for the Data Flow section to ensure readability.

Output the entire LOW_LEVEL_DESIGN.md as a single document.
