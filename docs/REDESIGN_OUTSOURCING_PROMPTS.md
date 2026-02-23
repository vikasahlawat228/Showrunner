# Showrunner Redesign: Outsourcing Prompts for Remaining Phases

The following prompts cover the remaining architectural and UX features defined in the `redesign_proposal.md`. Each prompt is self-contained so you can copy and paste it into a new agentic session to outsource the work in parallel.

---

## Prompt 1: Phase 3 — Multi-Agent Orchestration & Glass Box Trace

```markdown
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool.

## Context
We are implementing "Phase 3: Multi-Agent Orchestration & Glass Box Trace" from the UX & Architecture Redesign Proposal. The goal is to evolve the `ChatOrchestrator` into a multi-agent routing system (Planner Agent → Subagents) and surface their execution tree transparently to the user via the Glass Box Action Trace UI.

## Backend Tasks
1. **Modify `src/antigravity_tool/services/chat_orchestrator.py`:**
   - Implement a new routing layer for complex queries (e.g., "Build Chapter 5").
   - Instead of a single LLM call, the Orchestrator should act as a "Planner Agent" that breaks the prompt into steps and delegates them to specialized Subagents (e.g., Story Architect, Writing Agent, Continuity Analyst).
   - Ensure every subagent invocation yields a `ChatEvent` of type `action_trace` with a parent-child relationship so the frontend can render a nested execution tree.

## Frontend Tasks
2. **Modify `src/web/src/components/chat/ChatMessage.tsx`:**
   - Locate the `ActionTraceBlock` component.
   - Upgrade it to support nested, collapsible steps (e.g., `Writing Agent > Checking continuity... > Continuity Analyst > Clear`).
   - Allow the user to click on sub-bullets to open a modal or inline block showing the exact raw JSON or prompt string (satisfying the Glass Box vision).

## Key Files
- `src/antigravity_tool/services/chat_orchestrator.py`
- `src/antigravity_tool/schemas/chat.py` (to update the `ChatActionTrace` schema for nesting)
- `src/web/src/components/chat/ChatMessage.tsx`

## Success Criteria
- The ChatOrchestrator successfully delegates complex requests to subagents.
- Nested `action_trace` events stream to the frontend in real-time.
- The UI renders them as a collapsible, interactive Glass Box execution trace.
```

---

## Prompt 2: Phase 4 — Asynchrony and The Background Queue

```markdown
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool.

## Context
We are implementing "Phase 4: Asynchrony and The Background Queue" from the UX & Architecture Redesign Proposal. Currently, generative tasks can block the UI or the active chat session. We need to detach long-running AI pipelines (like "Scene → Panels") from the chat and run them in a background queue.

## Backend Tasks
1. **Enhance Pipeline/Task Queueing:**
   - Implement or enhance a background task worker (using asyncio.create_task or a lightweight queue like Redis/Celery if already available; otherwise, an in-memory async queue in FastAPI).
   - Create a new endpoint `POST /api/v1/jobs/` that starts a pipeline and immediately returns a `job_id`.
   - Provide `GET /api/v1/jobs/{job_id}/status` to poll for progress, or emit SSE updates globally.

## Frontend Tasks
2. **Implement Non-Blocking Progress Widget:**
   - Create a `GlobalActivityBar` or `BackgroundJobsWidget` in `src/web/src/app/layout.tsx` or `Navbar.tsx`.
   - When a long-running pipeline starts, show a non-blocking progress indicator (e.g., "Generating panels for Ch. 2... 45%").
   - Free up the ChatSidebar so the user can continue talking to the AI while the background processing happens.

## Key Files
- `src/antigravity_tool/server/routers/pipeline.py` or new `jobs.py`
- `src/antigravity_tool/services/pipeline_service.py`
- `src/web/src/components/ui/Navbar.tsx` or new `BackgroundJobsWidget.tsx`

## Success Criteria
- Triggering a long generative pipeline returns a job ID immediately.
- The Chat session remains completely responsive.
- A global progress widget displays the background task's status out of the Chat flow.
```

---

## Prompt 3: Phase 5 — Non-Destructive Branching (Timeline Slider)

```markdown
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool.

## Context
We are implementing "Phase 5: Non-Destructive Branching (Timeline Slider)" from the UX & Architecture Redesign Proposal. We need a visual way for users to manage alternate text paths without losing previous versions.

## Backend Tasks
1. **Support Branch Artifacts:**
   - If not already supported, ensure the `ContainerRepository` or `writing_service.py` supports branching entity IDs and fragment IDs.

## Frontend Tasks
2. **Implement Timeline Ribbon UI:**
   - In `src/web/src/components/zen/ZenEditor.tsx` (or a global position), add a Timeline Ribbon component (Slider or discrete tracks).
   - When the AI generates alternate text for a scene, automatically create a "Branch Copy" in the state.
   - Display a split-pane or interactive toggle allowing the user to view Branch A vs Branch B.
   - Provide actions to "Accept Branch", "Discard", or "Merge".

## Key Files
- `src/web/src/components/zen/ZenEditor.tsx`
- `src/web/src/lib/store/zenSlice.ts`
- `src/antigravity_tool/services/writing_service.py` (if backend changes are needed)

## Success Criteria
- The frontend displays a Timeline Ribbon for branch management.
- Re-generating a text fragment creates an interactive branch instead of destructively overwriting the old text.
- The user can select, compare, and merge branches smoothly in the editor.
```
