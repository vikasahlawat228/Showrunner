# Session 27: Continuity Auto-Check + Style Enforcer

**Goal**: Wire the existing `continuity_analyst` and `style_enforcer` agent skills into the live application — backend services, API endpoints, and frontend components integrated into Zen Mode and the Pipeline approval flow.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 19 routers, 28 services, and a Next.js frontend with 9 pages. The `AgentDispatcher` already has `continuity_analyst` and `style_enforcer` skills loaded from markdown files. The `ContextEngine` does token-budgeted context assembly with semantic search. The `AnalysisService` already runs LLM-powered emotional arc, voice scorecard, and ribbon analysis.

This session adds two features:
1. **Continuity Auto-Check** — Validates story changes against the KG and future dependencies, surfaced as a sidebar panel in Zen Mode
2. **Style Enforcer** — Evaluates prose against the project's narrative style guide, surfaced in Zen Mode and the PromptReviewModal

**Read these files first** (essential context):
- `agents/skills/continuity_analyst.md` — Full system prompt for continuity analysis (64 lines)
- `agents/skills/style_enforcer.md` — Full system prompt for style evaluation (81 lines)
- `src/showrunner_tool/services/agent_dispatcher.py` — AgentDispatcher with execute() method (700+ lines)
- `src/showrunner_tool/services/analysis_service.py` — Existing analysis service pattern (484 lines)
- `src/showrunner_tool/services/context_engine.py` — ContextEngine for token-budgeted assembly (312 lines)
- `src/showrunner_tool/server/routers/analysis.py` — Existing analysis endpoints (50 lines)
- `src/showrunner_tool/server/deps.py` — DI graph (219 lines)
- `src/showrunner_tool/repositories/event_sourcing_repo.py` — EventService with branching (256 lines)
- `src/web/src/components/zen/ContextSidebar.tsx` — Zen sidebar with context cards (187 lines)
- `src/web/src/components/zen/SlashCommandList.tsx` — Slash commands registry (161 lines)
- `src/web/src/components/zen/ZenEditor.tsx` — TipTap editor (381 lines)
- `src/web/src/components/pipeline/PromptReviewModal.tsx` — Pipeline approval modal
- `src/web/src/lib/api.ts` — API client (822 lines)
- `src/web/src/lib/store/zenSlice.ts` — Zen Mode store

---

## Feature 1: Continuity Auto-Check

### Backend

**1. Create `src/showrunner_tool/services/continuity_service.py`**

```python
class ContinuityVerdict:
    status: str          # "APPROVED", "REJECTED", "REVISION"
    reasoning: str
    suggestions: str
    affected_entities: list[str]
    severity: str        # "high", "medium", "low"

class ContinuityService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        event_service: EventService,
        agent_dispatcher: AgentDispatcher,
    ): ...

    async def check_continuity(
        self,
        container_id: str,
        proposed_changes: dict | None = None,
    ) -> ContinuityVerdict:
        """Validate a container's current state against the KG and future deps."""
        # 1. Get the container and its current state from KG
        # 2. Get related entities (1-hop neighbors from KG)
        # 3. Query future dependencies: events that reference these entities
        #    (use event_service.get_all_events() filtered by entity IDs in payload)
        # 4. Build the input payload matching continuity_analyst.md format:
        #    { "proposed_events": [...], "graph_context": {...}, "future_dependencies": [...] }
        # 5. Call agent_dispatcher.execute() with continuity_analyst skill
        # 6. Parse the JSON verdict from the agent response
        # 7. Return structured ContinuityVerdict

    async def check_scene_continuity(self, scene_id: str) -> list[ContinuityVerdict]:
        """Run continuity checks on all entities in a scene."""
        # Get scene container
        # Get all characters_present and related entities
        # Run check_continuity for each entity
        # Return aggregated verdicts

    async def get_recent_issues(
        self,
        scope: str = "all",  # "all", "scene", "chapter"
        scope_id: str | None = None,
    ) -> list[ContinuityVerdict]:
        """List recently detected continuity issues (cached from last check)."""
        # Store recent verdicts in an in-memory cache (dict keyed by container_id)
        # Return filtered by scope
```

Implementation notes:
- Use `context_engine.assemble_context()` to gather relevant context for each entity
- Parse future dependencies by scanning events for entities referenced in the container's relationships
- The `continuity_analyst` agent expects { proposed_events, graph_context, future_dependencies } — build this from the KG
- Cache verdicts in `self._recent_issues: dict[str, ContinuityVerdict]` (TTL: clear on next check)

**2. Add continuity endpoints to `src/showrunner_tool/server/routers/analysis.py`**

```python
from showrunner_tool.services.continuity_service import ContinuityService, ContinuityVerdict

@router.post("/continuity-check")
async def check_continuity(
    body: ContinuityCheckRequest,  # { container_id: str, proposed_changes?: dict }
    svc: ContinuityService = Depends(get_continuity_service),
) -> ContinuityCheckResponse:
    """Run continuity validation on a container."""
    ...

@router.post("/continuity-check/scene/{scene_id}")
async def check_scene_continuity(
    scene_id: str,
    svc: ContinuityService = Depends(get_continuity_service),
) -> list[ContinuityCheckResponse]:
    """Run continuity checks on all entities in a scene."""
    ...

@router.get("/continuity-issues")
async def get_continuity_issues(
    scope: str = Query("all"),
    scope_id: str | None = Query(None),
    svc: ContinuityService = Depends(get_continuity_service),
) -> list[ContinuityCheckResponse]:
    """List recent continuity issues."""
    ...
```

Request/Response models (add to `api_schemas.py` or inline):
```python
class ContinuityCheckRequest(BaseModel):
    container_id: str
    proposed_changes: dict | None = None

class ContinuityCheckResponse(BaseModel):
    status: str
    reasoning: str
    suggestions: str
    affected_entities: list[str]
    severity: str
```

**3. Add DI provider to `deps.py`**

```python
from showrunner_tool.services.continuity_service import ContinuityService

def get_continuity_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    event_service: EventService = Depends(get_event_service),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> ContinuityService:
    return ContinuityService(kg_service, context_engine, event_service, agent_dispatcher)
```

### Frontend

**4. Create `src/web/src/components/zen/ContinuityPanel.tsx`**

A panel component showing continuity issues for the current scene:

```
┌──────────────────────────────────────┐
│ 🔍 Continuity Check                  │
│ Scene: "The Marketplace"    [Check]  │
├──────────────────────────────────────┤
│ ✅ APPROVED — No issues found        │
│                                      │
│ — or —                               │
│                                      │
│ ⚠️ REVISION NEEDED (2 issues)       │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🔴 HIGH: Character "Kael" is    │ │
│ │ marked as imprisoned in Ch3 but  │ │
│ │ appears free in this scene.      │ │
│ │                                  │ │
│ │ 💡 Suggestion: Add a breakout   │ │
│ │ scene or flashback explaining    │ │
│ │ Kael's release.                  │ │
│ │                                  │ │
│ │ Affected: Kael, Prison, Ch3-S2  │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 🟡 MEDIUM: Timeline gap — 2     │ │
│ │ days pass between scenes but     │ │
│ │ dialogue implies "yesterday".    │ │
│ │                                  │ │
│ │ 💡 Suggestion: Adjust dialogue  │ │
│ │ to "a couple of days ago".       │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

Implementation:
- Props: `sceneId: string`
- State: `issues: ContinuityCheckResponse[]`, `loading: boolean`, `lastChecked: Date | null`
- "Check" button triggers `POST /api/v1/analysis/continuity-check/scene/{sceneId}`
- Issue cards color-coded by severity: red (high), amber (medium), blue (low)
- Each card shows: status icon, reasoning text, suggestion (collapsible), affected entities as badges
- Empty state: green checkmark "No continuity issues detected"
- Loading state: skeleton pulse with "Analyzing continuity..."

**5. Integrate ContinuityPanel into ContextSidebar**

Add a tab system to `ContextSidebar.tsx`:

```tsx
type SidebarTab = "context" | "continuity";

// In the header area, add tab buttons:
<div className="flex gap-1 px-4 py-2 border-b border-gray-800">
  <button
    onClick={() => setActiveTab("context")}
    className={`px-2 py-1 text-xs rounded ${activeTab === "context" ? "bg-indigo-600/30 text-white" : "text-gray-500"}`}
  >
    📎 Context
  </button>
  <button
    onClick={() => setActiveTab("continuity")}
    className={`px-2 py-1 text-xs rounded ${activeTab === "continuity" ? "bg-indigo-600/30 text-white" : "text-gray-500"}`}
  >
    🔍 Continuity
  </button>
</div>

// Conditionally render based on activeTab:
{activeTab === "context" && /* existing context cards */}
{activeTab === "continuity" && <ContinuityPanel sceneId={currentSceneId} />}
```

Pass the current scene ID from `useZenStore` (via URL params or store state).

---

## Feature 2: Style Enforcer

### Backend

**6. Create `src/showrunner_tool/services/style_service.py`**

```python
class StyleIssue:
    category: str       # "pov_violation", "tense_inconsistency", "tone_mismatch", etc.
    severity: str       # "high", "medium", "low"
    location: str       # "paragraph 3, sentence 2"
    description: str
    suggestion: str

class StyleEvaluation:
    status: str         # "APPROVED", "NEEDS_REVISION", "REJECTED"
    overall_score: float  # 0.0-1.0
    issues: list[StyleIssue]
    strengths: list[str]
    summary: str

class StyleService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        agent_dispatcher: AgentDispatcher,
    ): ...

    async def evaluate_style(
        self,
        text: str,
        scene_id: str | None = None,
    ) -> StyleEvaluation:
        """Evaluate prose against the project's narrative style guide."""
        # 1. Load NarrativeStyleGuide from containers (type="style_guide")
        #    If none found, use a default "general literary fiction" guide
        # 2. If scene_id provided, load scene context (tone override, POV character, mood)
        # 3. Build input for style_enforcer agent:
        #    { text, style_guide, scene_context }
        # 4. Call agent_dispatcher.execute() with style_enforcer skill
        # 5. Parse JSON response into StyleEvaluation
        # 6. Return structured result
```

Implementation notes:
- Look for containers with `container_type: "style_guide"` in the KG
- If no style guide exists, construct a default guide: "Third-person past tense, accessible literary vocabulary, medium pacing"
- The `style_enforcer` agent expects { text, style_guide, scene_context } — build this from KG lookups
- Parse the JSON output matching the style_enforcer.md output format

**7. Add style endpoints to `src/showrunner_tool/server/routers/analysis.py`**

```python
from showrunner_tool.services.style_service import StyleService, StyleEvaluation

@router.post("/style-check")
async def check_style(
    body: StyleCheckRequest,  # { text: str, scene_id?: str }
    svc: StyleService = Depends(get_style_service),
) -> StyleCheckResponse:
    """Evaluate prose against the project's style guide."""
    result = await svc.evaluate_style(text=body.text, scene_id=body.scene_id)
    return StyleCheckResponse(
        status=result.status,
        overall_score=result.overall_score,
        issues=[i.__dict__ for i in result.issues],
        strengths=result.strengths,
        summary=result.summary,
    )
```

Request/Response models:
```python
class StyleCheckRequest(BaseModel):
    text: str
    scene_id: str | None = None

class StyleIssueResponse(BaseModel):
    category: str
    severity: str
    location: str
    description: str
    suggestion: str

class StyleCheckResponse(BaseModel):
    status: str
    overall_score: float
    issues: list[StyleIssueResponse]
    strengths: list[str]
    summary: str
```

**8. Add DI provider to `deps.py`**

```python
from showrunner_tool.services.style_service import StyleService

def get_style_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> StyleService:
    return StyleService(kg_service, context_engine, agent_dispatcher)
```

### Frontend

**9. Create `src/web/src/components/zen/StyleScorecard.tsx`**

A scorecard component showing style evaluation results:

```
┌──────────────────────────────────────┐
│ ✍️ Style Check           Score: 0.72 │
│ ████████████░░░░  NEEDS REVISION    │
├──────────────────────────────────────┤
│ Issues (3):                          │
│                                      │
│ 🔴 pov_violation                     │
│ Paragraph 3, sentence 2             │
│ Switches to omniscient POV while    │
│ style guide mandates 3rd-limited.   │
│ 💡 Remove the Kael POV break...     │
│                                      │
│ 🟡 tense_inconsistency              │
│ Paragraph 5                         │
│ Three sentences shift to present... │
│ 💡 Convert to past tense...         │
│                                      │
│ 🔵 vocabulary_level                  │
│ Paragraph 1                         │
│ Uses 'pulchritudinous'...           │
│ 💡 Replace with 'beautiful'...      │
│                                      │
│ Strengths:                           │
│ ✅ Strong sensory imagery            │
│ ✅ Minimal dialogue tags             │
│ ✅ Pacing matches style guide        │
└──────────────────────────────────────┘
```

Implementation:
- Props: `evaluation: StyleCheckResponse | null`, `loading: boolean`, `onCheck: () => void`
- Score displayed as a progress bar with color coding:
  - 0.9+ = green (APPROVED)
  - 0.6-0.9 = amber (NEEDS_REVISION)
  - <0.6 = red (REJECTED)
- Issues sorted by severity (high → medium → low)
- Issue categories color-coded with matching icons
- Strengths displayed as green checkmark list
- Summary shown at top
- "Check Style" button to trigger analysis

**10. Add Style tab to ContextSidebar**

Extend the tab system added in step 5:

```tsx
type SidebarTab = "context" | "continuity" | "style";

// Add third tab button:
<button
  onClick={() => setActiveTab("style")}
  className={`px-2 py-1 text-xs rounded ${activeTab === "style" ? "bg-indigo-600/30 text-white" : "text-gray-500"}`}
>
  ✍️ Style
</button>

// Render:
{activeTab === "style" && (
  <StyleScorecard
    evaluation={styleEvaluation}
    loading={isCheckingStyle}
    onCheck={handleCheckStyle}
  />
)}
```

The `handleCheckStyle` function:
1. Get current editor content from `useZenStore`
2. Call `POST /api/v1/analysis/style-check` with the text
3. Store result in local state

**11. Add `/check-style` slash command to `SlashCommandList.tsx`**

```tsx
{
    id: "check-style",
    label: "Check Style",
    description: "Evaluate prose against the style guide",
    icon: <CheckSquare className="w-4 h-4 text-rose-400" />,
    action: "check-style",
},
```

Add handling in `ZenEditor.tsx` for the "check-style" action:
- When triggered, get the current editor content
- Call the style-check API
- Switch ContextSidebar to the "style" tab
- Show the results in StyleScorecard

**12. Add Style tab to PromptReviewModal**

In `PromptReviewModal.tsx`, add a "Style" tab alongside the existing edit/refine/paste tabs:

```tsx
type ModalTab = 'edit' | 'refine' | 'paste' | 'style';

// When the "style" tab is active, show StyleScorecard with the generated output text
// Add a "Check Style" button that sends the prompt text to the style-check API
```

This gives writers immediate feedback on AI-generated prose before accepting it.

**13. Add API client methods to `api.ts`**

```typescript
// Continuity
checkContinuity: (body: { container_id: string; proposed_changes?: Record<string, unknown> }) =>
  post<ContinuityCheckResponse>("/api/v1/analysis/continuity-check", body),
checkSceneContinuity: (sceneId: string) =>
  post<ContinuityCheckResponse[]>(`/api/v1/analysis/continuity-check/scene/${encodeURIComponent(sceneId)}`, {}),
getContinuityIssues: (scope?: string, scopeId?: string) =>
  request<ContinuityCheckResponse[]>(
    `/api/v1/analysis/continuity-issues?scope=${scope || "all"}${scopeId ? `&scope_id=${encodeURIComponent(scopeId)}` : ""}`
  ),

// Style
checkStyle: (body: { text: string; scene_id?: string }) =>
  post<StyleCheckResponse>("/api/v1/analysis/style-check", body),
```

Add interfaces:
```typescript
export interface ContinuityCheckResponse {
  status: string;
  reasoning: string;
  suggestions: string;
  affected_entities: string[];
  severity: string;
}

export interface StyleIssueResponse {
  category: string;
  severity: string;
  location: string;
  description: string;
  suggestion: string;
}

export interface StyleCheckResponse {
  status: string;
  overall_score: number;
  issues: StyleIssueResponse[];
  strengths: string[];
  summary: string;
}
```

---

## Output Specification

Provide the complete code for:
1. `src/showrunner_tool/services/continuity_service.py` (new file)
2. `src/showrunner_tool/services/style_service.py` (new file)
3. Updates to `src/showrunner_tool/server/routers/analysis.py` (add 4 new endpoints)
4. Updates to `src/showrunner_tool/server/deps.py` (add 2 new providers)
5. Updates to `src/showrunner_tool/server/api_schemas.py` (add request/response models — or inline in analysis.py)
6. `src/web/src/components/zen/ContinuityPanel.tsx` (new file)
7. `src/web/src/components/zen/StyleScorecard.tsx` (new file)
8. Updates to `src/web/src/components/zen/ContextSidebar.tsx` (add tab system + Continuity + Style tabs)
9. Updates to `src/web/src/components/zen/SlashCommandList.tsx` (add /check-style command)
10. Updates to `src/web/src/components/zen/ZenEditor.tsx` (handle check-style action)
11. Updates to `src/web/src/components/pipeline/PromptReviewModal.tsx` (add Style tab)
12. Updates to `src/web/src/lib/api.ts` (add continuity + style methods + interfaces)

---

## Important Notes

- **A parallel session is implementing Translation Agent + NL Pipeline Wizard (Session 28).** Do NOT modify `pipeline.py` router, `pipeline_service.py`, `pipelines/page.tsx`, or create any translation-related files.
- The `continuity_analyst` skill expects JSON with `{ proposed_events, graph_context, future_dependencies }` — match this format exactly.
- The `style_enforcer` skill returns JSON with `{ status, overall_score, issues, strengths, summary }` — parse this directly.
- Use `agent_dispatcher.execute(skill, prompt, context=...)` for both agents.
- Use `toast.success()` / `toast.error()` from `sonner` for notifications.
- Use icons from `lucide-react`: `Shield`, `ShieldCheck`, `ShieldAlert`, `CheckSquare`, `AlertTriangle`, `Info`.
- Follow dark theme styling (bg-gray-900/950, border-gray-800, text-gray-300).
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
