# Coding Task: SSE Stream Hook & Glass Box UI (Phase 4 UI)

**Context:** We are building "Showrunner", an AI co-writer with a transparent "Glass Box" pipeline. Our FastAPI backend executes AI generation via a state-machine and streams the transitions using Server-Sent Events (SSE). We need the Next.js frontend code to ingest this stream and provide the UI for intercepting and editing the AI's prompts.

**Your Objective: Write the React Frontend Code**
You need to implement the SSE streaming logic and the React UI modal in `src/web/src/components/pipeline/`.

**Requirements:**
1. **`usePipelineStream.ts` (Custom React Hook):**
   - Must use the native `EventSource` API (or a robust fetch-based SSE parser) to connect to `GET /api/pipeline/{run_id}/stream`.
   - Should parse incoming JSON events containing `state` (e.g., `CONTEXT_GATHERING`, `PAUSED_FOR_USER`, `COMPLETED`) and `payload`.
   - Must return the current pipeline state, the latest payload, and an `error` state.
   - Example SSE message format expected from backend: `data: {"state": "PAUSED_FOR_USER", "payload": {"prompt_text": "Hero walks into..."}, "step_name": "Assemble Prompt"}\n\n`
2. **`PromptReviewModal.tsx` (React Component):**
   - A Tailwind CSS UI component that overlays the screen when the pipeline state is `PAUSED_FOR_USER`.
   - It should display a `textarea` containing the generated prompt `payload.prompt_text` so the user can freely edit it.
   - It needs a "Resume Pipeline" button that triggers a callback `onResume(editedText: string)`.
   - Provide sleek, modern styling indicating the AI is "waiting for alignment".

**Output:** Provide the exact, production-ready TypeScript code for these two files. Ensure it is compatible with Next.js (App Router) and Tailwind CSS v4.
