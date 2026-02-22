# Showrunner: Ideal User Journeys & Critical User Journeys (CUJs)
**Status:** Living Document
**Last Updated:** 2026-02-21

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

## Cross-Journey UX Principles

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

## Summary: The 10 Critical User Journeys

| # | Journey | Primary Persona | Key Pages | Key Features Used | Target Time |
|---|---------|----------------|-----------|-------------------|-------------|
| 1 | First Session: Quick Capture | Discovery Writer | Brainstorm → Timeline → Zen | Quick Capture, IdeaCards, Structure Tree, Writing, Entity Detection | 45 min |
| 2 | Deep Worldbuilding | Architect | Schemas → Dashboard → Research | NL Wizard, Custom Schemas, Research Agent, KG Relationships | 40 min |
| 3 | Writing the Middle | Discovery Writer | Pipelines → Timeline → Zen | Concept→Outline template, Brainstorm slash, Style Check | 90 min |
| 4 | Script to Storyboard | Visual Storyteller | Storyboard | Layout Intelligence, Panel CRUD, Prompt Composer, Voice-to-Scene | 30 min |
| 5 | Alternate Timelines | Architect | Timeline | Branch, Compare, Continuity Validation | 15 min |
| 6 | Polish Before Export | All | Dashboard → Zen → Preview → Export | Continuity Check, Voice Scorecard, Style Enforcer, Reader Sim, Export | 60 min |
| 7 | Translation | Architect | Translation | Glossary, Translator Agent, Cultural Adaptation | 30 min/chapter |
| 8 | Custom Pipeline | Architect (power) | Pipelines | NL Wizard, DAG Builder, Per-node Model Config | 10 min |
| 9 | Returning After Break | Any | Dashboard → Zen | Command Center, Session Continuity, Resume | 2 min |
| 10 | Deep AI Conversation | Discovery Writer | Zen | Brainstorm Chat Refinement, Story Notes, Context Memory | 15 min |
