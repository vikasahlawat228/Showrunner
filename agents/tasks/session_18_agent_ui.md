# Prompt: Track 3 — The Multi-Agent UI

**Goal**: Expose the new `AgentDispatcher` (built in Phase D) in the frontend so users can see which specialized AI agent is currently working or chatting with them.

**Context**:
Currently, the `/director` endpoints and the `PromptReviewModal.tsx` rely on a generic "AI" persona. With our new `AgentDispatcher`, API calls to `/api/v1/director/dispatch` route the query to a specific skill (Architect, Director, Analyst, etc.). We want the UI to visually reflect the active agent with unique avatars, colors, and names.

**Required Actions (Frontend Only)**:

1. **Agent Metadata Mapping**:
   - Create an `agentConfig.ts` file in `src/web/src/lib/` tracking metadata for each specific skill ID (e.g., `schema_architect`, `continuity_analyst`, `pipeline_director`, `schema_wizard`, `storyboard_artist`). Assign unique colors (using tailwind text/bg names), display names, and lucide-react icons for each.

2. **Update `Canvas.tsx` / `DirectorControls.tsx`**:
   - If a pipeline run invokes a specific agent, display the agent's name and icon in the "Loading..." or status badge.

3. **Update `PromptReviewModal.tsx`**:
   - In the "Chat" mode of the review modal, align the AI's responses with the active agent's avatar instead of the generic Sparkles icon. Ensure the active agent name is visible.
   - You may need to update the `usePipelineStream` hook or the backend SSE payloads to ensure the `current_agent_id` is passed down with the streaming step data. If so, apply small modifications to `pipeline_service.py` to include it.

**Output Specification**:
Provide the updated React component code for:
1. `src/web/src/lib/agentConfig.ts` (new)
2. `src/web/src/components/pipeline/PromptReviewModal.tsx`
3. `src/web/src/components/workbench/DirectorControls.tsx`
4. Associated small updates to API/TypeScript interfaces if required.

*Note: The goal is to maximize the "Glass Box" experience. The user must know exactly who is typing at all times.*
