# Prompt: Phase Next-B Session A — Emotional Arc Dashboard + Story Ribbons

**Goal**: Build an Emotional Arc Dashboard and Story Ribbons visualization on the Timeline page, giving writers analytical superpowers to understand pacing and character presence across their story.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 15 FastAPI routers, 24 services, and a Next.js frontend with 6 pages. The Timeline page (`/timeline`) currently shows a real-time SSE event stream with branching.

This session adds two new analytical visualizations to the Timeline page:
1. **Emotional Arc Dashboard** — LLM-scored emotional valence per scene, visualized as a multi-line chart
2. **Story Ribbons** — Character presence + prominence per scene as colored SVG ribbons

**Read these files first** (essential context):
- `docs/LOW_LEVEL_DESIGN.md` §10 — Full detailed design for Phase Next-B (service, endpoints, components, DI)
- `docs/PRD.md` §13 — Phase Next-B description
- `src/antigravity_tool/server/deps.py` — Current dependency injection graph
- `src/antigravity_tool/server/app.py` — Router registration
- `src/antigravity_tool/server/api_schemas.py` — Existing API schema patterns
- `src/antigravity_tool/services/context_engine.py` — Context assembly (you'll inject this into AnalysisService)
- `src/antigravity_tool/services/knowledge_graph_service.py` — KG queries (for ribbon data)
- `src/web/src/components/timeline/TimelineView.tsx` — Current Timeline page (add charts here)
- `src/web/src/lib/api.ts` — API client (follow existing patterns)
- `src/web/src/lib/store.ts` — Zustand store

---

## Required Actions

### Backend (Python)

**1. Create `src/antigravity_tool/services/analysis_service.py`**

Create the `AnalysisService` class with two methods for this session:

- `async analyze_emotional_arc(chapter: int | None = None) -> EmotionalArcResult`
  - Query all scenes via `KnowledgeGraphService.find_containers(container_type="scene")`
  - For each scene, assemble context via `ContextEngine` and call LLM (via litellm) to score emotional valence
  - LLM prompt should ask for scores (0.0–1.0) for: hope, conflict, tension, sadness, joy, plus dominant emotion and 1-line summary
  - After scoring all scenes, detect "flat zones" (3+ consecutive scenes with tension < 0.3)
  - Detect "peak moments" (scenes with any emotion > 0.8)
  - Compute pacing grade (A–F based on variance and peak distribution)
  - Generate recommendations for flat zones

- `compute_character_ribbons(chapter: int | None = None) -> list[CharacterRibbon]`
  - Query scenes via KG
  - For each scene, get `characters_present` from scene attributes/relationships
  - Score prominence heuristically: POV character = 1.0, dialogue participant = 0.7, mentioned = 0.3
  - Return per-scene per-character prominence data
  - **No LLM call required** — pure KG query + heuristics

Use the dataclass definitions from `docs/LOW_LEVEL_DESIGN.md` §10.1.

**2. Create `src/antigravity_tool/server/routers/analysis.py`**

New router with prefix `/api/v1/analysis`, tags `["analysis"]`:

- `GET /emotional-arc` — optional query param `chapter: int | None = None`. Returns `EmotionalArcResponse`.
- `GET /ribbons` — optional query param `chapter: int | None = None`. Returns `list[CharacterRibbonResponse]`.

Add the Pydantic response models to `api_schemas.py` (see LLD §10.2).

**3. Wire DI in `deps.py`**

```python
def get_analysis_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    context_engine: ContextEngine = Depends(get_context_engine),
) -> AnalysisService:
    return AnalysisService(kg_service, container_repo, context_engine)
```

**4. Register router in `app.py`**

Add: `app.include_router(analysis.router)`

### Frontend (TypeScript/React)

**5. Install `recharts`**

```bash
cd src/web && npm install recharts
```

**6. Add API client methods to `api.ts`**

```typescript
// Analysis
getEmotionalArc: (chapter?: number) =>
  request<EmotionalArcResponse>(
    chapter ? `/api/v1/analysis/emotional-arc?chapter=${chapter}` : "/api/v1/analysis/emotional-arc"
  ),
getCharacterRibbons: (chapter?: number) =>
  request<CharacterRibbonResponse[]>(
    chapter ? `/api/v1/analysis/ribbons?chapter=${chapter}` : "/api/v1/analysis/ribbons"
  ),
```

Add the TypeScript response interfaces matching the Pydantic models.

**7. Create `src/web/src/components/timeline/EmotionalArcChart.tsx`**

Requirements:
- Use `recharts` `LineChart` with multiple `Line` series (hope, conflict, tension, sadness, joy)
- X-axis = scene labels ("Sc1", "Sc2", ...)
- Y-axis = 0.0–1.0
- Color coding: tension=red, hope=green, conflict=orange, joy=yellow, sadness=blue
- "Analyze" button to trigger the API call (shows loading spinner during LLM analysis)
- Below the chart, show:
  - Flat zone warnings with scene range
  - Peak moment highlights
  - Pacing grade badge (A=green, B=teal, C=yellow, D=orange, F=red)
  - Recommendation text
- Click a data point → call `selectItem({ id: scene_id, type: 'scene', name: scene_name })` to open in Inspector
- Follow the existing dark theme styling (bg-gray-900, text-gray-300, border-gray-800)

**8. Create `src/web/src/components/timeline/StoryRibbons.tsx`**

Requirements:
- Pure SVG rendering — `<svg>` with `<rect>` elements per character per scene
- Each character gets a consistent color (use a color palette indexed by character position)
- Rect width = column width per scene, height proportional to `prominence` (0.0–1.0) scaled to max ribbon height (e.g., 24px)
- Gap between character rows
- Hover tooltip showing character name + scene name + prominence percentage
- X-axis labels (scene names) below the ribbons
- Y-axis labels (character names) on the left
- If prominence is 0 (character not present), render a very thin gray line to show the lane
- Follow dark theme styling

**9. Integrate into `TimelineView.tsx`**

Add both components to the Timeline page:
- Add a tab or toggle to switch between "Events" (existing), "Emotional Arc", and "Story Ribbons"
- Or stack them vertically below the event stream (simpler approach, preferred)
- Each section should be collapsible with a chevron

---

## Output Specification

Provide the complete code for:
1. `src/antigravity_tool/services/analysis_service.py` (new file — `EmotionalScore`, `EmotionalArcResult`, `CharacterRibbon` dataclasses + `AnalysisService` class with `analyze_emotional_arc` and `compute_character_ribbons`)
2. `src/antigravity_tool/server/routers/analysis.py` (new file — 2 endpoints)
3. Updates to `src/antigravity_tool/server/api_schemas.py` (add response models)
4. Updates to `src/antigravity_tool/server/deps.py` (add `get_analysis_service`)
5. Updates to `src/antigravity_tool/server/app.py` (register router)
6. `src/web/src/components/timeline/EmotionalArcChart.tsx` (new file)
7. `src/web/src/components/timeline/StoryRibbons.tsx` (new file)
8. Updates to `src/web/src/components/timeline/TimelineView.tsx` (integrate both)
9. Updates to `src/web/src/lib/api.ts` (add methods + interfaces)

---

## Important Notes

- **A parallel session (Session B) is implementing Character Voice Scorecard.** It will also add methods to `AnalysisService`. Leave a clear comment `# Voice Scorecard methods added by Session B` where voice methods would go, so the merge is clean.
- **Do NOT modify** files outside the scope listed above. Specifically, do not touch `CharacterInspector.tsx` or `zenSlice.ts`.
- Follow existing patterns: dark theme (bg-gray-900, border-gray-800, text-gray-300), Zustand for state, `api.ts` typed helpers.
- Use `toast.success()` / `toast.error()` from `sonner` for user feedback (already installed).
- The LLM call in `analyze_emotional_arc` should use `litellm.completion()` — follow the pattern in `agent_dispatcher.py` for how LLM calls are made.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles cleanly.
