# Session 12: Product Manager UX Audit & Flow Review

## 1. Executive Summary

The Phase 7 Alpha build of the "Showrunner" AI Co-Writer brings the core structural foundation of the "Glass Box" vision to life, successfully transitioning from a CLI-only application to a visual Next.js + FastAPI environment. The unified dark theme and Sidebar/Canvas layout provide a professional, premium feel suitable for a complex professional tool.

However, the current user experience is severely degraded by critical frontend bugs, unhandled errors, and incomplete integrations that prevent the user from actually experiencing the "Transparent Workflow" end-to-end. While the architecture (Event Sourcing, Generic Containers, React Flow) is solid, the UX layer lacks the polish and error resilience required to build confidence. The app feels fragile.

## 2. Flow Analysis

### Flow 1: Dashboard & Infinite Canvas
*   **Impression:** The React Flow canvas feels vast but currently serves as an unresponsive "empty state" rather than an intuitive workspace. 
*   **Friction Points:**
    *   **Data Hydration Failure:** Despite the Assets sidebar successfully loading "Test Character," the canvas remains completely empty ("Containers: 0 | Links: 0"). Users cannot drag-and-drop or visualize their existing containers.
    *   **Broken Minimap:** The React Flow minimap renders as an unstyled, pure white rectangle in the bottom-right corner, breaking the dark mode aesthetic and looking like a visual glitch.
    *   **Client/Server Mismatch error:** A persistent "1 Issue" badge appears in the bottom left. Clicking it reveals a Next.js Hydration Error (`A tree hydrated but some attributes of the server rendered HTML didn't match the client properties`). This severe React error likely breaks event handlers across the entire dashboard.

### Flow 2: AI Pipeline (Glass Box)
*   **Impression:** The core value proposition of the app—the transparent pipeline execution—is currently inaccessible in the UI.
*   **Friction Points:**
    *   The "Start Director Pipeline" button is present, but clicking it yields no visible feedback, loading states, or state transitions. 
    *   There is no active "Workbench" or "Pipeline View" visible to observe the SSE stream or the `PromptReviewModal`. The user is left wondering if the AI is generating anything in the background or if the system is simply frozen.

### Flow 3: Timeline Branching
*   **Impression:** The Timeline view toggle exists, but the user receives no onboarding or visual cues on how to utilize it to manage alternative drafts.
*   **Friction Points:**
    *   With the AI pipeline failing to trigger and create new event sourced events, the Timeline view remains a static, un-testable feature in this build. We need a way to visualize branching even when the AI fails.

### Flow 4: Schema Builder
*   **Impression:** This is the most complete and visually impressive flow. The split-pane design with the YAML preview on the right provides excellent transparency into how the Generic Container architecture works under the hood.
*   **Friction Points:**
    *   **Natural Language Generation Bug:** The "Generate Fields" wizard is fundamentally broken. When provided a prompt (e.g., "A spell with mana cost..."), the UI returns an unhandled `[object Object]` error string directly below the input field. 
    *   **Manual Fallback:** Fortunately, the manual fallback works flawlessly. Adding fields manually (e.g., `mana_cost` as a `Number`) updates the YAML preview instantaneously, which is highly satisfying.

## 3. PRD Alignment

*   **Where the app MEETS the vision:** 
    *   **"Everything is a Container" (Schema Builder):** The Schema Builder successfully demonstrates the "Total Structural Freedom" goal. Authors can indeed create custom entities like "Spells" with specific data types (`Number`, `Reference`, etc.) visually without writing code. 
    *   **Knowledge Graph (Assets Panel):** The filtering system on the top nav (World / Characters / Story / Scenes) aligns perfectly with the relational filtering goals.

*   **Where the app FALLS SHORT of the vision:**
    *   **"Total Workflow Transparency" (The Glass Box):** The Pipeline execution is currently a "Broken Box" rather than a "Glass Box." Because the SSE streaming and intermediate node views (Context Gathering, Prompt Assembly) are not rendering or firing properly, the primary objective of eliminating the black-box AI experience is not yet met.

## 4. Actionable Recommendations (Day 2 Sprint)

These are the immediate, high-priority tickets for the engineering team to address before Phase 8 (Beta):

**P0 (Critical Blockers):**
1.  **Fix Next.js Hydration Error:** Resolve the `data-jetski-tab-id` client/server mismatch on the root layout. This is likely breaking React Flow and button `onClick` handlers.
2.  **Fix AI Pipeline Trigger:** Ensure the "Start Director Pipeline" button correctly initiates the SSE stream and opens the Pipeline Execution view/modal so users can intercept prompts.
3.  **Fix Schema LLM Wizard:** Intercept and parse the `[object Object]` error in the Schema Builder's natural language generation step. Ensure the API response is correctly formatted and handled by the frontend state.

**P1 (Core UX Polish):**
4.  **Canvas Initial State & Hydration:** Ensure the React Flow canvas automatically populates with existing Containers listed in the Assets sidebar on initial load.
5.  **React Flow Minimap Styling:** Apply proper Tailwind utility classes to the React Flow minimap so it matches the application's dark theme instead of rendering as a white box.
6.  **Pipeline Loading States:** Add visual feedback (spinners, toasts, or node-activation styles) immediately upon clicking "Start Director Pipeline" so the user knows the AI is thinking.

**P2 (Quality of Life):**
7.  **Empty Canvas Onboarding:** If the graph is truly empty, display a faint, centered call-to-action on the canvas grid (e.g., "Drag a Container from the Assets panel to begin mapping your story").
