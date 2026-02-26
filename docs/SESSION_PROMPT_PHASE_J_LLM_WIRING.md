# Session Prompt: Phase J-2 — LLM Integration + Gap Fixes for Agentic Chat CUJs

## Goal

Replace the ChatOrchestrator's "shell mode" (Phase J-1) placeholder responses with real LLM-powered responses via LiteLLM, fix the remaining infrastructure gaps identified in the CUJ audit, and ensure CUJs 11-17 can proceed past the current blockers.

## Context & Current State

The Agentic Chat system (Phase J) has been fully scaffolded:
- **Backend**: ChatOrchestrator, IntentClassifier, ChatSessionService, ChatSessionRepo, ChatContextManager, ProjectMemoryService, ChatToolRegistry — all implemented and passing 401 tests
- **Frontend**: ChatSidebar, ChatInput (with @-mention + /command autocomplete), ChatMessage, ArtifactPreview, SessionPicker, ApprovalBanner, PlanViewer, useChatStream hook, Zustand chatSlice — all wired
- **Tool Registry**: 9 intent tools (search, create, update, delete, navigate, evaluate, research, pipeline, decide) are wired into the orchestrator via `build_tool_registry()` in `app.py` lifespan

**The core blocker**: When the IntentClassifier returns `CHAT` (the most common intent — general conversation, brainstorming, writing), the orchestrator falls through to `_generate_shell_response()` which returns a hardcoded placeholder: *"I received your message. The chat orchestrator is running in shell mode (Phase J-1)."*

This means the primary CUJ flow — natural language brain-dumping, brainstorming, style feedback, continuity queries, world-building — all produce useless responses.

## Audit Findings (5 gaps to fix)

### Gap 1: CHAT intent returns shell mode placeholder (CRITICAL)
- **File**: `src/showrunner_tool/services/chat_orchestrator.py` lines 422-433
- **Problem**: `_generate_shell_response()` is a hardcoded string. No LLM call.
- **Fix**: Replace with a real LLM call via LiteLLM using the context assembled by `ChatContextManager`

### Gap 2: Markdown not rendered in ChatMessage (MEDIUM)
- **File**: `src/web/src/components/chat/ChatMessage.tsx`
- **Problem**: Message content is rendered with `whitespace-pre-wrap` — no markdown parsing. Bold, italic, headers, code blocks, lists are all displayed as raw text.
- **Fix**: Add `react-markdown` (or equivalent) for assistant message rendering

### Gap 3: Em-dash (—) handling broken (LOW)
- **File**: `src/web/src/components/chat/ChatMessage.tsx` or `src/web/src/hooks/useChatStream.ts`
- **Problem**: Em-dash characters (—) in streamed content cause display issues. The SSE tokenizer splits on whitespace, so em-dashes attached to words may cause token boundary problems.
- **Fix**: Ensure the SSE parser doesn't corrupt multi-byte UTF-8 characters. The token streaming in the orchestrator splits on `response.split()` which handles em-dashes correctly (they're part of the word), so the issue is likely in the frontend concatenation or rendering.

### Gap 4: `GET /api/pipeline/runs` endpoint missing → 404 (LOW)
- **File**: `src/showrunner_tool/server/routers/pipeline.py`
- **Problem**: Frontend calls `api.getPipelineRuns(state)` → `GET /api/pipeline/runs?state=PAUSED_FOR_USER` but this endpoint doesn't exist in the pipeline router. Only definition CRUD and run/stream/resume endpoints exist.
- **Fix**: Add a `GET /pipeline/runs` endpoint that queries `PipelineService._runs` (in-memory dict) with optional state filter.

### Gap 5: Artifact events never emitted by orchestrator (LOW)
- **File**: `src/showrunner_tool/services/chat_orchestrator.py`
- **Problem**: The `ChatArtifact` schema is imported but never used. The `artifact` SSE event type is defined in the schema but the orchestrator never yields `ChatEvent(event_type="artifact", ...)`. The frontend handler `onArtifact` exists but is never triggered.
- **Fix**: When tool execution produces structured content (search results, plan outlines, entity previews), emit an `artifact` event alongside the token stream.

## Detailed Implementation Plan

### Task 1: LLM Integration in ChatOrchestrator (Gap 1 — CRITICAL)

**File to modify**: `src/showrunner_tool/services/chat_orchestrator.py`

Replace `_generate_shell_response()` with a real LLM call:

```python
async def _generate_llm_response(
    self, session_id: str, user_content: str, intent: str
) -> AsyncGenerator[str, None]:
    """Stream an LLM response using ChatContextManager + LiteLLM."""
    import litellm

    # Build context from the 3-layer model
    context = {}
    if self._context_manager:
        context = self._context_manager.build_context(session_id)

    system_prompt = self._build_system_prompt(context.get("system_context", ""), intent)
    messages = context.get("messages", [])
    messages.append({"role": "user", "content": user_content})

    # Stream from LiteLLM
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        stream=True,
        max_tokens=2048,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

**System prompt assembly** — create a `_build_system_prompt()` method that includes:
1. Base persona: "You are the Showrunner story co-pilot for a manga/manhwa creation tool..."
2. Project Memory entries (Layer 1) from `context["system_context"]`
3. Intent-specific instructions: if CHAT, be conversational; if intent fell through to CHAT, explain capabilities

**Fallback**: If `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` is not set, or if `litellm` import fails, fall back to the existing shell response with a message like: "LLM not configured. Set ANTHROPIC_API_KEY or configure a model in showrunner.yaml to enable AI responses."

**Update the main `handle_message` flow** (lines 124-157):
- Replace `response_text = self._generate_shell_response(content, intent)` with an async generator call
- Stream chunks directly as `ChatEvent(event_type="token", ...)` instead of word-splitting a static string
- Accumulate full response for persistence

**Key considerations**:
- Use `ModelConfigRegistry` if available (it's already in `app.state.model_config_registry`) to resolve the model name. Add `model_config_registry` as an optional `__init__` parameter.
- Keep `_generate_shell_response` as the fallback when no LLM is configured
- Add a `try/except` around the LiteLLM call — on failure, yield an error event and fall back to shell mode
- Token counting: after streaming completes, use `litellm.token_counter()` or estimate from chunk count for `update_token_usage()`

### Task 2: Markdown Rendering in ChatMessage (Gap 2)

**File to modify**: `src/web/src/components/chat/ChatMessage.tsx`

1. Install `react-markdown` and `remark-gfm`:
   ```bash
   cd src/web && npm install react-markdown remark-gfm
   ```

2. In `ChatMessage.tsx`, for assistant messages, replace:
   ```tsx
   <p className="whitespace-pre-wrap">{msg.content}</p>
   ```
   with:
   ```tsx
   import ReactMarkdown from 'react-markdown'
   import remarkGfm from 'remark-gfm'

   <ReactMarkdown
     remarkPlugins={[remarkGfm]}
     className="prose prose-invert prose-sm max-w-none"
   >
     {msg.content}
   </ReactMarkdown>
   ```

3. For the streaming content display, also wrap in `ReactMarkdown` (the partial markdown will render progressively).

4. Apply the same to the `ArtifactPreview.tsx` prose rendering for consistency.

**Note**: User messages should remain plain text (not markdown-rendered).

### Task 3: Pipeline Runs Endpoint (Gap 4)

**File to modify**: `src/showrunner_tool/server/routers/pipeline.py`

Add a `GET /pipeline/runs` endpoint:

```python
@router.get("/runs")
async def list_pipeline_runs(
    state: str | None = None,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    """List pipeline runs, optionally filtered by state."""
    runs = list(PipelineService._runs.values())
    if state:
        runs = [r for r in runs if r.state.value == state]
    return [
        {
            "id": r.id,
            "definition_id": r.definition_id,
            "state": r.state.value,
            "current_step": r.current_step,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
        }
        for r in runs
    ]
```

**Important**: This endpoint must be registered BEFORE any `/{run_id}` path endpoints to avoid path conflicts.

### Task 4: Artifact Event Emission (Gap 5)

**File to modify**: `src/showrunner_tool/services/chat_orchestrator.py`

In `_execute_tool()`, after the tool produces a result, check if the result is structured enough to warrant an artifact:

```python
# After tool_fn returns result
if result and intent.lower() in ("search", "create", "evaluate", "pipeline"):
    artifact = ChatArtifact(
        artifact_type=self._intent_to_artifact_type(intent),
        title=f"{intent.title()} Results",
        content=str(result),
    )
    yield ChatEvent(
        event_type="artifact",
        data=artifact.model_dump(),
    )
```

Add a helper to map intents to artifact types:
```python
def _intent_to_artifact_type(self, intent: str) -> str:
    mapping = {
        "search": "table",
        "create": "yaml",
        "evaluate": "outline",
        "pipeline": "outline",
        "research": "prose",
    }
    return mapping.get(intent.lower(), "prose")
```

### Task 5: Em-dash Handling (Gap 3)

**File to investigate**: `src/web/src/hooks/useChatStream.ts`

The em-dash issue is likely in how the SSE parser splits lines. Check:
1. The `data:` line parsing — ensure it doesn't truncate multi-byte characters
2. The JSON.parse of the data payload — ensure the `text` field preserves em-dashes
3. The `streamingContent` concatenation in the Zustand store — ensure no encoding issues

The backend `chat_orchestrator.py` splits response on whitespace (`response.split()`), which correctly keeps em-dashes as part of words. The real fix is:
- In the LLM streaming path (Task 1), stream raw LiteLLM deltas directly (which are character-level, not word-level), so em-dashes flow through naturally
- If em-dashes still break in the non-LLM path, change the word splitter to preserve punctuation: `re.findall(r'\S+\s*', response)` instead of `response.split()`

## Files Changed Summary

| File | Change Type | Priority |
|------|------------|----------|
| `src/showrunner_tool/services/chat_orchestrator.py` | Major rewrite of response generation path | CRITICAL |
| `src/web/src/components/chat/ChatMessage.tsx` | Add react-markdown rendering | MEDIUM |
| `src/showrunner_tool/server/routers/pipeline.py` | Add `GET /runs` endpoint | LOW |
| `src/web/package.json` | Add react-markdown + remark-gfm deps | MEDIUM |
| `src/web/src/components/chat/ArtifactPreview.tsx` | Consistent markdown rendering | LOW |
| `src/web/src/hooks/useChatStream.ts` | Investigate em-dash (may need no changes) | LOW |

## Testing Plan

### Backend Tests
```bash
# Existing tests must still pass
pytest tests/ -v --tb=short

# New tests to add:
# tests/test_chat_llm_integration.py — mock LiteLLM, verify streaming + context assembly
# tests/test_pipeline_runs_endpoint.py — test GET /pipeline/runs with state filter
```

### Frontend Verification
```bash
cd src/web && npx tsc --noEmit  # TypeScript must compile
cd src/web && npm run build     # Production build must succeed
```

### Manual CUJ Verification
1. Start backend: `cd /path/to/project && showrunner server start --reload`
2. Start frontend: `cd src/web && npm run dev`
3. Open http://localhost:3000, toggle chat sidebar
4. Send: "Tell me about the story so far" → Should get a real LLM response (not shell mode)
5. Send: "Create a character called Zara" → Should get tool result with CREATE intent
6. Send: "Find all characters" → Should get SEARCH tool result with actual KG data
7. Verify markdown renders correctly (bold, lists, headers)
8. Verify em-dashes display correctly in responses

## Environment Requirements

- `ANTHROPIC_API_KEY` environment variable set (for LiteLLM → Claude)
- OR `GEMINI_API_KEY` for Gemini models
- OR configure model in `showrunner.yaml` under `model_config`
- `litellm` package must be installed (already in requirements as it's used by pipeline steps)

## Important Constraints

1. **Do NOT break existing tests** — all 401 tests must continue to pass
2. **LLM calls must be optional** — if no API key is configured, fall back gracefully to shell mode with a clear message
3. **Token budgeting** — `ChatContextManager.build_context()` already handles token budgeting. Use its output directly.
4. **The `_generate_shell_response` method must be kept** as fallback — do not delete it
5. **Do NOT modify the IntentClassifier** — its keyword-based classification is working correctly for all 11 intents
6. **Do NOT modify the ChatToolRegistry** — all 9 tool implementations are wired and tested
7. **The system prompt must include Project Memory** — decisions stored via the DECIDE tool must appear in the system prompt for subsequent messages
