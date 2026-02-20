# Coding Task: Timeline Branching UI (Phase 5 UI)

**Context:** We are building "Showrunner", an AI co-writer powered by a CQRS Event Sourcing architecture. Instead of overwriting files, the AI creates an append-only log of granular events, allowing users to branch parallel story timelines (exactly like Git branches). We need a visualization of this "Undo Tree" on the frontend.

**Your Objective: Write the React Frontend Code**
You need to implement the visual tree component in `src/web/src/components/timeline/TimelinePanel.tsx`.

**Requirements:**
1. **Data Model:** Assume you receive an array of `TimelineEvent` objects: `[{ id: 'evt_1', parent_id: null, branch_id: 'main', description: 'Created Scene 1', timestamp: '...' }, { id: 'evt_2', parent_id: 'evt_1', branch_id: 'alt_ending', description: 'Killed Hero', timestamp: '...' }]`.
2. **`TimelinePanel.tsx` (React Component):**
   - A scrollable Tailwind CSS sidebar or panel that renders these events as a vertical "Git Graph" or tree.
   - Visually group or color-code events that belong to different `branch_id`s.
   - Connect parent and child nodes visually (using basic CSS borders/lines or SVG if you prefer).
   - Each event node should have a "Checkout State" button. When clicked, it should call an `onCheckout(eventId: str)` callback, allowing the user to "time-travel" to that exact narrative state.
   - The UI should look modern, utilizing smooth hover states and clear typography.

**Output:** Provide the exact, production-ready TypeScript code for this component. Ensure it is compatible with Next.js (App Router) and Tailwind CSS v4.
