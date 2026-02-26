# Prompt: Phase Next-C/D Session B — Character Progressions + Reader Scroll Simulation

**Goal**: Build a Character DNA Timeline showing how characters evolve visually across chapters, and a Reader Scroll Simulation that previews the webtoon reading experience with pacing analysis.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 16 routers, 25 services, and 6 frontend pages. Characters have a `CharacterDNA` model (face, hair, body, outfit) stored as attributes on GenericContainer instances. The Storyboard page shows panels per scene.

This session adds two features:
1. **Character Progressions** — Visual DNA Timeline showing character appearance evolution over chapters (e.g., Ch.1: casual → Ch.5: battle scars → Ch.12: power-up)
2. **Reader Scroll Simulation** — `/preview` route that simulates the webtoon reading experience with auto-scroll, reading time estimates, and pacing analysis

**Read these files first** (essential context):
- `docs/PRD.md` §13 — Phase Next-C description
- `src/showrunner_tool/schemas/storyboard.py` — Panel model with duration_seconds
- `src/showrunner_tool/schemas/character.py` — Legacy CharacterDNA, FacialFeatures, HairDescription, BodyDescription, OutfitCanon
- `src/showrunner_tool/services/storyboard_service.py` — Panel CRUD + generation (314 lines)
- `src/showrunner_tool/services/knowledge_graph_service.py` — KG queries for character-scene relationships
- `src/web/src/components/workbench/CharacterInspector.tsx` — Current character detail view (187 lines, includes Voice Scorecard at bottom)
- `src/web/src/lib/api.ts` — API client (follow existing patterns)
- `src/web/src/app/storyboard/page.tsx` — Storyboard page (reference for panel data)
- `src/showrunner_tool/server/deps.py` — DI graph

---

## Feature 1: Character Progressions (Visual DNA Timeline)

### Backend

**1. Add progression support to character containers**

Characters are stored as GenericContainer with `container_type="character"`. Add a `progressions` field to character attributes that tracks visual evolution:

```python
# In character container attributes:
{
    "name": "Zara",
    "role": "protagonist",
    "dna": { ... },  # Base DNA
    "progressions": [
        {
            "id": "prog_01...",
            "chapter": 1,
            "label": "Casual Zara",
            "changes": {
                "hair": {"style": "ponytail", "color": "black"},
                "body": {"notable_features": ["no scars"]},
                "default_outfit": {"name": "Street clothes", "colors": ["gray", "blue"]}
            },
            "notes": "Before the inciting incident"
        },
        {
            "chapter": 5,
            "label": "Battle-Scarred Zara",
            "changes": {
                "face": {"distinguishing_marks": ["scar across left cheek"]},
                "default_outfit": {"name": "Light armor", "colors": ["silver", "red"]}
            },
            "notes": "After the Market Ambush"
        },
        {
            "chapter": 12,
            "label": "Awakened Zara",
            "changes": {
                "face": {"eye_color": "glowing amber"},
                "hair": {"notable_details": "streaked with silver"},
                "body": {"notable_features": ["glowing tattoo markings"]}
            },
            "notes": "Post power awakening"
        }
    ]
}
```

**2. Add progression CRUD endpoints**

New endpoints in a dedicated section of an existing router (e.g., `characters.py` or create a new section in `containers` handling):

```
GET  /api/v1/characters/{character_id}/progressions       → list progressions
POST /api/v1/characters/{character_id}/progressions       → add progression
PUT  /api/v1/characters/{character_id}/progressions/{id}  → update progression
DELETE /api/v1/characters/{character_id}/progressions/{id} → delete progression
GET  /api/v1/characters/{character_id}/dna-at-chapter/{chapter} → get resolved DNA for chapter
```

The `dna-at-chapter` endpoint should:
- Start with base DNA
- Apply all progressions with `chapter <= requested_chapter` in order
- Deep-merge changes onto base DNA
- Return the resolved DNA state at that point in the story

**3. Add Pydantic models for progressions**

Add to `api_schemas.py`:
```python
class CharacterProgression(BaseModel):
    id: Optional[str] = None
    chapter: int
    label: str
    changes: dict  # Partial DNA changes
    notes: str = ""

class ProgressionCreateRequest(BaseModel):
    chapter: int
    label: str
    changes: dict
    notes: str = ""

class ResolvedDNAResponse(BaseModel):
    character_id: str
    character_name: str
    chapter: int
    resolved_dna: dict  # Full merged DNA at this chapter
    progressions_applied: list[str]  # Labels of applied progressions
```

### Frontend

**4. Create `src/web/src/components/workbench/CharacterProgressionTimeline.tsx`**

A horizontal timeline visualization showing DNA evolution:

```
┌──────────────────────────────────────────────────────────┐
│ Visual Evolution                         [+ Add Stage]   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Ch.1              Ch.5              Ch.12                │
│  ●─────────────────●─────────────────●                   │
│  │                 │                 │                    │
│  ┌─────────┐     ┌─────────┐      ┌─────────┐          │
│  │ Casual  │     │ Battle- │      │ Awakened│          │
│  │ Zara    │     │ Scarred │      │ Zara    │          │
│  │         │     │ Zara    │      │         │          │
│  │ ponytail│     │ +scar   │      │ +glow   │          │
│  │ gray/   │     │ light   │      │ amber   │          │
│  │ blue    │     │ armor   │      │ eyes    │          │
│  └────[✏]──┘     └────[✏]──┘      └────[✏]──┘          │
│                                                           │
│  Key Changes:                                             │
│  • Ch.5: Scar across left cheek, switched to armor       │
│  • Ch.12: Eyes changed to glowing amber, silver streaks  │
└──────────────────────────────────────────────────────────┘
```

Requirements:
- Horizontal timeline with nodes at each progression chapter
- Each node shows: label, key visual changes (extracted from `changes` dict)
- Edit button per node → opens inline edit form for that progression
- "Add Stage" button → form with chapter number, label, DNA change fields
- Delete button per node (with confirmation)
- Below timeline: summary of key changes between stages
- Calls the progressions API endpoints for CRUD
- Follow dark theme (bg-gray-900, text-gray-300)

**5. Integrate into `CharacterInspector.tsx`**

Add between "Character DNA" section and "Character Arc" section:
```tsx
{/* Visual Evolution Timeline */}
<CharacterProgressionTimeline
  characterId={character.id}
  characterName={character.name}
  baseDNA={character.dna}
/>
```

**6. Add API client methods**

```typescript
getCharacterProgressions: (characterId: string) =>
  request<CharacterProgression[]>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions`),
addCharacterProgression: (characterId: string, body: ProgressionCreateRequest) =>
  post<CharacterProgression>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions`, body),
updateCharacterProgression: (characterId: string, progressionId: string, body: Partial<ProgressionCreateRequest>) =>
  put<CharacterProgression>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions/${encodeURIComponent(progressionId)}`, body),
deleteCharacterProgression: (characterId: string, progressionId: string) =>
  del(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions/${encodeURIComponent(progressionId)}`),
getDNAAtChapter: (characterId: string, chapter: number) =>
  request<ResolvedDNAResponse>(`/api/v1/characters/${encodeURIComponent(characterId)}/dna-at-chapter/${chapter}`),
```

---

## Feature 2: Reader Scroll Simulation

### Backend

**7. Create `src/showrunner_tool/services/reader_sim_service.py`**

```python
@dataclass
class PanelReadingMetrics:
    panel_id: str
    panel_number: int
    panel_type: str
    estimated_reading_seconds: float  # Based on text length + image complexity
    text_density: float               # Words per panel (0.0–1.0 normalized)
    is_info_dense: bool               # > 0.7 text density
    pacing_type: str                  # "fast" | "medium" | "slow"

@dataclass
class ReadingSimResult:
    scene_id: str
    scene_name: str
    total_reading_seconds: float
    panels: list[PanelReadingMetrics]
    pacing_dead_zones: list[dict]     # Consecutive slow panels
    info_overload_warnings: list[dict] # Too-dense panels
    engagement_score: float           # 0.0–1.0
    recommendations: list[str]
```

Methods:
- `simulate_reading(scene_id: str) -> ReadingSimResult`
  - Get all panels for scene
  - For each panel, estimate reading time:
    - Base: `duration_seconds` field (default 3s)
    - Text factor: +0.5s per 10 words of dialogue, +0.3s per 10 words of description
    - Type factor: splash panels +2s, establishing +1.5s, transition +0.5s
  - Compute text density: words / max_expected_words (normalize to 0-1)
  - Flag info-dense panels (density > 0.7)
  - Detect pacing dead zones: 3+ consecutive "slow" panels (reading time > 5s each)
  - Compute engagement score based on pacing variety
  - Generate recommendations

- `simulate_chapter_reading(chapter: int) -> list[ReadingSimResult]`
  - Aggregate across all scenes in a chapter

**8. Add endpoints**

```
GET /api/v1/preview/scene/{scene_id}    → ReadingSimResponse
GET /api/v1/preview/chapter/{chapter}   → list[ReadingSimResponse]
```

Create `src/showrunner_tool/server/routers/preview.py` with prefix `/api/v1/preview`.

### Frontend

**9. Create `src/web/src/app/preview/page.tsx`**

New page at `/preview` — the Reader Scroll Simulation experience:

```
┌──────────────────────────────────────────────────────────┐
│ ← Back to Storyboard    Reader Preview    Chapter: [1 ▼] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────┐  ┌───────────────┐ │
│  │                                  │  │ Pacing Map    │ │
│  │  [Panel 1 - Full Width]         │  │               │ │
│  │  "The marketplace hummed..."    │  │ ██░░██░░██    │ │
│  │  ⏱ 4.2s                        │  │ fast  slow    │ │
│  │                                  │  │               │ │
│  ├──────────────────────────────────┤  │ ⚠ Dead zone  │ │
│  │                                  │  │   panels 3-5  │ │
│  │  [Panel 2 - Medium]             │  │               │ │
│  │  Zara: "We need to move."      │  │ Engagement:   │ │
│  │  ⏱ 2.8s                        │  │ ████████░░    │ │
│  │                                  │  │ 78%           │ │
│  ├──────────────────────────────────┤  │               │ │
│  │  ⚠ INFO DENSE                   │  │ Total: 42.5s  │ │
│  │  [Panel 3 - Small]              │  │               │ │
│  │  (Heavy exposition panel)       │  │ Suggestions:  │ │
│  │  ⏱ 7.1s                        │  │ • Split P3    │ │
│  │                                  │  │ • Add pause   │ │
│  └──────────────────────────────────┘  └───────────────┘ │
│                                                           │
│  [▶ Auto-Scroll]  [⏸ Pause]  Speed: [1x ▼]              │
└──────────────────────────────────────────────────────────┘
```

Requirements:
- **Left column (70%)**: Vertical panel sequence simulating webtoon scroll
  - Each panel shows: description, dialogue, duration estimate
  - Info-dense panels highlighted with warning border (amber)
  - Panel type/camera badges
  - Smooth scroll behavior
- **Right sidebar (30%)**: Pacing analysis
  - Pacing heatmap (fast=green bars, medium=gray, slow=red)
  - Dead zone warnings with panel ranges
  - Info overload warnings
  - Engagement score (percentage bar)
  - Total reading time
  - Recommendations list
- **Bottom controls**:
  - Auto-scroll play/pause button (scrolls at estimated reading speed per panel)
  - Speed multiplier (0.5x, 1x, 1.5x, 2x)
  - Chapter selector
- Scene dividers between scenes within a chapter
- Use `useRef` for scroll container + `requestAnimationFrame` for smooth auto-scroll

**10. Add API client methods**

```typescript
getReadingSimScene: (sceneId: string) =>
  request<ReadingSimResponse>(`/api/v1/preview/scene/${encodeURIComponent(sceneId)}`),
getReadingSimChapter: (chapter: number) =>
  request<ReadingSimResponse[]>(`/api/v1/preview/chapter/${chapter}`),
```

Add interfaces matching the backend dataclasses.

**11. Add navigation link**

Add a link to `/preview` in the storyboard page header (next to Strips/Canvas toggle):
```tsx
<a href="/preview" className="px-3 py-1 text-xs font-medium rounded-md text-gray-500 hover:text-gray-300">
  Preview
</a>
```

Also add to the main Canvas.tsx header nav (where Zen/Pipelines/Storyboard links are).

---

## Output Specification

Provide the complete code for:
1. Updates to character handling — progression CRUD (backend endpoints + service logic)
2. Updates to `src/showrunner_tool/server/api_schemas.py` (progression + preview models)
3. `src/showrunner_tool/services/reader_sim_service.py` (new file)
4. `src/showrunner_tool/server/routers/preview.py` (new file)
5. Updates to `src/showrunner_tool/server/deps.py` (add get_reader_sim_service)
6. Updates to `src/showrunner_tool/server/app.py` (register preview router)
7. `src/web/src/components/workbench/CharacterProgressionTimeline.tsx` (new file)
8. Updates to `src/web/src/components/workbench/CharacterInspector.tsx` (integrate timeline)
9. `src/web/src/app/preview/page.tsx` (new file)
10. Updates to `src/web/src/lib/api.ts` (add methods + interfaces)
11. Updates to navigation links in storyboard page + Canvas.tsx header

---

## Important Notes

- **Parallel sessions are implementing Panel Layout Intelligence + Approval Gate (Session 22) and Workflow Templates + Research UI (Session 24).** Do NOT modify StoryboardService.generate_panels, SceneStrip, PromptReviewModal, TemplateGallery, or research router.
- Character progressions should use the existing GenericContainer system — store progressions as an array within the character container's `attributes.progressions`.
- The Reader Scroll Sim is a heuristic-based analysis — **no LLM calls needed**. Pure computation from panel metadata.
- For the `/preview` page, keep it simple: vertical scroll with panels rendered as cards. No actual image rendering needed — just descriptions and metadata.
- Use `toast.success()` / `toast.error()` from `sonner`.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
