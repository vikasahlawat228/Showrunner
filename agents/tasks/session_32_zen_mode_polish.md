# Session 32: Zen Mode Polish — Word Count, Focus Mode, Reading Stats

## Context

You are working on **Showrunner**, a Next.js 14 + FastAPI platform for AI-assisted manga/manhwa creation. The Zen Mode writing editor (`ZenEditor.tsx`, 432 lines) is the primary writing surface. It already has TipTap rich text editing, semantic @mentions, /slash commands, debounced auto-save, entity detection, and a 4-tab context sidebar.

This session adds polish features that make Zen Mode feel like a professional writing tool:
1. **Word count + reading time** — Real-time word/character count with reading time estimate in the status bar
2. **Focus mode** — Distraction-free writing mode that dims everything except the current paragraph
3. **Session writing stats** — Track words written in this session, show progress
4. **Keyboard shortcuts overlay** — Help modal showing all available shortcuts
5. **Backend word count tracking** — Fragment save response includes word_count field

## Architecture

- **Frontend**: Next.js 14 App Router + Tailwind CSS + Zustand
- **Backend**: FastAPI, Python 3.12
- **Editor**: TipTap (ProseMirror) — `@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-mention`, `@tiptap/extension-placeholder`
- **No new npm packages needed** (all features use built-in TipTap/React capabilities)

## Feature 1: Word Count + Reading Time

### Modify `src/web/src/components/zen/ZenEditor.tsx`

Add a real-time word count and reading time display to the toolbar/status bar area.

**Implementation:**

1. Add a `useMemo` or `useState` to track word count from editor content:
```typescript
const [wordCount, setWordCount] = useState(0);
const [charCount, setCharCount] = useState(0);
```

2. Update these counts in the `onUpdate` callback of `useEditor` (already exists at line ~253):
```typescript
onUpdate: ({ editor }) => {
    const text = editor.getText();
    // Update word count
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    setWordCount(words);
    setCharCount(text.length);
    // ... existing debounce logic ...
}
```

3. Add a reading time estimate:
```typescript
const readingTime = Math.max(1, Math.ceil(wordCount / 250)); // 250 wpm average
```

4. Display in the toolbar area (right side, next to the save status). Add between the detecting/saving indicators and the Save button:
```tsx
<div className="flex items-center gap-2 text-[11px] text-gray-600 border-r border-gray-800 pr-3 mr-1">
    <span>{wordCount.toLocaleString()} words</span>
    <span className="text-gray-700">|</span>
    <span>{charCount.toLocaleString()} chars</span>
    <span className="text-gray-700">|</span>
    <span>~{readingTime} min read</span>
</div>
```

## Feature 2: Focus Mode (Typewriter Mode)

### Modify `src/web/src/components/zen/ZenEditor.tsx`

Add a distraction-free focus mode that:
- Dims all paragraphs except the one currently being edited
- Hides the toolbar
- Centers the active paragraph vertically (typewriter scrolling)

**Implementation:**

1. Add focus mode state to the component:
```typescript
const [focusMode, setFocusMode] = useState(false);
```

2. Add a toggle button in the toolbar (right side):
```tsx
<button
    onClick={() => setFocusMode(!focusMode)}
    className={`p-1 rounded transition-colors ${
        focusMode
            ? 'bg-indigo-600/30 text-indigo-300'
            : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'
    }`}
    title={focusMode ? "Exit focus mode (⌘⇧F)" : "Focus mode (⌘⇧F)"}
>
    <Focus className="w-3.5 h-3.5" />
</button>
```

3. Import `Focus` from lucide-react (the icon for focus mode).

4. Add keyboard shortcut `Cmd+Shift+F` to toggle focus mode in the existing keydown handler:
```typescript
if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'f') {
    e.preventDefault();
    setFocusMode(prev => !prev);
}
```

5. Apply CSS classes when focus mode is active. On the editor wrapper div (the one with `flex-1 overflow-y-auto`):
```tsx
<div className={`flex-1 overflow-y-auto px-6 lg:px-16 xl:px-24 2xl:px-32 ${
    focusMode ? 'zen-focus-mode' : ''
}`}>
```

6. When focus mode is active, conditionally hide the toolbar:
```tsx
{!focusMode && (
    <div className="flex items-center justify-between px-6 py-2 border-b border-gray-800/60">
        {/* existing toolbar content */}
    </div>
)}
```

7. Add a minimal floating status bar at the bottom when in focus mode (so user can still see word count):
```tsx
{focusMode && (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40
        bg-gray-900/90 backdrop-blur-sm border border-gray-800 rounded-full
        px-4 py-1.5 flex items-center gap-4 text-[11px] text-gray-500
        opacity-0 hover:opacity-100 transition-opacity duration-300">
        <span>{wordCount.toLocaleString()} words</span>
        <span>~{readingTime} min</span>
        <button
            onClick={() => setFocusMode(false)}
            className="text-gray-600 hover:text-gray-300 ml-1"
        >
            Exit Focus
        </button>
    </div>
)}
```

### Add CSS for focus mode

Add to the `src/web/src/app/globals.css` file (within the existing styles):

```css
/* Zen Focus Mode — dims non-active paragraphs */
.zen-focus-mode .ProseMirror > * {
    opacity: 0.25;
    transition: opacity 0.3s ease;
}

.zen-focus-mode .ProseMirror > *.has-focus,
.zen-focus-mode .ProseMirror > *:focus,
.zen-focus-mode .ProseMirror > *:has(.ProseMirror-focused) {
    opacity: 1;
}

/* Use :has() selector for the parent of the cursor position */
.zen-focus-mode .ProseMirror > .is-active,
.zen-focus-mode .ProseMirror:focus-within > .has-focus {
    opacity: 1;
}
```

**Note on ProseMirror focus detection:** TipTap/ProseMirror doesn't natively add a "focused paragraph" class. We need to use the editor's `onSelectionUpdate` to manually add a class to the active node:

```typescript
// In useEditor config, add onSelectionUpdate:
onSelectionUpdate: ({ editor }) => {
    if (!focusMode) return;
    // Remove previous active marks
    const editorEl = document.querySelector('.ProseMirror');
    editorEl?.querySelectorAll('.is-active').forEach(el => el.classList.remove('is-active'));
    // Mark the current block
    const { $from } = editor.state.selection;
    const pos = $from.before(1);
    const dom = editor.view.nodeDOM(pos);
    if (dom instanceof HTMLElement) {
        dom.classList.add('is-active');
    }
},
```

## Feature 3: Session Writing Stats

### Modify `src/web/src/lib/store/zenSlice.ts`

Add session writing stats to the Zen store:

**New state fields:**
```typescript
// Session stats
sessionStartWordCount: number;
sessionWordsWritten: number;
sessionStartTime: Date | null;
```

**New actions:**
```typescript
setSessionStartWordCount: (count: number) => void;
updateSessionWords: (currentWordCount: number) => void;
startSession: () => void;
```

**Implementation in the store:**
```typescript
sessionStartWordCount: 0,
sessionWordsWritten: 0,
sessionStartTime: null,

setSessionStartWordCount: (count) => set({ sessionStartWordCount: count }),

updateSessionWords: (currentWordCount) => {
    const start = get().sessionStartWordCount;
    set({ sessionWordsWritten: Math.max(0, currentWordCount - start) });
},

startSession: () => set({
    sessionStartTime: new Date(),
    sessionStartWordCount: 0,
    sessionWordsWritten: 0,
}),
```

### Modify `src/web/src/components/zen/ZenEditor.tsx`

1. Pull `sessionWordsWritten`, `updateSessionWords`, `setSessionStartWordCount`, `sessionStartTime`, `startSession` from `useZenStore`.

2. On first text content (when editor first gets content and sessionStartWordCount is 0):
```typescript
useEffect(() => {
    if (wordCount > 0 && !useZenStore.getState().sessionStartTime) {
        useZenStore.getState().startSession();
        useZenStore.getState().setSessionStartWordCount(wordCount);
    }
}, [wordCount]);
```

3. Update session words on every word count change:
```typescript
useEffect(() => {
    useZenStore.getState().updateSessionWords(wordCount);
}, [wordCount]);
```

4. Display session stats in the status bar (or the floating focus bar):
```tsx
{sessionWordsWritten > 0 && (
    <span className="text-emerald-500/80">
        +{sessionWordsWritten} this session
    </span>
)}
```

## Feature 4: Keyboard Shortcuts Overlay

### Modify `src/web/src/components/zen/ZenEditor.tsx`

Add a keyboard shortcuts help overlay (triggered by `Cmd+/` or `?` key).

**State:**
```typescript
const [showShortcuts, setShowShortcuts] = useState(false);
```

**Keyboard handler (add to existing keydown listener):**
```typescript
if ((e.metaKey || e.ctrlKey) && e.key === '/') {
    e.preventDefault();
    setShowShortcuts(prev => !prev);
}
```

**Overlay component (render at the end of ZenEditor):**
```tsx
{showShortcuts && (
    <div
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center"
        onClick={() => setShowShortcuts(false)}
    >
        <div
            className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl"
            onClick={e => e.stopPropagation()}
        >
            <h3 className="text-sm font-semibold text-white mb-4">Keyboard Shortcuts</h3>
            <div className="space-y-3">
                {[
                    { keys: '⌘S', desc: 'Save fragment' },
                    { keys: '⌘⇧F', desc: 'Toggle focus mode' },
                    { keys: '⌘/', desc: 'Show shortcuts' },
                    { keys: '@', desc: 'Mention a character, location, or scene' },
                    { keys: '/', desc: 'Slash commands (AI actions)' },
                    { keys: '⌘B', desc: 'Bold' },
                    { keys: '⌘I', desc: 'Italic' },
                    { keys: '⌘⇧7', desc: 'Ordered list' },
                    { keys: '⌘⇧8', desc: 'Bullet list' },
                ].map(({ keys, desc }) => (
                    <div key={keys} className="flex items-center justify-between">
                        <span className="text-sm text-gray-400">{desc}</span>
                        <kbd className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-xs text-gray-300 font-mono">
                            {keys}
                        </kbd>
                    </div>
                ))}
            </div>
            <button
                onClick={() => setShowShortcuts(false)}
                className="mt-4 w-full py-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
                Press Escape or ⌘/ to close
            </button>
        </div>
    </div>
)}
```

## Feature 5: Backend Word Count Tracking

### Modify `src/antigravity_tool/services/writing_service.py`

In the `save_fragment` method (or wherever fragments are saved), compute and store word_count:

```python
# Compute word count
word_count = len(text.split()) if text.strip() else 0

# Store in fragment attributes
attrs = {"text": text, "word_count": word_count}
if title:
    attrs["title"] = title
```

Ensure the `word_count` is included in the saved fragment's attributes dict.

### Modify `src/antigravity_tool/server/routers/writing.py`

Ensure the response from `save_fragment` includes `word_count`. If `FragmentResponse` doesn't already have it, add it.

### Modify `src/antigravity_tool/server/api_schemas.py`

Add `word_count` field to `FragmentResponse`:
```python
class FragmentResponse(BaseModel):
    id: str
    text: str
    title: str | None = None
    detected_entities: list[EntityDetection] = []
    word_count: int = 0
```

### Modify `src/web/src/lib/api.ts`

Update the `FragmentResponse` interface to include `word_count`:
```typescript
export interface FragmentResponse {
    id: string;
    text: string;
    title?: string;
    detected_entities: EntityDetection[];
    word_count: number;
}
```

## Modify `src/web/src/app/zen/page.tsx`

Remove the local nav header (lines 28-63) since Session 30 adds a persistent Navbar. If Session 30 hasn't been applied yet, simplify the header to just show "Zen Mode" without redundant page links:

**Replace the header section** with a simpler one:
```tsx
<header className="flex items-center justify-between px-4 py-2 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-sm shrink-0">
    <div className="flex items-center gap-2">
        <Feather className="w-4 h-4 text-indigo-400" />
        <span className="text-sm font-semibold text-gray-200">Zen Mode</span>
    </div>
</header>
```

Remove the `<nav>` section with Canvas/Zen Mode/Schemas links (these will be in the global Navbar).

## Files Summary

### Files to MODIFY:
1. `src/web/src/components/zen/ZenEditor.tsx` — Word count, focus mode, session stats, shortcuts overlay
2. `src/web/src/lib/store/zenSlice.ts` — Session writing stats state + actions
3. `src/web/src/app/zen/page.tsx` — Simplify header (remove redundant nav links)
4. `src/web/src/app/globals.css` — Focus mode CSS for paragraph dimming
5. `src/antigravity_tool/services/writing_service.py` — Compute word_count on save
6. `src/antigravity_tool/server/routers/writing.py` — Include word_count in response
7. `src/antigravity_tool/server/api_schemas.py` — Add word_count to FragmentResponse
8. `src/web/src/lib/api.ts` — Update FragmentResponse interface with word_count

### Files you must NOT modify:
- `src/web/src/app/layout.tsx` (modified by parallel session 30)
- `src/web/src/components/workbench/Canvas.tsx` (modified by parallel session 30)
- `src/web/src/components/command-center/*` (modified by parallel session 31)
- `src/antigravity_tool/services/export_service.py` (modified by parallel session 31)
- `src/antigravity_tool/server/routers/export.py` (modified by parallel session 31)
- `src/web/src/components/ui/Navbar.tsx` (may not exist yet)
- `src/web/src/components/ui/CommandPalette.tsx` (may not exist yet)
- `src/web/src/components/ui/ExportModal.tsx` (may not exist yet)

## Existing Code Reference

### Current ZenEditor.tsx structure (432 lines):
- Lines 1-21: Imports (TipTap, Mention, SlashCommandList, zustand, lucide)
- Lines 25-80: `createMentionSuggestion()` — semantic search via `api.semanticSearchContainers()`
- Lines 82-212: `createSlashSuggestion()` — slash commands dispatching to backend agents
- Lines 216-363: `ZenEditor` component:
  - `useZenStore()` for save/detect state
  - `useEditor()` with StarterKit, Placeholder, Mention (2x: @mentions + /slash)
  - `onUpdate` with 3s auto-save debounce + 1.5s entity detection debounce
  - `Cmd+S` keyboard shortcut handler
  - Translation event handlers (zen:replace, zen:insertBelow)
  - Toolbar: B/I/H2/H3/❝/• buttons + save status + Save button
  - Editor surface: `EditorContent` with `prose prose-invert prose-lg`
- Lines 366-421: `EditorToolbar` component
- Lines 425-432: `formatTime` helper

### Current zenSlice.ts structure (201 lines):
- `ContextEntry` interface (7 fields)
- `ZenSlice` interface (15 state fields + 10 actions)
- `useZenStore` create: all state + action implementations
- Key actions: `saveFragment`, `detectEntities`, `fetchContext`, `searchContainers`
- Sidebar tabs: `activeSidebarTab: "context" | "continuity" | "style" | "translation"`

### Current zen/page.tsx structure (87 lines):
- Imports ZenEditor, ContextSidebar, StoryboardStrip, InlineTranslation
- Header with "Back to Dashboard" link + redundant nav tabs (Canvas, Zen, Schemas)
- Main area: ZenEditor + ContextSidebar side-by-side
- Translation overlay at bottom (conditionally shown)
- StoryboardStrip at very bottom

## Acceptance Criteria

1. **Word count displays in real-time** — As you type, the word count, character count, and reading time update instantly in the toolbar
2. **Focus mode works** — Press Cmd+Shift+F → toolbar hides, all paragraphs except current one dim to 25% opacity, floating status bar appears at bottom (hidden until hover)
3. **Focus mode dims correctly** — Only the paragraph containing the cursor is fully opaque; typing in a new paragraph correctly moves the focus
4. **Session stats track** — Shows "+N words this session" in emerald green once you've written new words
5. **Keyboard shortcuts overlay** — Press Cmd+/ → overlay shows all shortcuts. Press Escape or Cmd+/ again to close.
6. **Backend word count** — `POST /api/v1/writing/fragments` response now includes `word_count` integer
7. **Zen page header simplified** — No more redundant Canvas/Schemas nav links in the Zen page header
8. **No regressions** — @mentions, /slash commands, auto-save, entity detection, context sidebar all still work correctly

## Technical Notes

- The focus mode CSS relies on ProseMirror's DOM structure where top-level paragraphs are direct children of `.ProseMirror`. The `is-active` class is manually applied via `onSelectionUpdate`.
- `onSelectionUpdate` fires on every cursor movement — keep the DOM manipulation minimal (classList.add/remove only).
- The session word tracking starts counting from the first text the editor has (not from 0), so opening an existing document with 500 words and writing 100 more shows "+100 this session".
- The floating status bar in focus mode uses `opacity-0 hover:opacity-100` so it's invisible by default but appears when the user moves their mouse to the bottom of the screen.
- Word count computation: `text.trim().split(/\s+/).length` handles multiple spaces correctly. Use `text.trim() ? ... : 0` to handle empty documents.
