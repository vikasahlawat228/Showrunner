# Phase F, Track 1: Universal Buckets & Multi-Project Isolation

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 1 of Phase F**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Update `GenericContainer`**
   - Open `src/antigravity_tool/schemas/container.py`.
   - Add the 6 new properties required for Phase F: `context_window` (Optional[str]), `timeline_positions` (List[str] = []), `tags` (List[str] = []), `model_preference` (Optional[str]), `parent_id` (Optional[str]), `sort_order` (int = 0).

2. **Build Project Schemas**
   - Create `src/antigravity_tool/schemas/project.py`.
   - Implement `ProjectCreate`, `ProjectSummary`, `ProjectSettings`.
   - **Crucial:** Implement the `StructureTree` recursive Pydantic model. It should represent the hierarchical tree formed by walking the `parent_id` property of `GenericContainer` (e.g., Season holds Chapters which hold Scenes).

3. **Build the Projects Router**
   - Create `src/antigravity_tool/server/routers/projects.py`.
   - Implement `POST /api/v1/projects/` to generate a new multi-project directory layout on disk. It must create the subfolders: `containers/`, `schemas/`, `.antigravity/`, and initialize empty `event_log.db` and `knowledge_graph.db` databases.
   - Implement `GET /api/v1/projects/{id}/structure` which utilizes `KnowledgeGraphService` to fetch all containers for the project and assemble them into the `StructureTree` JSON response.

Please execute these changes, write tests in a new file `tests/test_projects.py`, and run `pytest` to ensure functionality.
