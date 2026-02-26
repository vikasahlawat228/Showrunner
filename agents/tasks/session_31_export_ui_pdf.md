# Session 31: Export UI Modal + HTML/Print-to-PDF Export

## Context

You are working on **Showrunner**, a Next.js 14 + FastAPI platform for AI-assisted manga/manhwa creation. The backend already has 3 export formats (Markdown, JSON bundle, Fountain screenplay) via `export_service.py` (224 lines) and `export.py` router (49 lines), but there is **zero frontend UI** for export. Users have no way to trigger exports from the web app.

This session adds:
1. **Export UI Modal** — A polished modal to select format, preview output, and download
2. **HTML export endpoint** — A styled HTML export that users can Print → Save as PDF from the browser
3. **Frontend API methods** — Wire all export endpoints to the API client
4. **Export trigger button** — Add an export button accessible from the Dashboard

## Architecture

- **Backend**: FastAPI, Python 3.12
- **Frontend**: Next.js 14 App Router + Tailwind CSS + Zustand
- **Styling**: Dark theme (gray-950 backgrounds, gray-800 borders, white/gray-300 text)
- **Icons**: lucide-react
- **Toasts**: sonner
- **No new Python dependencies required** (we use Python's built-in `html` module for HTML generation)

## Feature 1: HTML Export (Backend)

### Modify `src/showrunner_tool/services/export_service.py`

Add a new method `export_html() -> str` that renders the manuscript as a styled HTML document.

**Implementation:**
```python
def export_html(self) -> str:
    """Render the manuscript as a styled HTML document suitable for printing to PDF."""
    tree = self.kg_service.get_structure_tree("")
    body_lines: list[str] = []
    self._render_html_node(tree, body_lines)
    body_html = "\n".join(body_lines)
    return self._wrap_html(body_html)
```

**`_render_html_node`** — Recursive method similar to `_render_md_node` but outputting HTML:
- Season → `<h1 class="season">Season Name</h1>`
- Chapter → `<h2 class="chapter">Chapter Name</h2>`
- Scene → `<h3 class="scene">Scene Name</h3>` + `<div class="scene-divider"></div>`
- Fragment text → `<p class="prose">text</p>` (split by `\n\n` into paragraphs)

**`_wrap_html`** — Wrap body in a full HTML document with embedded CSS:
```python
def _wrap_html(self, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Manuscript Export</title>
    <style>
        @media print {{
            body {{ font-size: 12pt; }}
            .scene-divider {{ page-break-before: auto; }}
        }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 700px;
            margin: 2rem auto;
            padding: 0 1rem;
            line-height: 1.8;
            color: #1a1a1a;
            background: #fff;
        }}
        h1 {{ font-size: 2em; margin-top: 3em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; margin-top: 2em; color: #333; }}
        h3 {{ font-size: 1.2em; margin-top: 1.5em; color: #555; font-style: italic; }}
        .prose {{ text-indent: 2em; margin: 0.8em 0; }}
        .scene-divider {{ margin: 2em 0; border-top: 1px solid #ddd; }}
        .export-meta {{ color: #999; font-size: 0.8em; text-align: center; margin-bottom: 3em; }}
    </style>
</head>
<body>
    <div class="export-meta">Exported from Showrunner</div>
    {body}
</body>
</html>"""
```

### Modify `src/showrunner_tool/server/routers/export.py`

Add a new endpoint:

```python
@router.post("/html")
async def export_html(
    svc: ExportService = Depends(get_export_service),
):
    """Export the manuscript as a styled HTML document (print to PDF from browser)."""
    content = svc.export_html()
    return Response(
        content=content,
        media_type="text/html",
        headers={
            "Content-Disposition": 'attachment; filename="manuscript.html"',
        },
    )
```

Also add an **inline preview** endpoint (returns HTML without Content-Disposition for iframe preview):

```python
@router.post("/preview")
async def export_preview(
    svc: ExportService = Depends(get_export_service),
):
    """Return styled HTML manuscript for inline preview (no download header)."""
    content = svc.export_html()
    return Response(content=content, media_type="text/html")
```

## Feature 2: Frontend API Methods

### Modify `src/web/src/lib/api.ts`

Add export methods to the `api` object. These should be added **at the end** of the api object, just before the closing brace. Also add the supporting types.

**Types to add** (add near the other interface definitions):
```typescript
export type ExportFormat = 'markdown' | 'json' | 'fountain' | 'html';
```

**Methods to add** inside the `api` object:
```typescript
// Export
async exportManuscript(): Promise<Blob> {
    const res = await fetch(`${BASE}/api/v1/export/manuscript`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
},

async exportBundle(): Promise<any> {
    const res = await fetch(`${BASE}/api/v1/export/bundle`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.json();
},

async exportScreenplay(): Promise<Blob> {
    const res = await fetch(`${BASE}/api/v1/export/screenplay`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
},

async exportHTML(): Promise<Blob> {
    const res = await fetch(`${BASE}/api/v1/export/html`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
},

async exportPreview(): Promise<string> {
    const res = await fetch(`${BASE}/api/v1/export/preview`, { method: 'POST' });
    if (!res.ok) throw new Error('Export preview failed');
    return res.text();
},
```

## Feature 3: Export Modal (Frontend)

### Create `src/web/src/components/ui/ExportModal.tsx`

A modal dialog for selecting export format, previewing output, and downloading.

**Visual design:**
```
┌──────────────────────────────────────────────────┐
│  Export Project                              [X]  │
├──────────────────────────────────────────────────┤
│                                                   │
│  Select Format:                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │   📝   │ │   📦   │ │   🎬   │ │  🖨️   │    │
│  │Markdown│ │  JSON  │ │Fountain│ │  HTML  │    │
│  │  .md   │ │  .json │ │.fountain│ │ (PDF)  │    │
│  └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │                                           │   │
│  │          Preview area (iframe)            │   │
│  │          Shows HTML preview               │   │
│  │          for all formats                  │   │
│  │                                           │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  [Cancel]                        [Download ↓]    │
│                                  [Print to PDF]  │
└──────────────────────────────────────────────────┘
```

**Props:**
```typescript
interface ExportModalProps {
    isOpen: boolean;
    onClose: () => void;
}
```

**Implementation details:**

1. **Format selector** — 4 format cards in a horizontal grid:
   - Each card: `w-28 h-24 rounded-lg border border-gray-700 flex flex-col items-center justify-center gap-2 cursor-pointer`
   - Selected card: `border-indigo-500 bg-indigo-600/10`
   - Icon + label + file extension subtitle
   - Icons: FileText (markdown), Package (JSON), Clapperboard (fountain), Printer (HTML)

2. **Preview area** — Conditionally shown when a format is selected:
   - For HTML format: Use an `<iframe>` that loads the preview endpoint (`api.exportPreview()`)
   - For Markdown: Render preview text in a `<pre>` block with `font-mono text-xs text-gray-300 bg-gray-900 rounded-lg p-4 overflow-auto max-h-64`
   - For JSON: Same as Markdown but formatted with `JSON.stringify(data, null, 2)`
   - For Fountain: Same as Markdown
   - Show loading spinner while preview is fetching
   - Fetch preview on format selection (debounced)

3. **Action buttons:**
   - "Cancel" — `text-gray-400 hover:text-white`
   - "Download" — `bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg flex items-center gap-2` with Download icon
   - For HTML format, show additional "Print to PDF" button that opens browser print dialog
   - Show loading spinner on download button while downloading

4. **Download logic:**
   ```typescript
   const handleDownload = async () => {
       setDownloading(true);
       try {
           let blob: Blob;
           let filename: string;
           switch (selectedFormat) {
               case 'markdown':
                   blob = await api.exportManuscript();
                   filename = 'manuscript.md';
                   break;
               case 'json':
                   const data = await api.exportBundle();
                   blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                   filename = 'project-bundle.json';
                   break;
               case 'fountain':
                   blob = await api.exportScreenplay();
                   filename = 'screenplay.fountain';
                   break;
               case 'html':
                   blob = await api.exportHTML();
                   filename = 'manuscript.html';
                   break;
           }
           // Create download link
           const url = URL.createObjectURL(blob);
           const a = document.createElement('a');
           a.href = url;
           a.download = filename;
           a.click();
           URL.revokeObjectURL(url);
           toast.success(`Exported as ${filename}`);
           onClose();
       } catch (err) {
           toast.error('Export failed');
       } finally {
           setDownloading(false);
       }
   };
   ```

5. **Print to PDF logic** (HTML format only):
   ```typescript
   const handlePrint = async () => {
       const html = await api.exportPreview();
       const printWindow = window.open('', '_blank');
       if (printWindow) {
           printWindow.document.write(html);
           printWindow.document.close();
           printWindow.print();
       }
   };
   ```

6. **Modal overlay:**
   - `fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] flex items-center justify-center`
   - Content: `bg-gray-900 border border-gray-700 rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col`
   - Close on Escape key
   - Close on backdrop click

## Feature 4: Export Button on Dashboard

### Modify `src/web/src/components/command-center/ProgressOverview.tsx`

Add an "Export" button in the header of the ProgressOverview component.

**Changes:**
1. Import `Download` icon from lucide-react
2. Import `ExportModal` component
3. Add `useState` for `exportOpen`
4. Add an export button next to the "Story Progress" header label:
   ```tsx
   <button
       onClick={() => setExportOpen(true)}
       className="ml-auto p-1.5 rounded-lg text-gray-500 hover:text-emerald-400 hover:bg-gray-800/50 transition-colors"
       title="Export project"
   >
       <Download className="w-3.5 h-3.5" />
   </button>
   ```
5. Render `<ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />` at the end of the component

**Also** listen for a custom event so other components (like a future Navbar export button) can open the modal:
```tsx
useEffect(() => {
    const handler = () => setExportOpen(true);
    window.addEventListener('open:export', handler);
    return () => window.removeEventListener('open:export', handler);
}, []);
```

## Files Summary

### Files to CREATE:
1. `src/web/src/components/ui/ExportModal.tsx` — Export format selector, preview, download modal

### Files to MODIFY:
2. `src/showrunner_tool/services/export_service.py` — Add `export_html()` method + helpers
3. `src/showrunner_tool/server/routers/export.py` — Add `POST /html` and `POST /preview` endpoints
4. `src/web/src/lib/api.ts` — Add 5 export API methods + `ExportFormat` type
5. `src/web/src/components/command-center/ProgressOverview.tsx` — Add export button + modal integration

### Files you must NOT modify:
- `src/web/src/app/layout.tsx`
- `src/web/src/components/workbench/Canvas.tsx`
- `src/web/src/components/zen/*` (all Zen components)
- `src/web/src/app/zen/*`
- `src/web/src/lib/store.ts` or any store slice files
- `src/web/src/components/ui/Navbar.tsx` (may not exist yet — created by parallel session)
- `src/web/src/components/ui/CommandPalette.tsx` (may not exist yet)
- `src/showrunner_tool/server/deps.py`
- `src/showrunner_tool/server/app.py`

## Existing Code Reference

### Current `export_service.py` structure (224 lines):
- `ExportService.__init__(kg_service, container_repo, schema_repo, event_service)`
- `_get_fragments_for_scene(scene_id)` — Returns ordered fragment dicts
- `_fragment_text(fragment)` — Extracts prose text from fragment
- `_fragment_attributes(fragment)` — Parses full attributes dict
- `_HEADING_LEVELS` — Maps container_type to heading depth
- `export_markdown()` → calls `_render_md_node()` recursively
- `export_json_bundle()` → returns dict of containers/schemas/relationships/events
- `export_fountain()` → calls `_render_fountain_node()` → `_render_fountain_scene()`

### Current `export.py` router (49 lines):
- `POST /manuscript` — Markdown file download
- `POST /bundle` — JSON response
- `POST /screenplay` — Fountain file download

### Current `api.ts` structure:
- `api` object with 80+ methods
- `BASE` constant for API URL
- Add new methods at the END of the `api` object (before closing brace)
- Add new types after the existing type definitions

## Acceptance Criteria

1. **HTML export works** — `POST /api/v1/export/html` returns a styled HTML document with proper manuscript formatting, print-friendly CSS, and Season/Chapter/Scene headings
2. **Preview endpoint works** — `POST /api/v1/export/preview` returns HTML without download headers
3. **Export modal opens** — Click the Download icon in ProgressOverview → modal appears with 4 format cards
4. **Format selection works** — Click a format card → preview loads showing the output
5. **Download works** — Click "Download" → browser downloads file with correct name and format
6. **Print to PDF works** — Select HTML format → click "Print to PDF" → browser print dialog opens with styled manuscript
7. **JSON export shows formatted preview** — Select JSON → shows pretty-printed JSON in the preview area
8. **Toast notifications** — Success toast on download, error toast on failure
9. **Custom event integration** — `window.dispatchEvent(new CustomEvent('open:export'))` opens the modal
10. **No regressions** — Existing 3 export endpoints still work as before

## Technical Notes

- The HTML export uses a light theme (white background, dark text) even though the app is dark-themed — this is intentional for printing and PDF generation.
- The `_wrap_html()` method includes `@media print` CSS rules for optimal PDF output.
- For the iframe preview, use `srcDoc` attribute or `Blob URL` to avoid CORS issues with the API.
- The ExportModal should be rendered by ProgressOverview (not a global portal) to keep the component self-contained.
- The `open:export` custom event allows future integration points (Navbar, keyboard shortcut) without modifying this file.
