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

### 3.3 Event Sourcing & The "Undo" Tree
AI generations are unpredictable. Standard state overwriting is dangerous.
*   Instead of `UPDATE container_x SET content = "new"`, the backend records an **Event**: `{"action": "UPDATE_CONTAINER", "diff": "{...}"}`.
*   This creates an append-only log of User and AI actions.
*   **Benefits:** Enables "Time Travel" (undo/redo to any exact state), makes debugging the "Transparent Workflow" trivial (we know exactly what the AI changed), and supports alternate timeline branching.

## 4. The Transparent "Glass Box" Director

The `DirectorService` no longer executes a monolithic black-box function. It is a pipeline execution engine.
1.  **Pipeline Definition:** Workflows (e.g., "Generate Scene") are defined as a graph of Nodes (Context Node, System Prompt Node, LLM Node).
2.  **Execution Hooks:** The execution pauses at defined user-intervention points.
3.  **API Streaming:** The backend streams the *pipeline state* (not just the LLM tokens) to the frontend via SSE/WebSockets. The UI knows if the Director is currently "Fetching Context", "Assembling Prompt", or "waiting for user approval."

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
