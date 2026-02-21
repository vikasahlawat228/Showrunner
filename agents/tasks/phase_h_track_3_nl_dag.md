# Phase H, Track 3: Intelligent Pipeline Generation (NL-to-DAG)

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 3 of Phase H**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Build NL-to-DAG Pipeline Generation**
   - Open `src/antigravity_tool/services/pipeline_service.py`.
   - Implement `generate_pipeline_from_nl(intent: str, title: str) -> PipelineDefinition`.
   - This function should invoke `AgentDispatcher` (specifically using the `pipeline_director` skill). The LLM prompt must request a rigorous JSON output matching the Pydantic structure of a `PipelineDefinition`.

2. **Add API Endpoint**
   - Open `src/antigravity_tool/server/routers/pipeline.py`.
   - Add a `POST /api/pipeline/definitions/generate` endpoint. It expects a payload like `{"intent": "Create a 3-act structure and critique it", "title": "Structure Gen"}`.
   - It should call your new `generate_pipeline_from_nl` service method, save the resulting `PipelineDefinition` to the `ContainerRepository`, and return it.

3. **Backend Tests**
   - Create `tests/test_nl_to_dag.py`.
   - Write tests mocking the `litellm` response from the agent dispatcher. Ensure the JSON maps correctly into a valid `PipelineDefinition` containing at least 2 nodes and 1 connecting edge, and that logic nodes (if requested by the intent) are mapped successfully.

Please execute these changes and ensure existing tests remain green.
