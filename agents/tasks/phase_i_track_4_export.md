# Phase I, Track 4: Export System

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 4 of Phase I**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Implement `ExportService`**
   - Create `src/antigravity_tool/services/export_service.py`.
   - It should walk the story structure tree (Season → Chapter → Scene) using `KnowledgeGraphService.get_structure_tree()`.
   - For each Scene node, collect the associated `fragment` containers (via `parent_id` or relationships) and concatenate their text in `sort_order`.
   - Implement three export methods:
     - `export_markdown() -> str` — Renders a Markdown manuscript with `# Season`, `## Chapter`, `### Scene` headings.
     - `export_json_bundle() -> dict` — Returns the full project state as a JSON dict including all containers, schemas, relationships, and the event log.
     - `export_fountain() -> str` — Renders in Fountain screenplay format. Use container attributes like `scene_heading`, `action`, `character`, `dialogue` if available. Fall back to plain prose otherwise.

2. **Build the Export Router**
   - Create `src/antigravity_tool/server/routers/export.py`.
   - `POST /api/v1/export/manuscript` — Returns the Markdown as a `text/markdown` file download with `Content-Disposition` header.
   - `POST /api/v1/export/bundle` — Returns the JSON bundle as `application/json`.
   - `POST /api/v1/export/screenplay` — Returns the Fountain file as `text/plain`.

3. **Wire DI and Router**
   - Update `src/antigravity_tool/server/deps.py` to add `get_export_service()`.
   - Update `src/antigravity_tool/server/app.py` to register the export router.

4. **Backend Tests**
   - Create `tests/test_export.py`.
   - Write tests with a mock 3-chapter hierarchy. Assert that `export_markdown()` produces headings in the correct order and includes fragment text.
   - Assert `export_json_bundle()` returns a dict with `containers`, `schemas`, and `events` keys.

Please execute these changes and ensure all existing tests remain green.
