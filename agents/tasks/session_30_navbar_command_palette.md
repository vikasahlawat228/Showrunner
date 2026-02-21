# Session 30: Global Navigation Bar + Command Palette + Error Boundary

## Context

You are working on **Showrunner**, a Next.js 14 + FastAPI platform for AI-assisted manga/manhwa creation. The app has **10 pages** but **no persistent navigation**. Each page either recreates its own header links (Canvas.tsx has nav tabs for Zen/Pipelines/Storyboard/etc.) or has no nav at all. There is also no global search, no command palette, and no error boundary for component crashes.

This session adds three foundational polish features:
1. **Persistent Navbar** — Consistent top navigation across all pages
2. **Command Palette** (Cmd+K) — Quick search + actions + page navigation
3. **Error Boundary** — Graceful crash recovery for component errors

## Architecture

- **Framework**: Next.js 14 App Router + Tailwind CSS + Zustand
- **Styling**: Dark theme (gray-950 backgrounds, gray-800 borders, white/gray-300 text)
- **Icons**: lucide-react
- **Toasts**: sonner (already configured in layout.tsx)
- **Package to install**: `cmdk` (command palette library — lightweight, unstyled, composable)

## Feature 1: Persistent Navbar

### Create `src/web/src/components/ui/Navbar.tsx`

A fixed top navbar that appears on ALL pages. Design specs:

```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Showrunner    [Dashboard][Zen][Pipelines][Storyboard]   │
│                  [Timeline][Brainstorm][Research]            │
│                  [Translation][Preview]     [⌘K] [Export]   │
└─────────────────────────────────────────────────────────────┘
```

**Layout:**
- Height: `h-12` (48px), fixed at top with `sticky top-0 z-50`
- Background: `bg-gray-950/95 backdrop-blur-sm border-b border-gray-800`
- Left section: Logo/brand ("Showrunner" with gradient text like Canvas.tsx uses)
- Center section: Page navigation tabs (horizontal pill tabs)
- Right section: Command palette trigger button (`⌘K`), compact

**Navigation tabs:**
- Use `next/link` with `usePathname()` from `next/navigation` for active state detection
- Active tab: `bg-indigo-600/20 text-indigo-300 border-indigo-500/30`
- Inactive tab: `text-gray-500 hover:text-gray-300 hover:bg-gray-800/50`
- Tab size: `px-2.5 py-1 text-xs font-medium rounded-md`
- Include icons from lucide-react for each route:
  - `/dashboard` → LayoutDashboard
  - `/zen` → PenTool
  - `/pipelines` → Workflow
  - `/storyboard` → Film
  - `/timeline` → Clock
  - `/brainstorm` → Lightbulb
  - `/research` → BookOpen
  - `/translation` → Globe
  - `/preview` → Smartphone

**Command palette trigger:**
- Button showing "⌘K" with `text-[10px]` badge style
- On click or Cmd+K keypress: open CommandPalette

### Modify `src/web/src/app/layout.tsx`

- Import and render `<Navbar />` above `{children}`
- Import and render `<ErrorBoundary>` wrapping `{children}`
- The Navbar is outside ErrorBoundary (so nav survives crashes)
- Add `pt-12` to body or a wrapper div so page content doesn't overlap with sticky nav

### Modify `src/web/src/components/workbench/Canvas.tsx`

**Remove the cross-page navigation links** from the header (lines ~103–158). Keep:
- The "Antigravity Studio" brand + project name
- The `Graph` / `Timeline` view toggle (these are dashboard-local views, not pages)
- The `DirectorControls`
- The sidebar toggle button

The removed links (Zen, Pipelines, Storyboard, Brainstorm, Research, Translation, Preview) are now in the Navbar.

## Feature 2: Command Palette (Cmd+K)

### Install dependency

```bash
cd src/web && npm install cmdk
```

### Create `src/web/src/components/ui/CommandPalette.tsx`

A full-screen overlay command palette using the `cmdk` library.

**Visual design:**
- Centered modal: `max-w-lg w-full mx-auto mt-[20vh]`
- Background overlay: `fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]`
- Container: `bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden`
- Search input: Full-width, `px-4 py-3 text-sm`, placeholder "Search pages, characters, scenes..."
- Results list: Grouped by category, max-height scrollable

**Categories and items:**

1. **Pages** (always available, filtered by query):
   - All 9 page routes with their icons
   - Action: `router.push(route)` using `useRouter()` from `next/navigation`

2. **Actions** (always available):
   - "Create New Pipeline" → `router.push('/pipelines')`
   - "Start AI Director" → trigger director pipeline
   - "Export Project" → dispatch custom event `window.dispatchEvent(new CustomEvent('open:export'))`
   - "Open Zen Mode" → `router.push('/zen')`

3. **Recent** (if applicable — can be a static list for now):
   - Show last 3 visited pages from sessionStorage

**Keyboard shortcuts:**
- `Cmd+K` / `Ctrl+K`: Toggle open/close
- `Escape`: Close
- `ArrowUp/ArrowDown`: Navigate items
- `Enter`: Select item
- Register the global `Cmd+K` listener in `useEffect` on mount

**State management:**
- Local state in the component (open/closed)
- Export a `useCommandPalette()` hook or use a global event to open from Navbar button

**Implementation with cmdk:**
```tsx
import { Command } from 'cmdk';

// Use Command.Dialog for the overlay
// Command.Input for search
// Command.List > Command.Group > Command.Item for results
```

**Styling with cmdk:**
- cmdk provides unstyled components — style everything with Tailwind classes
- Each item: `px-3 py-2 text-sm flex items-center gap-3 rounded-md`
- Selected item: `bg-indigo-600/20 text-white` (cmdk handles the `data-selected` attribute)
- Group heading: `text-[10px] uppercase text-gray-600 font-semibold px-3 py-1.5`

## Feature 3: Error Boundary

### Create `src/web/src/components/ui/ErrorBoundary.tsx`

A React error boundary (must be a class component) with a user-friendly fallback UI.

**Implementation:**
```tsx
"use client";
import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  // Standard getDerivedStateFromError + componentDidCatch
  // Reset button to try again (setState hasError: false)
}
```

**Fallback UI:**
- Centered on page
- Icon: AlertTriangle from lucide-react (render as static SVG to avoid import issues in class component)
- Heading: "Something went wrong"
- Error message in a `bg-gray-900 rounded-lg p-4 text-sm text-red-400 font-mono` block
- "Try Again" button: `bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg`
- "Go to Dashboard" link: `text-gray-400 hover:text-gray-200`

## Files Summary

### Files to CREATE:
1. `src/web/src/components/ui/Navbar.tsx` — Persistent navigation bar
2. `src/web/src/components/ui/CommandPalette.tsx` — Cmd+K command palette
3. `src/web/src/components/ui/ErrorBoundary.tsx` — Error boundary wrapper

### Files to MODIFY:
4. `src/web/src/app/layout.tsx` — Add Navbar + ErrorBoundary
5. `src/web/src/components/workbench/Canvas.tsx` — Remove cross-page nav links from header

### Files you must NOT modify:
- `src/web/src/lib/api.ts`
- `src/web/src/lib/store.ts` or any store slice files
- `src/web/src/components/zen/*` (all Zen components)
- `src/web/src/app/zen/*`
- Any backend Python files
- `src/web/src/components/command-center/*`
- `src/web/src/components/pipeline/*`
- `src/web/package.json` (except via npm install cmdk)

## Acceptance Criteria

1. **Navbar visible on every page** — Navigate to /dashboard, /zen, /pipelines, /storyboard, /timeline, /brainstorm, /research, /translation, /preview — each shows the Navbar with correct active tab highlighted
2. **Cmd+K opens command palette** — Press Cmd+K (or Ctrl+K) anywhere in the app, palette opens. Type "zen" → shows Zen page. Press Enter → navigates to /zen.
3. **Canvas header cleaned up** — The Dashboard canvas header no longer has cross-page links (Zen, Pipelines, Storyboard, etc.) but still shows Graph/Timeline toggle, project name, and DirectorControls
4. **Error boundary works** — If a component throws, the fallback UI shows with "Try Again" button instead of a white screen
5. **Keyboard navigation in palette** — Arrow keys move selection, Enter selects, Escape closes
6. **No regressions** — All existing page layouts still render correctly with the new navbar spacing

## Technical Notes

- The Navbar height is 48px. All page content needs `pt-12` to avoid being hidden under it. The easiest approach is adding this to the body wrapper in layout.tsx.
- Canvas.tsx's header still exists (for Graph/Timeline toggle) but is now the dashboard's local header, not the global nav.
- The command palette should be rendered in layout.tsx (portal-like) so it's available globally.
- Use `usePathname()` from `next/navigation` for active route detection in the Navbar.
