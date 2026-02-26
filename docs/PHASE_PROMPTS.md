# Showrunner: Parallel Implementation Prompts

Each prompt below is **self-contained** — paste it into a fresh session to outsource that phase. Sessions can run in parallel except where noted.

> **Dependency chain:** Phase 0 → (Phases 1, 2, 3 can run in parallel) → Phase 4 → Phase 5

---

## Prompt 1: Phase 0 — Fix Test Environment

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool.

## Problem
The test suite (26 files in tests/) cannot run. The .venv uses Python 3.13 but .pylibs_v2 has pydantic_core compiled for Python 3.11. All tests fail with:
  ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'

## Task
1. Create a clean Python 3.11 virtualenv that can run all tests:
   - Use /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
   - Create venv at .venv_clean
   - Install all project dependencies from pyproject.toml
   - Install test dependencies: pytest, pytest-asyncio
   - The project also needs: chromadb, litellm, sse-starlette, watchdog, pyyaml, python-ulid, Jinja2

2. Run the full test suite:
   PYTHONPATH=src .venv_clean/bin/python -m pytest tests/ --tb=short -q

3. Document any test failures that are pre-existing vs environment-related.

4. Update start_server.sh to use the new venv:
   - Change the python invocation to use .venv_clean/bin/python

5. Create a simple script run_tests.sh at the project root:
   #!/bin/bash
   PYTHONPATH=$(pwd)/src $(pwd)/.venv_clean/bin/python -m pytest tests/ "$@"

## Key Files
- pyproject.toml — project dependencies and pytest config
- start_server.sh — current server start script
- tests/ — 26 test files + fixtures/ directory
- .pylibs_v2/ — current (broken) vendored dependencies

## Success Criteria
- All 26 test files collect successfully
- run_tests.sh works as a one-liner to run tests
- Document exact pass/fail counts
```

---

## Prompt 2: Phase 1 — Quick Wins (Slash Command, Chat Context, Create Tool)

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool, a creative writing tool with a FastAPI backend (src/showrunner_tool/) and Next.js frontend (src/web/).

## Context
Showrunner has 22 Critical User Journeys (CUJs). This phase fixes 3 high-impact gaps affecting CUJs 1, 3, 10, 11, 13, 14.

## Task 1.1: Wire /brainstorm Slash Command in Zen Editor

### Problem
The /brainstorm command is defined in src/web/src/components/zen/SlashCommandList.tsx (SLASH_COMMANDS array, id="brainstorm") but when the user selects it, the execution handler in ZenEditor.tsx's createSlashSuggestion.command() may not have a working case for action="brainstorm".

### What to do
1. Open src/web/src/components/zen/ZenEditor.tsx
2. Find the createSlashSuggestion.command() function (around line 189-260)
3. Ensure there's a case for action === "brainstorm" that:
   - Gets the current editor selection or paragraph text
   - Gets the active scene context from useZenStore (activeSceneId, activeChapterId)
   - Calls the backend: POST /api/v1/director/brainstorm with { text, scene_id, chapter_id }
   - Displays result in the ContextSidebar or as an inline suggestion
4. If the backend endpoint doesn't exist, check src/showrunner_tool/server/routers/director.py for a brainstorm endpoint. If missing, add one that delegates to the AgentDispatcher or DirectorService.

### Key files
- src/web/src/components/zen/ZenEditor.tsx — slash command execution
- src/web/src/components/zen/SlashCommandList.tsx — command definitions
- src/web/src/lib/store/zenSlice.ts — Zen state store
- src/showrunner_tool/server/routers/director.py — director router
- src/showrunner_tool/services/director_service.py — director service

---

## Task 1.2: Chat Context Auto-Injection from Zen

### Problem
The ChatSidebar (src/web/src/components/chat/ChatSidebar.tsx) is globally available via layout.tsx, but when a user opens chat while writing in Zen Mode, the chat has no idea what scene/content they're working on. The AI responds generically instead of referencing the current writing context.

### What to do
1. In ChatSidebar.tsx:
   - Import useZenStore from "../../lib/store/zenSlice"
   - Before sending a message (in the send handler), read:
     - zenStore.activeSceneId
     - zenStore.activeChapterId
     - zenStore.contextEntries (existing KG context)
     - zenStore.currentContent (first 2000 chars of editor content)
   - Pass these as context_payload in the API call:
     api.sendChatMessage(sessionId, { content, context_payload: { zen_context: { scene_id, chapter_id, current_text, entities } } })

2. In the backend src/showrunner_tool/services/chat_orchestrator.py:
   - In handle_message() (around line 68-170), extract context_payload
   - If context_payload has "zen_context", include it in the system prompt sent to LLM
   - Specifically, in _generate_llm_response() or _build_system_prompt(), append:
     "The writer is currently working on scene {scene_id}. Current text:\n{current_text[:2000]}"

3. Add a test in tests/test_chat_orchestrator.py:
   - Send a message with context_payload={"zen_context": {"scene_id": "sc1", "current_text": "Zara drew her blade..."}}
   - Verify the LLM system prompt includes the Zen context

### Key files
- src/web/src/components/chat/ChatSidebar.tsx — chat UI
- src/web/src/lib/store/zenSlice.ts — has activeSceneId, contextEntries, etc.
- src/showrunner_tool/services/chat_orchestrator.py — handle_message(), _build_system_prompt()
- src/showrunner_tool/services/chat_context_manager.py — context assembly
- tests/test_chat_orchestrator.py — existing tests

---

## Task 1.3: Harden create_tool Reliability

### Problem
The create_tool() in src/showrunner_tool/services/chat_tool_registry.py (lines 70-190) uses LLM to parse natural language into structured entity creation. It sometimes fails with "automatic scaffolding failed" because the LLM returns malformed JSON.

### What to do
1. Open src/showrunner_tool/services/chat_tool_registry.py, find create_tool() (line 70-190)
2. Add 3-layer JSON parsing fallback:
   ```python
   # Layer 1: Direct JSON parse
   try:
       parsed = json.loads(llm_response)
   except json.JSONDecodeError:
       # Layer 2: Extract JSON from markdown code block
       match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
       if match:
           parsed = json.loads(match.group(1))
       else:
           # Layer 3: Find any JSON object in the response
           match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', llm_response, re.DOTALL)
           if match:
               parsed = json.loads(match.group(0))
           else:
               # Final fallback: extract fields with regex
               name = re.search(r'"name"\s*:\s*"([^"]+)"', llm_response)
               ctype = re.search(r'"(?:type|container_type)"\s*:\s*"([^"]+)"', llm_response)
               parsed = {"name": name.group(1) if name else "Untitled", "container_type": ctype.group(1) if ctype else "character"}
   ```
3. Wrap the entire entity creation block in try/except — on failure, return a user-friendly error message instead of a traceback:
   ```python
   except Exception as e:
       logger.error(f"create_tool failed: {e}", exc_info=True)
       return f"I understood you want to create something, but I had trouble processing the details. Could you try again with a simpler description? Error: {str(e)[:200]}"
   ```
4. Add structured logging at each fallback level: logger.info("create_tool: using fallback layer N")

5. Add tests in tests/test_chat_tool_registry.py:
   - Test with clean JSON response
   - Test with JSON wrapped in ```json code block
   - Test with JSON embedded in prose text
   - Test with completely malformed response (should return friendly error)

### Key files
- src/showrunner_tool/services/chat_tool_registry.py — create_tool() function
- tests/test_chat_tool_registry.py — existing tests to extend

## Success Criteria
- /brainstorm in Zen triggers AI brainstorming with scene context
- Chat sidebar auto-injects Zen context into messages
- create_tool handles malformed LLM JSON gracefully with 3-layer fallback
- All new behavior has corresponding tests
```

---

## Prompt 3: Phase 2 — Session Intelligence (Welcome-Back, Dashboard)

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool, a creative writing tool with a FastAPI backend (src/showrunner_tool/) and Next.js frontend (src/web/).

## Context
When writers return after a break, the app doesn't recognize the time gap — no "welcome back" message, no session summary, no "Previously..." context. This affects CUJs 9 ("Returning After a Week Away") and 17 ("What Happened While I Was Gone?").

## Task 2.1: Welcome-Back Detection & Auto-Brief

### Backend Changes

1. In src/showrunner_tool/services/chat_orchestrator.py:
   - Add method `_check_session_gap(self, session_id: str)`:
     ```python
     async def _check_session_gap(self, session_id):
         session = self.session_service.get_session(session_id)
         if not session:
             return None
         last_activity = session.updated_at  # datetime
         gap = datetime.utcnow() - last_activity
         if gap.total_seconds() > 24 * 3600:  # 24 hours
             return gap
         return None
     ```
   - In handle_message(), at the very beginning (before intent classification), call _check_session_gap(). If gap detected AND this is the first message of the resumed session (message_count == 0 or session was just resumed):
     - Compile a brief using world_summary_tool (if available in tool_registry) or project_memory_service
     - Yield ChatEvent tokens with a welcome-back message:
       "Welcome back! It's been {days} days. Here's what's in your world: ..."
     - Then proceed with normal message handling

2. Add test in tests/test_chat_orchestrator.py:
   - Create a session, manually set updated_at to 48 hours ago
   - Send a message
   - Verify the response stream includes welcome-back content

### Frontend Changes

3. Create src/web/src/components/chat/WelcomeBackBanner.tsx:
   ```tsx
   // A dismissable banner shown at the top of chat when resuming after a break
   // Props: { daysSince: number, summary: string, onDismiss: () => void, onCatchUp: () => void }
   // "Catch me up" button sends "/plan catch-up" to chat
   // Styling: gradient bg (indigo-600/20 to purple-600/20), border-indigo-500/30
   ```

4. In src/web/src/components/chat/ChatSidebar.tsx:
   - When loading a session (setActiveSession), check if the session's updated_at is > 24h ago
   - If so, show WelcomeBackBanner at the top of the message list
   - Dismiss after first message or explicit close

## Task 2.2: Dashboard "Last Session" Card

5. In src/web/src/components/command-center/ProgressOverview.tsx:
   - Add a "Last Chat Session" card section:
     - Fetch latest session via existing api.getChatSessions() (take first result)
     - Show: session name, time ago, message count, 1-line preview
     - "Resume" button that opens ChatSidebar and sets that session active

6. In src/web/src/components/zen/ContextSidebar.tsx:
   - Add a "Previously..." collapsible section at the top when the user hasn't edited in > 4 hours
   - Show: last 3 modified scenes/chapters with timestamps
   - Data source: existing api.getContainers() filtered by modified time, or a new lightweight endpoint

### Key files
- src/showrunner_tool/services/chat_orchestrator.py — handle_message(), new _check_session_gap()
- src/showrunner_tool/services/chat_session_service.py — session data access
- src/web/src/components/chat/ChatSidebar.tsx — session loading
- src/web/src/components/chat/WelcomeBackBanner.tsx — NEW
- src/web/src/components/command-center/ProgressOverview.tsx — dashboard card
- src/web/src/components/zen/ContextSidebar.tsx — "Previously..." section
- tests/test_chat_orchestrator.py — new test

## Design Guidelines
- Use dark theme: bg-gray-900, text-gray-200, accents in indigo/purple
- Smooth animations: animate-in, slide-in-from-top, fade-in
- Keep components under 150 lines

## Success Criteria
- Resuming a session after 24h+ shows welcome-back message from AI
- Dashboard shows "Last Session" card with resume button
- ContextSidebar shows "Previously..." with recent edits after 4h gap
- WelcomeBackBanner is dismissable and triggers catch-up on click
```

---

## Prompt 4: Phase 3 — Intelligence Upgrades (Continuity, Voice, Branches)

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool, a creative writing tool with a FastAPI backend (src/showrunner_tool/) and Next.js frontend (src/web/).

## Context
Three intelligence features need upgrades: continuity checking should suggest fixes (not just flag issues), style enforcement should target individual characters' dialogue, and writing should be branch-aware.

## Task 3.1: Continuity Analyst — Auto-Suggest Resolutions

### Problem
src/showrunner_tool/services/continuity_service.py flags contradictions but returns no resolution suggestions.

### Changes

1. In continuity_service.py, add:
   ```python
   async def suggest_resolutions(self, issue: dict, kg_context: dict) -> list:
       """Given a continuity issue, generate 3 resolution options via LLM."""
       prompt = f"""You found this continuity issue in a story:
       Issue: {issue['description']}
       Scenes involved: {issue['scenes']}
       
       Story context: {json.dumps(kg_context)[:3000]}
       
       Generate exactly 3 resolution options as JSON array:
       [
         {{"description": "...", "affected_scenes": ["scene_id1"], "edits": "what to change", "risk": "low|medium|high", "trade_off": "what the writer gives up"}}
       ]"""
       # Use LiteLLM to generate, parse JSON response
   ```

2. In src/showrunner_tool/server/routers/analysis.py:
   - Add endpoint: POST /api/v1/analysis/continuity/suggest-resolutions
   - Request body: { issue_id: str } or { issue: object }
   - Returns: List of resolution options

3. In src/web/src/components/zen/ContinuityPanel.tsx:
   - Add "Suggest Fixes" button per issue
   - On click, call the new endpoint
   - Display resolution options as cards with "Apply" button each
   - Apply button calls the appropriate update endpoint

## Task 3.2: Batch Style Enforcer — Per-Character Dialogue

### Problem
The style enforcer in pipeline_service.py operates on full text. CUJ 20 needs "restyle only Kael's dialogue."

### Changes

1. In src/showrunner_tool/services/style_service.py, add:
   ```python
   async def extract_dialogue_by_speaker(self, text: str, speaker_name: str) -> list:
       """Use LLM to identify lines of dialogue attributed to a specific character.
       Returns list of {"line_number": int, "original_text": str, "speaker": str}"""
   
   async def enforce_style_on_dialogue(self, text: str, speaker_name: str, voice_profile: dict) -> str:
       """Restyle only the specified character's dialogue while preserving surrounding prose.
       voice_profile contains: tone, vocabulary_level, speech_patterns, forbidden_words"""
   ```

2. In src/showrunner_tool/services/pipeline_service.py:
   - In _execute_step(), add a new step type handler: "style_enforce_dialogue"
   - Step config expects: { speaker_name, voice_profile_bucket_id }
   - Handler: loads voice profile from bucket → calls style_service.enforce_style_on_dialogue()

3. In frontend pipeline builder, ensure the new step type appears in the step type dropdown (src/web/src/components/pipeline-builder/).

## Task 3.3: Branch-Aware Writing

### Problem
Zen editor saves fragments without branch context. Writing on a branch isn't isolated.

### Changes

1. In src/web/src/lib/store/zenSlice.ts:
   - Add field: activeBranch: string | null (default null = main)
   - Add action: setActiveBranch(branchId: string | null)

2. In ZenEditor.tsx save/autosave logic:
   - Read activeBranch from zenStore
   - Include branch_id in the save API call payload

3. In src/showrunner_tool/services/writing_service.py:
   - Accept optional branch_id in save_fragment() and save_scene()
   - Store branch_id as metadata on the saved container

4. In src/showrunner_tool/services/continuity_service.py:
   - Accept optional branch_id parameter in check methods
   - Filter KG queries to only include entities/fragments tagged with that branch

5. In the Timeline page (src/web/src/app/timeline/page.tsx):
   - When user selects a branch in BranchList, update zenStore.activeBranch
   - Show active branch indicator in Zen header

### Key files
- src/showrunner_tool/services/continuity_service.py
- src/showrunner_tool/services/style_service.py
- src/showrunner_tool/services/pipeline_service.py
- src/showrunner_tool/services/writing_service.py
- src/showrunner_tool/server/routers/analysis.py
- src/web/src/components/zen/ContinuityPanel.tsx
- src/web/src/lib/store/zenSlice.ts
- src/web/src/components/zen/ZenEditor.tsx
- src/web/src/app/timeline/page.tsx

## Success Criteria
- Continuity issues have "Suggest Fixes" → 3 resolution options with trade-offs
- Style enforcer can target a single character's dialogue across a chapter
- Writing in Zen on a branch tags fragments with branch_id
- Continuity checks can be scoped to a single branch
```

---

## Prompt 5: Phase 4 — Advanced Chat & Pipeline Features

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool, a creative writing tool with a FastAPI backend (src/showrunner_tool/) and Next.js frontend (src/web/).

## Context
The agentic chat system (Phase J) has plan/execute mode and pipeline control from chat. This phase adds mid-plan modification, runtime model switching, and research auto-injection.

## Task 4.1: Mid-Plan Modification (/replan command)

### Problem
ChatOrchestrator has /plan, /approve, /execute commands but no way to modify a plan mid-execution.

### Changes

1. In src/showrunner_tool/services/chat_orchestrator.py:
   - Add /replan to the command detection in _handle_command() (around line 174-202)
   - Add _handle_replan(self, session_id, new_instructions, start):
     ```python
     async def _handle_replan(self, session_id, new_instructions, start):
         """Modify the current plan based on new instructions.
         - Preserves completed steps (status=done)
         - Re-generates remaining steps with LLM using new_instructions + completed context
         - Updates session._plan_steps in place
         """
         session = self.session_service.get_session(session_id)
         current_plan = getattr(session, '_plan_steps', [])
         completed = [s for s in current_plan if s.get('status') == 'done']
         # Build prompt with completed context + new instructions
         # Call LLM to generate updated remaining steps
         # Merge completed + new steps
     ```

2. In src/web/src/components/chat/PlanViewer.tsx:
   - Add "Modify Plan" button below the step list
   - Shows inline textarea for new instructions
   - "Re-plan" submit button sends `/replan {instructions}` as a chat message

## Task 4.2: Pipeline Model Switching from Chat

### Problem
Users can launch pipelines from chat but can't change the model mid-execution when paused at an approval gate.

### Changes

1. In src/showrunner_tool/services/pipeline_service.py:
   - Add method:
     ```python
     def set_step_model_override(self, run_id: str, step_id: str, model_name: str):
         run = self._runs.get(run_id)
         if not run: raise ValueError(f"Run {run_id} not found")
         # Store override that will be picked up when the step resumes
         run.step_overrides = getattr(run, 'step_overrides', {})
         run.step_overrides[step_id] = {"model": model_name}
     ```
   - In _execute_step(), before calling LiteLLM, check run.step_overrides for the current step

2. In src/showrunner_tool/services/chat_tool_registry.py:
   - Extend pipeline_tool() to detect model-switching intent:
     - Pattern: "use {model} for this step" or "switch to {model}"
     - Extract model name, find the currently paused run and step, call set_step_model_override()

3. In src/showrunner_tool/server/routers/pipeline.py:
   - Add endpoint: PATCH /api/v1/pipeline/runs/{run_id}/steps/{step_id}/model
   - Body: { model: str }

## Task 4.3: Research Auto-Injection & Plausibility Check

### Problem
Research buckets exist but aren't automatically surfaced when writing about researched topics. No plausibility checking.

### Changes

1. In src/showrunner_tool/services/context_engine.py:
   - In assemble_context() or get_context_for_entities():
     - After assembling entity context, also query containers where container_type="research"
     - If any research bucket's topic keywords overlap with entity names or scene text, include its summary
     - Add to returned context under a "Research Notes" section

2. In src/showrunner_tool/services/chat_tool_registry.py:
   - Add plausibility_check_tool():
     ```python
     def plausibility_check_tool(content, entity_ids, **kwargs):
         """Cross-reference scene excerpt against research buckets.
         - Extract claims/facts from the text
         - Compare against stored research
         - Flag implausible claims with explanations
         """
     ```
   - Register as "plausibility_check" in the tool registry

3. In the chat intent classifier (src/showrunner_tool/services/intent_classifier.py):
   - Add "PLAUSIBILITY_CHECK" intent for queries like "is this realistic?", "does this make sense?", "fact check this"

### Key files
- src/showrunner_tool/services/chat_orchestrator.py — /replan handler
- src/showrunner_tool/services/pipeline_service.py — model override
- src/showrunner_tool/services/chat_tool_registry.py — pipeline_tool extension + plausibility tool
- src/showrunner_tool/services/context_engine.py — research injection
- src/showrunner_tool/services/intent_classifier.py — new intent
- src/web/src/components/chat/PlanViewer.tsx — modify plan UI
- src/showrunner_tool/server/routers/pipeline.py — model override endpoint

## Success Criteria
- /replan modifies existing plan, preserving completed steps
- "use claude for this step" in chat switches the model on a paused pipeline step
- Research auto-injects into context when writing about researched topics
- "Is this fight scene realistic?" in chat triggers plausibility check against research buckets
```

---

## Prompt 6: Phase 5 — Multi-Season State Versioning

```
You are working on the Showrunner project at /Users/vikasahlawat/Documents/writing_tool, a creative writing tool with a FastAPI backend (src/showrunner_tool/) and Next.js frontend (src/web/).

## Context
Writers working on multi-season stories need entity versioning — "Zara in Season 1" vs "Zara in Season 2" should be distinct states. Currently, a character bucket is a single document with no temporal versioning.

> WARNING: This is architecturally complex. Read the existing entity model carefully before making changes.

## Task 5.1: Entity State Versioning (era_id)

### Background
Entities are stored as GenericContainer objects (see src/showrunner_tool/schemas/ for the schema). They're managed by ContainerRepository (src/showrunner_tool/repositories/) and linked via KnowledgeGraphService.

### Changes

1. Schema changes — find the GenericContainer model in src/showrunner_tool/schemas/:
   - Add field: era_id: Optional[str] = None  # "season_1", "season_2", etc.
   - Add field: parent_version_id: Optional[str] = None  # links to the previous era's version
   - A None era_id means "global / all eras"

2. In src/showrunner_tool/services/knowledge_graph_service.py:
   - Add method: get_entity_at_era(entity_id: str, era_id: str) -> Optional[GenericContainer]
     - First look for a version with matching era_id
     - If not found, fall back to the era_id=None (global) version
   - Add method: create_era_fork(entity_id: str, new_era_id: str) -> GenericContainer
     - Clone the current entity bucket
     - Set era_id = new_era_id, parent_version_id = original entity's id
     - Save as a new container

3. In src/showrunner_tool/services/context_engine.py:
   - Add active_era_id parameter to context assembly
   - When resolving entity references, use get_entity_at_era() instead of direct get()
   - This ensures that when writing Season 2, "Zara" resolves to the Season 2 version

4. In the chat tool registry (src/showrunner_tool/services/chat_tool_registry.py):
   - The create_tool should accept era_id context
   - When user says "Create Season 2 version of Zara as the leader", it should:
     - Detect existing Zara entity
     - Call create_era_fork() with new era
     - Update the forked version with new attributes

5. API endpoint in src/showrunner_tool/server/routers/containers.py:
   - POST /api/v1/containers/{container_id}/fork-era
   - Body: { era_id: str, updates: dict }

## Task 5.2: Unresolved Thread Mining

### Changes

1. In the KG relationship model (find in src/showrunner_tool/schemas/ or knowledge_graph_service.py):
   - Add field to relationship edges: resolved: bool = False
   - Add field: resolved_in_era: Optional[str] = None

2. In src/showrunner_tool/services/knowledge_graph_service.py:
   - Add method: get_unresolved_threads(era_id: Optional[str] = None) -> List[dict]
     - Query all relationship edges where resolved=False
     - If era_id provided, filter to edges created in or before that era
     - Return: [{"source": entity_name, "target": entity_name, "relationship": type, "created_in": era, "description": "..."}]
   - Add method: resolve_thread(edge_id: str, resolved_in_era: str)

3. In src/showrunner_tool/services/chat_tool_registry.py:
   - Add unresolved_threads_tool():
     - Queries get_unresolved_threads()
     - Formats as readable list for chat display
   - Register in build_tool_registry()

4. In src/showrunner_tool/services/intent_classifier.py:
   - Add "UNRESOLVED_THREADS" intent for: "show unresolved threads", "what plots are open", "unfinished storylines"

5. Frontend — in Timeline page or Dashboard:
   - Add "Open Plot Threads" section or tab
   - Shows list of unresolved relationships with "Mark Resolved" button

### Key files to READ FIRST before coding
- src/showrunner_tool/schemas/ — ALL schema files, especially container and relationship schemas
- src/showrunner_tool/repositories/ — ContainerRepository, how entities are stored
- src/showrunner_tool/services/knowledge_graph_service.py — KG operations
- src/showrunner_tool/services/context_engine.py — context assembly
- src/showrunner_tool/services/chat_tool_registry.py — tool registration pattern

## Testing
- Create character "Zara" with era_id=None (global)
- Fork to era "season_2" → verify new container created with parent_version_id
- Query get_entity_at_era("zara", "season_2") → returns forked version
- Query get_entity_at_era("zara", "season_1") → falls back to global
- Create relationship edges, mark some resolved → query unresolved → verify correct results
- Chat: "Show me open plot threads from Season 1" → verify formatted list

## Success Criteria
- GenericContainer has era_id and parent_version_id fields
- create_era_fork() clones entity to new era
- Context engine resolves entities by era
- Unresolved thread query works with era filtering
- Chat tool surfaces open threads on request
```

---

## Quick Reference: Which Prompt to Run When

| Session | Prompt | Can Start | Depends On |
|---------|--------|-----------|------------|
| A | Phase 0 (Test Env) | Immediately | Nothing |
| B | Phase 1 (Quick Wins) | Immediately | Nothing (tests optional) |
| C | Phase 2 (Sessions) | Immediately | Nothing (tests optional) |
| D | Phase 3 (Intelligence) | Immediately | Nothing (tests optional) |
| E | Phase 4 (Advanced) | After B, D merge | Phase 1 chat changes, Phase 3 style service |
| F | Phase 5 (Multi-Season) | After B merge | Phase 1 create_tool changes |

> Phases 0–3 can all run in parallel. Phase 4 should start after 1 & 3 are merged. Phase 5 can start after Phase 1 is merged.
