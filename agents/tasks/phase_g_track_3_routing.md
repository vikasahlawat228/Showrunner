# Phase G, Track 3: Automatic Context Routing

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 3 of Phase G**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Implement Entity Detection Logic**
   - Open `src/showrunner_tool/services/writing_service.py`.
   - Update `save_fragment` (or an asynchronous processor paired with it) to detect entities mentioned in the text.
   - You can use the `AgentDispatcher` (perhaps the `story_architect` or a new specialized `entity_detector` skill) to analyze the text and return a list of recognized entities (characters, locations, items).

2. **Auto-Link to Knowledge Graph**
   - For each detected entity, look it up in the `KnowledgeGraphService` (via `sqlite_indexer`).
   - If the entity exists, automatically create a `relationships` entry on the saved `fragment` container linking it to the referenced entity bucket.
   - Ensure the updated fragment container is saved to `ContainerRepository` and emits an event via `EventService`.

3. **Backend Tests**
   - Create `tests/test_context_routing.py`.
   - Write tests that mock the AI entity detection and verify that saving a fragment successfully creates relationships in the `knowledge_graph.db` index.

Please execute these changes and ensure all existing tests still pass.
