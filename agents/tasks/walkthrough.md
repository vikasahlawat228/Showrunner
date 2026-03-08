# Showrunner Studio — Gap-Fix Walkthrough

All 4 phases from the product review gap-fix plan are implemented and build-verified.

## Phase 1: Onboarding & Writer's Dashboard

### Onboarding Wizard (auto-trigger, 5-step flow)
- **File**: [OnboardingWizard.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/ui/OnboardingWizard.tsx)
- Auto-detects first visit via `localStorage` (key: `showrunner:onboarded`)
- Steps: Welcome → Premise (title + logline) → Genre Picker (8 visual cards) → Character Creation → Ready
- On completion: saves project settings, creates character container, navigates to Zen

![Onboarding wizard welcome screen](/Users/vikasahlawat/.gemini/antigravity/brain/7bc06f1a-5fe0-4ff4-8c22-2fbd53282d5e/.system_generated/click_feedback/click_feedback_1772914576438.png)

### Onboarding Checklist
- **File**: [OnboardingChecklist.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/ui/OnboardingChecklist.tsx)
- Circular SVG progress indicator, 5 milestones: world, 3+ characters, chapter outline, first scene, first panel
- Hides when all items complete

### Writer's Dashboard
- **File**: [WriterDashboard.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/dashboard/WriterDashboard.tsx)
- Welcome header with project name, "Continue Writing" CTA
- Stats row: streak days, total words, today's words
- 7-day word count bar chart from session history
- Quick-link cards to Brainstorm and Storyboard

### Dashboard Page Redesign
- **File**: [dashboard/page.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/app/dashboard/page.tsx)
- Left column: WriterDashboard + checklist. Advanced Tools collapsed into accordion
- Right column: Knowledge graph canvas preserved

### Session Persistence
- **File**: [zenSlice.ts](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/lib/store/zenSlice.ts)
- `sessionWordsWritten` and `sessionStartTime` hydrated from `localStorage`
- Previous session words auto-saved to `showrunner:wordHistory` for dashboard chart

---

## Phase 2: Unified Story Context Sidebar

### Story Context Store
- **File**: [storyContextSlice.ts](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/lib/store/storyContextSlice.ts)
- Manages scene summary, characters present, continuity flags, writing goals
- Fetches from scene/character/continuity APIs in parallel

### Route-Adaptive Sidebar
- **File**: [StoryContextSidebar.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/shared/StoryContextSidebar.tsx)
- **Zen**: scene summary, characters present, emotional intensity bar, writing goals progress
- **Storyboard**: visual continuity guidance, characters in scene
- **Timeline**: structure overview, metrics explanation
- **Brainstorm**: idea connection tips
- **Preview**: pacing legend
- Continuity flags shown on all routes when present

### Navbar Enhancements
- **File**: [Navbar.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/ui/Navbar.tsx)
- Grouped navigation: **Write** (Zen, Brainstorm) | **Visualize** (Storyboard, Timeline, Preview) | **Manage** (Dashboard, Pipelines, Research, Translation)
- Story Context toggle button (Library icon)
- Pending approval badge on chat button

---

## Phase 3: Cross-Tool Linking

### PanelCard → Zen Deep Link
- **File**: [PanelCard.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/storyboard/PanelCard.tsx)
- "Edit" button navigates to `/zen?scene=<sceneId>`

### Preview → Zen
- **File**: [preview/page.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/app/preview/page.tsx)
- Scene headers show hover "Edit" button linking to Zen
- Dead zone items are clickable jump links with → arrow

### Enhanced Command Palette
- **File**: [CommandPalette.tsx](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/components/ui/CommandPalette.tsx)
- Dynamically loads characters and scenes when opened
- Real-time entity search (debounced 250ms) via `api.searchEntities`
- AI Director action now calls `api.directorAct()` with toast feedback
- "Re-run Onboarding" action added

---

## Phase 4: Design Tokens & Polish

### Design System
- **File**: [globals.css](file:///Users/vikasahlawat/Documents/Showrunner/src/web/src/app/globals.css)
- 56 CSS custom properties: spacing (7 steps), typography (6 sizes), brand colors (7), surfaces (5), radius (4), shadows (3), button heights (3), modal/card padding
- Body font-family updated to use `--font-sans` variable

---

## Build Verification

All 4 phases compile successfully with `next build`:

```
✓ Compiled successfully in 2.7s
✓ Generating static pages (16/16) in 231.4ms
```

All 16 routes pass: `/`, `/dashboard`, `/zen`, `/brainstorm`, `/storyboard`, `/timeline`, `/preview`, `/pipelines`, `/research`, `/translation`, `/schemas`, `/auth/callback`, `/timeline-test`, `/_not-found`.

![Onboarding flow demo](/Users/vikasahlawat/.gemini/antigravity/brain/7bc06f1a-5fe0-4ff4-8c22-2fbd53282d5e/dashboard_onboarding_test_1772914535771.webp)

## Files Changed

| Phase | File | Action |
|-------|------|--------|
| 1 | `OnboardingWizard.tsx` | Rewritten |
| 1 | `OnboardingChecklist.tsx` | **New** |
| 1 | `WriterDashboard.tsx` | **New** |
| 1 | `dashboard/page.tsx` | Rewritten |
| 1 | `zenSlice.ts` | Modified |
| 1 | `store.ts` | Modified |
| 2 | `storyContextSlice.ts` | **New** |
| 2 | `StoryContextSidebar.tsx` | **New** |
| 2 | `StoryContextSidebarWrapper.tsx` | **New** |
| 2 | `layout.tsx` | Modified |
| 2 | `Navbar.tsx` | Modified |
| 3 | `PanelCard.tsx` | Modified |
| 3 | `preview/page.tsx` | Modified |
| 3 | `CommandPalette.tsx` | Rewritten |
| 4 | `globals.css` | Modified |
