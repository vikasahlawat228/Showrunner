# Showrunner: Agentic Chat Co-Pilot — Critical User Journeys

**Status:** Living Document
**Last Updated:** 2026-02-21

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
