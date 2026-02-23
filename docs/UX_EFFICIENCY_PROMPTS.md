# UX & UI Efficiency Enhancement Prompts

This document contains modular instructions for autonomous agent sessions to implement the UX and UI efficiency improvements proposed for the Showrunner application. 

Each prompt is designed to be handed off to an independent AI coding session. Agents are explicitly encouraged to be innovative and think of even better or more efficient ways to achieve the final UX goals.

---

## Prompt 1: The "Setup Tax" - Data-First Worldbuilding & Drag-and-Drop
**Target:** Frontend & Backend capabilities for entity creation, knowledge graph, and schema inference.

**Prompt for Session:**
> Your objective is to eliminate the "Setup Tax" for worldbuilding in the Showrunner application, specifically improving Master CUJs 1 and 2. Currently, writers must define rigid schemas upfront using a wizard before populating their world.
> 
> **Core Task:** Implement "Implicit Schema Inference" and "Drag-and-Drop Context" creation.
> - Modify the system to allow the creation of bare, schema-less `GenericContainer` buckets. Users should be able to just add arbitrary key-value pairs (e.g., `power_source: emotional resonance`).
> - Build a background service that detects structural patterns across these buckets and proactively suggests creating a formal Schema when similar structures emerge.
> - On the frontend Zen Editor, implement a drag-and-drop interaction: users should be able to highlight a paragraph of lore from their manuscript, drag it to the Knowledge Graph sidebar, and instantly spawn a Bucket based on the highlighted text.
> 
> **Challenge:** Be innovative! Can you think of a more efficient or magical way to bridge the gap between unstructured prose and structured graph data? Feel free to propose and implement a better interaction model if it feels faster and more intuitive for the writer.

---

## Prompt 2: Eliminating Approval Fatigue - The Smart Glass Box
**Target:** Pipeline Execution Engine, Approval Gates, and Event Sourcing UI.

**Prompt for Session:**
> Your objective is to reduce "Approval Fatigue" in Showrunner workflows (improving Master CUJ 8) while strictly maintaining the transparency and trust of the "Glass Box" philosophy.
> 
> **Core Task:** Shift from mandatory modal pop-ups to "Confidence-Based Auto-Execution" combined with a flexible "Timeline Audit Trail".
> - Update the pipeline engine and AI endpoints to accept a confidence threshold (e.g., if AI confidence > 90% and continuity errors = 0, automatically approve the node output).
> - Replace blocking modal popups with a non-intrusive, scrolling feed/sidebar of auto-executed steps.
> - Ensure the Timeline Audit Trail allows the writer to retroactively click any step in the feed, inspect the exact prompt, context, and model used, and seamlessly reverse or edit that operation without breaking the main state (utilizing our event-sourcing architecture).
> 
> **Challenge:** We want the system to feel proactive but safe. Is there a better UI paradigm than a sidebar feed for retroactive auditing? Think outside the box and implement the most fluid, unobtrusive review mechanism possible.

---

## Prompt 3: Workflow Creation via "Macro Recording"
**Target:** Workflow Studio, Action Tracking, Pipeline Builder.

**Prompt for Session:**
> Your objective is to reinvent how custom AI pipelines are created (Master CUJs 8 and 10). Natural language pipeline generation can carry a cognitive load and visual DAG builders are complex. We want users to build pipelines simply by "doing the work" once.
> 
> **Core Task:** Implement a graphical "Record Workflow" feature.
> - Add a prominent "Record" toggle in the main UI. When active, intercept and record a sequence of high-level AI and UI actions (e.g., text selection ->`/brainstorm` invocation -> option selection -> `/expand` -> save).
> - When the user hits "Stop", distill these recorded actions into a reusable pipeline DAG inside the Workflow Studio.
> - Generalize the specific inputs from the recorded session into abstract prompt variables for the pipeline template (so it can be re-run on different scenes).
> 
> **Challenge:** Translating ad-hoc user UI interactions into a rigid, reusable DAG is complex. Feel free to refine this concept or propose a vastly superior method for capturing and automating a writer's personal flow without requiring them to become a visual programmer.

---

## Prompt 4: Semantic Zooming & Inline Edit Resolution
**Target:** Timeline View, Zen Editor, Continuity Analyst Integration.

**Prompt for Session:**
> Your objective is to drastically reduce navigation friction between the structural "10,000-foot view" and the prose "ground level" (Master CUJs 3, 5, 6).
> 
> **Core Task:** Implement Semantic Zooming and unified inline actions.
> - Create a seamless "Semantic Zoom" UI: Scrolling heavily on the Timeline View should visually zoom from Arc -> Chapter -> Scene, and smoothly crossfade directly into the Zen Editor for that scene's actual prose, without traditional page loads or hard navigation jumps.
> - Enhance the Continuity Analyst feedback: Instead of just listing errors in a side panel, weave an `Apply AI Fix` button directly next to flagged text inside the Zen Editor, showing a 1-click red/green inline diff.
> - Introduce "Inline Alt-Takes" to replace full timeline branches for minor scene variations. Allow a writer to highlight a paragraph and cycle through locally scoped "Takes" (Take 1, Take 2).
> 
> **Challenge:** Semantic zooming performance and UX can be tricky to get right. How can we make the transition between "structural macro-view" and "prose micro-editing" feel instantaneous and deeply connected? If you have a better pattern for bridging structure and editing, build it!

---

## Prompt 5: Proactive Ambient AI
**Target:** Zen Editor, Storyboard, AI Orchestrator UI.

**Prompt for Session:**
> Your objective is to transform Showrunner from a reactive tool (waiting for slash commands) into a proactive "Ambient AI" partner (Master CUJs 3 and 4).
> 
> **Core Task:** Implement Ambient Generation within the workspace.
> - Introduce "Customizable Ghost Text" in the Zen Editor. During idle moments (user stops typing for 2 seconds), fetch contextually aware ahead-of-cursor prose suggestions. Note: the writer must be able to define the constraints of this ghost text (e.g., "Only suggest dialogue", or "Use the 'Action' model temperament").
> - Implement "Live Margin Storyboarding": As the writer types prose, auto-generate low-resolution sketch panels in a side margin that scroll alongside the text, dynamically reacting to the beats being written in real-time.
> 
> **Challenge:** Ambient generation can easily become annoying or distracting if it steals focus. How do we make the ghost text and live storyboarding feel magically helpful rather than intrusive? Implement a solution that sets a new standard for non-blocking, ambient AI collaboration.
