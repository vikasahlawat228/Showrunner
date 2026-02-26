# Prompt: Phase Next-B Session B — Character Voice Scorecard

**Goal**: Build a Character Voice Scorecard that analyzes dialogue patterns per character, detects when characters sound too similar, and surfaces voice metrics in the Character Inspector.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The codebase has 15 FastAPI routers, 24 services, and a Next.js frontend with 6 pages. Characters are stored as `GenericContainer` instances (and some legacy YAML). The Character Inspector in the Dashboard's right panel already shows identity, personality, DNA, arc, and relationships.

This session adds a Voice Scorecard feature: analyze all dialogue attributed to a character, compute stylometric metrics, and warn when two characters' voices are too similar.

**Read these files first** (essential context):
- `docs/LOW_LEVEL_DESIGN.md` §10 — Full detailed design for Phase Next-B (service, endpoints, components, DI)
- `docs/PRD.md` §13 — Phase Next-B description
- `src/showrunner_tool/server/deps.py` — Current dependency injection graph
- `src/showrunner_tool/server/app.py` — Router registration
- `src/showrunner_tool/server/api_schemas.py` — Existing API schema patterns
- `src/showrunner_tool/services/knowledge_graph_service.py` — KG queries
- `src/showrunner_tool/services/context_engine.py` — Context assembly
- `src/web/src/components/workbench/Inspector.tsx` — Inspector routing component
- `src/web/src/components/workbench/CharacterInspector.tsx` — Character detail view (add scorecard here)
- `src/web/src/lib/api.ts` — API client patterns
- `src/web/src/lib/store.ts` — Zustand store

---

## Required Actions

### Backend (Python)

**1. Create or extend `src/showrunner_tool/services/analysis_service.py`**

> **IMPORTANT:** A parallel session (Session A) is creating this file with `analyze_emotional_arc` and `compute_character_ribbons` methods. If the file already exists when you start, ADD your code to it. If it doesn't exist yet, create the file with your code and leave placeholder comments for Session A's methods.

Add the following to `AnalysisService`:

- Dataclasses:
  ```python
  @dataclass
  class VoiceProfile:
      character_id: str
      character_name: str
      avg_sentence_length: float
      vocabulary_diversity: float   # unique words / total words (0.0–1.0)
      formality_score: float        # 0.0 (casual) – 1.0 (formal)
      top_phrases: list[str]        # Most distinctive phrases (3-5)
      dialogue_sample_count: int

  @dataclass
  class VoiceScorecardResult:
      profiles: list[VoiceProfile]
      similarity_matrix: list[dict]  # [{ char_a, char_b, similarity: 0.0–1.0 }]
      warnings: list[str]            # "Zara and Kael sound 82% similar"
  ```

- Method: `async analyze_character_voices(character_ids: list[str] | None = None) -> VoiceScorecardResult`
  - Step 1: Get all characters via `KnowledgeGraphService.find_containers(container_type="character")`
  - Step 2: For each character, find all writing fragments where the character appears. Query the KG for fragments linked to scenes where the character is present.
  - Step 3: Extract dialogue text attributed to each character. If explicit dialogue attribution isn't available, use LLM (via litellm) to extract dialogue from prose fragments: prompt with "Extract all dialogue lines spoken by {character_name} from this text."
  - Step 4: For each character's collected dialogue:
    - `avg_sentence_length`: Split into sentences, count words per sentence, average
    - `vocabulary_diversity`: Count unique words / total words
    - `formality_score`: Use LLM to rate formality on a 0.0–1.0 scale
    - `top_phrases`: Use LLM to identify 3-5 distinctive phrases or verbal tics
  - Step 5: Compute similarity between every pair of character profiles:
    - Cosine similarity on normalized vector: [avg_sentence_length / 30, vocabulary_diversity, formality_score]
    - If similarity > 0.7, add to warnings list with suggestion
  - Step 6: Return `VoiceScorecardResult`

**2. Add endpoint to analysis router**

> If Session A already created `src/showrunner_tool/server/routers/analysis.py`, add to it. Otherwise, create it with prefix `/api/v1/analysis`, tags `["analysis"]`.

- `GET /voice-scorecard` — optional query param `character_ids: str | None = None` (comma-separated). Returns `VoiceScorecardResponse`.

Add Pydantic response models to `api_schemas.py`:

```python
class VoiceProfileResponse(BaseModel):
    character_id: str
    character_name: str
    avg_sentence_length: float
    vocabulary_diversity: float
    formality_score: float
    top_phrases: list[str]
    dialogue_sample_count: int

class VoiceScorecardResponse(BaseModel):
    profiles: list[VoiceProfileResponse]
    similarity_matrix: list[dict]
    warnings: list[str]
```

**3. Wire DI (if not already done by Session A)**

Add to `deps.py`:
```python
def get_analysis_service(
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
    container_repo: ContainerRepository = Depends(get_container_repo),
    context_engine: ContextEngine = Depends(get_context_engine),
) -> AnalysisService:
    return AnalysisService(kg_service, container_repo, context_engine)
```

**4. Register router in `app.py` (if not already done by Session A)**

### Frontend (TypeScript/React)

**5. Add API client method to `api.ts`**

```typescript
// Analysis — Voice Scorecard
getVoiceScorecard: (characterIds?: string[]) =>
  request<VoiceScorecardResponse>(
    characterIds
      ? `/api/v1/analysis/voice-scorecard?character_ids=${characterIds.join(",")}`
      : "/api/v1/analysis/voice-scorecard"
  ),
```

Add TypeScript interfaces:
```typescript
export interface VoiceProfile {
  character_id: string;
  character_name: string;
  avg_sentence_length: number;
  vocabulary_diversity: number;
  formality_score: number;
  top_phrases: string[];
  dialogue_sample_count: number;
}

export interface VoiceScorecardResponse {
  profiles: VoiceProfile[];
  similarity_matrix: Array<{ char_a: string; char_b: string; similarity: number }>;
  warnings: string[];
}
```

**6. Create `src/web/src/components/workbench/CharacterVoiceScorecard.tsx`**

Requirements:
- Receives `characterId: string` and `characterName: string` as props
- "Analyze Voice" button that calls `api.getVoiceScorecard([characterId])`
- Shows loading spinner during analysis (use `Loader2` from lucide-react)
- Renders a table with the voice metrics for the selected character:
  - Avg Sentence Length (with bar visualization, max ~30 words)
  - Vocabulary Diversity (percentage bar, 0–100%)
  - Formality Score (percentage bar, 0–100%, color gradient: casual=blue, formal=purple)
  - Top Phrases (as tags/chips)
  - Dialogue Sample Count
- If `similarity_matrix` contains entries involving this character, show warning cards:
  - "⚠️ Sounds 82% similar to Kael"
  - "Suggestion: Give [character] shorter, more abrupt sentences"
- Optionally, "Compare All Characters" button that calls without character_ids filter, showing a full comparison table
- Follow dark theme styling (bg-gray-900, border-gray-800, text-gray-300)
- Use `toast.success("Voice analysis complete")` / `toast.error()` from sonner

**7. Integrate into `CharacterInspector.tsx`**

Add a collapsible section at the bottom of the Character Inspector:
```tsx
{/* Voice Analysis */}
<div className="border-t border-gray-800 pt-3 mt-3">
  <CharacterVoiceScorecard
    characterId={character.id}
    characterName={character.name}
  />
</div>
```

---

## Output Specification

Provide the complete code for:
1. `src/showrunner_tool/services/analysis_service.py` — `VoiceProfile`, `VoiceScorecardResult` dataclasses + `analyze_character_voices` method (leave clear placeholders for Session A's methods if creating the file fresh)
2. `src/showrunner_tool/server/routers/analysis.py` — voice-scorecard endpoint (leave placeholders for Session A's endpoints if creating fresh)
3. Updates to `src/showrunner_tool/server/api_schemas.py` (add `VoiceProfileResponse`, `VoiceScorecardResponse`)
4. Updates to `src/showrunner_tool/server/deps.py` (add `get_analysis_service` if not present)
5. Updates to `src/showrunner_tool/server/app.py` (register analysis router if not present)
6. `src/web/src/components/workbench/CharacterVoiceScorecard.tsx` (new file)
7. Updates to `src/web/src/components/workbench/CharacterInspector.tsx` (integrate scorecard)
8. Updates to `src/web/src/lib/api.ts` (add method + interfaces)

---

## Important Notes

- **A parallel session (Session A) is implementing Emotional Arc + Story Ribbons.** It will also create/modify `AnalysisService` and the `analysis.py` router. Ensure your code merges cleanly by using clear section comments.
- **Do NOT modify** files outside the scope listed above. Specifically, do not touch `TimelineView.tsx`, `StoryRibbons.tsx`, or `EmotionalArcChart.tsx`.
- The LLM calls should use `litellm.completion()` — follow the pattern in `src/showrunner_tool/services/agent_dispatcher.py` for how LLM calls are made in this codebase.
- For dialogue extraction, be pragmatic: if fragments don't have explicit dialogue attribution, use simple heuristic first (text between quotation marks) and fall back to LLM extraction.
- Use `toast.success()` / `toast.error()` from `sonner` for user feedback.
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles cleanly.
- Run `python -c "from showrunner_tool.services.analysis_service import AnalysisService; print('OK')"` to verify Python imports.
