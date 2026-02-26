# Prompt: Phase Next-C/D Session A — Panel Layout Intelligence + Enhanced Approval Gate

**Goal**: Build AI-powered panel layout suggestions for the Storyboard page, and enhance the PromptReviewModal with context pinning, temperature control, and regeneration.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 16 FastAPI routers, 25 services, and a Next.js frontend with 6 pages. The Storyboard page (`/storyboard`) already has panel CRUD, drag-to-reorder, and AI panel generation. The PromptReviewModal already has Edit/Refine/Paste tabs with model selection.

This session adds two features:
1. **Panel Layout Intelligence** — AI analyzes narrative beat type per scene and suggests optimal panel layouts (count, sizes, camera angles)
2. **Enhanced Approval Gate** — Add context pinning, temperature slider, and "regenerate with different model" to the PromptReviewModal

**Read these files first** (essential context):
- `docs/PRD.md` §13 — Phase Next-C and Next-D descriptions
- `src/showrunner_tool/services/storyboard_service.py` — Current panel generation logic (314 lines)
- `src/showrunner_tool/schemas/storyboard.py` — Panel/PanelType/CameraAngle models (136 lines)
- `src/showrunner_tool/services/pipeline_service.py` — Pipeline execution, especially `_handle_llm_generate` for model resolution pattern
- `src/web/src/components/storyboard/SceneStrip.tsx` — Scene strip with "Generate Panels" button
- `src/web/src/components/storyboard/PanelCard.tsx` — Panel card component
- `src/web/src/app/storyboard/page.tsx` — Storyboard page layout
- `src/web/src/components/pipeline/PromptReviewModal.tsx` — Current modal (274 lines, 3 tabs)
- `src/web/src/components/pipeline/usePipelineStream.ts` — Pipeline SSE hook
- `src/web/src/lib/api.ts` — API client patterns
- `src/showrunner_tool/server/routers/storyboard.py` — Storyboard API endpoints
- `src/showrunner_tool/server/routers/pipeline.py` — Pipeline resume endpoint

---

## Feature 1: Panel Layout Intelligence

### Backend

**1. Add `suggest_layout` method to `StoryboardService`**

Add a new method that analyzes scene narrative beat type and suggests an optimal panel layout:

```python
async def suggest_layout(self, scene_id: str, scene_text: str, scene_name: str) -> dict:
    """
    Analyze the narrative beat type of a scene and suggest panel layout.

    Returns:
    {
        "beat_type": "action" | "dialogue" | "dramatic_reveal" | "transition" | "montage" | "emotional",
        "suggested_panel_count": int,
        "layout": [
            {
                "panel_number": 0,
                "panel_type": "action",
                "camera_angle": "wide",
                "size_hint": "large" | "medium" | "small" | "splash",
                "description_hint": "Establishing shot of the battlefield",
                "composition_notes": "Rule of thirds, character in left third"
            },
            ...
        ],
        "reasoning": "This scene is an action climax with a dramatic reveal...",
        "pacing_notes": "Consider splash panel for the reveal moment"
    }
    ```

Implementation:
- Call LLM (via litellm) with scene text + existing panel types/camera angles as schema
- Prompt should explain beat types and their visual conventions:
  - **Action** → diagonal panel cuts, motion lines, dynamic camera angles (LOW_ANGLE, DUTCH), more panels (6-8)
  - **Dialogue** → small panels, close-ups, over-shoulder shots, medium count (4-6)
  - **Dramatic reveal** → splash panel (full-width) for the key moment, few supporting panels (3-4)
  - **Transition** → horizontal widescreen panels, establishing shots, few panels (2-3)
  - **Montage** → grid of equal-sized panels, varied subjects, many panels (6-9)
  - **Emotional** → close-ups, extreme close-ups, medium panels with white space (3-5)
- Parse JSON response with fallback
- Validate panel_type and camera_angle against existing enums

**2. Add endpoint to storyboard router**

```python
@router.post("/scenes/{scene_id}/suggest-layout")
async def suggest_layout(
    scene_id: str,
    svc: StoryboardService = Depends(get_storyboard_service),
) -> dict:
    """AI-suggested panel layout based on narrative beat analysis."""
```

The endpoint should:
- Fetch scene data from KnowledgeGraphService or ContainerRepository
- Extract scene text/description from attributes
- Call `svc.suggest_layout(scene_id, scene_text, scene_name)`
- Return the layout suggestion

**3. Add "Apply Layout" endpoint (optional, can reuse generate_panels)**

The frontend will send the accepted layout back to `generate_panels_for_scene` with the suggested parameters, OR add a new endpoint:

```python
@router.post("/scenes/{scene_id}/apply-layout")
async def apply_layout(
    scene_id: str,
    body: ApplyLayoutRequest,  # { layout: [...], style: "manga" }
    svc: StoryboardService = Depends(get_storyboard_service),
) -> list:
    """Generate panels using the AI-suggested layout."""
```

### Frontend

**4. Add "Suggest Layout" button to `SceneStrip.tsx`**

Next to the existing "Generate Panels" button, add a "Suggest Layout" button:
- Calls `api.suggestLayout(sceneId)`
- Shows loading spinner during analysis
- Opens a `LayoutSuggestionPanel` (new component) showing the suggested layout

**5. Create `src/web/src/components/storyboard/LayoutSuggestionPanel.tsx`**

A panel/modal that displays the AI layout suggestion:

```
┌──────────────────────────────────────────────────────────┐
│ Layout Suggestion for "The Market Ambush"                │
│ Beat Type: ACTION                              [Apply ✓] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────┐  ┌──────┐  ┌──────┐    │
│  │ Panel 1 (LARGE)            │  │ P2   │  │ P3   │    │
│  │ WIDE - Establishing shot   │  │MEDIUM│  │CLOSE │    │
│  │ "Battlefield overview"     │  │      │  │      │    │
│  └─────────────────────────────┘  └──────┘  └──────┘    │
│  ┌──────┐  ┌──────────────────────────────────────┐      │
│  │ P4   │  │ Panel 5 (SPLASH)                    │      │
│  │DUTCH │  │ LOW_ANGLE - The dramatic reveal      │      │
│  │      │  │ "Hero's power activation"            │      │
│  └──────┘  └──────────────────────────────────────┘      │
│                                                           │
│ Reasoning: "This action scene builds from wide           │
│ establishing to dramatic reveal..."                       │
│                                                           │
│ Pacing: "Consider adding speed lines to panels 2-4"      │
│                                                           │
│ [Discard]                              [Apply & Generate] │
└──────────────────────────────────────────────────────────┘
```

- Visual preview of panel sizes (large/medium/small/splash mapped to CSS widths)
- Each panel preview shows: type badge, camera angle, description hint, composition notes
- "Apply & Generate" button → calls generate_panels with the layout parameters
- "Discard" button → closes panel
- Beat type displayed as colored badge (action=red, dialogue=blue, reveal=purple, etc.)

**6. Add API client method**

```typescript
suggestLayout: (sceneId: string) =>
  post<LayoutSuggestion>(`/api/v1/storyboard/scenes/${encodeURIComponent(sceneId)}/suggest-layout`),
```

Add TypeScript interfaces:
```typescript
export interface PanelLayoutHint {
  panel_number: number;
  panel_type: string;
  camera_angle: string;
  size_hint: 'large' | 'medium' | 'small' | 'splash';
  description_hint: string;
  composition_notes: string;
}

export interface LayoutSuggestion {
  beat_type: string;
  suggested_panel_count: number;
  layout: PanelLayoutHint[];
  reasoning: string;
  pacing_notes: string;
}
```

---

## Feature 2: Enhanced Approval Gate

### Backend

**7. Extend pipeline resume payload**

The `POST /api/pipeline/{runId}/resume` endpoint already accepts `{ payload: any }`. The payload already supports `prompt_text`, `model`, and `refine_instructions`. Extend to also support:

- `pinned_context_ids: string[]` — Container IDs to force-include in context (bypass relevance scoring)
- `temperature: float` — Override temperature for the next LLM call
- `regenerate: boolean` — If true, re-run the last LLM_GENERATE step with changed parameters

In `pipeline_service.py`, modify `_handle_llm_generate` to:
- Check `run.payload.get("temperature_override")` and use it if present
- Check `run.payload.get("pinned_context_ids")` and force those containers into context assembly

### Frontend

**8. Enhance `PromptReviewModal.tsx`**

Add to the existing modal (do NOT replace existing functionality):

**a) Temperature Slider** — Add below the model selector in the header area:
```tsx
<div className="flex items-center gap-2">
  <label className="text-xs text-gray-500">Temp:</label>
  <input
    type="range"
    min="0" max="2" step="0.1"
    value={temperature}
    onChange={(e) => setTemperature(parseFloat(e.target.value))}
    className="w-24 accent-indigo-500"
  />
  <span className="text-xs text-gray-400 w-8">{temperature}</span>
</div>
```

**b) Context Pinning** — In the Glass Box / ContextInspector section, add pin/unpin toggles per context bucket:
```tsx
{contextBuckets?.map(bucket => (
  <div key={bucket.id} className="flex items-center justify-between">
    <span className="text-xs text-gray-400">{bucket.name}</span>
    <button
      onClick={() => togglePinContext(bucket.id)}
      className={pinnedContextIds.includes(bucket.id) ? 'text-indigo-400' : 'text-gray-600'}
    >
      <Pin className="w-3 h-3" />
    </button>
  </div>
))}
```

**c) Regenerate Button** — Add a "Regenerate" button in the footer that resumes with `regenerate: true`:
```tsx
<button
  onClick={() => onResume({
    prompt_text: promptText || '',
    model: selectedModel || undefined,
    temperature: temperature !== 0.7 ? temperature : undefined,
    pinned_context_ids: pinnedContextIds.length > 0 ? pinnedContextIds : undefined,
    regenerate: true,
  })}
  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium rounded-lg"
>
  <RefreshCw className="w-4 h-4 inline mr-1" />
  Regenerate
</button>
```

**d) Update Resume handler** — Include new fields when resuming normally:
```tsx
onClick={() => onResume({
  prompt_text: promptText || '',
  model: selectedModel || undefined,
  temperature: temperature !== 0.7 ? temperature : undefined,
  pinned_context_ids: pinnedContextIds.length > 0 ? pinnedContextIds : undefined,
})}
```

---

## Output Specification

Provide the complete code for:
1. Updates to `src/showrunner_tool/services/storyboard_service.py` (add `suggest_layout` method)
2. Updates to `src/showrunner_tool/server/routers/storyboard.py` (add suggest-layout endpoint)
3. `src/web/src/components/storyboard/LayoutSuggestionPanel.tsx` (new file)
4. Updates to `src/web/src/components/storyboard/SceneStrip.tsx` (add Suggest Layout button)
5. Updates to `src/web/src/lib/api.ts` (add suggestLayout method + interfaces)
6. Updates to `src/showrunner_tool/services/pipeline_service.py` (temperature_override + pinned_context_ids in _handle_llm_generate)
7. Updates to `src/web/src/components/pipeline/PromptReviewModal.tsx` (temperature slider, context pinning, regenerate button)

---

## Important Notes

- **Parallel sessions are implementing Character Progressions + Reader Scroll Sim (Session 23) and Workflow Templates + Research UI (Session 24).** Do NOT modify CharacterInspector, the `/preview` route, TemplateGallery, workflowTemplates, or research router.
- The `suggest_layout` LLM call should use `litellm.completion()` — follow the pattern in `storyboard_service.py`'s existing `generate_panels_for_scene` method.
- For the PromptReviewModal changes, preserve ALL existing functionality (Edit/Refine/Paste tabs, model selector, Glass Box). Only ADD new elements.
- Use `Pin` and `RefreshCw` icons from `lucide-react`.
- Follow dark theme styling (bg-gray-900, border-gray-800, text-gray-300).
- Use `toast.success()` / `toast.error()` from `sonner` for feedback.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles cleanly.
