# Prompt: Track 3 — Agent Orchestration & Routing

**Goal**: Transform our static markdown skill files into an active, multi-agent orchestrator utilizing the ReAct (Think, Act, Observe) loop pattern.

**Context**:
We currently have 5 agent skill files in `agents/skills/*.md` (Schema Architect, Graph Arranger, Pipeline Director, Continuity Analyst, Schema Wizard). They are excellent instructions but are statically read. To achieve proper agentic workflow, we need a dispatcher that delegates tasks to these specialized agents and coordinates their responses.

**Required Actions (Backend Only)**:

1. **Create `services/agent_dispatcher.py`**:
   - Build an `AgentDispatcher` class.
   - Implement a routing mechanism using a Router Agent (an LLM call) that reads a user intent and decides which specific skill (Architect, Director, Analyst, Wizard, Arranger) to invoke.
   - Implement the execution wrapper that passes the parsed `.md` skill file as the System Prompt along with the dynamic user context.

2. **Refactor `routers/director.py`**:
   - Replace the simplistic `POST /act` endpoint logic with a call to your new `AgentDispatcher.route_and_execute(intent: str, active_state: dict)`.

3. **Orchestrator-Worker Pattern**:
   - Ensure the `AgentDispatcher` handles the "orchestrator" role, while the skills define the "worker" roles.

**Output Specification**:
Provide the Python code for:
1. `src/showrunner_tool/services/agent_dispatcher.py`
2. `src/showrunner_tool/server/routers/director.py` (updated to use the dispatcher)

*Note: The skill files are located at `agents/skills/`. The dispatcher should read these files from disk at boot or runtime to construct the `system_prompt` for LiteLLM calls.*
