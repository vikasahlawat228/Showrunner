# Product Requirements Document (PRD): Showrunner Visual Studio
**Status:** Approved v2.0
**Date:** 2026-02-20

## 1. Problem Statement & Vision
**The Black Box Problem:** Current AI writing tools are "Black Boxes." Users provide a high-level prompt, wait, and get a wall of text. If the text is wrong, the user does not know *why* the AI made that decision, what context it used, or how to fix it other than blindly "regenerating." Furthermore, most tools rigidly define what a "Character" or "Location" is, forcing authors to adapt their worldbuilding to the software.

**The Goal:** Build the "Ultimate Extensible Co-Writer." 
1. **Total Structural Freedom:** Everything is a generic, customizable "Container." (Whether it's a Character, a Magic Spell, a Spaceship, or a Faction, the user defines the schema).
2. **Total Workflow Transparency:** Every AI action is a visible, inspectable pipeline (like n8n or Google Opu). The user sees exactly what context is gathered, what the compiled prompt looks like, and can intervene at any node.

## 2. Core Feature: "Everything is a Container"
The fundamental unit of the software is the **Container**.

### 2.1 Generic Container Model
*   A Container is a generic data construct with a user-defined `Type`.
*   Users can use pre-defined Types (Character, Scene, World) or map their own Custom Types using a UI-based Schema Builder (e.g., adding a "Mana Cost" field to a "Spell" container type).
*   **Infinite Nesting:** A "Solar System" container holds "Planet" containers, which hold "City" containers.

### 2.2 The Knowledge Graph
Because everything is a Container, the story world is a relational Knowledge Graph.
*   **Dynamic Relationships:** Containers link to one another (e.g., "Neo" is linked to "Morpheus" with the relationship `Teacher/Student`). 
*   **Visualizing Connections:** A node-based UI view where authors can physically map how plot points, rules, and characters intersect.

## 3. Core Feature: The Transparent "Glass Box" Workflow
AI interaction is modeled after node-based automation tools (n8n, ComfyUI, Zapier).

### 3.1 Node-Based Generation Pipelines
When a user asks the AI to "Write Scene 1", the software does not just spin a loading wheel. It executes a visible pipeline:
1.  **Context Gathering Node:** The UI shows exactly which Containers (Characters, Locations) were pulled into context. *User Intervention:* The user can click an "X" to remove a character the AI wrongfully included, or drag-in a missing container.
2.  **Prompt Assembly Node:** The UI shows the exact compiled text prompt. *User Intervention:* The user can manually type into this prompt before finalizing it.
3.  **Model Selection Node:** The user can select the LLM on a per-step basis (e.g., Claude 3.5 Sonnet for reasoning out the plot, Gemini 1.5 Pro for expanding the prose).

### 3.2 Human-in-the-Loop Iteration
*   **Multi-variant Generation:** The AI generates 2-3 variations of a plot point or dialogue exchange. The human picks, merges, or discards.
*   **Steerable Output:** If the generation is off, the user adds a specific steering prompt (*"Make the dialogue punchier"*) rather than a blind regeneration.

## 4. User Experience (UX) Layout
1. **The Infinite Canvas (The Graph):** Powered by React Flow. A spatial canvas where users map their Custom Containers, narrative arcs, and relationships visually.
2. **The Workbench (The Pipeline):** A view where users orchestrate the "Glass Box" AI workflows, adjusting context and prompts.
3. **Zen Mode (The Editor):** A distraction-free, keyboard-first writing environment. Typing `@` opens an autocomplete menu to instantly link and summon a Container (like Notion).

## 5. Success Metrics
*   **Context Transparency:** 100% of LLM prompts and injected context are visible and editable by the user before execution.
*   **Extensibility:** Users can successfully create a completely non-standard Container type (e.g., a "Heist Plan" container) without developer intervention.
*   **Trust:** Reduced "generation abandonment." Users fix bad generations via steering and prompt editing rather than deleting the output and starting from scratch.
