# Phase I, Track 3: Workflow Templates Gallery

You are a Senior Frontend Engineer working on "Showrunner", an AI-augmented writing tool built with Next.js and Tailwind CSS.
You are executing **Track 3 of Phase I**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Create Template Data**
   - Create `src/web/src/lib/workflowTemplates.ts`.
   - Define 5–8 pre-built `PipelineDefinition` JSON templates. Each template should have a `title`, `description`, `icon`, `category`, and the full `steps` + `edges` arrays.
   - Suggested templates:
     - "Scene → Storyboard Panels" (gather_context → llm_generate → save_to_bucket)
     - "Character Profile Builder" (gather_context → llm_generate × 3 → merge_outputs → save_to_bucket)
     - "Chapter Outline → First Draft" (gather_context → review_prompt → llm_generate → save_to_bucket)
     - "Research Deep Dive" (research_deep_dive → save_to_bucket)
     - "Style Guide Check" (gather_context → llm_generate → review_prompt)
     - "Translate Chapter" (gather_context → llm_generate → review_prompt → save_to_bucket)

2. **Create `TemplateGallery.tsx`**
   - Create `src/web/src/components/pipeline-builder/TemplateGallery.tsx`.
   - Render the templates as visually appealing cards with title, description, icon, and a "Use Template" button.
   - On click, call `POST /api/pipeline/definitions` with the template JSON and redirect to the Pipeline Builder page with the new definition loaded.

3. **Integrate into Pipeline Page**
   - Update `src/web/src/app/pipelines/page.tsx` to show the `TemplateGallery` above the existing pipeline definitions list.

Please ensure `npm run build` completes with zero errors.
