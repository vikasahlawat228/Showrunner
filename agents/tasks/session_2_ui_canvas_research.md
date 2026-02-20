# Task: React Flow UI & Graph Visualization

**Context:** We are building "Showrunner", a node-based, transparent AI co-writer. The primary workspace will shift from a basic drag-and-drop grid (using `@dnd-kit`) to an Infinite Node Canvas (like n8n, ComfyUI, or Miro). Users will drag Generic Containers (Characters, Scenes, Plot Points) onto the canvas and connect them with relational edges (e.g., "Character A [loves] Character B", "Scene 1 [leads to] Scene 2").

**Your Objective (Outsourced Research & Skill Prompt Definition):**
1. **Research & UX Analysis:** Analyze the optimal way to integrate `React Flow` into a Next.js (App Router) + Zustand architecture to represent a massive storytelling Knowledge Graph. How should we manage immense state (thousands of nodes/edges) without performance degradation? Should we break `store.ts` into specific slices?
2. **Graph Arranger Skill Prompt Creation:** Writing node graphs is easy for humans, but LLMs struggle to assign X/Y coordinates that don't overlap. Based on your research, write a comprehensive System Prompt (Skill) for a "Graph Layout Agent" or "Canvas Arranger." This agent’s job is to analyze a list of new nodes/edges created by the AI and assign them logical, non-overlapping X/Y coordinates using standard layout algorithms (like Dagre or ELK) before updating the UI state.
3. **Output:** Provide your React Flow architecture recommendation and the exact Markdown text for the `graph_arranger.md` skill file.
