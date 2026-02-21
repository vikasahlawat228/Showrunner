# Phase G, Track 2: Research Agent & Library

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 2 of Phase G**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Deploy the Research Agent Skill**
   - Create `agents/skills/research_agent.md`.
   - Write a high-quality system prompt that defines the agent's persona: A hyper-factual research librarian who specializes in history, science, and world-building trivia. 
   - The agent should be instructed to output its findings in a structured JSON format suitable for a `GenericContainer` with `container_type: "research_topic"`.

2. **Implement `ResearchService`**
   - Create `src/antigravity_tool/services/research_service.py`.
   - Implement logic to take research findings and save them as `GenericContainer` objects in the `containers/research_topic/` folder.
   - Fields should include: `summary`, `confidence_score` (0-1), `sources` (list of URLs/citations), and `key_facts` (dictionary).

3. **Build the Research Router**
   - Create `src/antigravity_tool/server/routers/research.py`.
   - `POST /api/v1/research/query`: Triggers the `AgentDispatcher` using the `research_agent` skill and the user's query. Saves the output via `ResearchService`.
   - `GET /api/v1/research/library`: Returns a list of all research containers in the Knowledge Graph.

4. **Integration with Pipelines**
   - Open `src/antigravity_tool/services/pipeline_service.py`.
   - Implement the handler for `StepType.RESEARCH_DEEP_DIVE`. This step should invoke the `ResearchService` and return the resulting container ID to the pipeline payload.

Please write tests in `tests/test_research.py` to verify the agent dispatch and container creation.
