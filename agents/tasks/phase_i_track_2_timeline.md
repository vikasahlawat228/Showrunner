# Phase I, Track 2: Story Timeline UI

You are a Senior Frontend Engineer working on "Showrunner", an AI-augmented writing tool built with Next.js and Tailwind CSS.
You are executing **Track 2 of Phase I**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Create `StoryStructureTree.tsx`**
   - Create `src/web/src/components/timeline/StoryStructureTree.tsx`.
   - This is a recursive tree component. Each node represents a `StructureTreeNode` (Season, Arc, Chapter, Scene).
   - It should support:
     - **Expand/Collapse**: Click a node to expand or collapse its children.
     - **Drag-and-Drop Reordering**: Use a library like `@dnd-kit/sortable` to allow reordering sibling nodes. On drop, call `PUT /api/v1/projects/{id}/settings` (or a dedicated endpoint) to update the `sort_order` of affected containers.
     - **Inline Rename**: Double-click a node name to edit it inline, saving via the container update API.
   - Fetch data from `GET /api/v1/projects/{id}/structure`.

2. **Update Timeline Page**
   - Update `src/web/src/app/timeline/page.tsx` to split into two panels:
     - **Left Panel**: The `StoryStructureTree` component.
     - **Right Panel**: The existing `TimelineView` component (event sourcing branch visualization).
   - Add a "Create Branch" button that calls `POST /api/v1/timeline/branch` with a user-provided branch name and the currently selected event ID.

3. **SSE Integration**
   - Wire the right panel to receive live event updates via SSE (`GET /api/v1/timeline/stream`).
   - New events should animate into the visualization.

Please ensure `npm run build` completes with zero errors.
