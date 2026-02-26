# Prompt: Track 1 — Universal Persistence & Event Sourcing

**Goal**: Integrate the existing `EventService` and `ContainerRepository` into the newly created phases (Zen Mode, Pipelines, Storyboard). 

**Context**:
Currently, `pipeline_service.py`, `writing_service.py`, and `storyboard_service.py` use local, in-memory Python dictionaries (e.g., `_panels = {}`, `_fragments = {}`) to store data. This means data is lost on server restart, bypassing the `EventService` (CQRS event log) and `KnowledgeGraphService` (SQLite indexing).

**Required Actions (Backend Only)**:

1. **Refactor `services/pipeline_service.py`**:
   - Save/Load `PipelineDefinition` objects in `ContainerRepository` using `container_type="pipeline_def"`.
   - Before executing a step, emit an event to `EventService.append_event()`.

2. **Refactor `services/writing_service.py` (Zen Mode)**:
   - Convert `Fragment` saves to `GenericContainer` writes (with `container_type="fragment"`) using `ContainerRepository.save_container()`.
   - Update `save_fragment()` to emit an event via `EventService`.

3. **Refactor `services/storyboard_service.py` (Phase C)**:
   - Convert `Panel` storage to `GenericContainer` writes (with `container_type="panel"`).
   - Any reorder, map creation, or LLM generation must trigger `ContainerRepository.save_container()` and emit an event.

4. **Update `server/deps.py`**:
   - Ensure these services receive the injected `ContainerRepository` and `EventService` dependencies rather than relying on class-level dictionaries.

**Output Specification**:
Provide the updated Python code for:
1. `src/showrunner_tool/services/writing_service.py`
2. `src/showrunner_tool/services/storyboard_service.py`
3. `src/showrunner_tool/services/pipeline_service.py`
4. `src/showrunner_tool/server/deps.py` (if dependency injection changes)

*Note: Ensure you comply exactly with the `ShowrunnerBase` and `GenericContainer` paradigms found in `schemas/container.py` and `repositories/container_repo.py`.*
