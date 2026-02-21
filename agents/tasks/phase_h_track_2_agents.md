# Phase H, Track 2: The 10-Agent Ecosystem

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 2 of Phase H**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Create the Missing Skills**
   - Head to `agents/skills/`. You currently have `research_agent.md` and `writing_agent.md`.
   - You must create the remaining system prompts:
     - `story_architect.md` — Structural planner for Acts/Chapters/Scenes.
     - `prompt_composer.md` — Agent that refines prompts before execution.
     - `style_enforcer.md` — Evaluator checking vs. Style Guide buckets.
     - `translator_agent.md` — Localizer and adapter.
     - `schema_wizard.md` — Generates Pydantic/JSON models for Universal Buckets.
     - `continuity_analyst.md` — Fact-checks narrative flow.
     - `brainstorm_agent.md` — High-divergence ideator.

2. **Enhance AgentDispatcher**
   - Open `src/antigravity_tool/services/agent_dispatcher.py`.
   - Update `route_and_execute()` to parse "ReAct" responses. For instance, if an agent responds with `Action: SearchKG("spaceship design")`, the dispatcher uses `KnowledgeGraphService/ChromaIndexer` to fetch context, appends the result to the history, and calls the LLM again.
   - You do NOT need to implement the actual complex tools yet, just the parsing loop (Reason/Act/Observe) around LiteLLM.

3. **Backend Tests**
   - Create `tests/test_react_dispatcher.py`.
   - Write a unit test simulating a ReAct loop with a mocked tool execution to ensure `AgentDispatcher` can successfully proxy intermediate tool requests before returning a final parsed block.

Please execute these changes and ensure existing tests remain green.
