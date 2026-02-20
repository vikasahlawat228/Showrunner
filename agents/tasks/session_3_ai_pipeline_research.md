# Task: AI Orchestration Pipeline & SSE Streaming

**Context:** We are building "Showrunner", a transparent AI co-writer. Unlike ChatGPT, the AI acts as a "Glass Box Pipeline" similar to ComfyUI or Langchain node-graphs. When the user requests "Write the next scene," the backend executes a state-machine:
1. **Context Gathering:** Finding related characters/world rules via the SQLite Knowledge Graph.
2. **Prompt Assembly:** Injecting context into a Jinja template.
3. **Execution:** Actually calling `litellm`.
4. **Critique:** Self-evaluating the output.

Crucially, **the user must be able to see these steps happen in real-time on the GUI and intercept them.** For example, the pipeline pauses at "Prompt Assembly," allows the user to manually edit the prompt, and then resumes.

**Your Objective (Outsourced Research & Skill Prompt Definition):**
1. **Architectural Analysis:** How should we structure the FastAPI backend to stream these state-machine transitions to the Next.js frontend? (Server-Sent Events vs WebSockets? How do we handle "pausing" execution to wait for a user's `POST` request with the edited prompt before resuming?).
2. **Director Agent Skill Prompt Creation:** Write a comprehensive System Prompt (Skill) for the "Pipeline Director Agent." This agent is responsible for dynamically assembling the steps of the pipeline based on the user's initial request.
3. **Output:** Provide your specific architectural recommendation for the Backend->Frontend pause/resume pipeline, and the exact Markdown text for the `pipeline_director.md` skill file.
