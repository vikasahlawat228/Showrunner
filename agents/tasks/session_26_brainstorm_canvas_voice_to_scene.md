# Prompt: Phase Next-E Session B — Spatial Brainstorming Canvas + Voice-to-Scene

**Goal**: Build an infinite canvas for free-form idea cards with AI-suggested connections, and a voice dictation feature that transcribes speech into scene descriptions and generates storyboard panels.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 18 routers, 28 services, and a Next.js frontend with 8 pages. The dashboard already uses ReactFlow (`@xyflow/react` v12) for the Knowledge Graph canvas. The `AgentDispatcher` has a `brainstorm_agent` skill with keyword routing and ReAct loop execution. The `StoryboardService` has `generate_panels_for_scene()` and `suggest_layout()` methods for panel generation from text.

This session adds two features:
1. **Spatial Brainstorming Canvas** — New `/brainstorm` page with an infinite ReactFlow canvas for placing idea cards, with AI-suggested connections between nearby cards
2. **Voice-to-Scene** — Dictation button using Web Speech API that transcribes speech, then generates storyboard panels from the transcribed text

**Read these files first** (essential context):
- `src/web/src/components/storyboard/SemanticCanvas.tsx` — ReactFlow canvas with semantic zoom (161 lines, pattern for brainstorm canvas)
- `src/web/src/components/canvas/InfiniteCanvas.tsx` — KG ReactFlow canvas (existing infinite canvas pattern)
- `src/web/src/lib/store/reactFlowSlice.ts` — ReactFlow state management pattern (266 lines)
- `src/antigravity_tool/services/agent_dispatcher.py` — AgentDispatcher with brainstorm_agent (702 lines)
- `src/antigravity_tool/server/routers/director.py` — `POST /dispatch` endpoint for agent calls
- `src/antigravity_tool/services/storyboard_service.py` — `generate_panels_for_scene()` and `suggest_layout()` (388 lines)
- `src/antigravity_tool/server/routers/storyboard.py` — Panel generation endpoints
- `src/web/src/components/zen/ZenEditor.tsx` — TipTap editor (381 lines, reference for slash commands)
- `src/web/src/components/workbench/Canvas.tsx` — Main nav header with page links (194 lines)
- `src/web/src/app/storyboard/page.tsx` — Storyboard page (129 lines)
- `src/web/src/lib/api.ts` — API client (check `directorDispatch`, `generateStoryboardPanels`, `suggestLayout`)
- `src/web/package.json` — Current dependencies (`@xyflow/react`, `@dnd-kit`, `@tiptap`)
- `src/antigravity_tool/server/deps.py` — DI graph

---

## Feature 1: Spatial Brainstorming Canvas

### Backend

**1. Add a brainstorm endpoint for AI-suggested connections**

Add to the existing `src/antigravity_tool/server/routers/director.py` (do NOT create a new router):

```python
class BrainstormSuggestRequest(BaseModel):
    cards: list[dict]  # [{ "id": "...", "text": "...", "x": 0, "y": 0 }]
    intent: str = ""   # Optional focus query

@router.post("/brainstorm/suggest-connections")
async def suggest_connections(
    req: BrainstormSuggestRequest,
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
):
    """AI analyzes idea cards and suggests connections/new ideas."""
    ...
```

Implementation:
- Build a prompt listing all card texts with their IDs
- Ask the LLM to identify: (a) connections between existing cards, (b) missing ideas that would bridge gaps, (c) themes/clusters
- Use `agent_dispatcher.execute()` with the `brainstorm_agent` skill
- Parse the LLM response into structured format:

```python
# Response format:
{
    "suggested_edges": [
        {"source": "card_id_1", "target": "card_id_2", "label": "leads to", "reasoning": "..."},
    ],
    "suggested_cards": [
        {"text": "What if the villain is also searching for...", "near_card_id": "card_id_3", "reasoning": "..."},
    ],
    "themes": [
        {"name": "Power Dynamics", "card_ids": ["card_1", "card_3"]},
    ]
}
```

**2. Add persistence for brainstorm cards**

Brainstorm cards should be stored as `GenericContainer` instances with `container_type: "idea_card"`. The existing `ContainerRepository` and KG indexing handles this automatically. Add attributes:
```python
attributes = {
    "text": "What if the villain was the mentor all along?",
    "position_x": 450.0,
    "position_y": 200.0,
    "color": "#4F46E5",  # Indigo
    "tags": ["plot_twist", "villain"],
}
```

Use existing endpoints:
- Save card: The parallel Session 25 is creating `POST /api/v1/containers` — you can rely on it, OR save cards via the KG service. For safety, add a simple save method within the brainstorm endpoint or use `container_repo.save_container()` directly from a new endpoint.

Add to `director.py`:
```python
@router.post("/brainstorm/save-card")
async def save_brainstorm_card(
    req: BrainstormCardSaveRequest,
    container_repo: ContainerRepository = Depends(get_container_repo),
    event_service: EventService = Depends(get_event_service),
):
    """Save an idea card as a GenericContainer."""
    ...

@router.get("/brainstorm/cards")
async def get_brainstorm_cards(
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    """List all idea_card containers."""
    return [c.model_dump() for c in container_repo.list_by_type("idea_card")]

@router.delete("/brainstorm/cards/{card_id}")
async def delete_brainstorm_card(
    card_id: str,
    container_repo: ContainerRepository = Depends(get_container_repo),
):
    """Delete a brainstorm card."""
    ...
```

### Frontend

**3. Create `src/web/src/app/brainstorm/page.tsx`**

New page at `/brainstorm` — the Spatial Brainstorming Canvas:

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Dashboard    Brainstorm Canvas    [+ Add Card] [🤖 Suggest]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐            ┌─────────────┐                      │
│  │ 💡 What if  │ ── leads ──│ 💡 Then the │                      │
│  │ the villain │  to ──→   │ hero would  │                      │
│  │ was the     │            │ need to...  │                      │
│  │ mentor?     │            └─────────────┘                      │
│  └─────────────┘                    │                             │
│         │                      conflicts                          │
│      related                   with ↓                             │
│      to ↓               ┌─────────────┐                          │
│  ┌─────────────┐        │ 💡 The magic │                         │
│  │ 💡 Mentor's │        │ system needs │                         │
│  │ secret past │        │ a weakness   │                         │
│  └─────────────┘        └─────────────┘                          │
│                                                                   │
│  ┌─ AI Suggestions ─────────────────────────────────────────────┐│
│  │ 🤖 Suggested connections:                                    ││
│  │   • "Mentor's secret past" → "Magic system weakness"         ││
│  │     (The mentor might know the weakness from personal exp.)  ││
│  │ 🤖 New idea: "What triggers the hero's suspicion?"           ││
│  │   [Add to Canvas]                    [Dismiss]                ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

Requirements:
- **ReactFlow canvas** with custom `IdeaCardNode` node type
- Each card node shows: text content (editable on double-click), color indicator, delete button
- **"Add Card" button**: Creates a new card at a random position near the viewport center
- **"Suggest" button**: Sends all cards to `POST /director/brainstorm/suggest-connections`
  - Shows suggestions in a bottom panel
  - "Add to Canvas" accepts a suggested card (creates it on the canvas near the referenced card)
  - Suggested edges rendered as dashed lines with labels
- **Edge creation**: Drag from one card's handle to another to manually create connections
- **Card persistence**: Auto-save card positions on drag-end via `POST /director/brainstorm/save-card`
- **Load on mount**: Fetch existing cards via `GET /director/brainstorm/cards`
- **Delete card**: Click trash icon → confirmation → `DELETE /director/brainstorm/cards/{id}`
- **Minimap**: Show ReactFlow minimap for navigation on large canvases
- Dark theme: bg-gray-950 canvas background, cards with bg-gray-800 + colored left border

**4. Create `src/web/src/components/brainstorm/IdeaCardNode.tsx`**

Custom ReactFlow node component:
```tsx
- Text content (truncated to 3 lines in compact view, full on hover/click)
- Editable on double-click (inline textarea)
- Color indicator (left border, 6 preset colors)
- Delete button (top-right corner, appears on hover)
- Source/target handles (left/right for horizontal connections)
- Tag badges (small pills at bottom)
- Drag handle area
```

**5. Create `src/web/src/components/brainstorm/SuggestionPanel.tsx`**

Bottom panel showing AI suggestions:
- List of suggested edges: source card → target card with reasoning
- List of suggested new cards with "Add to Canvas" / "Dismiss" buttons
- Theme clusters (color-coded groupings)
- Loading state with spinner
- Collapsible (toggle open/close)

**6. Add nav link in `Canvas.tsx`**

Add a "Brainstorm" link to the nav header in `src/web/src/components/workbench/Canvas.tsx`, between "Research" and "Preview":
```tsx
<a href="/brainstorm" className="px-3 py-1 text-xs font-medium rounded-md transition-colors text-gray-500 hover:text-gray-300">
  💡 Brainstorm
</a>
```

**7. Add API client methods**

```typescript
// Brainstorm
getBrainstormCards: () =>
  request<GenericContainer[]>("/api/v1/director/brainstorm/cards"),
saveBrainstormCard: (body: { text: string; position_x: number; position_y: number; color?: string; tags?: string[] }) =>
  post<GenericContainer>("/api/v1/director/brainstorm/save-card", body),
deleteBrainstormCard: (cardId: string) =>
  del(`/api/v1/director/brainstorm/cards/${encodeURIComponent(cardId)}`),
suggestBrainstormConnections: (body: { cards: Array<{ id: string; text: string; x: number; y: number }>; intent?: string }) =>
  post<BrainstormSuggestion>("/api/v1/director/brainstorm/suggest-connections", body),
```

Add interface:
```typescript
export interface BrainstormSuggestion {
  suggested_edges: Array<{ source: string; target: string; label: string; reasoning: string }>;
  suggested_cards: Array<{ text: string; near_card_id: string; reasoning: string }>;
  themes: Array<{ name: string; card_ids: string[] }>;
}
```

---

## Feature 2: Voice-to-Scene

### Backend

**8. Add a voice transcription endpoint (Whisper fallback)**

Create a simple endpoint for audio transcription. For the browser-native Web Speech API path, no backend is needed. But for Whisper fallback (when Web Speech API is unavailable or for better accuracy), add:

```python
# Add to src/antigravity_tool/server/routers/storyboard.py

@router.post("/voice-to-scene")
async def voice_to_scene(
    scene_text: str = Form(...),
    scene_name: str = Form("Voice Scene"),
    panel_count: int = Form(6),
    style: str = Form("manga"),
    svc: StoryboardService = Depends(get_storyboard_service),
):
    """
    Generate storyboard panels from dictated text.
    The frontend handles speech-to-text via Web Speech API.
    This endpoint receives the transcribed text and generates panels.
    """
    # First suggest a layout based on the text
    layout = await svc.suggest_layout(
        scene_id="voice_scene",
        scene_text=scene_text,
        scene_name=scene_name,
    )

    # Then generate panels
    panels = await svc.generate_panels_for_scene(
        scene_id="voice_scene",
        scene_text=scene_text,
        scene_name=scene_name,
        panel_count=layout.get("suggested_panel_count", panel_count),
        style=style,
    )

    return {
        "layout_suggestion": layout,
        "panels": [p.model_dump() for p in panels],
        "scene_text": scene_text,
    }
```

### Frontend

**9. Create `src/web/src/components/storyboard/VoiceToSceneButton.tsx`**

A microphone button component using the Web Speech API:

```tsx
// Usage in storyboard page header:
<VoiceToSceneButton onTranscript={(text) => handleVoiceTranscript(text)} />
```

Implementation:
- Uses `window.SpeechRecognition` or `window.webkitSpeechRecognition` (browser-native, no package needed)
- Three states: `idle` → `recording` → `processing`
- **Idle**: Shows a microphone icon button (gray)
- **Recording**: Pulsing red microphone, live transcript displayed below, "Stop" button
- **Processing**: Spinner, calling the API
- On stop recording:
  1. Show the transcript in an editable textarea for review
  2. "Generate Panels" button → calls `POST /api/v1/storyboard/voice-to-scene`
  3. Shows the returned layout suggestion + panel previews
  4. "Apply to Scene" button → saves panels to the selected scene
- Fallback text: "Your browser doesn't support speech recognition. Type your scene description instead." (show a textarea fallback)

```
┌────────────────────────────────────────────┐
│ 🎤 Voice to Scene                          │
│                                            │
│ [🔴 Recording...]   "The marketplace      │
│                       hummed with activity  │
│                       as Zara approached    │
│                       the merchant's stall" │
│                                            │
│ [⏹ Stop]                                   │
├────────────────────────────────────────────┤
│ Transcript (editable):                      │
│ ┌────────────────────────────────────────┐ │
│ │ The marketplace hummed with activity   │ │
│ │ as Zara approached the merchant's      │ │
│ │ stall...                               │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ Scene: [Select scene ▼]  Panels: [6]      │
│                                            │
│ [Generate Panels]                          │
├────────────────────────────────────────────┤
│ Generated Panels:                          │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│ │ P1   │ │ P2   │ │ P3   │ │ P4   │      │
│ │ WIDE │ │ MED  │ │ CU   │ │ ACT  │      │
│ └──────┘ └──────┘ └──────┘ └──────┘      │
│                                            │
│ [Apply to Scene]              [Discard]    │
└────────────────────────────────────────────┘
```

**10. Integrate into Storyboard page**

Add the `VoiceToSceneButton` to `src/web/src/app/storyboard/page.tsx` header, next to the view mode toggle:

```tsx
<div className="flex items-center gap-2">
  {/* Existing Strip/Canvas toggle */}
  <button onClick={() => setViewMode("strip")} ...>Strips</button>
  <button onClick={() => setViewMode("canvas")} ...>Canvas</button>

  {/* New Voice-to-Scene button */}
  <VoiceToSceneButton
    scenes={scenes}
    onPanelsGenerated={(sceneId, panels) => {
      // Refresh the scene strip to show new panels
      fetchPanelsForScene(sceneId);
      toast.success(`Generated ${panels.length} panels from voice input`);
    }}
  />
</div>
```

**11. Add Voice nav link in Canvas.tsx**

Add a link in the nav header — but since Voice-to-Scene is integrated into the Storyboard page (not a separate page), just update the Storyboard link to indicate it has voice support. Alternatively, add to `Canvas.tsx`:
```tsx
<a href="/storyboard" className="px-3 py-1 text-xs font-medium rounded-md transition-colors text-gray-500 hover:text-gray-300">
  🎬 Storyboard
</a>
```
(No change needed if Voice-to-Scene is within the Storyboard page.)

**12. Add API client methods**

```typescript
// Voice-to-Scene
voiceToScene: (body: { scene_text: string; scene_name?: string; panel_count?: number; style?: string }) =>
  post<{ layout_suggestion: LayoutSuggestion; panels: Panel[]; scene_text: string }>(
    "/api/v1/storyboard/voice-to-scene",
    body
  ),
```

---

## Output Specification

Provide the complete code for:
1. Updates to `src/antigravity_tool/server/routers/director.py` (add brainstorm endpoints: suggest-connections, save-card, get-cards, delete-card)
2. Updates to `src/antigravity_tool/server/routers/storyboard.py` (add voice-to-scene endpoint)
3. `src/web/src/app/brainstorm/page.tsx` (new file — Brainstorm Canvas page)
4. `src/web/src/components/brainstorm/IdeaCardNode.tsx` (new file — custom ReactFlow node)
5. `src/web/src/components/brainstorm/SuggestionPanel.tsx` (new file — AI suggestion display)
6. `src/web/src/components/storyboard/VoiceToSceneButton.tsx` (new file — mic button + transcript + generate)
7. Updates to `src/web/src/app/storyboard/page.tsx` (integrate VoiceToSceneButton)
8. Updates to `src/web/src/components/workbench/Canvas.tsx` (add Brainstorm nav link)
9. Updates to `src/web/src/lib/api.ts` (add methods + interfaces for brainstorm + voice)

---

## Important Notes

- **A parallel session is implementing Story Structure Editor + Alternate Timeline Browser (Session 25).** Do NOT modify `StoryStructureTree.tsx`, `TimelineView.tsx`, `TimelinePanel.tsx`, `timeline/page.tsx`, `timeline.py` router, `event_sourcing_repo.py`, `projects.py` router, or create `containers.py` router.
- For the Brainstorm Canvas, follow the ReactFlow patterns in `SemanticCanvas.tsx` and `InfiniteCanvas.tsx`. Use `@xyflow/react` v12 (already installed).
- The `brainstorm_agent` skill in `agent_dispatcher.py` already handles brainstorm requests. Route through `agent_dispatcher.route_and_execute("brainstorm: {intent}", ...)`.
- For Voice-to-Scene, use the **browser-native Web Speech API** (`window.SpeechRecognition`). No additional npm packages needed. Provide a textarea fallback for browsers without speech support.
- The `StoryboardService.generate_panels_for_scene()` already generates panels from text — reuse it via `suggest_layout()` → `generate_panels_for_scene()` pipeline.
- Use `toast.success()` / `toast.error()` from `sonner`.
- Use `Pin`, `RefreshCw`, `Mic`, `MicOff`, `Trash2`, `Plus`, `Sparkles` icons from `lucide-react`.
- Follow dark theme styling (bg-gray-900/950, border-gray-800, text-gray-300).
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
