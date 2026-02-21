# Showrunner: The Complete Vision
**Version:** 1.0  
**Status:** Approved Direction  
**Last Updated:** 2026-02-21

---

## 1. One-Line Purpose

> Showrunner is a **context-aware creative studio** where a writer provides story fragments in any order, and the system automatically organizes, connects, and enriches them across every dimension — characters, places, timelines, panels — while giving the writer full control over every AI decision, every model choice, and every output.

---

## 2. What Makes Showrunner Different

| Other Tools | Showrunner |
|---|---|
| Fixed schemas (Character = Name + Age + Backstory) | **User-defined schemas** — anything can be a bucket |
| AI is a black box — hit "generate" and hope | **Glass Box** — every AI step visible, editable, pausable |
| Linear workflow: write → generate | **Non-linear fragments** — write in any order, system maintains coherence |
| One project, one timeline | **Multi-project, multi-timeline, multi-season** architecture |
| AI decides everything | **Writer in the driver's seat** — AI proposes, writer disposes |
| One model fits all | **Per-step model control** — pick the right model for each task |
| No domain knowledge | **Research Agent** — AI researches real-world topics for factual accuracy |

---

## 3. Core Concepts

### 3.1 Universal Buckets — The Generalized Container

Everything in Showrunner is a **Bucket** (the writer-friendly name for `GenericContainer`).

```
┌─────────────────────────────────────────────────────┐
│                     BUCKET                          │
│                                                     │
│  Type: user-defined (Character, Scene, World,       │
│        Magic System, Faction, Vehicle, Season,      │
│        Research Topic, Science Concept...)           │
│                                                     │
│  Schema: user-defined fields via Schema Builder     │
│  Attributes: { key: value } — the actual data       │
│  Relationships: typed edges to other buckets        │
│  Context Window: auto-summary for LLM consumption   │
│  Timeline Position(s): where in the story this      │
│                         bucket is relevant           │
│  Tags: #act1 #subplot-revenge #draft-2              │
│  Version History: via Event Sourcing                │
│  Model Preference: optional model override          │
└─────────────────────────────────────────────────────┘
```

**Key properties:**
- **Context Window** — Auto-generated LLM-friendly summary, customizable by the writer
- **Timeline Position(s)** — A bucket can span multiple story points
- **Tags** — Free-form labels for filtering and workflow triggers
- **Model Preference** — Override the default model when AI operates on this bucket

### 3.2 The Story Structure Layer

Hierarchical story organization, all built from Buckets:

```
Project
├── Season 1
│   ├── Arc: "The Awakening"
│   │   ├── Act 1
│   │   │   ├── Chapter 1 → Scene 1, 2, 3
│   │   │   └── Chapter 2 → Scene 4, 5, 6
│   │   ├── Act 2
│   │   └── Act 3
│   └── Arc: "The Betrayal"
├── Season 2
├── Alternate Timeline: "What if Character A survived?"
│   └── (branched from Season 1, Act 2, Scene 5)
└── World Bible (season-independent)
    ├── Characters    ├── Locations
    ├── Magic System  ├── Factions
    └── Research Library (science, history, culture...)
```

**Design rules:**
- Everything is a Bucket — Season, Arc, Act, Chapter, Scene are `GenericContainer` types with hierarchical relationships
- **World Bible** persists across seasons/timelines
- **Research Library** holds factual knowledge the Research Agent discovers
- **Alternate Timelines** branch from a story point and inherit all parent context

### 3.3 The Model Control Layer

> **At every step, the writer chooses the model.**

```
┌─────────────────────────────────────────────────┐
│              MODEL CONFIGURATION                │
│                                                 │
│  🌐 Project Default:  gemini-2.0-flash          │
│                                                 │
│  Per-Agent Overrides:                           │
│  ├─ 🔬 Research Agent:    gemini-2.0-pro        │
│  ├─ ✍️  Writing Agent:     claude-3.5-sonnet     │
│  ├─ 🎨 Image Prompts:     gpt-4o               │
│  ├─ 🧠 Brainstorm Agent:  gemini-2.0-flash      │
│  └─ 📐 Schema Wizard:     gemini-2.0-flash      │
│                                                 │
│  Per-Step Overrides (in Pipeline Builder):      │
│  └─ Each LLM node has a model selector dropdown│
│     + temperature + max tokens + system prompt  │
│                                                 │
│  Per-Bucket Overrides:                          │
│  └─ "For Character backstory generation,        │
│      always use claude-3.5-sonnet"              │
└─────────────────────────────────────────────────┘
```

**Priority cascade:** Per-Step > Per-Bucket > Per-Agent > Project Default

All models route through **LiteLLM**, so any provider (Gemini, OpenAI, Anthropic, local Ollama, etc.) is supported via a single config change.

---

## 4. The Agent Ecosystem

### 4.1 Complete Agent Roster

| Agent | Purpose | Default Model | Trigger |
|---|---|---|---|
| **🔬 Research Agent** | Deep-dives into real-world topics (science, history, culture, law) for factual accuracy. Builds a Research Library of verified knowledge. | `gemini-2.0-pro` | User clicks "Research", or auto-triggered when AI-generated content references real-world concepts |
| **🧠 Brainstorm Agent** | Generates ideas, "what if" scenarios, thematic explorations | `gemini-2.0-flash` | User clicks "Brainstorm" |
| **📐 Story Architect** | Builds outlines, act structures, arc planning | `gemini-2.0-flash` | User clicks "Outline from concept" |
| **✍️ Writing Agent** | Writes prose drafts from outlines + context | `claude-3.5-sonnet` | User clicks "Draft scene" |
| **🎨 Prompt Composer** | Builds optimized prompts for image generation | `gpt-4o` | Pipeline reaches image prompt step |
| **🔍 Continuity Analyst** | Validates changes against story state, catches plot holes | `gemini-2.0-flash` | Auto-runs on scene save |
| **🧩 Schema Wizard** | NL → field definitions for custom types | `gemini-2.0-flash` | Schema Builder wizard |
| **🎬 Pipeline Director** | Assembles pipeline steps from description | `gemini-2.0-flash` | Pipeline builder assist |
| **🎭 Style Enforcer** | Ensures consistent tone/voice across scenes | Configurable | Optional pipeline step |
| **🌍 Translator Agent** | Translates content while preserving style | Configurable | Optional pipeline step |

### 4.2 The Research Agent — Deep Dive

The Research Agent is special because it builds **persistent knowledge** that enriches the story:

```
Writer asks: "How would a railgun actually work in low gravity?"
                              │
              ┌───────────────┴───────────────┐
              │      Research Agent             │
              │  Model: gemini-2.0-pro          │
              └───────────────┬───────────────┘
                              │
        1. Searches existing Research Library
        2. If insufficient → generates detailed research
        3. Structures findings into knowledge bucket:
                              │
              ┌───────────────▼───────────────┐
              │  Research Bucket:               │
              │  "Railgun Physics (Low-G)"      │
              │                                 │
              │  category: "Physics / Weapons"  │
              │  summary: "In low gravity..."   │
              │  key_facts: [...]               │
              │  constraints: [...]             │
              │  story_implications: [...]       │
              │  sources: [...]                 │
              │  confidence: "high"             │
              │  linked_to: [Scene 12, Ch. A]   │
              └─────────────────────────────────┘
                              │
              4. ⏸️ User approves research findings
              5. Saved to Research Library bucket
              6. Auto-linked to relevant scenes/chapters
              7. Future AI calls in those scenes
                 include this context automatically
```

**Research Agent capabilities:**
- **Factual deep-dives** — science, history, culture, geography, law, medicine
- **Consistency checking** — "You said the planet has 0.3g, but your character is jumping 10 meters — that's plausible" or "That's not plausible"
- **Knowledge categorization** — organizes research into structured buckets with tags
- **Source tracking** — marks confidence level and whether facts need verification
- **Auto-injection** — when writing a scene that touches a researched topic, the Research Library context is automatically included in the AI prompt

### 4.3 Universal Agent Invocation Pattern

Every agent follows this exact pattern:

```
1. GATHER CONTEXT → assemble from Knowledge Graph + Research Library
2. SELECT MODEL   → per-step > per-bucket > per-agent > project default
3. BUILD PROMPT   → system prompt + context + user intent
4. ⏸️ SHOW PROMPT TO USER
   ├─ ✏️ Edit prompt directly
   ├─ 💬 Chat to refine ("make it more technical")
   ├─ 🔧 Change model for this call
   ├─ 📋 Paste response from external AI
   └─ ✅ Approve as-is
5. EXECUTE        → send to selected model via LiteLLM
6. ⏸️ SHOW OUTPUT TO USER
   ├─ ✏️ Edit output
   ├─ 🔄 Regenerate (with different model/temp)
   ├─ 📌 Pin/unpin context buckets
   └─ ✅ Approve
7. SAVE           → persist to bucket via ContainerRepository
8. EVENT          → emit to EventService
9. INDEX          → update Knowledge Graph
```

---

## 5. The Workflow Engine — Three Layers

### Layer 1: Quick Actions (Inline, in Zen Mode)
`/expand`, `/dialogue`, `/describe`, `/brainstorm`, `/research`, `/continuity-check`

Each quick action auto-injects the current scene's context and uses the appropriate agent + model.

### Layer 2: Workflow Templates (1-Click, pre-built)

| Template | Steps | Agents Used |
|---|---|---|
| **Scene → Panels** | Gather context → Build prompt → ⏸️ → Generate panels → ⏸️ → Save | Prompt Composer → Storyboard AI |
| **Concept → Outline** | Brainstorm → ⏸️ → Architect outline → ⏸️ → Create structure | Brainstorm → Story Architect |
| **Outline → Draft** | Gather context → ⏸️ → Write prose → ⏸️ → Entity extract → Save | Writing Agent |
| **Topic → Research** | Identify topics → ⏸️ → Deep research → ⏸️ → Save to library | Research Agent |
| **Draft → Polish** | Style check → ⏸️ → Continuity check → ⏸️ → Final edit | Style Enforcer → Continuity Analyst |
| **Panel → Image** | Compose prompt → ⏸️ → Generate image → ⏸️ → Save | Prompt Composer → External |
| **Full Pipeline** | Brainstorm → Outline → Draft → Panels → Images | All agents |

Every `⏸️` is an Approval Gate where the writer can edit, change model, paste external output, or regenerate.

### Layer 3: Custom Pipelines (Visual DAG Builder)

Enhanced with new step types:

| Category | Steps |
|---|---|
| **Context** | `gather_buckets`, `semantic_search`, `research_lookup` |
| **Transform** | `prompt_template`, `multi_variant`, `merge_outputs` |
| **Human** | `review_prompt`, `approve_output`, `approve_image`, `select_model` |
| **Execute** | `llm_generate`, `image_generate`, `save_to_bucket`, `http_request`, `research_deep_dive` |
| **Logic** | `if_else`, `loop`, `parallel_branch`, `merge` |

Each `llm_generate` and `research_deep_dive` step has a **model selector** dropdown in its config panel.

---

## 6. Automatic Context Routing — The Core Magic

When the writer writes **anything**, the system automatically:

```
Writer types: "Zara draws her obsidian blade and steps into the Whispering Market"
                                    │
                    ┌───────────────┴───────────────┐
                    │     Entity Detection (LLM)     │
                    └───────────────┬───────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
   ┌──────▼──────┐          ┌──────▼──────┐          ┌───────▼───────┐
   │ Character:   │          │ Item:        │          │ Location:      │
   │ Zara         │          │ Obsidian     │          │ Whispering     │
   │ +scene_ref   │          │ Blade        │          │ Market         │
   │ +context     │          │ +scene_ref   │          │ +scene_ref     │
   └──────────────┘          └──────────────┘          └────────────────┘
          │                                                     │
          │              ┌──────────────────┐                   │
          └──────────────│ Research Library: │───────────────────┘
                         │ "Market trade    │
                         │ economics" auto- │
                         │ linked if exists │
                         └──────────────────┘
```

**How it works:**
1. Entity Detection runs (debounced, 2s after writer stops typing)
2. For each entity: search Knowledge Graph + Research Library
3. If **found** → auto-link to current scene
4. If **not found** → show inline suggestion: "Create new Character: Zara?"
5. Update Knowledge Graph incrementally
6. Emit event to Event Sourcing log
7. Push SSE update to all connected frontends

---

## 7. UI Surfaces

### 7.1 Command Center (`/dashboard`)

Writer's home base with multi-project support:

```
┌─────────────────────────────────────────────────────────────┐
│  📚 Projects                         [+ New Project]  [⚙️]  │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ 🌙 Midnight       │  │ 🚀 Star Drift     │                 │
│  │ Chronicle        │  │ S2 • Ch.4 • Sc.2 │                 │
│  │ S1 • Ch.3 • Sc.7 │  │ 12 panels        │                 │
│  │ 45 panels        │  │ Last: 2h ago     │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                             │
│  ── Active: Midnight Chronicle ──                           │
│  📊 Progress    │ 🕐 Recent Activity   │ 🤖 Pending (3)     │
│  Act 1: 80%    │ Wrote 340 words      │ Panel prompts      │
│  Act 2: 40%    │ Generated 6 panels   │ Research findings  │
│  Act 3:  0%    │ Updated "Zara"       │ Continuity check   │
│                │                      │                    │
│  ⚙️ Model Config: [gemini-2.0-flash ▾] │ 🔬 Research: [pro]│
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Story Timeline (`/timeline`)

Visual story structure — click any node to open in Zen Mode or Storyboard:

```
Season 1: The Awakening
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACT 1                    ACT 2                    ACT 3
┌─────────┐             ┌─────────┐             ┌─────────┐
│ Ch.1    │─────────────│ Ch.4    │─────────────│ Ch.7    │
│ Sc.1-3  │             │ Sc.10-12│             │ Sc.19-21│
│ 🟢 Done │             │ 🟡 WIP  │             │ ⚪ Plan  │
└─────────┘             └─────────┘             └─────────┘

🌿 Branches: [Main] [What if Zara joined the enemy?] [Prequel]
```

### 7.3 Writing Desk (enhanced `/zen`)

```
┌──────────────────────────────────────────────────────────────────┐
│  ✍️ Scene 7: "The Market Encounter"  │ 📍 Ch.3 > Act 1 > S1    │
│  Model: [claude-3.5-sonnet ▾]                                   │
│  ┌─EDITOR─────────────────────┐  ┌─CONTEXT PANEL──────────────┐│
│  │ Zara drew her obsidian     │  │ 🧑 Characters: Zara, Kael  ││
│  │ blade and stepped into     │  │ 📍 Location: Market        ││
│  │ the @[Whispering Market].  │  │ 📖 Prev: Scene 6 summary   ││
│  │                            │  │ 🔬 Research: Market trade   ││
│  │ [@ to reference buckets]  │  │ ⚠️ Continuity: Blade was   ││
│  │ [/ for AI + /research]    │  │    broken in Sc.4 — fixed? ││
│  └────────────────────────────┘  └─────────────────────────────┘│
│  ┌─STORYBOARD STRIP──────────────────────────────────────────┐  │
│  │ [P1: Wide] [P2: Close] [P3: OTS] [P4: Action] [+Generate]│  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.4 Workflow Studio (enhanced `/pipelines`)

Each node in the DAG has a model selector:

```
┌──────────────────────────────────────────────────────────────┐
│  🔧 Workflow Studio              [Templates ▾] [My Flows]   │
│  ┌─TEMPLATES──────┐  ┌─CANVAS────────────────────────────┐  │
│  │ Scene → Panels │  │ [Gather] → [Template] → [⏸️ Rev]  │  │
│  │ Concept→Outline│  │              ↓              ↓     │  │
│  │ Topic→Research │  │        [LLM Gen]      [⏸️ Output]  │  │
│  │ Draft → Polish │  │    model: [claude ▾]        ↓     │  │
│  │                │  │    temp:  [0.7]       [Save Bucket]│  │
│  ├─STEP LIBRARY───┤  └──────────────────────────────────┘  │
│  │ Context        │  ┌─CONFIG─────────────────────────────┐  │
│  │ Transform      │  │ LLM Generate                       │  │
│  │ Human Gates    │  │ Model: [gemini-2.0-flash ▾]        │  │
│  │ Execute        │  │ Temperature: [0.7]                 │  │
│  │ Logic ⭐        │  │ Max Tokens: [2000]                 │  │
│  │  If/Else       │  │ Fallback Model: [gpt-4o-mini ▾]   │  │
│  │  Loop          │  └────────────────────────────────────┘  │
│  │  Merge         │                                          │
│  └────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Bucket Customization Options

Every bucket type offers these customization points:

| Option | Description | Example |
|---|---|---|
| **Schema** | Define the fields | Character: name, age, backstory, abilities |
| **Context Template** | How this bucket appears in AI prompts | `"{{name}} is a {{age}}-year-old {{role}}"` |
| **Display Template** | How it renders in UI cards | Card with portrait + key stats |
| **Validation Rules** | Constraints on values | Age > 0; name unique within project |
| **Auto-link Rules** | When to auto-create relationships | "If Character name found in Scene text, link" |
| **Lifecycle Hooks** | Workflows triggered on CRUD | "On Character create → generate portrait" |
| **Model Preference** | Default model for AI on this bucket | "Use claude for backstory gen" |
| **Research Tags** | Topics to auto-research | "physics, medieval_weapons" |

---

## 9. Multi-Project & Multi-Timeline Management

```
POST /api/v1/projects/                        # Create project
GET  /api/v1/projects/                        # List all projects
GET  /api/v1/projects/{id}/structure          # Story structure tree
PUT  /api/v1/projects/{id}/settings           # Model defaults, style, target medium

POST /api/v1/projects/{id}/seasons/           # Add season
POST /api/v1/projects/{id}/timelines/branch   # Branch alternate timeline

# Model configuration endpoints:
GET  /api/v1/models/available                 # List LiteLLM-supported models
PUT  /api/v1/projects/{id}/model-config       # Project-level model defaults
PUT  /api/v1/agents/{name}/model-config       # Agent-level model override
```

---

## 10. Design Principles

1. **Bucket-First** — Every piece of data is a bucket. If it can't be a `GenericContainer`, rethink the model.
2. **Writer Over AI** — AI proposes, writer disposes. Never auto-commit without approval.
3. **Context is King** — Every AI call gets the richest relevant context within the token budget.
4. **Show the Plumbing** — Writer always sees: what context the AI used, what prompt was sent, which agent handled it, which model ran it.
5. **Model Freedom** — The writer picks the model at every level. No lock-in.
6. **Non-Linear Input, Coherent Output** — Write Scene 15 before Scene 3. The system maintains coherence.
7. **Research-Backed Accuracy** — Real-world claims are fact-checked and persisted in the Research Library.
8. **Everything is Event-Sourced** — Every mutation tracked, every state recoverable, every timeline branchable.
9. **Progressive Complexity** — Quick actions → Templates → Full pipeline builder.
10. **Connector Architecture** — External tools (image gen, translation, TTS) are first-class pipeline steps.

---

## 11. Implementation Roadmap

### Phase F: Foundation Rework
- Wire Event Sourcing into all mutation paths
- Add Story Structure layer (Season/Arc/Act/Chapter)
- Multi-Project support with project-scoped data
- Fix persistence (route all services through `ContainerRepository`)
- Auto-Context Routing (entity detection → auto-link)
- Model Configuration layer (project/agent/step/bucket cascade)

### Phase G: Workflow & Agent Enhancement
- Workflow Templates library (pre-built 1-click flows)
- Logic Steps in pipeline builder (If/Else, Loop, Merge)
- **Research Agent** implementation + Research Library buckets
- Prompt Vault (save, version, share prompt templates)
- External tool integration (webhook steps for image generators)
- Enhanced Approval Gate (regenerate, pin context, change model)

### Phase H: Intelligence Layer
- RAG / Vector Search for semantic context retrieval
- Continuity auto-check on every save
- New agents: Brainstorm, Story Architect, Writing, Style Enforcer
- NL → Workflow generation (describe a pipeline in words)
- Research auto-trigger (detect real-world claims, auto-research)

### Phase I: Polish & Scale
- Command Center UI redesign
- Story Timeline interactive visualization
- Enhanced Writing Desk (context panel + continuity + storyboard strip)
- Auth & Collaboration (multi-user, sharing)
- Export (PDF, EPUB, image pack, print-ready)

---

## 12. Reference Inspirations

| Tool | What We Take |
|---|---|
| **n8n** | Visual DAG builder, orchestrator-worker pattern, template marketplace, webhook triggers |
| **Google Opal** | NL → workflow generation, step-level prompt chaining, `@reference` syntax for data flow |
| **Opus AI** | Script → storyboard pipeline, consistent character visuals, brand/style consistency |
| **ComfyUI** | Per-node model selection, visual parameter tuning, checkpoint-based workflow control |
