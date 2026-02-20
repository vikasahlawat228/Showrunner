# Coding Task: The Glass Box Pipeline (Phase 4 Execution)

**Context:** We are building "Showrunner", a node-based AI co-writer. The architecture dictates an Event-Driven backend where complex AI workflows (like generating a scene) are broken down into a state-machine pipeline (Context -> Prompt -> User_Intercept -> Execute). We use FastAPI and need to stream these state changes to the frontend using Server-Sent Events (SSE).

**Your Objective: Write the Python Backend Code**
You need to implement the core streaming engine in `src/antigravity_tool/services/pipeline_service.py` and the FastAPI router in `src/antigravity_tool/server/routers/pipeline.py`.

**Requirements:**
1. **Pydantic Models:** 
   - `PipelineState` enum (`CONTEXT_GATHERING`, `PROMPT_ASSEMBLY`, `PAUSED_FOR_USER`, `EXECUTING`, `COMPLETED`, `FAILED`).
   - `PipelineRun` (id, current_state, payload, created_at).
2. **The PipelineService:**
   - Use `asyncio` to run the pipeline steps in the background.
   - We need an in-memory dictionary or basic SQLite table to store active `PipelineRun`s.
   - Implement an async generator function `stream_pipeline(run_id: str)` that yields JSON SSE events whenever the pipeline state changes.
   - Implement a pausing mechanism: When the state transitions to `PAUSED_FOR_USER` (waiting for prompt review), the background task should `await` on an `asyncio.Event` or simply terminate and save its state, waiting for the user to hit a `resume` endpoint.
3. **The Router:**
   - `POST /api/pipeline/run`: Initializes the run, starts the background task, and returns `{"run_id": "123"}`.
   - `GET /api/pipeline/{run_id}/stream`: Returns an `EventSourceResponse` (using `sse_starlette`) mapped to the `stream_pipeline` generator.
   - `POST /api/pipeline/{run_id}/resume`: Accepts edited user payloads, updates the run state to `EXECUTING`, and triggers the resumption of the pipeline.

**Output:** Provide the exact, production-ready Python code for these two files (and any necessary schema files). Ensure it integrates smoothly with a standard FastAPI app.
