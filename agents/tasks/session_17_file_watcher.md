# Prompt: Track 2 — Real-time File System Watcher

**Goal**: Keep the Knowledge Graph in sync with external file system changes (e.g., when a user edits a YAML file in VSCode), and notify the frontend to refresh.

**Context**:
Showrunner's source-of-truth is the local YAML files. Currently, `KnowledgeGraphService.sync_all()` only runs when the FastAPI server boots. If a user modifies a file directly, the frontend and SQLite index become stale. We need a live file watcher.

**Required Actions (Backend Only)**:

1. **Implement `services/file_watcher_service.py`**:
   - Use the Python `watchdog` library (already commonly used, add to dependencies if needed).
   - Watch the `schemas/` and `containers/` (or root project path) for `.yaml` file changes (`on_modified`, `on_created`, `on_deleted`).
   - When a change is detected:
     1. Pass the file path to `ContainerRepository` to reload/delete.
     2. Update `SQLiteIndexer` accordingly.

2. **Server-Sent Events (SSE) Broadcaster**:
   - Create a global SSE broadcaster in `routers/project.py` (e.g., `GET /api/v1/project/events`).
   - When the watcher detects a change, emit a JSON event: `{"type": "GRAPH_UPDATED", "path": "..."}`.

3. **Lifecycle Integration**:
   - Start the `watchdog` observer in the FastAPI `/server/app.py` lifespan context manager. Ensure it shuts down cleanly.

**Output Specification**:
Provide the Python code for:
1. `src/showrunner_tool/services/file_watcher_service.py`
2. `src/showrunner_tool/server/routers/project.py` (with the new SSE broadcast endpoint)
3. Modified `src/showrunner_tool/server/app.py` linking the lifespan events.

*Note: Ensure the file watcher uses a small debounce (e.g., 0.5s) to avoid spamming updates when a file is saved multiple times in rapid succession.*
