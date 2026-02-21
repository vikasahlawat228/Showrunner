# Phase D: Architectural Consolidation & Agentic Workflows
**Status:** ✅ Completed
**Objective:** Address the technical debt from Phases A/B/C and align the backend with 2025 best practices for agentic AI architectures.

---

## The Master Plan

We are executing **Phase D** through a parallelized, multi-agent strategy. The heavy lifting is divided into three distinct, non-overlapping streams that can be outsourced to parallel chat sessions.

### Why Phase D Before New Features?
The UI and creative surfaces (Zen Mode, Pipelines, Storyboard) are structurally complete, but their backends suffer from "in-memory amnesia" and isolated logic. To build true autonomous agents, we need:
1. **Memory:** Every change persisted to the Knowledge Graph and Event Log.
2. **Context:** A centralized engine to manage LLM token budgets and RAG.
3. **Orchestration:** Dynamic routing of tasks to specialized agents.

---

## Parallel Execution Tracks

These tracks are designed to rely on different areas of the codebase to prevent merge conflicts.

### Track 1: Universal Persistence & Event Sourcing (Session 13)
**Goal:** Terminate all in-memory dictionaries. Connect phases A, B, and C to `ContainerRepository` (for YAML/Knowledge Graph persistence) and `EventService` (for the undo tree).
- **Target Files:** `pipeline_service.py`, `writing_service.py`, `storyboard_service.py`.
- **Outcome:** Every fragment, pipeline definition, and storyboard panel is a true `GenericContainer` saved to disk, and every mutation emits an event to SQLite.
- **Reference Prompt:** `agents/tasks/session_13_persistence_events.md`

### Track 2: The Context Engine (Session 14)
**Goal:** Build a centralized context manager that handles RAG, hierarchical summarization, and token budgeting for all LLM calls.
- **Target Files:** `context_service.py` (NEW), integrations into `director_service.py` and `pipeline_service.py`.
- **Outcome:** LLMs receive clean, highly relevant context, eliminating "lost in the middle" hallucinations and reducing API costs.
- **Reference Prompt:** `agents/tasks/session_14_context_engine.md`

### Track 3: Agent Orchestration (Session 15)
**Goal:** Move away from static markdown files into a dynamic, multi-agent dispatcher using a ReAct (Reason + Act) loop pattern.
- **Target Files:** `agent_dispatcher.py` (NEW), transforming `agents/skills/*.md` into executable classes.
- **Outcome:** The system can autonomously decide *which* specific agent (Schema Wizard, Pipeline Director, etc.) should handle a request based on intent.
- **Reference Prompt:** `agents/tasks/session_15_agent_orchestration.md`

---

## Instructions for Orchestration

To accelerate development, open **three separate AI chat interfaces**. 
1. Copy the contents of `session_13_persistence_events.md` into Chat A.
2. Copy the contents of `session_14_context_engine.md` into Chat B.
3. Copy the contents of `session_15_agent_orchestration.md` into Chat C.
