# Showrunner Architecture & Design Document
**Status:** Approved v2.0
**Date:** 2026-02-20

## 1. System Overview
Showrunner is transitioning from a rigid, YAML-backed CLI tool into a **Node-based, Transparent AI Co-Writer**. 
The architecture must support dynamic schemas (Generic Containers), high-performance relational querying (Knowledge Graph), and infinite undo/branching (Event Sourcing).

## 2. Technical Stack
*   **Backend:** FastAPI (Python)
*   **Frontend:** Next.js (App Router), React, Zustand, React Flow (for Node Graph UI), Tailwind CSS v4
*   **Persistence:** Local YAML (Source of Truth) + Local SQLite/DuckDB (In-Memory/Cache for Relational Querying)

## 3. Core Architecture Shifts

### 3.1 The "Generic Container" Database Architecture
Instead of rigid tables/files for `Character`, `World`, and `Scene`, the system uses a polymorphic Document/EAV (Entity-Attribute-Value) model.
*   **The Container Entity:** `id` (UUID), `container_type` (String), `name` (String), `yaml_path` (String), and `attributes` (JSON — stores all dynamic EAV fields).
*   **Schema Definitions:** Users define `Schema` templates. The backend uses dynamic Pydantic generation (`pydantic.create_model`) mapped to Python primitives. A generic endpoint `POST /api/containers/{container_type}` handles incoming JSON payloads, auto-generates the corresponding Pydantic class in-memory, validates the payload, and syncs it.

### 3.2 CQRS & SQLite Graph Indexing
YAML files remain the git-friendly source of truth.
*   **Command (Writes):** Modifying a Container updates the local `.yaml` file.
*   **Query (Reads):** On application boot, the backend parses all YAMLs and populates a local SQLite database leveraging the `JSON1` extension. The frontend hits fast SQL queries against the indexed table for relationships.
*   **Sync:** File watchers (`watchdog` in Python) ensure that external manual edits to YAML files immediately re-sync the SQLite database.

### 3.3 Event Sourcing & The "Undo" Tree (CQRS)
AI generations are unpredictable. Standard state overwriting is dangerous. To support parallel branching (like Git) in an unpredictable AI writing environment:
*   Instead of mutating YAML files directly, every AI action is an immutable atomic event in an append-only log: `{"action": "UPDATE_CONTAINER", "diff": "{...}"}`.
*   **The Data Model (SQLite DAG):**
    *   `events` table: `id`, `parent_event_id`, `branch_id`, `timestamp`, `event_type`, `payload`.
    *   `branches` table: `id` (e.g., "main"), `head_event_id`.
*   **State Projection:** The active story state (the YAML files or in-memory Knowledge Graph) is a Materialized View built by walking the event log backwards from a branch's head and applying payloads sequentially.
*   **Benefits:** Enables cheap "Time Travel" (checkout an old event to spawn a parallel `timeline_diverged` branch), makes debugging trivial, and allows the specific Continuity Analyst Agent to vet proposed diffs against the Projected State before merging.

## 4. The Transparent "Glass Box" Director

The `DirectorService` no longer executes a monolithic black-box function. It is a state-machine execution engine.
1.  **Pipeline Definition:** Workflows (e.g., "Generate Scene") are defined dynamically by the Pipeline Director Agent into discrete steps (Context Gathering -> Prompt Assembly -> User Intercept -> Execution -> Critique).
2.  **Streaming & Pause (SSE):** The backend uses Server-Sent Events (SSE) to stream state transitions to the Next.js client. Unidirectional SSE is inherently more stable than WebSockets for long-running human-in-the-loop workflows.
3.  **Human Interception:** When the state machine reaches a `USER_INTERCEPT` node, the backend persists the current payload (e.g., the assembled LLM prompt) with a `PAUSED` state to the DB and safely awaits.
4.  **Resumption:** The frontend displays the paused payload. The user edits it and hits a standard REST `POST /api/pipeline/{run_id}/resume`. The backend restores the context, switches state to `IN_PROGRESS`, and spins up a resumption background task.

## 5. Frontend Architecture (React Flow)
The `@dnd-kit` grid is being deprecated in favor of `React Flow`.
*   **The Canvas:** The main workspace is an infinite canvas, wrapped entirely in a `"use client"` directive. Containers are rendered as nodes wrapped in `React.memo` to prevent cascading re-renders.
*   **Initial Load:** The immense graph payload is fetched via React Server Components (RSCs) and passed as the initial state to Zustand, preventing waterfall loading spinners.
*   **State Management ("Slice" Pattern):** To manage thousands of nodes without lag, `store.ts` is divided into highly specialized slices:
    *   `graphDataSlice`: Semantic Data (Text, relationships, types) — Syncs with backend.
    *   `reactFlowSlice`: Interactive Graph State (Format expected by React Flow, including strict X,Y coords).
    *   `canvasUISlice`: Viewport/Interaction State (Pan X/Y, Zoom, Selection) — Updates 60 FPS without re-rendering the whole DOM.

## 6. Strict Context Isolation (Security)
Creative Room secrets (plot twists, true mechanics) must never leak into the LLM context.
*   **Enforcement:** Pydantic `dump()` with dynamic `exclude` sets. 
*   When a Container is queried by the `ContextCompiler` for an LLM prompt, a strict filter strips any JSON field marked with `{ "is_secret": true }` in the schema definition.

## 7. Migration Strategy (From v1 to v2)
1.  **Phase 1: Foundation.** Implement the generic Container Base Model and SQLite indexing. Migrate existing Characters/Scenes to be instances of "Generic Container" with standard Schemas.
2.  **Phase 2: The Graph.** Swap `@dnd-kit` for `React Flow` on the frontend. Connect edges between Containers.
3.  **Phase 3: The Glass Box.** Refactor `DirectorService` to expose pipeline steps over the API. Build the n8n-style prompt review UI.
4.  **Phase 4: Schema Builder.** Add the UI allowing users to dynamically define their own custom Container types.

## 8. Schema Builder (Dynamic Container Types)
Users must be able to create custom entity types ("Spell", "Spaceship") without writing code.
*   **Three Interaction Modes:** Natural Language Wizard (Schema Wizard Agent → LLM), Visual Property Builder (Notion-style rows), and Raw YAML editor.
*   **Extended `FieldType` enum:** adds `enum` (→ `Literal[...]` with `options`) and `reference` (→ UUID with `target_type` constraint) beyond the original 6 types.
*   **API Surface:** 7 REST endpoints (`/api/v1/schemas/` CRUD + `/generate` NL→AI + `/validate`).
*   **Frontend:** A dedicated `/schemas` page with `SchemaBuilderPanel`, `FieldRow`, `FieldTypeSelector`, `NLWizardInput`, and `SchemaPreview` components, using local React state (not Zustand).
*   **Glass Box Principle:** AI-generated schemas are always drafts — the user must review, edit, and explicitly save.
