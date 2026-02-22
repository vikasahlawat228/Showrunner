# Showrunner: Master Critical User Journeys (CUJs)
**Status:** Living Document
**Last Updated:** 2026-02-22

---

## How to Read This Document

Each journey maps a **real writer scenario** to the ideal Showrunner experience — from the moment the writer opens the app to the moment they close it for the day. Every journey specifies:

- **Persona** — who is doing this
- **Trigger** — what brings them to the app
- **Steps** — the ideal flow, referencing exact pages, components, and features
- **Glass Box Moments** — where the writer sees the AI's reasoning
- **Friction to Eliminate** — current UX gaps that block this ideal flow
- **Success Metric** — how we know the journey works

The three personas from the PRD drive all journeys:
1. **The Architect** — meticulous planner, worldbuilder, structure-first
2. **The Discovery Writer (Pantser)** — writes fragments, discovers story in the process
3. **The Visual Storyteller** — thinks in panels, camera angles, and storyboards

---

## Design Philosophy & Research Foundation

### The Core Insight

Modern IDE agents (Cursor, Claude Code, Windsurf) proved that a **persistent conversational interface** can replace most point-and-click workflows without losing power. Writers don't want to navigate 9 different pages to do their work — they want to **talk to the tool** and have it execute on their behalf, while visual surfaces (storyboard, timeline, knowledge graph) remain available as **read-only views** the agent can update.

### Research-Backed Design Patterns

| Pattern | Inspired By | Showrunner Adaptation |
|---|---|---|
| **Free-form sessions with resume** | Claude Code `--resume`, `--continue` | Named writing sessions, resume from session picker, persistent per-project |
| **Context compaction** | Claude Code `/compact`, Cursor `/compress` | `/compact` summarizes conversation, preserves story-critical context, respects token budget |
| **@-mention for deterministic context** | Cursor `@file`, Windsurf `@codebase`, VS Code `@workspace` | `@character`, `@scene`, `@research`, `@pipeline`, `@bucket` — pulls entity into chat context |
| **Plan/Execute mode separation** | Cline Plan & Act, Windsurf Planning Mode, Cursor custom modes | `/plan` mode for complex tasks — agent proposes steps, writer approves, then `/execute` |
| **Artifact preview** | Claude Artifacts split-screen | Chat generates content → preview panel shows live result (prose, outline, panels, schema) |
| **Lorebook-style context injection** | NovelAI lorebook entries with keyword triggers | Project Memory auto-injects relevant world rules, character DNA, decisions when keywords appear |
| **Async background tasks** | GitHub Copilot coding agent | Long-running pipelines continue in background, chat notifies on completion |
| **Multi-step agentic workflows** | Replit Agent, Cursor Agent mode | "Build Chapter 5" → agent plans outline → writes scenes → runs style check → reports back |
| **Guided/Auto write modes** | Sudowrite Story Engine | `/auto-write` lets agent draft with minimal input; `/guided` shows suggestions for writer to pick |
| **Structured content pipelines** | Jasper Grid | Chat can trigger pre-built pipeline templates by name: "run Scene→Panels on Ch.3 Sc.1" |

### Architectural Principle: Hybrid UI

The Agentic Chat is **NOT** a replacement for the existing UI. It's a **superlayer** that:

1. **Starts as a sidebar** — collapsible panel on the right side of every page
2. **Can control any page** — "open the storyboard for Ch.3" navigates the main view
3. **Some operations become chat-ONLY** — Quick capture, pipeline control, bulk operations, context queries
4. **Visual operations stay GUI** — Storyboard drag-n-drop, timeline visualization, KG minimap remain direct manipulation
5. **The agent can "show" results** — Chat responses include previews (prose, outlines, schemas, panels) in an artifact-like panel

---

## The Agentic Chat Architecture

### Chat Capabilities (The "Tool Belt")

The chat agent has access to these tool categories, mirroring the 10-agent ecosystem:

```
┌─────────────────────────────────────────────────────────────┐
│  AGENTIC CHAT TOOL BELT                                     │
│                                                             │
│  📝 WRITE     — Draft prose, expand, rewrite, dialogue      │
│  🧠 BRAINSTORM — Generate ideas, "what if" scenarios         │
│  📐 OUTLINE   — Create/modify story structure                │
│  🔬 RESEARCH  — Deep-dive factual topics, search library     │
│  🔍 CONTINUITY — Check for plot holes, validate consistency  │
│  🎭 STYLE     — Check tone, voice, pacing                   │
│  🌍 TRANSLATE — Translate with glossary, cultural adaptation │
│  🎨 STORYBOARD — Generate panels, suggest layouts            │
│  ⚙️ PIPELINE  — Run/stop/resume workflow templates           │
│  📦 BUCKET    — Create/edit/link any bucket type             │
│  🔎 SEARCH    — Semantic search across all buckets           │
│  🗺️ NAVIGATE  — Open pages, scenes, panels in main view     │
│  📊 STATUS    — Project progress, session stats, pending items│
│  💾 MEMORY    — Save/recall project decisions and preferences │
│                                                             │
│  @-MENTION TYPES:                                           │
│  @character  @scene  @chapter  @location  @item             │
│  @research   @pipeline  @schema  @bucket  @session          │
│  @all (semantic search across everything)                   │
└─────────────────────────────────────────────────────────────┘
```

### Context Management: The Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: PROJECT MEMORY (Persistent)                   │
│  ─────────────────────────────────────                  │
│  • Story decisions (tone, POV, rules)                   │
│  • World rules ("magic costs memories")                 │
│  • Character DNA blocks (stable identity)               │
│  • Style guide preferences                              │
│  • Custom glossary / terminology                        │
│  • Stored as: project_memory.yaml                       │
│  • Auto-injected into EVERY chat session                │
│  • Equivalent to: Claude Code's CLAUDE.md               │
│                                                         │
│  LAYER 2: SESSION CONTEXT (Ephemeral, Compactable)      │
│  ─────────────────────────────────────                  │
│  • Current conversation history                         │
│  • @-mentioned entities and their data                  │
│  • Agent execution results and approvals                │
│  • Working drafts and in-progress edits                 │
│  • Token budget: configurable (default 100K)            │
│  • On /compact: LLM summarizes into ~2K token digest    │
│  • On session end: digest persisted to session_log      │
│  • Equivalent to: Claude Code conversation context      │
│                                                         │
│  LAYER 3: ON-DEMAND RETRIEVAL (Pulled by agent)         │
│  ─────────────────────────────────────                  │
│  • Semantic search via ChromaDB                         │
│  • KG relationship traversal                            │
│  • Research Library lookups                             │
│  • Previous session digests                             │
│  • Full bucket data on @-mention                        │
│  • Equivalent to: Cursor @codebase, Windsurf RAG       │
└─────────────────────────────────────────────────────────┘
```

### Session Lifecycle

```
START SESSION                    DURING SESSION                 END SESSION
─────────────                    ──────────────                 ───────────
• Name session (optional)        • Free-form chat               • /end "summary"
• Auto-load Project Memory       • @-mention pulls context      • LLM generates digest
• Auto-load current page         • Agent executes tools          • Digest → session_log
  context (scene/chapter)        • /compact when context full   • Stats persisted
• Resume from session picker     • Background tasks notify      • "Next steps" suggested
  or /resume <name>              • Artifacts show previews      • Session appears in picker
```

---

## Journey 1: "I Have Fragments in My Head" — First Session with a New Story

**Persona:** Discovery Writer
**Trigger:** Writer has a story rattling around — they know the opening image, the ending, two key emotional beats in the middle, and a character name. Nothing else. They want to dump it all before they lose the spark.

### Ideal Flow

#### Phase A: Quick Capture (0–5 minutes)

1. **Open Showrunner → `/dashboard`**
   - If first time: A single-card onboarding says "Start by capturing what's in your head."
   - The Command Center left panel shows a "New Project" card. Writer clicks it.
   - **Quick modal**: Just a name. "Midnight Chronicle." Done. Project created.

2. **Jump to Brainstorm → `/brainstorm`**
   - Empty ReactFlow canvas with a gentle prompt: "Type your first idea and press Enter."
   - **Quick Capture input bar** at the bottom (like a chat box). Writer types rapidly:
     - "Zara is a thief with a cursed blade"
     - "The story ends with Zara choosing to destroy the blade instead of using it"
     - "There's a market scene — rain, tension, she meets Kael for the first time"
     - "Kael betrays her in Act 2"
     - "The blade whispers to her at night"
   - Each line becomes an **IdeaCardNode** on the canvas, auto-positioned in a loose cluster.
   - Cards auto-tagged by the Brainstorm Agent: `character`, `ending`, `scene`, `plot_point`, `worldbuilding`. Color-coded accordingly.

3. **AI Suggests Connections**
   - Writer clicks "Suggest" in the SuggestionPanel.
   - The Brainstorm Agent analyzes the 5 cards and returns:
     - Suggested edge: "Zara → cursed blade" (character-item relationship)
     - Suggested edge: "market scene → Kael betrayal" (could be foreshadowed here)
     - Suggested new card: "What is the blade's curse? What does it cost Zara?"
     - Suggested theme: "Sacrifice vs. Power"
   - Writer accepts the edges (they animate into place) and the new card.
   - **Glass Box Moment**: The sidebar shows what context the AI used and which model ran it.

4. **Brainstorm → Buckets (seamless transition)**
   - Writer right-clicks "Zara" card → "Create as Character Bucket"
   - A minimal form pre-fills: Name = "Zara", one-liner = "A thief with a cursed blade"
   - Writer adds nothing else yet. Saves. Zara now exists in the Knowledge Graph.
   - Same for "Cursed Blade" → Item bucket, "The Whispering Market" → Location bucket.

**Time spent:** 5 minutes. Five ideas captured, three buckets created, AI-suggested connections mapped. Zero schema configuration required.

#### Phase B: Rough Structure (5–15 minutes)

5. **Jump to Timeline → `/timeline`**
   - The **StoryStructureTree** in the left panel shows the project is empty.
   - Writer clicks "Add Season" → "Season 1" created.
   - Under Season 1: "Add Arc" → "The Awakening"
   - Under Arc: "Add Act" → Act 1, Act 2, Act 3 (three clicks).
   - Under Act 1: "Add Chapter" → "Chapter 1: The Market"
   - Under Chapter 1: "Add Scene" → "Scene 1: Rain in the Market"
   - Writer repeats loosely: Act 3 gets "Chapter 7: The Choice" with "Scene: Blade Destruction"
   - Act 2 gets "Chapter 4: The Betrayal"
   - **The tree is sparse and that's fine.** Acts have 1 chapter each. The middle is empty.

6. **Emotional Arc Preview**
   - Even with 3 scenes, the **EmotionalArcChart** shows a crude line: neutral → (gap) → high tension → (gap) → bittersweet resolution.
   - The chart highlights "Flat Zone: Act 2 has no scenes yet" — a gentle nudge, not a blocker.

#### Phase C: First Prose Session (15–45 minutes)

7. **Open Scene in Zen → click "Open in Zen" on "Scene 1: Rain in the Market"**
   - `/zen?scene_id=xxx` loads. The **ZenEditor** is empty, cursor blinking.
   - **ContextSidebar** on the right shows:
     - Linked characters: Zara (from brainstorm linking)
     - Location: The Whispering Market
     - Scene mood: unset (writer can set it later)
   - Writer starts typing:

   > The rain fell sideways through the Market's cloth canopy, drumming against clay pots and copper lamps. Zara pulled her hood lower and stepped between the stalls, one hand on the hilt of the blade at her hip.

8. **Entity Detection fires (debounced 2s)**
   - The system detects: `Zara` (matched to Character bucket), `the blade` (matched to "Cursed Blade" item).
   - ContextSidebar updates: Zara's card appears with her one-liner. Cursed Blade card appears.
   - A subtle suggestion: "Create location: The Market's cloth canopy?" — Writer dismisses (it's part of Whispering Market).

9. **Writer keeps writing, uses `/expand` slash command**
   - Writer selects a paragraph about the market atmosphere, types `/expand`.
   - The **Writing Agent** (Claude 3.5 Sonnet) fires.
   - **Glass Box**: PromptReviewModal opens showing:
     - Context used: Zara character summary, Whispering Market location, scene mood
     - System prompt: "Expand this passage with sensory details..."
     - Model: `anthropic/claude-3.5-sonnet`
   - Writer glances at context, approves.
   - Expanded prose appears inline. Writer edits two sentences. Moves on.

10. **Auto-save fires every 2 seconds while idle**
    - Fragment saved to `containers/fragment/`.
    - Event logged to `event_log.db`.
    - Toast: "Saved" (tiny, bottom-right, disappears in 1s).

11. **Word count + session stats visible in the footer bar**
    - "342 words | +342 this session | ~1 min read"

**Time spent:** 30 minutes. First scene drafted. Three AI assists used. Full context transparency.

### Friction to Eliminate
- Brainstorm "Quick Capture" input bar doesn't exist yet — cards require title + description fields.
- Right-click → "Create as Bucket" doesn't exist on IdeaCardNode.
- "Open in Zen" button exists on StoryStructureTree but needs scene_id query param wired.
- Entity detection sometimes misses due to 500 errors on `/detect-entities`.

### Success Metric
Writer captures 5+ ideas and writes 300+ words in their first 45-minute session without touching Settings, Schemas, or Pipelines.

---

## Journey 2: "Building Out the World Bible" — Deep Worldbuilding Session

**Persona:** The Architect
**Trigger:** Writer has the rough structure from Journey 1. Now they want to build out the world: magic system, factions, geography, character backstories. They want AI help but want to control every schema.

### Ideal Flow

#### Phase A: Custom Schema Creation (0–10 minutes)

1. **Navigate to `/schemas`**
   - Writer sees existing default schemas: character, location, scene, etc.
   - Writer clicks "New Schema" and uses the **NL Wizard**:
     - Types: "A magic system with power source, cost to the user, visual manifestation, societal restrictions, and rarity level"
     - The **Schema Wizard** (Gemini Flash) generates 5 `FieldDefinition` objects:
       - `power_source` (string), `user_cost` (string), `visual_manifestation` (string), `societal_restrictions` (list[string]), `rarity` (enum: common/uncommon/rare/legendary)
     - **Glass Box**: Writer sees the NL prompt that was sent and the parsed fields.
     - Writer tweaks: renames `user_cost` to `personal_cost`, adds a `limitations` field (list[string]).
     - **SchemaPreview** on the right shows live YAML output.
     - Saves as "magic_system".

2. **Create another schema: "Faction"**
   - NL Wizard: "A political faction with leader, territory, ideology, military strength (1-10), and allied/rival factions"
   - Generated fields include a `reference` type for `leader` (pointing to a Character), and `reference` types for `allies`/`rivals` (pointing to Faction).
   - Writer approves. Saves.

#### Phase B: Populating the World (10–30 minutes)

3. **Back to `/dashboard`**
   - The Knowledge Graph canvas is now alive — Zara, Cursed Blade, Whispering Market, Season 1 structure all visible as nodes.
   - Writer clicks "+" in the sidebar → selects "magic_system" type → creates "Whisper Magic":
     - power_source: "Emotional resonance with ancient artifacts"
     - personal_cost: "Memory loss — each use erases a personal memory"
     - visual_manifestation: "Black smoke that forms into shapes"
     - rarity: "rare"
   - On save, the KG canvas animates a new node into view.

4. **Research Agent for factual grounding**
   - Writer navigates to `/research`.
   - Types: "What are historical examples of magic systems where power comes at a personal cost? Think Faustian bargains, Greek mythology, etc."
   - The **Research Agent** (Gemini Pro) executes.
   - **Glass Box**: PromptReviewModal shows the compiled prompt with existing world context.
   - Results come back as a structured research topic:
     - Summary, key_facts (Faust, Icarus, The Monkey's Paw), constraints, story_implications.
     - Confidence: "high"
   - Writer approves. Research bucket "Faustian Bargain Tropes" saved to Research Library.
   - Auto-linked to "Whisper Magic" bucket.
   - **Future AI calls about Whisper Magic now include this research context automatically.**

5. **Character backstory generation**
   - Writer opens Zara's character bucket from the dashboard inspector.
   - Clicks "Generate Backstory" (a Quick Action).
   - The **Writing Agent** fires with context: Zara's one-liner, Whisper Magic rules, Cursed Blade item, market scene.
   - **Glass Box**: Full context assembly visible. Token budget: 3200/4000 used.
   - Writer reviews the 3-paragraph backstory. Edits the second paragraph. Saves.

#### Phase C: Relationship Mapping (30–40 minutes)

6. **Knowledge Graph interaction**
   - Writer drags an edge from "Zara" to "Whisper Magic" → relationship type dropdown: "practitioner_of".
   - Drags "Kael" to "Zara" → "rival" / "former_ally".
   - Drags "Cursed Blade" to "Whisper Magic" → "artifact_of".
   - Each edge creation fires an event to `event_log.db`.

7. **Continuity Check**
   - Writer clicks "Check Continuity" on the dashboard.
   - The **Continuity Analyst** scans all relationships and flags:
     - "Kael is referenced in Scene 1 but has no character bucket yet. Create one?"
   - Writer creates Kael with a one-liner and moves on.

### Friction to Eliminate
- NL Wizard currently returns `[object Object]` errors (per UX audit). Must parse schema generation response correctly.
- "Generate Backstory" Quick Action doesn't exist as a button on the inspector — writer would need to go to Zen mode and use `/expand`. Should be a 1-click action.
- Edge creation on the ReactFlow canvas may not be wired to persist relationships.

### Success Metric
Writer creates 2+ custom schemas, 5+ world buckets, and 3+ relationship edges. Research Library has 1+ topic. All done without writing Python or YAML by hand.

---

## Journey 3: "Writing Through the Middle" — Sustained Writing Session

**Persona:** Discovery Writer
**Trigger:** The writer has their opening and ending. Today they're tackling the dreaded middle — Act 2. They need AI help with structure and momentum but want to stay in flow.

### Ideal Flow

#### Phase A: AI-Assisted Outlining (0–15 minutes)

1. **Open `/pipelines` → Template Gallery**
   - Writer selects the "Concept → Outline" template.
   - Input: "Kael betrays Zara by revealing her secret to the faction leaders. She loses the blade temporarily. The middle act should build tension toward this betrayal while Zara believes Kael is her closest ally."
   - Template executes:
     - Step 1: **Brainstorm Agent** generates 5 "what if" scenarios for the betrayal arc.
     - **Approval Gate**: Writer reviews scenarios. Picks "Kael is secretly working for the faction to repay a debt." Edits it. Approves.
     - Step 2: **Story Architect** generates a 4-chapter outline for Act 2.
     - **Approval Gate**: Writer sees the outline with chapter summaries. Reorders chapter 3 and 4. Adds a note to chapter 2. Approves.
     - Step 3: Structure buckets auto-created — 4 chapters, each with 2-3 scene placeholders.
   - The StoryStructureTree in `/timeline` now shows Act 2 populated.

2. **Writer reviews the structure in `/timeline`**
   - The tree shows: Act 2 → Ch.4 "Trust Building" → Ch.5 "First Cracks" → Ch.6 "The Reveal" → Ch.7 "Aftermath"
   - The **EmotionalArcChart** updates: tension gradually rising through Act 2, spiking at Ch.6.
   - **Story Ribbons** show Zara present in all scenes, Kael present in Ch.4-6, disappearing in Ch.7 (powerful visual storytelling).

#### Phase B: Deep Writing with Context (15–90 minutes)

3. **Open Ch.5 Scene 1 in Zen Mode**
   - ContextSidebar loads automatically:
     - Characters in this scene: Zara, Kael (from outline)
     - Previous scene summary: "Zara and Kael successfully raided the faction armory" (from Ch.4 context_window)
     - Research: "Faustian Bargain Tropes" (linked to Whisper Magic)
     - Continuity note: "Zara's blade was established as obsidian in Scene 1 — maintain consistency"
   - Writer writes freely for 20 minutes. 800 words flow.

4. **Mid-session, writer hits a wall. Uses `/brainstorm` inline.**
   - Types `/brainstorm How does Kael start distancing himself without being obvious?`
   - **Brainstorm Agent** fires with full Act 2 context.
   - Returns 4 suggestions:
     1. "Kael stops making eye contact during their planning sessions"
     2. "Kael volunteers for solo missions, claiming efficiency"
     3. "Kael gives Zara a gift — a token from the faction he's secretly allied with"
     4. "Kael starts questioning Zara's reliance on the blade, planting seeds of doubt"
   - Writer picks #3 and #4, incorporates them into the scene.

5. **Writer references another character with `@`**
   - Types `@` — the MentionList dropdown appears with semantic search.
   - Types `@faction leader` — even though no bucket is named exactly that, semantic search finds "The Iron Council" faction and its leader "Commander Vex".
   - Selects "Commander Vex" — auto-linked to this scene.
   - ContextSidebar updates with Commander Vex's details.

6. **Style Check before ending the session**
   - Writer selects the whole scene text, types `/check-style`.
   - **StyleScorecard** appears in the sidebar:
     - Overall: 0.85
     - Strengths: "Strong sensory detail", "Dialogue feels distinct"
     - Issues: "Paragraph 3 shifts to present tense (inconsistency)", "Zara's internal monologue is too expository in paragraph 5"
   - Writer fixes both issues. Re-checks: 0.92.

7. **Session summary**
   - Footer shows: "1,247 words | +1,247 this session | ~5 min read"
   - Writer closes the session. All fragments auto-saved. Events logged.

### Friction to Eliminate
- The "Concept → Outline" template must actually create structure buckets (Season → Scene) automatically — currently it generates text output but doesn't persist structure.
- `/brainstorm` slash command needs to be wired in SlashCommandList.tsx (currently only `/expand`, `/dialogue`, `/describe`, `/translate`, `/check-style` exist).
- Style check results should persist per scene for tracking improvement over time.

### Success Metric
Writer generates a 4-chapter outline in 15 minutes and writes 1000+ words in the subsequent writing session, using 3+ AI assists without leaving Zen Mode.

---

## Journey 4: "From Script to Storyboard" — Visual Storytelling Session

**Persona:** Visual Storyteller
**Trigger:** Writer has a completed scene in Zen Mode. Now they want to break it into panels, define camera angles, and create image prompts for an artist or AI image generator.

### Ideal Flow

#### Phase A: Panel Layout Intelligence (0–5 minutes)

1. **Navigate to `/storyboard`**
   - The scene list on the left shows all scenes with completion indicators.
   - Writer selects "Scene 1: Rain in the Market" (which has 800 words of prose).

2. **Click "Suggest Layout"**
   - The **LayoutSuggestionPanel** appears.
   - AI analyzes the narrative beat type of each paragraph:
     - Paragraph 1: `establishing` → Wide shot, 2 panels
     - Paragraph 2: `action` → Medium + close-up, 3 panels
     - Paragraph 3: `dialogue` → Over-the-shoulder alternating, 4 panels
     - Paragraph 4: `reveal` → Full-page splash, 1 panel
   - Total suggested: 10 panels with recommended sizes, camera angles, and composition notes.
   - **Glass Box**: Writer sees which model analyzed this and what context was used.

3. **Writer clicks "Apply & Generate"**
   - 10 panels created with metadata (panel_type, camera_angle, description extracted from prose).
   - Each panel has a description field pre-filled from the relevant prose paragraph.
   - Panels appear in the **SceneStrip** (horizontal strip view).

#### Phase B: Panel Refinement (5–20 minutes)

4. **Drag-to-reorder panels in the strip**
   - Writer moves the "reveal" panel from position 10 to position 7 (wants the reveal earlier).
   - Reorder persisted via `POST /panels/reorder`.

5. **Edit panel details**
   - Click panel 3 → **PanelEditor** slides out on the right.
   - Writer adjusts: camera_angle from "medium" to "close_up_face", adds dialogue: "You're not from around here, are you?"
   - Adds character reference: links to Kael bucket.

6. **Switch to Semantic Canvas view**
   - Toggle from "Strip" to "Canvas" at the top.
   - **SemanticCanvas** shows all 10 panels arranged in a 2D grid with zoom.
   - Writer can see the visual flow of the entire scene at once.
   - Zoom in on any panel for detail; zoom out for overview.

#### Phase C: Image Prompt Generation (20–30 minutes)

7. **Select panels for image prompt generation**
   - Writer selects panels 1, 4, 7 (the key establishing/action/reveal shots).
   - Runs the "Scene → Panels" pipeline template (or clicks "Generate Prompts").
   - The **Prompt Composer** (GPT-4o) generates optimized image generation prompts:
     - Panel 1: "Rain-soaked market at dusk, cloth canopy overhead, warm copper lamp light, a hooded figure (Zara) walking between stalls, wide establishing shot, manga art style, 9:16 vertical, high detail"
   - **Glass Box**: PromptReviewModal shows each prompt with the character DNA used, the location description sourced, and the style guide applied.
   - Writer edits panel 7's prompt to emphasize the blade's glow. Approves all.

8. **Export prompts**
   - Writer clicks Export → gets a JSON or text file of all panel prompts.
   - Can paste these into Midjourney, DALL-E, Stable Diffusion, or any external tool.
   - (Future: Direct webhook integration from pipeline steps.)

#### Phase D: Voice-to-Scene (Alternative Entry Point)

9. **For a new scene, writer uses Voice-to-Scene**
   - Clicks the microphone icon in the storyboard header.
   - **VoiceToSceneButton** activates browser speech recognition.
   - Writer speaks: "Zara runs through the back alleys. Kael is chasing her. She vaults over a cart. Close-up on her face, determined. Wide shot of the alley, rain pouring. She reaches a dead end and turns to face him."
   - Transcript appears for editing. Writer fixes "carts" to "cart" and confirms.
   - System generates: 5 panels with beat types (action/action/close-up/establishing/confrontation).
   - Panels appear in the strip. Writer adjusts and saves.

### Friction to Eliminate
- Panel image prompt generation (Prompt Composer agent) needs to be wired end-to-end with character DNA and style guide context injection.
- Export specifically for image prompts (not full manuscript export) needs a dedicated flow.
- Voice-to-Scene works but the transcript review step could be more streamlined.
- The storyboard page has had build errors (syntax error in page.tsx per audit). Must be rock-solid.

### Success Metric
Writer goes from completed prose to 10 exportable panel prompts in under 30 minutes. Voice-to-Scene creates accurate panels from verbal scene description.

---

## Journey 5: "What If?" — Alternate Timeline Exploration

**Persona:** The Architect
**Trigger:** Writer has a solid Act 2, but wonders: "What if Kael didn't betray Zara? What if instead he confessed his debt and they faced the faction together?" They want to explore this without losing their main draft.

### Ideal Flow

1. **Navigate to `/timeline`**
   - The **TimelineView** shows the main branch with all events.
   - Writer scrolls to the event: "Scene: The Betrayal (Ch.6, Scene 1)" — the moment Kael betrays Zara.

2. **Click "Branch from here"**
   - Input: Branch name = "kael-confesses"
   - `POST /timeline/branch` creates a new branch whose HEAD points to the event *before* the betrayal scene.
   - The timeline visualization now shows a fork — main branch continues to Act 3, new branch is empty.

3. **Switch to the new branch**
   - Writer clicks "kael-confesses" in the **BranchList** sidebar.
   - The story state is now "as if the betrayal never happened."
   - StoryStructureTree reflects this: Ch.6 exists but has no "Betrayal" scene.

4. **Write the alternative**
   - Writer adds a new scene to Ch.6: "The Confession"
   - Opens in Zen Mode. Writes 600 words where Kael confesses.
   - All saves go to the `kael-confesses` branch. Main branch untouched.

5. **Compare branches**
   - Writer clicks "Compare" in BranchList.
   - **BranchComparison** opens a two-column diff:
     - Left (main): "Kael reveals Zara's secret → She loses the blade → Aftermath"
     - Right (kael-confesses): "Kael confesses → They plan together → [unwritten]"
   - Additions in green, removals in red, changes in amber.
   - Writer can see exactly what diverges and decide which path to keep — or keep both.

6. **Continuity Analyst auto-validates**
   - On the new branch, the Continuity Analyst flags:
     - "Zara references losing the blade in Ch.7 Scene 2 (inherited from main timeline), but on this branch the blade was never lost."
   - Writer sees this in the PendingApprovals panel. Decides to fix Ch.7 on this branch.

### Friction to Eliminate
- Branch switching should contextually update StoryStructureTree (currently it always shows the "main" structure).
- The comparison view needs polished styling — currently functional but not beautiful.
- Writing on a branch should be seamless in Zen Mode (the branch context needs to flow through to fragment saves).

### Success Metric
Writer creates an alternate timeline, writes a divergent scene, and compares both timelines side-by-side in under 15 minutes.

---

## Journey 6: "Polishing Before Export" — Final Draft Session

**Persona:** All three personas converge here
**Trigger:** The manuscript is "done" — rough draft complete across all acts. Writer wants to polish prose, check continuity, ensure character voices are distinct, and export.

### Ideal Flow

#### Phase A: Continuity Sweep (0–15 minutes)

1. **Dashboard → ProgressOverview shows: Act 1: 100%, Act 2: 100%, Act 3: 95%**
   - PendingApprovals shows: "3 continuity issues, 1 style warning"

2. **Click through continuity issues**
   - Issue 1: "Zara's blade is described as 'obsidian' in Ch.1 but 'onyx' in Ch.5" → Writer fixes in Zen.
   - Issue 2: "Kael's eye color is blue in Ch.2 but unmentioned thereafter" → Writer adds a note to Kael's character DNA.
   - Issue 3: "The Market is 'east of the river' in Ch.1 but 'by the docks' in Ch.3" → Writer reconciles.

3. **Run global continuity check**
   - Clicks "Check All" → Continuity Analyst scans the entire manuscript.
   - Returns: "No critical issues. 2 minor suggestions."
   - Writer feels confident.

#### Phase B: Voice Analysis (15–25 minutes)

4. **Navigate to Character Voice Scorecard**
   - Open from Dashboard inspector or `/analysis` view.
   - **VoiceScorecardResult** shows:
     - Zara: avg sentence 12 words, vocabulary diversity 0.78, casual formality, phrases: "damn it", "let's move"
     - Kael: avg sentence 19 words, vocabulary diversity 0.62, formal, phrases: "Indeed", "observe"
     - Commander Vex: avg sentence 15 words, vocabulary diversity 0.55, formal, phrases: "The Council demands"
   - Warning: "Kael and Vex sound 71% similar — both use formal register."
   - Writer opens Kael's dialogue scenes and differentiates: Kael becomes more sardonic, less rigid.

#### Phase C: Style Polish (25–40 minutes)

5. **Open key scenes in Zen Mode, run `/check-style` on each**
   - Scene by scene, the StyleScorecard helps writer tighten prose:
     - Remove passive voice in Ch.3
     - Fix tense inconsistency in Ch.5
     - Strengthen weak verbs in the climax

6. **Run the "Draft → Polish" pipeline template on the full manuscript**
   - Template executes: Style Enforcer → Continuity Analyst → Final Edit suggestions.
   - Each step has an Approval Gate. Writer reviews and accepts/rejects per section.

#### Phase D: Reader Preview (40–50 minutes)

7. **Navigate to `/preview`**
   - Select Chapter 1.
   - **Reader Scroll Simulation** shows:
     - Auto-scrolling vertical preview of all panels.
     - Per-panel metrics: reading time, text density, pacing type (fast/medium/slow).
     - Engagement score: 0.83
     - Warnings: "Panel 5-7 are all slow pacing — consider adding a quick reaction shot."
   - Writer adjusts storyboard panels based on pacing feedback.

#### Phase E: Export (50–55 minutes)

8. **Open Export Modal (Cmd+K → "Export" or dashboard button)**
   - **ExportModal** shows 4 format cards:
     - **Markdown** — clean prose manuscript
     - **JSON** — full structured bundle (for backup/import)
     - **Fountain** — screenplay format
     - **HTML** — styled, print-ready document with browser Print-to-PDF
   - Writer exports HTML, uses browser Print → PDF.
   - Also exports JSON as a project backup.

### Friction to Eliminate
- Global continuity check ("Check All") needs to be a single button, not per-scene.
- Voice Scorecard needs a dedicated page or panel, not buried in CharacterInspector.
- "Draft → Polish" template needs to work across multiple chapters, not just single scenes.
- Export HTML needs print-friendly CSS that's been tested across browsers.

### Success Metric
Writer resolves all continuity issues, improves average style score by 10%+, and exports a polished PDF in under an hour.

---

## Journey 7: "Multi-Language Release" — Translation & Localization

**Persona:** The Architect (planning international release)
**Trigger:** The English manuscript is finalized. Writer wants to prepare Korean and Japanese translations with cultural adaptation.

### Ideal Flow

1. **Navigate to `/translation` (Translation Studio)**
   - Left panel: Source language text (loaded from manuscript).
   - Right panel: Translation output area.
   - Bottom: Glossary management.

2. **Set up project glossary first**
   - Writer adds key terms:
     - "Whisper Magic" → Korean: "속삭임 마법" (keep untranslated in Japanese: "ウィスパー・マジック")
     - "The Iron Council" → Korean: "철의 의회"
     - Character names: Keep as-is in all languages (phonetic transcription).
   - Glossary persisted and auto-applied to all future translations.

3. **Translate Chapter 1, Scene 1 → Korean**
   - Select scene text. Choose target: Korean.
   - **Translator Agent** fires with context: glossary, character voice profiles, cultural notes.
   - **Glass Box**: Writer sees the full prompt including "Maintain Zara's casual, direct tone."
   - Results come back with:
     - Translated text
     - Adaptation notes: "The marketplace haggling scene adapted for Korean cultural context."
     - Cultural flags: "The idiom 'playing with fire' was adapted to a Korean equivalent: '불장난하다'"
     - Glossary terms applied: 3 terms auto-substituted.
   - Writer reviews, adjusts two sentences, approves.

4. **Inline translation from Zen Mode**
   - For quick checks, writer can select text in Zen and use `/translate` slash command.
   - **InlineTranslation** widget appears in ContextSidebar "Translation" tab.
   - Quick "Replace" or "Insert Below" actions for workflow convenience.

### Friction to Eliminate
- Translation Studio needs side-by-side scrolling (source and target scroll together).
- Batch translation (full chapter at once) needs to be supported, not just per-scene.
- Cultural adaptation quality depends on the underlying model — need model selection per language pair.

### Success Metric
Writer translates a full chapter with consistent terminology (glossary applied to 100% of terms) and cultural adaptation notes for every culturally-specific passage.

---

## Journey 8: "Custom Workflow for My Process" — Power User Pipeline Creation

**Persona:** The Architect (power user)
**Trigger:** Writer has a specific creative process: Brainstorm → Outline → Research check → Draft → Style check → Save. They want to automate this as a reusable workflow.

### Ideal Flow

1. **Navigate to `/pipelines`**
   - Click "New Pipeline" or use **NLPipelineWizard** (Cmd+K → "Create pipeline from description").

2. **Describe in natural language**
   - "When I give you a scene concept, first brainstorm 3 variations, let me pick one, then outline it into beats, check if any beats reference real-world concepts and research them, then draft the prose, run a style check, and save the result as a scene."
   - The **Pipeline Director** generates a DAG:
     ```
     [Brainstorm] → [⏸️ Pick Variation] → [Outline] → [⏸️ Review] →
     [Research Check] → [If research needed] → [Research Deep Dive] → [⏸️ Review Research] →
     [Draft Prose] → [⏸️ Edit Draft] → [Style Check] → [⏸️ Review Style] → [Save to Bucket]
     ```
   - Writer sees this in the visual builder. Each node has its model, temperature, and system prompt visible.

3. **Customize nodes**
   - Writer clicks the "Draft Prose" node → changes model from default to `anthropic/claude-3.5-sonnet`.
   - Changes temperature to 0.9 (more creative).
   - Adjusts the "Brainstorm" node's max_tokens to 1000 (shorter ideas).
   - Saves the pipeline definition as "My Scene Pipeline."

4. **Run the pipeline**
   - Click "Run." Provide input: "Zara discovers that the blade can heal as well as destroy — but healing someone means losing a memory of them."
   - Pipeline executes. At each `⏸️` gate, the PromptReviewModal opens.
   - Writer picks their favorite brainstorm variant, tweaks the outline, approves the research, edits the draft, reviews the style score.
   - Final output: A polished scene saved to the story structure.

5. **Reuse**
   - Next time writer has a scene concept, they select "My Scene Pipeline" from the definition list and run it again. Same workflow, different input.

### Friction to Eliminate
- NL → Pipeline generation may produce imperfect DAGs — the writer must be able to visually correct the wiring.
- If_else and Loop logic nodes need to be fully implemented in the execution engine.
- Per-node model override must actually flow through to `ModelConfigRegistry.resolve()`.

### Success Metric
Writer creates a custom 8+ step pipeline from natural language description and successfully executes it end-to-end in under 10 minutes.

---

## Journey 9: "Returning After a Week Away" — Session Continuity

**Persona:** Any
**Trigger:** Writer hasn't opened Showrunner in a week. They need to quickly remember where they left off and resume.

### Ideal Flow

1. **Open `/dashboard`**
   - **Command Center** immediately shows:
     - **Last Session**: "7 days ago — wrote 1,247 words in Ch.5 Scene 1. Outlined Act 2."
     - **Progress Overview**: Act 1: 100%, Act 2: 60%, Act 3: 30%
     - **Pending Approvals**: "1 continuity issue from last session, 2 research topics pending review"
     - **Recent Activity feed**: Last 5 actions (scene saved, outline generated, research queried)

2. **Cmd+K → "Continue where I left off"**
   - **CommandPalette** shows a "Resume" action that opens the last-edited scene in Zen Mode.
   - Writer is immediately back in context.

3. **ContextSidebar in Zen shows a "Previously..." section**
   - Summary of what happened in the previous scene.
   - What was planned next (from session notes or AI-generated "Next steps" suggestion).
   - Writer reads the context for 30 seconds and starts typing.

4. **Knowledge Graph canvas shows the "frontier"**
   - Nodes near the writer's current position in the story are highlighted.
   - Completed nodes are green, in-progress amber, unstarted grey.
   - Writer visually sees the shape of their story and where the gaps are.

### Friction to Eliminate
- "Last Session" summary doesn't exist as a UI element on the dashboard.
- "Continue where I left off" action needs to be added to CommandPalette.
- Session persistence (`session_service.py`) needs to surface recent activity in the Command Center.

### Success Metric
Writer goes from opening the app to actively writing in under 2 minutes, with full context of where they left off.

---

## Journey 10: "Collaborating with the AI as Co-Writer" — Deep Agentic Interaction

**Persona:** Discovery Writer (leans into AI assistance)
**Trigger:** Writer is stuck on a specific narrative problem. They want to have a back-and-forth conversation with the AI, not just fire-and-forget prompts.

### Ideal Flow

1. **In Zen Mode, writer types `/brainstorm` with a complex question**
   - "I need Zara to discover Kael's betrayal in a way that feels earned, not contrived. The reader should figure it out one beat before Zara does. What are some ways to plant clues across Ch.4-5 that pay off in Ch.6?"

2. **Brainstorm Agent returns structured suggestions with context**
   - 4 suggestions, each grounded in existing story elements:
     1. "Have Kael give Zara a gift in Ch.4 that later turns out to be a faction tracking device" (connected to existing "gift" idea card from brainstorm)
     2. "In Ch.5, Kael hesitates before a lie — Zara notices but dismisses it. The reader won't."
     3. "Show the reader (but not Zara) a brief scene from Kael's POV where he sends a message to the faction."
     4. "Plant a physical clue: Kael's faction insignia falls out of his bag. Zara finds it but doesn't recognize it — the reader, who saw the insignia in Ch.1, does."

3. **Writer wants to refine option 4 — uses the Chat refinement in the Approval Gate**
   - Clicks "Chat" on the PromptReviewModal.
   - Types: "I like #4 but I want the insignia to be more subtle — not literally falling out. What if it's engraved on the blade's hilt and Zara only notices it when the blade catches light at a specific angle?"
   - Agent responds with a refined version that ties the insignia to the blade's curse lore.
   - Writer approves this version. It's saved as a note on Ch.5 Scene 2.

4. **The "conversation" becomes part of the story's memory**
   - The approved suggestion is stored as a `GenericContainer` (type: "story_note") linked to Ch.5 and Ch.6.
   - Future continuity checks reference it: "The insignia on the blade should be visible when light catches it at an angle (established in story note #xyz)."

### Friction to Eliminate
- The Chat refinement in PromptReviewModal needs proper multi-turn support (currently may be single-turn).
- Story notes from brainstorm conversations should auto-persist and auto-link — currently the output is ephemeral.
- The Brainstorm Agent needs to include existing story elements in its context (currently may not reference brainstorm cards or previous notes).

### Success Metric
Writer has a 3+ turn conversation with the AI about a narrative problem and gets a solution grounded in their existing story world. The solution is persisted and referenced in future AI calls.

---

## Journey 11: "Dumping My Brain" — First Encounter with the Co-Pilot

**Persona:** Discovery Writer
**Trigger:** Writer just created a new project. Instead of navigating to Brainstorm or Timeline, they see the chat sidebar and start talking.

### Ideal Flow

#### Phase A: Natural Language Capture (0–5 minutes)

1. **Writer opens `/dashboard` → new project "Midnight Chronicle" created**
   - The Chat Sidebar is visible on the right. A welcoming message:
     > "I'm your story co-pilot. Tell me about your story — characters, scenes, vibes — in any order. I'll organize everything."
   - A subtle hint: "Try @character, @scene, or just type freely."

2. **Writer types naturally into the chat:**
   > "ok so there's this thief called Zara, she has a cursed blade that whispers to her at night. The story ends with her destroying the blade instead of using its power. There's a big market scene in the rain where she meets Kael for the first time. Kael betrays her later in Act 2."

3. **Agent parses and responds with structured artifacts:**
   - Chat response:
     > "Got it! I've extracted 5 story elements from what you said. Here's what I captured:"
   - **Artifact Preview Panel** shows a card view:
     ```
     ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
     │ 👤 Zara      │  │ 👤 Kael       │  │ 🗡️ Cursed Blade  │
     │ Thief        │  │ (details TBD)│  │ Whispers at night│
     └─────────────┘  └──────────────┘  └──────────────────┘
     ┌────────────────────┐  ┌──────────────────────────┐
     │ 📍 The Market       │  │ 📖 Ending: Blade Destroyed│
     │ Rain, first meeting │  │ Zara chooses destruction  │
     └────────────────────┘  └──────────────────────────┘
     ```
   - Chat asks: *"Want me to create these as buckets? I can also set up a rough story structure (3 acts) based on what you've told me."*

4. **Writer responds:**
   > "yeah create them all. and yeah do the 3 act structure, put the market scene in act 1 and the betrayal in act 2"

5. **Agent executes (with Glass Box transparency):**
   - Chat shows a collapsible "Actions" block:
     ```
     ✅ Created Character: Zara (thief with cursed blade)
     ✅ Created Character: Kael
     ✅ Created Item: Cursed Blade (whispers at night)
     ✅ Created Location: The Market (rain, tension)
     ✅ Created Story Note: Ending — Blade Destroyed
     ✅ Created Structure: Season 1 → Arc 1 → Act 1, Act 2, Act 3
     ✅ Placed Scene "Market Meeting" in Act 1, Chapter 1
     ✅ Placed Scene "The Betrayal" in Act 2
     ✅ Linked Zara ↔ Cursed Blade (owner_of)
     ✅ Linked Zara ↔ Kael (first_meeting: Market scene)
     ```
   - **Dashboard KG canvas updates in real-time** (main panel behind the sidebar) — nodes animate into view.

6. **Writer continues dumping:**
   > "oh and the blade's power comes from whisper magic — each use erases a personal memory"

   Agent:
   > "That's a great cost mechanic! I'll create a Magic System bucket for 'Whisper Magic' with these attributes. Want me to research real-world 'Faustian bargain' tropes to enrich this?"

   Writer: "yes do that"

   Agent executes Research Agent in background → notification when done.

**Time spent:** 5 minutes. 6 buckets created, story structure scaffolded, research initiated. Zero page navigation. Zero forms filled.

#### Phase B: Refinement via Conversation (5–15 minutes)

7. **Writer refines through follow-up chat:**
   > "actually Kael should be more complex — he's not just a betrayer. He owes a debt to a faction called the Iron Council. His betrayal is transactional, not personal."

   Agent updates Kael's bucket, creates Iron Council faction bucket, links them:
   ```
   ✅ Updated Character: Kael — added motivation: "Debt to Iron Council"
   ✅ Created Faction: Iron Council
   ✅ Linked Kael → Iron Council (indebted_to)
   ✅ Linked Kael → Zara (complex_relationship: "betrayal is transactional")
   ```

8. **Writer asks a question:**
   > "what's the emotional arc looking like right now?"

   Agent queries the story structure and responds with a text summary + points the writer to the visual:
   > "Based on your 3 scenes: Act 1 starts neutral (market meeting), Act 2 spikes with betrayal, Act 3 resolves with bittersweet sacrifice. The middle is empty — that's where tension should build. Want me to suggest some Act 2 scenes to bridge the gap?"

9. **Background research completes — chat notification:**
   > "📬 Research complete: 'Faustian Bargain Tropes.' Found connections to Faust, Icarus, The Monkey's Paw. Want to review?"

   Writer: "show me"

   Artifact preview shows the structured research bucket. Writer approves. Auto-linked to Whisper Magic.

### Friction to Eliminate (from current state)
- Chat sidebar component doesn't exist yet — needs full implementation
- Natural language parsing → bucket creation needs a new "Quick Capture Agent" or extension of Brainstorm Agent
- Artifact preview panel for structured card views needs implementation
- Background task notification system needs chat integration

### Success Metric
Writer captures an entire story concept (5+ entities, 3-act structure, 1 research topic) in under 15 minutes through pure conversation. Zero page navigation required.

---

## Journey 12: "Run My Workflow" — Controlling Pipelines from Chat

**Persona:** The Architect (power user)
**Trigger:** Writer has a scene concept and wants to run their custom "My Scene Pipeline" (from Journey 8) without leaving the current page.

### Ideal Flow

#### Phase A: Pipeline Discovery & Launch (0–2 minutes)

1. **Writer is in Zen Mode writing Ch.4. Opens chat sidebar and types:**
   > "run 'My Scene Pipeline' with this concept: Zara discovers the blade can heal as well as destroy, but healing someone means losing her memory of them"

2. **Agent finds the pipeline and shows a preview:**
   > "Found pipeline **My Scene Pipeline** (8 steps). Here's the execution plan:"

   Artifact preview:
   ```
   ┌──────────────────────────────────────────────────┐
   │  MY SCENE PIPELINE — Execution Plan              │
   │                                                  │
   │  1. 🧠 Brainstorm (3 variations)                 │
   │  2. ⏸️ Pick Variation ← YOU APPROVE               │
   │  3. 📐 Outline into beats                        │
   │  4. ⏸️ Review Outline ← YOU APPROVE               │
   │  5. 🔬 Research Check (if needed)                │
   │  6. ✍️ Draft Prose (claude-3.5-sonnet, temp 0.9)  │
   │  7. ⏸️ Edit Draft ← YOU APPROVE                   │
   │  8. 🎭 Style Check                               │
   │  9. ⏸️ Review Style ← YOU APPROVE                 │
   │  10. 💾 Save to Ch.4                              │
   │                                                  │
   │  Context: @Zara, @Cursed Blade, @Whisper Magic   │
   │  Estimated: ~3 minutes active, ~2 minutes AI     │
   │                                                  │
   │  [▶️ Start]  [⚙️ Modify Steps]  [❌ Cancel]       │
   └──────────────────────────────────────────────────┘
   ```

3. **Writer types:** "start it"

#### Phase B: Interactive Pipeline Execution (2–8 minutes)

4. **Step 1 completes — Brainstorm Agent returns 3 variations:**

   Chat:
   > "Brainstorm complete. Here are 3 variations:"

   Artifact preview shows 3 cards:
   ```
   [A] Zara heals a dying child, forgets the child exists,
       then encounters the child later with no memory
   [B] Zara heals Kael after the betrayal, losing her anger
       — she forgives him because she literally can't remember why she's angry
   [C] Zara heals a stranger to test the blade, loses a
       trivial memory, but realizes each use makes the loss unpredictable
   ```

   Writer responds in chat: "B is incredible. use that one"

5. **Step 3 completes — Outline generated:**

   Chat shows the outline in the artifact preview. Writer reads it, types:
   > "move beat 3 before beat 2, and add a beat where Kael realizes what she's done"

   Agent modifies the outline and shows the updated version. Writer: "approved"

6. **Step 5 — Research check finds a real-world reference:**

   Chat:
   > "Research check found a relevant topic: 'Amnesia in mythology — the River Lethe.' This connects to Zara's memory loss. Adding to context."

   This happens automatically — no approval gate needed for context enrichment.

7. **Step 6 — Draft prose generated (streaming):**

   Chat shows the draft streaming in real-time in the artifact preview panel. The prose appears word by word. Writer can see it forming.

   When complete:
   > "Draft complete — 847 words. Zara's emotional state after healing Kael is particularly strong. Review and edit?"

   Writer reads in the artifact panel. Types:
   > "paragraph 3 is too expository. make it more show-don't-tell, use the blade's glow as a visual metaphor"

   Agent revises paragraph 3 and shows the diff:
   ```diff
   - Zara felt the memories slipping away. She knew what the cost would be
   - — every use of the blade's healing power took something from her.
   - The anger she'd carried for weeks began to dissolve.
   + The blade's obsidian surface pulsed with amber light as Zara pressed
   + it against Kael's wound. With each pulse, something loosened in her
   + chest — not pain leaving, but something else. Something she'd been
   + holding onto. The amber glow consumed it before she could name it.
   ```

   Writer: "perfect. approve"

8. **Step 8 — Style check returns inline:**

   Chat:
   > "Style score: 0.91. One note: 'The sentence starting with *Meanwhile* in paragraph 5 breaks the close-POV.' Shall I fix it?"

   Writer: "fix it and save"

9. **Pipeline complete:**
   > "✅ Pipeline complete! Scene saved to Ch.4, Scene 3: 'The Healing.'
   > 847 words | Style: 0.91 | Entities linked: Zara, Kael, Cursed Blade, Whisper Magic
   > The scene is now open in your Zen editor."

   Main panel updates — the Zen editor now shows the new scene.

#### Phase C: Mid-Pipeline Control (Alternative Flow)

10. **What if the writer wants to pause?**

    At any point during execution, writer types:
    > "pause the pipeline"

    Agent:
    > "⏸️ Pipeline paused after Step 5 (Research Check). You can `/resume` anytime or `/cancel` to discard."

11. **What if the writer wants to skip?**
    > "skip the style check, just save"

    Agent:
    > "Skipping Step 8 (Style Check). Saving directly to Ch.4."

12. **What if the writer wants to change the model mid-pipeline?**
    > "for the draft step, use claude-opus instead of sonnet"

    Agent:
    > "Switching Draft Prose step to `anthropic/claude-opus-4`. This may take longer but will produce richer prose."

### Friction to Eliminate
- Pipeline execution currently only works from the `/pipelines` page — needs API-level invocation from chat
- Approval gates currently use PromptReviewModal — need to also support inline chat-based approval
- Real-time pipeline status streaming needs to be routed to the chat sidebar, not just the pipeline page
- Mid-execution model switching needs to flow through `ModelConfigRegistry.resolve()` with runtime override support

### Success Metric
Writer launches, interacts with, and completes an 8-step pipeline entirely from the chat sidebar in under 10 minutes. Zero page navigation to the Pipelines page.

---

## Journey 13: "Build My World Through Conversation" — Deep Worldbuilding via Chat

**Persona:** The Architect
**Trigger:** Writer wants to build out a complex magic system, faction politics, and character relationships — all through natural conversation rather than filling out forms.

### Ideal Flow

#### Phase A: Schema Creation via Chat (0–5 minutes)

1. **Writer opens chat and types:**
   > "I need a new schema for my magic system. It should have: power source, personal cost, visual manifestation, societal restrictions, and a rarity level (common/uncommon/rare/legendary)"

2. **Agent creates the schema and shows preview:**

   Artifact preview:
   ```yaml
   Schema: magic_system
   Fields:
     power_source:         string
     personal_cost:        string
     visual_manifestation: string
     societal_restrictions: list[string]
     rarity:               enum [common, uncommon, rare, legendary]
   ```

   Chat: *"Schema 'magic_system' ready. Want me to create it, or adjust any fields first?"*

   Writer: "add a `limitations` field as a list of strings"

   Agent updates and writer confirms. Schema saved.

3. **Writer immediately creates an instance:**
   > "create a magic system called Whisper Magic. Power source is emotional resonance with ancient artifacts. Cost is memory loss — each use erases a personal memory. Visual: black smoke forming shapes. Rarity: rare. Limitations: can't target self, requires physical contact with artifact"

   Agent creates the bucket, shows it in the artifact preview, and auto-links it to existing entities:
   ```
   ✅ Created: Whisper Magic (magic_system)
   ✅ Auto-linked: Cursed Blade → Whisper Magic (artifact_of)
   ✅ Auto-linked: Zara → Whisper Magic (practitioner_of)
   ```

#### Phase B: Bulk World Building (5–20 minutes)

4. **Writer creates multiple entities rapidly:**
   > "create these factions:
   > - The Iron Council: military authoritarian, led by Commander Vex, controls the eastern territories
   > - The Whisper Seekers: secretive scholars who study Whisper Magic, led by Elder Mira
   > - The Free Market Alliance: merchant guild, controls trade, no single leader"

   Agent creates all three factions with proper schemas, auto-detects relationships:
   ```
   ✅ Created Faction: The Iron Council (leader: Commander Vex)
   ✅ Created Faction: The Whisper Seekers (leader: Elder Mira)
   ✅ Created Faction: The Free Market Alliance (decentralized leadership)
   ✅ Created Character: Commander Vex (leader of Iron Council)
   ✅ Created Character: Elder Mira (leader of Whisper Seekers)
   ✅ Suggested relationship: Iron Council ↔ Whisper Seekers (rivals — both want Whisper Magic artifacts)
   ```

   Writer: "accept all, and also link Kael to the Iron Council — he owes them a debt"

5. **Writer asks the agent to generate content:**
   > "write a 2-paragraph backstory for Commander Vex. He should feel like a military pragmatist, not a villain. Use @Iron Council and @Whisper Magic for context"

   Agent assembles context (Iron Council details, Whisper Magic rules, story tone from Project Memory), generates backstory, shows in artifact preview.

   Writer edits one sentence in the preview, approves.

6. **Writer asks for analysis:**
   > "what relationships am I missing? Are there any factions that should have connections but don't?"

   Agent queries the Knowledge Graph:
   > "I found 2 gaps:
   > 1. **Free Market Alliance** has no character connections — consider adding a key merchant NPC
   > 2. **Zara** has no faction allegiance — is she independent, or affiliated with one?
   >
   > Also, the **Whisper Seekers** and **Cursed Blade** should probably be linked — would the scholars know about Zara's blade?"

   Writer addresses each: "Zara is independent. Yes link Whisper Seekers to the blade. I'll create a merchant later."

#### Phase C: Research-Backed Enrichment (20–30 minutes)

7. **Writer uses research through chat:**
   > "research: what were real historical secret societies that studied forbidden knowledge? I want to enrich the Whisper Seekers"

   Agent dispatches Research Agent (background). When complete:
   > "📬 Research complete: 'Secret Knowledge Societies.' Found: The Pythagoreans (math as sacred), The Hermetic Order (alchemical transformation), The Assassins of Alamut (hidden knowledge + political power). Relevance to Whisper Seekers: high. Want to review?"

   Writer reviews in artifact preview, approves. Auto-linked to Whisper Seekers.

8. **Writer checks their world:**
   > "give me a summary of my world so far"

   Agent compiles:
   > **Midnight Chronicle — World Bible**
   > - **Characters:** Zara (thief, independent), Kael (debt to Iron Council), Commander Vex, Elder Mira
   > - **Factions:** Iron Council (military), Whisper Seekers (scholars), Free Market Alliance (merchants)
   > - **Magic:** Whisper Magic (artifact-resonance, memory cost, rare)
   > - **Items:** Cursed Blade (Whisper Magic artifact, owned by Zara)
   > - **Locations:** The Market (Act 1 setting)
   > - **Research:** Faustian Bargains, Secret Knowledge Societies
   > - **Structure:** 3 Acts, 2 placed scenes (Market Meeting, The Betrayal)
   > - **Gaps:** No Act 2 middle scenes, Free Market Alliance needs NPCs, Act 3 needs scenes

### Friction to Eliminate
- Bulk entity creation from a single chat message needs intelligent NLP parsing
- Relationship suggestion ("what am I missing?") needs KG graph analysis endpoint
- World summary compilation needs a dedicated context assembly call
- Auto-detection of implicit entities (e.g., recognizing "led by Commander Vex" as a character creation signal)

### Success Metric
Writer creates 3+ schemas, 8+ buckets, 5+ relationships, and 2+ research topics through pure conversation in under 30 minutes.

---

## Journey 14: "Writing Side-by-Side" — Zen Mode with Chat Co-Pilot

**Persona:** Discovery Writer
**Trigger:** Writer is in Zen Mode drafting a scene. Instead of using `/slash` commands, they use the chat sidebar for all AI interactions — brainstorming, research, style checks, and context queries.

### Ideal Flow

#### Phase A: Contextual Writing (0–20 minutes)

1. **Writer is in Zen Mode for Ch.5 Scene 1. Chat sidebar is open.**
   - Chat auto-loads scene context:
     > "📍 Context: Ch.5 Scene 1 — Characters: Zara, Kael. Previous scene: Zara and Kael raided the faction armory. Mood: unset."

2. **Writer writes 400 words. Hits a wall. Turns to chat:**
   > "I'm stuck. Kael needs to start pulling away from Zara subtly. How can I show this without telling?"

3. **Agent brainstorms with full scene context:**
   > "Here are 4 ways to show Kael distancing himself through action and body language:"
   >
   > 1. **Kael stops finishing her sentences** — they used to complete each other's thoughts. Now there's a beat of silence.
   > 2. **Physical spacing** — Kael positions himself on the opposite side of the room during their planning session.
   > 3. **The gift** — Kael gives Zara a pendant (which is actually an Iron Council tracking token). The gift feels generous but is loaded with subtext.
   > 4. **Misdirected eye contact** — Kael looks at the door whenever Zara mentions the blade, as if calculating escape routes.
   >
   > Options 3 and 4 create reader-vs-character knowledge asymmetry — the reader notices what Zara doesn't.

4. **Writer picks #3 and continues writing, then asks:**
   > "what would the Iron Council tracking token look like? something that fits this fantasy world"

   Agent:
   > "Based on @Iron Council's military aesthetic and @Whisper Magic's artifact lore:
   > - A thin copper ring with a barely visible sigil — heats faintly when near a Council outpost
   > - Kael could disguise it as a 'lucky charm' from his childhood
   > - The reader might recognize the sigil if we describe the Council's banners in an earlier scene"

   Writer writes 200 more words incorporating the token.

#### Phase B: Inline Research & Fact-Checking (20–35 minutes)

5. **Writer writes a scene involving poisons. Types in chat:**
   > "quick research: what's a poison that causes gradual weakness over days, not instant death? needs to be plausible in a fantasy setting with some real-world basis"

   Agent dispatches Research Agent:
   > "Found: **Chronic arsenic poisoning** — causes weakness, fatigue, skin lesions over days/weeks. Historical use: 'Inheritance powder' in Renaissance Italy. Fantasy adaptation: the poison could be derived from a dark mineral, slow-acting, detectable only by Whisper Magic users (adding plot utility)."

   Writer: "perfect, save that as research and link it to this scene"

6. **Writer finishes a passage and wants a quick check:**
   > "check the style of what I just wrote — last 3 paragraphs"

   Agent runs Style Enforcer on the selected text:
   > "Score: 0.87. Notes:
   > - Strong sensory detail in the market description
   > - ⚠️ Paragraph 2 shifts to passive voice ('was given' → 'received' or 'pressed into her hand')
   > - The dialogue tag 'he said quietly' could be shown through action instead"

   Writer fixes both issues inline in the Zen editor.

#### Phase C: Quick Context Queries (35–45 minutes)

7. **Writer needs to check a fact from earlier in the story:**
   > "what color did I describe Zara's blade as in chapter 1?"

   Agent searches all fragments:
   > "In Ch.1 Scene 1, you wrote: 'the obsidian blade at her hip.' Color: **obsidian** (black)."

8. **Writer needs to check continuity:**
   > "check continuity: I just had Kael give Zara the pendant in this scene. Does this conflict with anything?"

   Agent runs Continuity Analyst:
   > "No conflicts found. Note: You may want to establish that Kael has personal items in an earlier scene (currently he appears 'empty-handed' in all previous scenes). Consider adding a brief moment in Ch.4 where Kael is seen handling small objects."

9. **Session stats visible in chat footer:**
   > "📊 This session: 1,247 words written | 4 AI assists | Style: 0.87 avg | Duration: 45 min"

### Key Difference from Slash Commands

| Slash Command Approach | Chat Co-Pilot Approach |
|---|---|
| `/brainstorm How does Kael distance himself?` | Conversational: "I'm stuck. Kael needs to pull away subtly..." |
| Single-shot response | Multi-turn refinement: "what would the token look like?" |
| Context is automatic but invisible | Context is shown: "📍 Context: Ch.5 Sc.1, Characters: Zara, Kael" |
| Result appears inline in editor | Result appears in sidebar, writer chooses what to incorporate |
| No follow-up without new command | Natural follow-up conversation |

### Friction to Eliminate
- Chat sidebar doesn't exist on the Zen page yet
- Auto-loading scene context into chat needs ZenStore → Chat context bridge
- "Check what I just wrote" needs access to the current TipTap editor content
- Full-text search across all fragments ("what color was Zara's blade?") needs a dedicated search endpoint or enhanced ContextEngine

### Success Metric
Writer completes a 1000+ word writing session using 5+ chat interactions for brainstorming, research, style checks, and continuity — all without leaving Zen Mode or using slash commands.

---

## Journey 15: "Managing My Sessions" — Multi-Session Workflow

**Persona:** Any
**Trigger:** Writer works on multiple aspects of their story across different sessions. They need to create, switch, compact, and resume sessions without losing context.

### Ideal Flow

#### Phase A: Session Creation & Naming (0–2 minutes)

1. **Writer opens the chat sidebar. Current session: "unnamed-1"**
   - Writer types: `/new-session "Worldbuilding: Factions"`
   - Chat:
     > "Started new session: **Worldbuilding: Factions**
     > Project Memory loaded (tone: dark fantasy, 3 characters, 1 magic system)
     > What would you like to work on?"

2. **Writer works on faction worldbuilding for 30 minutes (Journey 13 style).**

#### Phase B: Context Getting Full — Compaction (30 minutes in)

3. **Token usage indicator in sidebar header shows: `78K / 100K tokens`**
   - Writer notices the indicator turning amber (80% threshold approaching).
   - Writer types: `/compact`
   - Agent compresses the conversation:
     > "🗜️ Context compacted: 78K → 8K tokens
     > **Session digest preserved:**
     > - Created 3 factions (Iron Council, Whisper Seekers, Free Market Alliance)
     > - Created 2 characters (Commander Vex, Elder Mira)
     > - Established 5 relationships
     > - 2 research topics saved
     > - Pending: Free Market Alliance needs NPCs
     >
     > All buckets are persisted. You can keep working with full context access via @-mentions."

4. **Writer continues working with compacted context.** When they @-mention an entity, the agent pulls full data fresh from the bucket store.

#### Phase C: Switching Sessions (45 minutes in)

5. **Writer wants to switch to writing. Types:**
   > `/new-session "Writing: Ch.5 Drafting"`

   Chat:
   > "Session **Worldbuilding: Factions** saved.
   > Started new session: **Writing: Ch.5 Drafting**
   > Project Memory loaded. Current page: still in Zen for Ch.5."

6. **Writer writes for an hour, then types:**
   > `/end "Drafted Ch.5 scenes 1-2, 1247 words. Introduced the copper pendant as Kael's tracking device. Need to foreshadow Council sigils in Ch.3."`

   Chat:
   > "Session **Writing: Ch.5 Drafting** ended.
   > Digest saved. Next steps noted: 'Foreshadow Council sigils in Ch.3'
   > Returning to session picker."

#### Phase D: Resuming a Session (Next Day)

7. **Writer opens Showrunner the next day. Types `/resume` in chat.**

   Chat shows a session picker:
   ```
   ┌─────────────────────────────────────────────────┐
   │  RECENT SESSIONS                                │
   │                                                 │
   │  📝 Writing: Ch.5 Drafting                      │
   │     Yesterday • 1,247 words • Ended             │
   │     Next: Foreshadow Council sigils in Ch.3     │
   │                                                 │
   │  🌍 Worldbuilding: Factions                     │
   │     Yesterday • 3 factions • Compacted          │
   │     Pending: Free Market Alliance needs NPCs    │
   │                                                 │
   │  🧠 Brainstorm: Initial Concept                 │
   │     2 days ago • 6 buckets • Ended              │
   │                                                 │
   │  [Resume Selected]  [New Session]               │
   └─────────────────────────────────────────────────┘
   ```

8. **Writer selects "Writing: Ch.5 Drafting":**

   Chat:
   > "Resuming **Writing: Ch.5 Drafting**
   > 📋 Last session summary:
   > - Drafted Ch.5 scenes 1-2 (1,247 words)
   > - Introduced copper pendant as Kael's tracking device
   > - Style score: 0.87
   >
   > 📌 Your noted next step: *Foreshadow Council sigils in Ch.3*
   >
   > Want to work on that, or continue Ch.5?"

9. **Writer types:**
   > "let's do the Ch.3 foreshadowing first. open Ch.3 Scene 2 in Zen"

   Main panel navigates to Zen with Ch.3 Scene 2 loaded. Chat has full context from the resumed session.

### Friction to Eliminate
- Session persistence backend needs new `ChatSessionService` with YAML storage
- Session digest generation needs LLM summarization endpoint
- Token counting needs real-time tracking in the chat frontend
- `/compact` needs to distinguish between "must preserve" context (decisions, bucket references) and "can summarize" context (brainstorming back-and-forth)
- Session picker UI component needs implementation

### Success Metric
Writer creates 3+ named sessions, compacts at least 1, resumes a previous session the next day, and picks up exactly where they left off within 30 seconds.

---

## Journey 16: "Plan This For Me" — Complex Multi-Step Task Delegation

**Persona:** Discovery Writer or Architect
**Trigger:** Writer has a complex request that requires multiple steps. Instead of doing each step manually, they ask the agent to plan and execute.

### Ideal Flow

#### Phase A: The Big Ask (0–1 minute)

1. **Writer types in chat:**
   > "I need to build out Act 2. Here's what I know: Kael slowly distances himself from Zara. She starts relying more on the blade. The tension builds until Kael's betrayal in Chapter 6. Can you plan out chapters 4-6 with scenes, emotional arcs, and key plot beats?"

2. **Agent enters Plan Mode:**
   > "🗺️ This is a big task. Let me create a plan for your approval before I start executing."
   >
   > **Plan: Build Act 2 (Chapters 4–6)**
   >
   > **Step 1: Analyze existing context**
   > - Review @Zara, @Kael, @Cursed Blade, @Iron Council, @Whisper Magic
   > - Check existing Act 1 scenes for continuity threads
   > - Review Act 3 ending for reverse-engineering setup requirements
   >
   > **Step 2: Outline Chapter 4 — "Trust Building"**
   > - 3 scenes: Zara & Kael's routine, the copper pendant gift, first solo blade use
   > - Emotional arc: warm → suspicious undertone (for the reader)
   > - Key beat: Kael gives the pendant (tracking device)
   >
   > **Step 3: Outline Chapter 5 — "First Cracks"**
   > - 3 scenes: Kael's distancing behavior, Zara's increasing blade dependency, a close call
   > - Emotional arc: trust eroding → anxiety → determination
   > - Key beat: Zara uses the blade to heal someone, loses a memory
   >
   > **Step 4: Outline Chapter 6 — "The Betrayal"**
   > - 2-3 scenes: The reveal, Zara's reaction, aftermath
   > - Emotional arc: shock → devastation → resolve
   > - Key beat: Kael's betrayal, but shown as agonized choice (not villainy)
   >
   > **Step 5: Create structure buckets**
   > - Create all chapters, scenes, and link to Act 2
   > - Add emotional arc metadata per scene
   >
   > **Step 6: Continuity check**
   > - Verify new outline against existing story elements
   > - Flag any gaps or contradictions
   >
   > *Estimated: 6 approval gates, ~15 minutes active time*
   >
   > **[▶️ Execute Plan]  [✏️ Modify Plan]  [❌ Cancel]**

3. **Writer reviews. Types:**
   > "step 3 should also include a scene from Kael's POV — we show the reader his inner conflict without Zara knowing. execute the plan"

4. **Agent updates the plan and begins executing step by step.**

#### Phase B: Plan Execution with Checkpoints (1–15 minutes)

5. **Step 1 (Analysis) runs automatically.** Agent shows findings:
   > "Context analysis complete. Key threads to weave:
   > - Zara's blade was established as obsidian in Ch.1
   > - Kael appears 'empty-handed' in Ch.4 — need to establish he carries personal items
   > - Act 3 requires Zara to have experienced significant memory loss — need at least 2 blade uses in Act 2
   > - The Iron Council sigil hasn't been visually described yet — need to establish it"

6. **Steps 2-4 (Outlines) execute with approval gates at each chapter.** Each shows:
   - Scene-by-scene breakdown with descriptions
   - Character presence per scene
   - Emotional arc visualization (text-based)
   - Key dialogue moments

   Writer can modify any scene, add/remove beats, and approve.

7. **Step 5 (Structure creation) executes in batch:**
   ```
   ✅ Created Chapter 4: "Trust Building" (3 scenes)
   ✅ Created Chapter 5: "First Cracks" (4 scenes, including Kael POV)
   ✅ Created Chapter 6: "The Betrayal" (3 scenes)
   ✅ Updated Act 2 emotional arc metadata
   ✅ Linked all scenes to relevant characters
   ✅ Updated Story Structure Tree
   ```

8. **Step 6 (Continuity check) runs and reports:**
   > "Continuity check passed with 1 suggestion: Consider mentioning the Iron Council's sigil in Ch.3 or Ch.4 before it becomes plot-relevant in Ch.6."

9. **Plan complete. Summary:**
   > "✅ Act 2 fully scaffolded:
   > - 3 chapters, 10 scenes, 4 emotional arc peaks
   > - Key beats placed: pendant gift, blade healing, Kael POV, betrayal
   > - Continuity: clean with 1 foreshadowing suggestion
   > - Timeline page updated. Want to start drafting any scene?"

### Friction to Eliminate
- Plan Mode as a distinct chat state doesn't exist yet — needs implementation
- Multi-step plan execution with per-step approval needs a plan execution engine (lighter than full Pipeline)
- Plan modification mid-execution ("also add a Kael POV scene") needs replanning capability
- Batch structure creation needs bulk `ContainerRepository` operations

### Success Metric
Writer scaffolds an entire act (3 chapters, 10 scenes) with emotional arcs, character placement, and continuity validation through a single conversational request in under 15 minutes.

---

## Journey 17: "What Happened While I Was Gone?" — Session Continuity via Chat

**Persona:** Any
**Trigger:** Writer returns after a week away. Instead of navigating the dashboard, they ask the chat to catch them up.

### Ideal Flow

1. **Writer opens Showrunner. Chat sidebar greets them:**
   > "Welcome back! It's been 7 days since your last session. Want a quick catch-up?"

   Writer: "yes, what's the current state?"

2. **Agent compiles a project brief:**
   > **Midnight Chronicle — Status Report**
   >
   > 📊 **Progress:**
   > - Act 1: 100% (3 chapters, 9 scenes, all drafted)
   > - Act 2: 60% (3 chapters scaffolded, 4/10 scenes drafted)
   > - Act 3: 10% (1 chapter, ending scene outlined)
   >
   > 📝 **Last session:** "Writing: Ch.5 Drafting" — 1,247 words
   > - Drafted Ch.5 scenes 1-2
   > - Introduced copper pendant as tracking device
   > - Style score: 0.87
   >
   > 📌 **Noted next steps:**
   > - Foreshadow Council sigils in Ch.3
   > - Draft remaining Ch.5 scenes (3-4)
   > - Free Market Alliance still needs NPC characters
   >
   > ⚠️ **Pending items:**
   > - 1 continuity issue: Kael appears 'empty-handed' before giving pendant
   > - 1 research topic awaiting review: "Amnesia in Mythology"
   >
   > 🧠 **World Bible:** 4 characters, 3 factions, 1 magic system, 2 research topics
   >
   > *Where would you like to pick up?*

3. **Writer responds:**
   > "let's handle that continuity issue first. what exactly is the problem?"

   Agent explains the Kael pendant continuity gap and suggests a fix. Writer approves. Agent navigates to the relevant scene in Zen Mode for a quick edit.

4. **Writer then asks:**
   > "open the research on amnesia mythology"

   Agent shows the pending research in the artifact preview. Writer reviews, approves. It's auto-linked to Whisper Magic and Ch.5.

5. **Writer decides what to work on:**
   > "ok start a new session 'Writing: Ch.5 continuation' and open Ch.5 Scene 3"

   Chat creates the session, loads context, navigates to Zen. Writer is back in flow within 2 minutes.

### Success Metric
Writer goes from "I haven't touched this in a week" to actively writing in under 2 minutes through pure conversational catch-up.

---

## Cross-Journey Principles for the Agentic Chat

### 1. Chat is the Universal Entry Point
Every operation that doesn't require direct spatial manipulation (drag-drop, zoom-pan) can be initiated from chat. The sidebar is available on every page.

### 2. Artifacts as Visual Bridge
When the agent generates structured content (outlines, schemas, prose, panels, research), it appears in a split-pane artifact preview — not buried in chat bubbles. The writer can interact with artifacts (edit, approve, dismiss).

### 3. Progressive Autonomy
- **Level 0 (Ask):** Agent asks before every action: "Want me to create this bucket?"
- **Level 1 (Suggest):** Agent acts on simple requests, confirms complex ones: "Created 3 factions. The relationships I'm less sure about — want to review?"
- **Level 2 (Execute):** Agent follows plans without per-step confirmation (writer opted in): "Plan complete. 10 scenes created."

### 4. Transparency is Non-Negotiable
Every agent action shows: what tool was used, what context was assembled, what model ran it. Collapsible by default, but always accessible. This is the Glass Box philosophy applied to chat.

### 5. Chat Never Blocks the Editor
The writer can always switch from chat to direct editing and back. Chat state is preserved. If the writer edits something in Zen Mode that contradicts a chat action, the agent notices and flags it.

### 6. Sessions are Cheap and Disposable
Creating a new session should be as frictionless as opening a new browser tab. Writers shouldn't feel committed to a session. Compact and move on.

### 7. @-Mentions are the Power User Shortcut
Free typing works for everyone. @-mentions provide precise context injection for power users. Both approaches lead to the same result.

---

## Summary: The 7 Agentic Chat CUJs

| # | Journey | Primary Persona | Key Chat Features | Integration Points | Target Time |
|---|---------|----------------|-------------------|--------------------|-------------|
| 11 | Brain Dump via Chat | Discovery Writer | NL parsing → bucket creation, artifact preview, auto-linking | Dashboard KG canvas, Project Memory | 15 min |
| 12 | Pipeline Control from Chat | Architect | Pipeline launch/pause/resume, inline approval, model switching | Pipeline Service, SSE streaming | 10 min |
| 13 | Worldbuilding via Conversation | Architect | Schema creation, bulk entity creation, relationship suggestions, research | Schema Builder, KG Service, Research Agent | 30 min |
| 14 | Writing Side-by-Side | Discovery Writer | Brainstorming, research, style checks, continuity queries, context search | Zen Mode editor, all 10 agents | 45 min |
| 15 | Multi-Session Management | Any | Session create/switch/compact/resume, token tracking, session picker | Session Service, LLM summarization | 2 min to resume |
| 16 | Complex Task Delegation | Any | Plan mode, multi-step execution, per-step approval, batch operations | Pipeline Service, Container Repository | 15 min |
| 17 | Catch-Up After Break | Any | Project status brief, pending items, quick fixes, session history | Session Service, Continuity Service | 2 min |

---

## Technical Requirements for Agentic Chat

### New Backend Components
| Component | Purpose |
|---|---|
| `ChatSessionService` | Session CRUD, digest generation, session picker data |
| `ProjectMemoryService` | Persistent Layer 1 memory (decisions, rules, style guide) |
| `ChatContextManager` | Token tracking, compaction, @-mention resolution |
| `QuickCaptureAgent` | NL parsing → structured bucket creation from free-form text |
| `PlanExecutionEngine` | Lightweight plan creation/execution (simpler than full Pipeline) |
| `chat.py` router | REST + SSE endpoints for chat messages, sessions, streaming |

### New Frontend Components
| Component | Purpose |
|---|---|
| `ChatSidebar.tsx` | Collapsible sidebar shell, available on all pages |
| `ChatInput.tsx` | Message input with @-mention autocomplete, /commands |
| `ChatMessageList.tsx` | Message thread with user/agent messages, action blocks |
| `ArtifactPreview.tsx` | Split-pane preview panel for structured content |
| `SessionPicker.tsx` | Session list with resume/create/delete |
| `TokenIndicator.tsx` | Token usage bar in sidebar header |
| `PlanViewer.tsx` | Plan mode display with step-by-step approval |
| `ActionBlock.tsx` | Collapsible block showing agent actions (created/updated/linked) |
| `chatStore.ts` | Zustand slice for chat state, sessions, messages |

### New API Endpoints
| Endpoint | Purpose |
|---|---|
| `POST /api/v1/chat/message` | Send message, receive streamed response |
| `GET /api/v1/chat/stream` | SSE stream for agent responses and action updates |
| `POST /api/v1/chat/sessions` | Create new session |
| `GET /api/v1/chat/sessions` | List sessions for session picker |
| `GET /api/v1/chat/sessions/{id}` | Get session with digest |
| `POST /api/v1/chat/sessions/{id}/compact` | Compact session context |
| `POST /api/v1/chat/sessions/{id}/end` | End session with summary |
| `GET /api/v1/chat/memory` | Get project-level persistent memory |
| `PUT /api/v1/chat/memory` | Update project-level persistent memory |
| `POST /api/v1/chat/plan` | Create execution plan from NL request |
| `POST /api/v1/chat/plan/{id}/execute` | Execute approved plan |
| `POST /api/v1/chat/plan/{id}/modify` | Modify plan before/during execution |

---

## Journey 18: "The Research Rabbit Hole" — Fact-Checking and Knowledge Building

**Persona:** Architect / Hard Sci-Fi Writer
**Trigger:** Writer intends to introduce a real-world scientific or historical concept (e.g., orbital mechanics for a space battle or renaissance medical practices) and needs it to be grounded and accurate.

### Ideal Flow
1. **Triggering the Deep Dive:** Writer opens Chat Sidebar: "I need to design a space battle in low orbit. Research realistic orbital mechanics, specifically how debris fields behave and the time delay in communications."
2. **Research Agent Execution:** Agent executes using `gemini-2.0-pro`, fetching verified data. The Artifact Preview shows structured facts, constraints (e.g., Kessler syndrome), and story implications. Writer approves. A Research Bucket "Low Orbit Mechanics" is added to the Research Library.
3. **Auto-Injection:** Writer drafts the scene in Zen Mode. Entity detection hooks phrases like "orbital debris", injecting the Research Bucket automatically into the scene's background context window.
4. **Plausibility Checking:** Writer asks in Chat: "Is it plausible it perform a tight turn here while maintaining velocity?" Agent evaluates against constraints and answers: "No, without atmosphere to push against, use bursts of reaction thrusters instead. Suggest adjusting the prose."

### Friction to Eliminate
- Full real-web search needs robust integrations (e.g., Google Search grounding).
- Context auto-injection needs to recognize implicit research connections, beyond proper nouns.

### Success Metric
Writer learns a complex topic and applies realistic constraints to their scene without breaking their Zen flow.

---

## Journey 19: "The Continuity Autopsy" — Resolving Complex Plot Holes

**Persona:** Story Architect
**Trigger:** Writer has merged several divergent scenes or alternate timelines, written out-of-order, and suspects the plot is tangled over an extended timeline.

### Ideal Flow
1. **Global Continuity Sweep:** Writer triggers `/continuity-check deep` in the chat or dashboard. The Continuity Analyst scans the entire Knowledge Graph, relationships, and all drafted scenes.
2. **Flagging Contradictions:** Analyst flags a major contradiction: "In Ch.3, Zara is injured in the leg (requires 3 weeks recovery). However, in Ch.4 (set 2 days later), she is described sprinting."
3. **Suggested Resolutions:** Chat Co-Pilot suggests solutions: 
   - 1) Add a scene where she uses Whisper Magic to heal the leg (cost: memory loss)
   - 2) Change the timeline of Act 2 to occur a month later
   - 3) Revise Ch.4 so she is restricted to limping.
4. **Automated Application:** Writer selects Option 1. The agent drafts a skeletal bridge scene, updates the Timeline node, and resolves the continuity error across the graph.

### Friction to Eliminate
- The Continuity Agent requires extremely high token context (or advanced RAG) to compare distant scenes chronologically accurately.
- LLMs often struggle with deterministic timeline math; needs tight Story Structure metadata integration.

### Success Metric
A major, multi-chapter continuity error is identified and patched with targeted edits in beneath 5 minutes.

---

## Journey 20: "Directing the Ensemble" — Voice and Tone Unification

**Persona:** Showrunner / Editor
**Trigger:** Writer feels the dialogue is blending together; all characters sound like the writer (or the default LLM). Wants strict character differentiation dynamically across scenes.

### Ideal Flow
1. **Voice Scorecard Review:** Writer navigates to the Character Voice Scorecard. The system highlights high phrase overlap between Zara and Kael (both use short, sarcastic sentences).
2. **Updating Character DNA:** Writer updates Kael's Bucket: "Formal, overly polite, uses complex vocabulary, never uses contractions. Tone: Aristocratic masking insecurity."
3. **Batch Style Enforcement:** Writer selects Chapters 1-5 in Pipeline Studio and runs a custom pipeline: "Style Enforcer applied to Kael's Dialogue Only".
4. **Approval & Apply:** The Style Enforcer processes all dialogue attributed to Kael. Approval gates show the diffs side-by-side (`Before: "I don't get why we're doing this." -> After: "I fail to comprehend the necessity of this endeavor."`). Writer approves en masse or tweaks individually.

### Friction to Eliminate
- Parsing speaker attributions reliably out of raw prose to target specific lines for an entire character.
- Maintaining the emotional subtext of a scene while altering the prose style.

### Success Metric
All dialogue of a major character across 10,000 words is rewritten in a distinct, constrained voice in a single pipeline run.

---

## Journey 21: "Power-User Model Tuning" — The Right Brain for the Right Job

**Persona:** Power User
**Trigger:** Writer wants maximum control over quality vs cost/speed. Default prose generation feels generic, but research needs maximum reasoning capacity.

### Ideal Flow
1. **Model Matrix Configuration:** Writer opens Model Configuration settings. They map `gemini-2.0-pro` specifically to the Research Agent and Continuity Analyst (for high reasoning and fact-checking). They map `claude-3.5-sonnet` (with temperature 0.85) to the Writing Agent (for creative prose). They map `gemini-2.0-flash` to Entity Detection (for speed).
2. **Pipeline Execution Observation:** Writer runs a full "Concept to Draft" pipeline. The UI's Glass Box tracks the execution, allowing the user to observe the orchestrator hand off Brainstorming instantly via Flash, and then pause to slowly stream the creative draft via Claude.
3. Writer achieves optimal cost-to-creativity ratio seamlessly.

### Friction to Eliminate
- Dealing with context-window variations between different model providers.

### Success Metric
Writer successfully executes a complex workflow securely and efficiently leveraging 3 different LLMs on a per-step basis transparently.

---

## Journey 22: "Season 2 Scaffold" — Bridging Arcs in the Multi-Season Universe

**Persona:** Series Showrunner
**Trigger:** Writer finishes Season 1. Wants to start Season 2 with a time jump, utilizing the existing World Bible but advancing characters and shifting political allegiances.

### Ideal Flow
1. **Creating the Next Era:** Writer creates a new Season bucket: "Season 2: The Fall". 
2. **Temporal Shifts in Chat:** In Chat: "We're doing a 5-year time jump. Zara is now leader of the Whisper Seekers. Kael is exiled. Update profiles for Season 2." Agent automatically handles state-versioning, keeping Season 1's state intact for its own timeline references, but creating "Season 2 active states" for the updated buckets.
3. **Mining Unresolved Threads:** Writer asks for a summary of unresolved plot threads from Season 1. The agent queries relationships without "resolved" edges and lists issues (e.g. "The Iron Council's missing artifact").
4. **Outlining with Universal Memory:** Writer uses the Story Architect agent to outline Season 2, Acts 1-3, specifically referencing those unresolved threads securely held in the Season 1 Knowledge Graph.

### Friction to Eliminate
- Cross-season bucket versioning is complex (understanding which version of Zara to reference when writing Season 1 vs Season 2 flashbacks).
- Ensuring chronological coherence of global rules.

### Success Metric
Writer sets up a new timeline era that preserves past traits but evolves relationships and seamlessly hooks into unresolved lore, without overwriting legacy histories.
\n## Cross-Journey UX Principles

These principles emerge from all journeys and should guide every design decision:

### 1. Progressive Disclosure
- **First 5 minutes**: Quick capture (Brainstorm), rough structure (Timeline), and writing (Zen). Nothing else needed.
- **First hour**: Schema customization, Research Agent, entity detection. Features appear naturally as the writer needs them.
- **Power user**: Custom pipelines, model configuration, alternate timelines, voice analysis. Always available but never forced.

### 2. The Writer Never Leaves Zen Mode Unnecessarily
- Quick actions (`/expand`, `/brainstorm`, `/research`, `/check-style`, `/translate`) handle 80% of AI interaction.
- ContextSidebar provides entity info, continuity warnings, style feedback, and translation — all without navigating away.
- StoryboardStrip at the bottom gives visual context without page switching.

### 3. Every AI Decision is Visible, Editable, and Attributable
- Every Approval Gate shows: what context was assembled, what model was used, what agent handled it.
- The writer can always: edit the prompt, change the model, paste external output, or skip entirely.
- After approval, the Glass Box log persists so the writer can always trace back: "Why did the AI say that?"

### 4. Context Flows Everywhere Automatically
- Writing "Zara" in Zen Mode automatically pulls her character bucket into the context.
- Research about "railgun physics" auto-injects into any scene involving the weapon.
- Continuity warnings surface proactively, not just on manual check.
- The writer adds context by writing naturally — the system does the linking.

### 5. State is Never Lost
- Every keystroke is debounce-saved. Every mutation is event-sourced.
- Session stats persist across visits. Progress is always visible.
- Alternate timelines are non-destructive. The main branch is always safe.
- Crash recovery via ErrorBoundary and auto-saved fragments.

### 6. Speed to Value
- New story → first AI-assisted writing in under 5 minutes.
- New scene concept → outlined, drafted, and styled in under 30 minutes.
- Returning after a break → back in context in under 2 minutes.
- Translation → glossary-consistent output in under 10 minutes per chapter.

---

\n## Summary: The 22 Critical User Journeys

| # | Journey | Primary Persona | Key Pages | Key Features Used |
|---|---------|----------------|-----------|-------------------|
| 1 | First Session: Quick Capture | Discovery Writer | Brainstorm → Timeline → Zen | Quick Capture, IdeaCards, Structure Tree, Writing, Entity Detection |
| 2 | Deep Worldbuilding | Architect | Schemas → Dashboard → Research | NL Wizard, Custom Schemas, Research Agent, KG Relationships |
| 3 | Writing the Middle | Discovery Writer | Pipelines → Timeline → Zen | Concept→Outline template, Brainstorm slash, Style Check |
| 4 | Script to Storyboard | Visual Storyteller | Storyboard | Layout Intelligence, Panel CRUD, Prompt Composer, Voice-to-Scene |
| 5 | Alternate Timelines | Architect | Timeline | Branch, Compare, Continuity Validation |
| 6 | Polish Before Export | All | Dashboard → Zen → Preview → Export | Continuity Check, Voice Scorecard, Style Enforcer, Reader Sim, Export |
| 7 | Translation | Architect | Translation | Glossary, Translator Agent, Cultural Adaptation |
| 8 | Custom Pipeline | Architect (power) | Pipelines | NL Wizard, DAG Builder, Per-node Model Config |
| 9 | Returning After Break | Any | Dashboard → Zen | Command Center, Session Continuity, Resume |
| 10 | Deep AI Conversation | Discovery Writer | Zen | Brainstorm Chat Refinement, Story Notes, Context Memory |
| 11 | "Dumping My Brain" | Discovery Writer | Dashboard / Chat | First encounter, Chat capture, Artifact previews |
| 12 | "Run My Workflow" | Architect | Chat | Pipeline control from Chat |
| 13 | Worldbuilding via Chat | Architect | Chat | Bulk bucket creation, Schema creation |
| 14 | Writing Side-by-Side | Discovery Writer | Zen / Chat | Inline research, style checks via Chat |
| 15 | Managing Sessions | Any | Chat | /new-session, /compact, /resume |
| 16 | "Plan This For Me" | Architect | Chat | Complex task delegation, Plan execution mode |
| 17 | "What Happened..." | Any | Chat | Catch-up summarization |
| 18 | The Research Rabbit Hole | Architect / Sci-Fi | Chat / Zen | Research Agent, Artifact Fact-Checking, Knowledge Library |
| 19 | The Continuity Autopsy | Architect | Dashboard / Chat | Global continuity sweep, plot hole resolution |
| 20 | Directing the Ensemble | Showrunner / Editor | Analysis / Pipelines | Voice Scorecard, Batch Style Enforcer on Dialogue |
| 21 | Power-User Model Tuning | Power User | Settings / Pipelines | Model Context Matrix, LiteLLM granular routing |
| 22 | Season 2 Scaffold | Showrunner | Timeline / Chat | Multi-season bucket versioning, temporal shifts |
