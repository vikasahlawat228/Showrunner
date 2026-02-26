# Session 29: Zen Mode Semantic @Mentions + /translate Slash Command

**Goal**: Upgrade Zen Mode's @mention search to use semantic (vector) search instead of keyword matching, and add a `/translate` slash command that opens an inline translation panel.

**Context**:
Showrunner is a CLI + FastAPI + Next.js platform for AI-assisted manga/manhwa creation. The Zen Mode editor has TipTap with @mentions (using `api.searchContainers()` which does keyword search) and slash commands. The Knowledge Graph already has ChromaDB semantic search wired via `kg_service.semantic_search()`. A separate Translation router exists at `/api/v1/translation/translate` (built in Session 28).

**Prerequisites**: Sessions 27 and 28 must be complete before this session. This session integrates their features into Zen Mode.

**Read these files first** (essential context):
- `src/web/src/components/zen/ZenEditor.tsx` — TipTap editor with @mentions and slash commands (381+ lines)
- `src/web/src/components/zen/MentionList.tsx` — Mention suggestion dropdown
- `src/web/src/components/zen/SlashCommandList.tsx` — Slash command registry (161+ lines, may have /check-style from Session 27)
- `src/web/src/components/zen/ContextSidebar.tsx` — May have Continuity + Style tabs from Session 27
- `src/showrunner_tool/server/routers/writing.py` — Writing router endpoints
- `src/showrunner_tool/services/writing_service.py` — WritingService with search methods
- `src/showrunner_tool/services/knowledge_graph_service.py` — Has `semantic_search()` method
- `src/showrunner_tool/server/routers/graph.py` — Has `GET /search?q=` (semantic search endpoint)
- `src/web/src/lib/api.ts` — API client (may have translation methods from Session 28)
- `src/web/src/lib/store/zenSlice.ts` — Zen Mode store
- `src/web/src/components/translation/TranslationPanel.tsx` — Translation panel (from Session 28)

---

## Feature 1: Semantic @Mentions

### Backend

**1. Add semantic search endpoint to writing router**

Add to `src/showrunner_tool/server/routers/writing.py`:

```python
@router.get("/semantic-search")
async def semantic_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
):
    """Semantic search for containers using vector similarity.

    Returns enriched results with container metadata, ordered by relevance.
    Used by Zen Mode @mentions for smarter entity suggestions.
    """
    results = kg_service.semantic_search(q, limit=limit)
    return results
```

This reuses the existing `kg_service.semantic_search()` which already:
- Embeds the query via LiteLLM (text-embedding-004)
- Queries ChromaDB for closest vectors
- Enriches results with SQLite metadata (name, container_type, attributes)

### Frontend

**2. Update @mention suggestion in ZenEditor.tsx**

Currently in `createMentionSuggestion()`:
```tsx
const results = await api.searchContainers(query, 8);
```

Change to:
```tsx
const results = await api.semanticSearchContainers(query, 8);
```

The `semanticSearchContainers` method calls the new `/api/v1/writing/semantic-search` endpoint.

**3. Update MentionList to show relevance indicator**

In `MentionList.tsx`, if the search result includes a `distance` or `similarity` field, show a subtle relevance indicator:

```tsx
// In each mention item, add a subtle relevance dot:
{item.similarity && (
  <span
    className={`w-1.5 h-1.5 rounded-full ${
      item.similarity > 0.8 ? "bg-green-400" :
      item.similarity > 0.5 ? "bg-amber-400" : "bg-gray-500"
    }`}
    title={`Relevance: ${(item.similarity * 100).toFixed(0)}%`}
  />
)}
```

**4. Add API method**

```typescript
semanticSearchContainers: (q: string, limit?: number) =>
  request<ContainerSearchResult[]>(
    `/api/v1/writing/semantic-search?q=${encodeURIComponent(q)}&limit=${limit || 8}`
  ),
```

---

## Feature 2: /translate Slash Command

### Frontend

**5. Add /translate slash command**

Add to `SLASH_COMMANDS` array in `SlashCommandList.tsx`:

```tsx
{
    id: "translate",
    label: "Translate",
    description: "Translate selected text to another language",
    icon: <Globe className="w-4 h-4 text-emerald-400" />,
    action: "translate",
},
```

Import `Globe` from `lucide-react`.

**6. Handle translate action in ZenEditor.tsx**

When the "translate" slash command is triggered:

1. Get the current selection or the entire editor content
2. Open an inline translation modal/panel below the editor
3. The panel uses the TranslationPanel component (from Session 28) in a compact mode:
   - Pre-fills the source text from the editor selection
   - Language selector (source + target)
   - "Translate" button → calls `api.translateText()`
   - Shows translated output
   - "Replace" button → replaces the selected text with the translation in the editor
   - "Insert Below" button → inserts the translation after the selection
   - "Close" button

Implementation approach:
```tsx
// Add state for inline translation:
const [showTranslation, setShowTranslation] = useState(false);
const [translationSource, setTranslationSource] = useState("");

// In the slash command handler (where action === "translate"):
case "translate": {
    const selection = editor?.state.selection;
    const selectedText = editor?.state.doc.textBetween(
        selection?.from || 0,
        selection?.to || editor.state.doc.content.size,
        "\n"
    );
    setTranslationSource(selectedText || editor?.getText() || "");
    setShowTranslation(true);
    break;
}
```

**7. Create `src/web/src/components/zen/InlineTranslation.tsx`**

A compact inline translation widget for Zen Mode:

```
┌───────────────────────────────────────────────────┐
│ 🌐 Translate    Source: [English ▼] → [Japanese ▼]│
├───────────────────────────────────────────────────┤
│ "The marketplace hummed with activity..."          │
│                                                    │
│ ↓ Translation (confidence: 0.92)                  │
│                                                    │
│ "市場は活気に満ちていた…"                          │
│                                                    │
│ [Replace Selection] [Insert Below] [Close]         │
│                                                    │
│ ▸ Adaptation Notes (2)                            │
│ ▸ Cultural Flags (1)                              │
└───────────────────────────────────────────────────┘
```

Props:
```tsx
interface InlineTranslationProps {
    sourceText: string;
    onReplace: (translatedText: string) => void;  // Replace selection in editor
    onInsertBelow: (translatedText: string) => void;  // Insert after selection
    onClose: () => void;
}
```

Implementation:
- Compact single-column layout (sits below the editor or in a floating panel)
- Source language + target language dropdowns (default: English → Japanese)
- Auto-translates on mount (if source text is short <500 chars) or shows "Translate" button
- Shows translated text in a styled output area
- "Replace Selection" → calls `onReplace(translated)` which uses `editor.commands.insertContent()`
- "Insert Below" → calls `onInsertBelow(translated)` which moves cursor to end of selection and inserts
- Collapsible adaptation notes and cultural flags sections
- Loading state with spinner
- Error state with retry button

**8. Integrate into Zen page layout**

In `src/web/src/app/zen/page.tsx`, render the InlineTranslation component when `showTranslation` is true, positioned below the editor area.

---

## Feature 3: Add Translation tab to ContextSidebar

**9. Add Translation tab to ContextSidebar**

Session 27 adds "Context | Continuity | Style" tabs. This session adds a "Translation" tab:

```tsx
type SidebarTab = "context" | "continuity" | "style" | "translation";

// Add tab button:
<button
  onClick={() => setActiveTab("translation")}
  className={`px-2 py-1 text-xs rounded ${activeTab === "translation" ? "bg-indigo-600/30 text-white" : "text-gray-500"}`}
>
  🌐 Translate
</button>

// Render:
{activeTab === "translation" && (
  <div className="p-3">
    <InlineTranslation
      sourceText={currentText}
      onReplace={(text) => { /* update editor */ }}
      onInsertBelow={(text) => { /* insert in editor */ }}
      onClose={() => setActiveTab("context")}
    />
  </div>
)}
```

---

## Output Specification

Provide the complete code for:
1. Updates to `src/showrunner_tool/server/routers/writing.py` (add semantic-search endpoint)
2. Updates to `src/web/src/components/zen/ZenEditor.tsx` (semantic @mentions + translate action handler)
3. Updates to `src/web/src/components/zen/MentionList.tsx` (relevance indicator)
4. Updates to `src/web/src/components/zen/SlashCommandList.tsx` (add /translate command)
5. `src/web/src/components/zen/InlineTranslation.tsx` (new file — compact translation widget)
6. Updates to `src/web/src/components/zen/ContextSidebar.tsx` (add Translation tab — extend Session 27's tab system)
7. Updates to `src/web/src/app/zen/page.tsx` (integrate InlineTranslation)
8. Updates to `src/web/src/lib/api.ts` (add semanticSearchContainers method)

---

## Important Notes

- **Sessions 27 and 28 must be complete before this session runs.** This session builds on their work:
  - Session 27 adds tabs to ContextSidebar (Context | Continuity | Style) — extend with Translation tab
  - Session 27 adds /check-style to SlashCommandList — add /translate alongside it
  - Session 28 creates `TranslationPanel.tsx` and the `/api/v1/translation/translate` endpoint — reuse the API
- Do NOT recreate translation backend or TranslationPanel — they already exist from Session 28
- The semantic search endpoint reuses `kg_service.semantic_search()` which uses ChromaDB + LiteLLM embeddings
- `MentionItem` interface may need a `similarity?: number` field added
- Use `toast.success()` / `toast.error()` from `sonner`
- Use icons from `lucide-react`: `Globe`, `Replace`, `ArrowDown`, `X`
- Follow dark theme styling (bg-gray-900/950, border-gray-800, text-gray-300)
- Run `cd src/web && npx tsc --noEmit` to verify TypeScript compiles
