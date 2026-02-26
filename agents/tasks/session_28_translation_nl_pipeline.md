# Session 28: Translation Agent UI + NL Pipeline Wizard

**Goal**: Build a Translation panel for multi-language prose adaptation, and a natural-language pipeline creation wizard that lets users describe workflows in plain English and auto-generate DAG definitions.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 19 routers, 28 services, and a Next.js frontend with 9 pages. The `AgentDispatcher` has a `translator_agent` skill for prose translation with cultural adaptation. The `PipelineService` already has a fully implemented `generate_pipeline_from_nl()` method and `POST /api/pipeline/definitions/generate` endpoint — the backend for NL→DAG is complete, only the frontend wizard is missing.

This session adds two features:
1. **Translation Agent UI** — New translation router + frontend panel for translating prose with cultural adaptation notes
2. **NL Pipeline Wizard** — Frontend modal that lets users describe a workflow in plain English and creates a pipeline definition

**Read these files first** (essential context):
- `agents/skills/translator_agent.md` — Full system prompt for translation (71 lines)
- `src/showrunner_tool/services/agent_dispatcher.py` — AgentDispatcher with execute() method (700+ lines)
- `src/showrunner_tool/services/pipeline_service.py` — Has `generate_pipeline_from_nl()` already (lines 1105-1260+)
- `src/showrunner_tool/server/routers/pipeline.py` — Has `POST /definitions/generate` already (lines 209-234)
- `src/showrunner_tool/services/context_engine.py` — ContextEngine for context assembly (312 lines)
- `src/showrunner_tool/services/knowledge_graph_service.py` — KG service with find_containers()
- `src/showrunner_tool/server/deps.py` — DI graph (219 lines)
- `src/web/src/app/pipelines/page.tsx` — Pipelines page with TemplateGallery
- `src/web/src/components/pipeline-builder/PipelineBuilder.tsx` — Visual DAG editor
- `src/web/src/components/pipeline-builder/TemplateGallery.tsx` — Template browser
- `src/web/src/lib/store/pipelineBuilderSlice.ts` — Pipeline builder Zustand store
- `src/web/src/lib/api.ts` — API client (822 lines)
- `src/web/package.json` — Current dependencies

---

## Feature 1: Translation Agent UI

### Backend

**1. Create `src/showrunner_tool/services/translation_service.py`**

```python
from dataclasses import dataclass, field

@dataclass
class AdaptationNote:
    original: str
    adapted: str
    reason: str

@dataclass
class CulturalFlag:
    location: str
    flag: str
    action_taken: str  # "adapted", "preserved", "flagged_for_review"

@dataclass
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    adaptation_notes: list[AdaptationNote]
    cultural_flags: list[CulturalFlag]
    glossary_applied: dict[str, str]
    confidence: float  # 0.0-1.0

class TranslationService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        agent_dispatcher: AgentDispatcher,
    ): ...

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        character_ids: list[str] | None = None,
        scene_id: str | None = None,
    ) -> TranslationResult:
        """Translate prose using the translator agent with cultural adaptation."""
        # 1. If character_ids provided, load character profiles from KG
        #    (get name, speech_style, personality from attributes)
        # 2. Load project glossary: containers with container_type="glossary_entry"
        #    Each has attributes: { term, translation_{lang}, notes }
        #    Build a dict of { source_term: target_translation }
        # 3. If scene_id provided, load scene context (mood, setting, tone)
        # 4. Build input for translator_agent:
        #    { source_text, source_language, target_language, character_profiles, glossary, scene_context }
        # 5. Call agent_dispatcher.execute() with translator_agent skill
        # 6. Parse JSON response into TranslationResult
        # 7. Return structured result

    def get_glossary(self) -> list[dict]:
        """List all glossary entries for the project."""
        entries = self.kg_service.find_containers(container_type="glossary_entry")
        return [{"id": e.id, "term": e.name, **e.attributes} for e in entries]

    def save_glossary_entry(
        self,
        term: str,
        translations: dict[str, str],  # { "ja": "日本語", "ko": "한국어" }
        notes: str = "",
    ) -> dict:
        """Create or update a glossary entry."""
        # Save as GenericContainer with container_type="glossary_entry"
        # attributes = { translations, notes }
        ...
```

**2. Create `src/showrunner_tool/server/routers/translation.py`**

New router (do NOT add to `analysis.py` — a parallel session is modifying that file):

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/translation", tags=["translation"])

class TranslateRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str = "ja"
    character_ids: list[str] | None = None
    scene_id: str | None = None

class AdaptationNoteResponse(BaseModel):
    original: str
    adapted: str
    reason: str

class CulturalFlagResponse(BaseModel):
    location: str
    flag: str
    action_taken: str

class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    adaptation_notes: list[AdaptationNoteResponse]
    cultural_flags: list[CulturalFlagResponse]
    glossary_applied: dict[str, str]
    confidence: float

class GlossaryEntryRequest(BaseModel):
    term: str
    translations: dict[str, str]
    notes: str = ""

@router.post("/translate")
async def translate_text(
    body: TranslateRequest,
    svc: TranslationService = Depends(get_translation_service),
) -> TranslateResponse:
    """Translate prose with cultural adaptation."""
    result = await svc.translate(
        text=body.text,
        source_language=body.source_language,
        target_language=body.target_language,
        character_ids=body.character_ids,
        scene_id=body.scene_id,
    )
    return TranslateResponse(
        translated_text=result.translated_text,
        source_language=result.source_language,
        target_language=result.target_language,
        adaptation_notes=[AdaptationNoteResponse(**n.__dict__) for n in result.adaptation_notes],
        cultural_flags=[CulturalFlagResponse(**f.__dict__) for f in result.cultural_flags],
        glossary_applied=result.glossary_applied,
        confidence=result.confidence,
    )

@router.get("/glossary")
async def get_glossary(
    svc: TranslationService = Depends(get_translation_service),
) -> list[dict]:
    """List all project glossary entries."""
    return svc.get_glossary()

@router.post("/glossary")
async def save_glossary_entry(
    body: GlossaryEntryRequest,
    svc: TranslationService = Depends(get_translation_service),
) -> dict:
    """Create or update a glossary entry."""
    return svc.save_glossary_entry(
        term=body.term,
        translations=body.translations,
        notes=body.notes,
    )
```

**3. Register the new router in `app.py`**

Add to `src/showrunner_tool/server/app.py`:
```python
from showrunner_tool.server.routers import translation as translation_router
# ...
app.include_router(translation_router.router)  # Phase H
```

**4. Add DI provider to `deps.py`**

```python
from showrunner_tool.services.translation_service import TranslationService

def get_translation_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    context_engine: ContextEngine = Depends(get_context_engine),
    agent_dispatcher: AgentDispatcher = Depends(get_agent_dispatcher),
) -> TranslationService:
    return TranslationService(kg_service, context_engine, agent_dispatcher)
```

### Frontend

**5. Create `src/web/src/components/translation/TranslationPanel.tsx`**

A standalone translation UI panel:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🌐 Translation                                                  │
│ Source: [English ▼]    Target: [Japanese ▼]    Confidence: 0.88 │
├────────────────────────────┬────────────────────────────────────┤
│ Source Text                │ Translation                        │
│                            │                                    │
│ The marketplace hummed     │ 市場は活気に満ちていた。ザラが      │
│ with activity as Zara      │ 商人の屋台に近づくと、              │
│ approached the merchant's  │ スパイスの香りが漂ってきた。        │
│ stall, the scent of        │                                    │
│ spices lingering in the    │                                    │
│ air.                       │                                    │
│                            │                                    │
│ [Paste or type source text]│ [Editable translated output]       │
├────────────────────────────┴────────────────────────────────────┤
│ Characters: [Select characters ▼]  Scene: [Select scene ▼]     │
│                                                                  │
│ [🌐 Translate]                         [Save Translation]       │
├─────────────────────────────────────────────────────────────────┤
│ 📝 Adaptation Notes                                             │
│  • "raining cats and dogs" → "バケツをひっくり返したような雨"    │
│    Reason: English idiom replaced with Japanese equivalent       │
│                                                                  │
│ 🚩 Cultural Flags                                               │
│  • Paragraph 2: "Thumbs up" gesture — preserved (Western setting)│
│                                                                  │
│ 📖 Glossary Applied: Obsidian Blade → 黒曜石の刃                │
└─────────────────────────────────────────────────────────────────┘
```

Implementation:
- Two-column layout: source text (textarea) on left, translated output on right
- Language selector dropdowns (common languages: English, Japanese, Korean, Chinese, Spanish, French, German)
- Character selector: multi-select dropdown of project characters (load from `api.getCharacters()`)
- Scene selector: optional scene for context (load from store)
- "Translate" button: calls `POST /api/v1/translation/translate`
- "Save Translation" button: stores translated text as `attributes.text_{target_lang}` on the selected container
- Adaptation notes section: collapsible, shows original → adapted with reasoning
- Cultural flags section: collapsible, color-coded by action_taken
- Glossary applied section: table showing source → target term mappings
- Confidence score: colored indicator (green ≥0.8, amber 0.6-0.8, red <0.6)
- Loading state: spinner on Translate button, skeleton on output panel

**6. Create `src/web/src/app/translation/page.tsx`**

New page at `/translation`:
```tsx
import { TranslationPanel } from "@/components/translation/TranslationPanel";

export default function TranslationPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <a href="/dashboard" className="text-gray-500 hover:text-gray-300">← Dashboard</a>
          <h1 className="text-2xl font-bold">Translation Studio</h1>
        </div>
        <TranslationPanel />
      </div>
    </div>
  );
}
```

**7. Add Translation nav link in Canvas.tsx**

Add a "Translation" link to the nav header in `src/web/src/components/workbench/Canvas.tsx`, after "Brainstorm":
```tsx
<a href="/translation" className="px-3 py-1 text-xs font-medium rounded-md transition-colors text-gray-500 hover:text-gray-300">
  🌐 Translation
</a>
```

---

## Feature 2: NL Pipeline Wizard

The backend is **already fully implemented** — `PipelineService.generate_pipeline_from_nl()` (120+ lines) and `POST /api/pipeline/definitions/generate` endpoint exist. This feature only needs the frontend wizard.

### Frontend

**8. Create `src/web/src/components/pipeline-builder/NLPipelineWizard.tsx`**

A modal wizard for creating pipelines from natural language:

```
┌─────────────────────────────────────────────────────────────────┐
│ ✨ Create Pipeline from Description                   [✕]       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Pipeline Name:                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Scene to Panels Pipeline                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Describe your workflow:                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Take a scene's text content, gather the character profiles  │ │
│ │ and world context, assemble everything into a prompt, let   │ │
│ │ me review the prompt before sending to the LLM, then        │ │
│ │ generate panel descriptions and save them to the scene.     │ │
│ │                                                             │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ 💡 Examples:                                                    │
│   • "Research a topic, summarize findings, then draft prose"    │
│   • "Gather character DNA, generate dialogue, review, save"     │
│   • "Outline a chapter, expand each beat, check style"          │
│                                                                  │
│                                           [✨ Generate Pipeline] │
├─────────────────────────────────────────────────────────────────┤
│ ✅ Generated! 5 steps, 4 edges                                  │
│                                                                  │
│ gather_buckets → prompt_template → review_prompt →              │
│ llm_generate → save_to_bucket                                   │
│                                                                  │
│              [Open in Builder]            [Discard]              │
└─────────────────────────────────────────────────────────────────┘
```

Implementation:
- Modal component with `isOpen` / `onClose` props
- Two inputs: Pipeline Name (text) and Description (textarea)
- Example prompts section (3-4 clickable examples that fill the textarea)
- "Generate Pipeline" button → calls `POST /api/pipeline/definitions/generate` with `{ intent, title }`
- Loading state: spinner, "Generating pipeline..." message
- Success state: shows step count + edge count, simplified flow visualization (step labels joined by arrows)
- "Open in Builder" button → calls `loadDefinition(id)` from `usePipelineBuilderStore` and closes the modal
- "Discard" button → deletes the definition via `api.deletePipelineDefinition(id)` and closes
- Error handling: show error toast if generation fails (422 from backend)

**9. Add "Create from Description" button to Pipelines page**

Update `src/web/src/app/pipelines/page.tsx` to add the wizard trigger:

```tsx
const [showNLWizard, setShowNLWizard] = useState(false);

// In the header buttons area (near the existing "New Pipeline" button):
<button
  onClick={() => setShowNLWizard(true)}
  className="flex items-center gap-2 px-3 py-2 bg-purple-600/20 text-purple-300 rounded-lg hover:bg-purple-600/30 border border-purple-500/30 transition-colors text-sm"
>
  <Sparkles className="w-4 h-4" />
  Create from Description
</button>

// At the bottom of the page:
<NLPipelineWizard
  isOpen={showNLWizard}
  onClose={() => setShowNLWizard(false)}
  onCreated={(definitionId) => {
    loadDefinitions();
    loadDefinition(definitionId);
    setShowGallery(false);
    setShowNLWizard(false);
    toast.success("Pipeline created from description!");
  }}
/>
```

**10. Add API client methods to `api.ts`**

```typescript
// Translation
translateText: (body: {
  text: string;
  source_language?: string;
  target_language?: string;
  character_ids?: string[];
  scene_id?: string;
}) =>
  post<TranslateResponse>("/api/v1/translation/translate", body),
getGlossary: () =>
  request<GlossaryEntry[]>("/api/v1/translation/glossary"),
saveGlossaryEntry: (body: { term: string; translations: Record<string, string>; notes?: string }) =>
  post<GlossaryEntry>("/api/v1/translation/glossary", body),

// NL Pipeline Generation
generatePipelineFromNL: (body: { intent: string; title: string }) =>
  post<PipelineDefinitionResponse>("/api/pipeline/definitions/generate", body),
```

Add interfaces:
```typescript
export interface AdaptationNote {
  original: string;
  adapted: string;
  reason: string;
}

export interface CulturalFlag {
  location: string;
  flag: string;
  action_taken: string;
}

export interface TranslateResponse {
  translated_text: string;
  source_language: string;
  target_language: string;
  adaptation_notes: AdaptationNote[];
  cultural_flags: CulturalFlag[];
  glossary_applied: Record<string, string>;
  confidence: number;
}

export interface GlossaryEntry {
  id: string;
  term: string;
  translations: Record<string, string>;
  notes: string;
}
```

---

## Output Specification

Provide the complete code for:
1. `src/showrunner_tool/services/translation_service.py` (new file)
2. `src/showrunner_tool/server/routers/translation.py` (new file — new router)
3. Updates to `src/showrunner_tool/server/app.py` (register translation router)
4. Updates to `src/showrunner_tool/server/deps.py` (add translation provider)
5. `src/web/src/components/translation/TranslationPanel.tsx` (new file)
6. `src/web/src/app/translation/page.tsx` (new file — Translation Studio page)
7. `src/web/src/components/pipeline-builder/NLPipelineWizard.tsx` (new file)
8. Updates to `src/web/src/app/pipelines/page.tsx` (add "Create from Description" button + wizard modal)
9. Updates to `src/web/src/components/workbench/Canvas.tsx` (add Translation nav link)
10. Updates to `src/web/src/lib/api.ts` (add translation + NL pipeline methods + interfaces)

---

## Important Notes

- **A parallel session is implementing Continuity Auto-Check + Style Enforcer (Session 27).** Do NOT modify `analysis.py` router, `analysis_service.py`, `ContextSidebar.tsx`, `SlashCommandList.tsx`, `ZenEditor.tsx`, or `PromptReviewModal.tsx`.
- The NL→DAG backend is **already fully implemented** in `pipeline_service.py` and `pipeline.py`. Do NOT modify these backend files. Only build the frontend wizard.
- The `translator_agent` skill expects JSON with `{ source_text, source_language, target_language, character_profiles, glossary }` — match this format.
- Translation is a **new router** (`translation.py`) with its own prefix `/api/v1/translation` — do NOT add endpoints to `analysis.py`.
- Use `toast.success()` / `toast.error()` from `sonner`.
- Use icons from `lucide-react`: `Globe`, `Languages`, `Sparkles`, `BookOpen`, `Flag`, `ChevronDown`, `ChevronUp`, `Save`.
- Follow dark theme styling (bg-gray-900/950, border-gray-800, text-gray-300).
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles.
