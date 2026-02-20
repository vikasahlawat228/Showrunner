# Task: Event Sourcing & Alternate Timelines

**Context:** We are building "Showrunner", a node-based AI co-writer. Generative AI is unpredictable. If the AI writes a scene and updates the state of 5 different Generic Containers (Characters, Factions), standard CRUD overwriting is dangerous. We need an "Undo Tree" that allows users to branch alternate timelines of the story, exactly like Git `.

**Your Objective (Outsourced Research & Skill Prompt Definition):**
1. **Architectural Analysis:** How can we implement a lightweight Event Sourcing log in Python/SQLite? Instead of mutating the local YAML files directly, every AI action should append a diff/event (e.g., `UpdateAttributeEvent(container_id='123', field='status', old='alive', new='dead')`). This log should allow the user to "checkout" a previous state, thereby spawning a parallel branch of the story. 
2. **Continuity Critic Skill Prompt Creation:** Write a comprehensive System Prompt (Skill) for a "Continuity Analyst Agent." This agent's job is to read the Event Log diffs proposed by the Writer Agent, and cross-reference them against the SQLite Knowledge Graph to ensure no sudden paradoxes are introduced (e.g., killing a character that is required in a future planned node).
3. **Output:** Provide your specific architectural recommendation for the Python Event Sourcing/Branching strategy, and the exact Markdown text for the `continuity_analyst.md` skill file.
