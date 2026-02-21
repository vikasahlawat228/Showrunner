# Phase I, Track 1: Command Center UI

You are a Senior Frontend Engineer working on "Showrunner", an AI-augmented writing tool built with Next.js and Tailwind CSS.
You are executing **Track 1 of Phase I**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Create `ProjectSwitcher.tsx`**
   - Create `src/web/src/components/command-center/ProjectSwitcher.tsx`.
   - Fetch projects from `GET /api/v1/projects`. Render as a dropdown or card grid.
   - Clicking a project sets it as active in `projectSlice` state.

2. **Create `ProgressOverview.tsx`**
   - Create `src/web/src/components/command-center/ProgressOverview.tsx`.
   - Fetch the story structure from `GET /api/v1/projects/{id}/structure`.
   - Render visual progress cards showing the number of Seasons, Chapters, and Scenes.

3. **Create `PendingApprovals.tsx`**
   - Create `src/web/src/components/command-center/PendingApprovals.tsx`.
   - Query pipeline runs with `state: PAUSED_FOR_USER` and render a list of pending approval items.
   - Each item should show the pipeline name, current step, and a "Review" button that navigates to the Pipeline Builder.

4. **Create `ModelConfigPanel.tsx`**
   - Create `src/web/src/components/command-center/ModelConfigPanel.tsx`.
   - Fetch current config from `GET /api/v1/models/config`.
   - Render a form with the project default model and per-agent overrides. Submit changes via `PUT /api/v1/models/config`.

5. **Redesign Dashboard**
   - Update `src/web/src/app/dashboard/page.tsx` to incorporate all four Command Center components alongside the existing Knowledge Graph canvas.
   - Use a responsive grid layout.

Please ensure `npm run build` completes with zero errors.
