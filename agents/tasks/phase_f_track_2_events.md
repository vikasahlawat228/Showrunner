# Phase F, Track 2: The Unified Mutation Path (Event Sourcing)

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 2 of Phase F**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Wire Event Sourcing into `WritingService`**
   - Open `src/showrunner_tool/services/writing_service.py`.
   - Update `save_fragment` to ensure it formats the incoming text fragment as a `GenericContainer` named "fragment".
   - Call `self.container_repo.save_container(container)`.
   - IMMEDIATELY call `self.event_service.append_event(...)` passing the `branch_id` (default "main"), `event_type` ("CONTAINER_CREATED"), and the container ID/payload.

2. **Audit & Fix `PipelineService` State Engine**
   - Open `src/showrunner_tool/services/pipeline_service.py`.
   - Active runs are stored in class-level dictionary `_runs: Dict[str, PipelineRun]`. This is fine for SSE streaming.
   - You must implement a `_persist_completed_run()` method that takes a finalized `PipelineRun`, converts it to a `GenericContainer` with `container_type: "pipeline_run"`, and saves it via `ContainerRepository`.
   - Ensure you emit a `"PIPELINE_RUN_COMPLETED"` event to the `EventService` and append it to the `event_log.db`.

3. **Update `SQLiteIndexer`**
   - Open `src/showrunner_tool/repositories/sqlite_indexer.py`.
   - Locate the `containers` table schema. Ensure it explicitly extracts and indexes the `parent_id` and `container_type` fields from the JSON wrapper, creating explicit columns so queries for "fetch all descendants of Scene X" are fast.

Please write tests in a new file `tests/test_event_sourcing.py` testing the unified mutation path and run the test suite.
