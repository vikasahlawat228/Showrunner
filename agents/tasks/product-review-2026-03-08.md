# Showrunner Studio — Product Review

**Date**: March 8, 2026
**Reviewer**: Cowork Agent (Product & UX perspective)
**Method**: Full frontend code audit, component analysis, state flow review
**Scope**: All 13 page routes, navigation, chat sidebar, command palette, state management, design system

---

## Executive Summary

Showrunner Studio has genuine creative innovation at its core — the Zen Mode editor with @mentions, slash commands, ghost text, and auto-branching is one of the best AI-integrated writing experiences I've seen in code. The problem isn't what's built, it's that the pieces don't feel like one product yet. A writer opening this app for the first time faces a complex workbench with no guidance, and moving between tools (writing → storyboarding → timeline) breaks flow rather than enhancing it.

**Overall Product Maturity**: ~65% (Strong Beta)

The technical foundation is solid. What's needed now isn't more features — it's connective tissue between the features you have, and a writer-first onboarding flow.

---

## The Scorecard

| Area | Grade | Polish | What Works | Critical Gap |
|------|-------|--------|------------|--------------|
| **Zen Mode (Writing Desk)** | A- | 85% | @mentions, slash commands, ghost text, focus fade, auto-branch | Sidebars underpowered, no writing goals |
| **Timeline** | B | 75% | Semantic zoom is brilliant, branch comparison | Metrics unclear, no merge UI |
| **Chat Sidebar** | C+ | 70% | Session persistence, artifact cards, contextual input | Hidden by default, no proactive help |
| **Preview / Reader Sim** | C+ | 70% | Pacing heatmap, engagement scoring, auto-scroll | Not actionable — can't jump to fix points |
| **Navigation** | C+ | 70% | Clear tabs, active states, icon+label | No task-flow grouping, context lost between pages |
| **Pipeline Builder** | C+ | 70% | Template gallery, NL wizard, DAG editor | Too complex for non-technical writers |
| **Command Palette** | C | 65% | Fast Cmd+K navigation | Can't jump to specific scenes/characters |
| **Storyboard Canvas** | C | 65% | Strip view, panel editor sidebar | No drag reorder, no templates, disconnected from text |
| **Brainstorm** | C- | 60% | Visual ideation on canvas, AI suggestions | No grouping, isolated from writing flow |
| **Design System** | C- | 60% | Cohesive dark theme | No tokens, inconsistent spacing/sizing |
| **Research** | C- | 55% | Query interface, agent status | Disconnected from writing, no citations |
| **Dashboard** | D+ | 50% | Git panel, project switcher | Feels like a dev cockpit, not a writer's home |
| **Translation** | D+ | 50% | Multi-language, context-aware | One-off only, no batch, unclear save target |
| **Onboarding** | F | 20% | OnboardingWizard component exists | Never auto-triggers, no guided flow |

---

## Deep Dive: What a Writer Actually Experiences

### First Launch: "Where do I start?"

A new user opens `localhost:3000` and lands on the Dashboard. They see a command center with Git status, database stats, model configuration, and an empty knowledge graph canvas. There is no welcome message, no "Create your first project" wizard, no guided tour.

The OnboardingWizard component exists in code (title, genre, premise fields) but it isn't auto-triggered on first visit. A writer's first thought: "This looks like developer tooling, not a creative space."

**What should happen instead**: First visit detects no project → triggers a warm, guided flow: "What's your story about?" → Set genre → Create first character → Write your opening scene. Five minutes from launch to writing.

### The Writing Session: "This is actually great"

Once a writer finds Zen Mode (`/zen`), the experience transforms. The TipTap editor is clean and responsive. Typing `@` brings up character/scene autocomplete with fuzzy search. Typing `/brainstorm` triggers an inline AI ideation without leaving the editor. Ghost text fades in after 2 seconds of idle — gentle suggestions that feel like a creative partner whispering, not an intrusion. Pressing Tab accepts, typing anything dismisses.

The auto-branching on brainstorm is genuinely clever: when you start experimenting, the system automatically creates a branch so your main story is protected. You can go wild without fear.

Focus mode is well-implemented — sidebars fade on typing, stats bar becomes translucent, and in full zen mode everything disappears except the text and a gentle top padding that centers your work. This is where the product shines.

**But the sidebars are thin.** The context sidebar and live storyboard panel exist but don't give the writer what they need mid-scene: Which characters are present? What happened in the previous scene? What's the emotional intensity target? Is this scene's pacing on track? These are the questions writers ask constantly, and right now the answer requires switching to a different page entirely.

### Moving Between Tools: "Wait, where did my context go?"

Here's the core friction. A writer finishes drafting a scene in Zen Mode and wants to see it as panels in the Storyboard. They click Storyboard in the top nav. The entire context shifts — sidebar content changes, the editor disappears, and they're now in a strip-view layout. The storyboard shows panels but editing a panel description here doesn't update the scene text back in Zen. They're two separate artifacts with no bidirectional link.

Same problem with Timeline: the semantic zoom is innovative (scroll to zoom from world-arc down to scene-level) but the emotional arc chart doesn't explain what it's measuring, and there's no way to click a data point and jump back to the relevant scene in the editor.

Same problem with Brainstorm: you can generate ideas on a visual canvas with AI suggestions, but there's no "Turn these 3 idea cards into a scene outline" action. Ideas live in isolation.

**The mental model issue**: Each page is a standalone tool rather than a view into the same story. Writers think in terms of flow (outline → draft → revise → visualize), not in terms of switching between disconnected applications.

### The AI Co-Pilot: "I didn't know this was here"

The chat sidebar is session-persistent, contextual (in Zen Mode it auto-includes the first 2000 characters of your scene plus detected entities), and can render artifacts inline. It's a capable co-pilot.

But it's hidden. The toggle button is in the right side of the navbar, visually equivalent to other utility buttons like Export and Inbox. A new user might use the app for days without discovering it. When they do find it, there's no introduction — no "I'm your AI writing partner, here's what I can help with."

The approval flow is also buried: when an AI agent makes a decision that needs sign-off, the notification appears in the chat sidebar. If the writer isn't looking at chat, they'll miss it entirely. There's no navbar badge or notification sound.

### The Pipeline Builder: "This isn't for me"

The pipeline builder is a full DAG editor with drag-and-drop nodes, conditional branches, and step configuration panels. It has a template gallery and an NL wizard that can generate pipelines from natural language descriptions. This is powerful for a technical user who wants to automate multi-step AI workflows.

For a writer who just wants to "automatically generate character sheets for everyone mentioned in chapter 1," it's overwhelming. The tool needs a guided layer on top — pre-built "1-click workflows" that hide the DAG complexity and just ask: "What do you want to automate?"

---

## The Five Things That Would Transform This Product

### 1. Guided Onboarding (Impact: Massive)

Auto-detect first launch → warm welcome → "What's your story about?" → genre picker → create world → first character → open Zen Mode with a template scene. Time-to-writing should be under 5 minutes.

Add a persistent onboarding checklist in the dashboard sidebar: Create World, Add Characters (3+), Outline Chapter 1, Write First Scene, Generate First Panel. Check them off as the writer progresses.

### 2. Unified Story Context Sidebar (Impact: High)

Instead of page-specific sidebars that break on navigation, build a persistent story context panel that follows the writer everywhere. It should show: current scene summary, characters present, previous scene recap, emotional arc target, continuity flags, and writing goals. It adapts to the current page (in Zen it emphasizes writing context, in Storyboard it emphasizes visual continuity, in Timeline it emphasizes structure) but never disappears.

### 3. Cross-Tool Linking (Impact: High)

Every artifact should be clickable-through to its source. Click a panel in Storyboard → jumps to that scene in Zen. Click a data point on the emotional arc → jumps to that scene. Select 3 brainstorm cards → "Create Scene Outline from These." Research notes should auto-appear in Zen's context sidebar when writing a related scene.

The data model already supports this (containers, ULIDs, relationships). The UI just needs the links.

### 4. Writer's Daily Dashboard (Impact: Medium)

Replace the current developer-style dashboard with a writer's home: "Welcome back, Vikas. You're on Chapter 3, Scene 2. You wrote 1,247 words yesterday. Today's goal: finish the confrontation scene. Here's what your AI co-pilot prepared while you were away: [3 suggestions]. Jump back in →"

Show: writing streak, word count trends, scene completion progress, recently edited scenes, pending AI suggestions, and a "Continue Writing" button that opens Zen at exactly where you left off.

### 5. 1-Click Workflow Templates (Impact: Medium)

Surface the pipeline builder's power without its complexity. On every page, offer contextual actions: "Generate character sheets for this chapter" (one click), "Check continuity for this scene" (one click), "Brainstorm 5 alternative endings" (one click). These are pre-built pipelines with a simple trigger UI — the DAG runs in the background.

---

## What's Already Excellent (Don't Touch These)

These are genuine product innovations that should be protected and polished further:

- **@Mentions + Auto-branch**: Typing `@"New Character"` auto-creates the entity and branches from main. Prevents destructive edits while staying in flow. This is the killer feature.

- **Slash Commands in Editor**: `/brainstorm`, `/translate`, `/alttake` are discoverable, contextual, and non-disruptive. This is how AI co-pilots should work — embedded in the creative surface, not in a separate chat window.

- **Ghost Text**: Idle-triggered suggestions that fade in after 2 seconds. Unobtrusive, dismissible, feels like a creative partner. The implementation (opacity transitions, Tab to accept) is polished.

- **Semantic Zoom in Timeline**: Scroll depth maps to narrative zoom level (world → arc → chapter → scene → editor). This matches how writers think about story structure.

- **Branch-First Architecture**: Auto-branching on experimental work, visual branch comparison, timeline checkout. This gives writers creative freedom without fear.

- **Dark Theme**: Consistent, easy on the eyes for long writing sessions. The indigo accent is distinctive without being distracting.

---

## Bugs and Polish Issues Noted

These aren't critical but affect perceived quality:

1. **Session word count resets on page reload** — `sessionWordsWritten` lives in volatile memory, not persisted to localStorage or API
2. **Command Palette "Start AI Director" is unimplemented** — comment in code says `/* TODO: trigger director */`
3. **Storyboard empty state says "Create scenes to start"** but doesn't tell you where or how to create scenes
4. **Word count uses naive `split(/\s+/)` regex** — doesn't handle contractions or CJK characters well
5. **Modal padding inconsistent** — OnboardingWizard uses `p-8`, QuickAddModal uses `p-6`
6. **Button sizes not standardized** — mix of `px-3 py-1.5` and `px-4 py-2` with no size system
7. **No favicon or app title** — tab shows empty title on localhost

---

## Recommended Priority Order

If I were planning the next 4 weeks of development:

**Week 1**: Guided onboarding flow + writer's daily dashboard. This is the front door — it determines whether a new user stays or bounces.

**Week 2**: Unified story context sidebar. This connects the dots between Zen, Storyboard, and Timeline without rebuilding any of those pages.

**Week 3**: Cross-tool linking (click-through from Storyboard → Zen, Timeline → Zen, Brainstorm → Scene outline). This makes the multi-tool architecture feel intentional rather than fragmented.

**Week 4**: 1-click workflow templates + polish pass on empty states, onboarding checklist completion tracking, and the small bugs listed above.

---

## Conclusion

Showrunner has the bones of something special. The Zen Mode editor is legitimately one of the best AI-integrated writing experiences possible — @mentions, slash commands, ghost text, and auto-branching are thoughtfully designed for creative flow. The backend architecture (event sourcing, branches, containers, 10-agent ecosystem) is more sophisticated than most writing tools ever get.

The gap is product design, not engineering. The app currently feels like a powerful toolkit with many separate drawers. What it needs to feel like is a single creative space where the drawers open for you at the right moment. Close that gap and you have something writers will genuinely love.
