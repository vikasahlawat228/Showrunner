# Showrunner Workflow Tiers
**Date:** 2026-03-08
**Purpose:** Clarify 4 levels of Showrunner usage and guide users to the right tool

---

## Overview

Showrunner can be used in different ways depending on your needs and expertise level. This document defines 4 workflow tiers, from casual writing to advanced automation.

| Tier | Name | Tools | Audience | Frequency |
|------|------|-------|----------|-----------|
| **1** | Writing Mode | Zen Mode + Chat | Discovery Writers, Pantsers | 80% of users |
| **2** | Structured Creation | Dashboard + UI + Chat | Architects, Planners | 15% of users |
| **3** | Advanced Automation | Pipelines + Chat + CLI | Power Users | 5% of users |
| **4** | IDE Integration | CLI + Code Editor | Tool Developers | Dev only |

---

## Tier 1: Writing Mode 📝 (Primary)

**Use When:** You want to write scenes without thinking about structure/architecture.

### The Workflow

```
1. Open QuantumDharma project in IDE or browser
2. Read project context (CLAUDE.md or Dashboard)
3. Open Zen Mode (/zen)
4. Chat sidebar provides character + world context
5. Write your scene prose
6. Commit to git
7. Move to next scene
```

### Tools Used
- **Zen Mode** — Distraction-free writing editor with TipTap
- **Chat Sidebar** — Ask questions, get character context, brainstorm
- **Git** — Commit your completed scenes

### Key Commands
```bash
# Start writing session
cd /Documents/QuantumDharma
# Open http://localhost:3000/zen in browser

# Chat shortcuts (when sidebar is visible)
Ctrl+K     → Toggle chat sidebar
Esc        → Close chat sidebar
@Character → @ mention a character for context
/research  → Research a topic
```

### IDE Agent Decision
✅ **Use Zen Mode + Chat** (NOT CLI)

Why? Because:
- Distraction-free environment
- Real-time collaboration with chat
- No need for CLI prompts
- Visual story outline context

---

## Tier 2: Structured Creation 🏗️ (Intermediate)

**Use When:** You're building characters, locations, world rules, or planning story structure before writing.

### The Workflow

```
1. Open Dashboard (/dashboard)
2. See project state and workflow progress
3. Use Schema Builder to create custom data types
4. Use Character/Location dialogs to create entities
5. Use Chat to brainstorm and refine
6. Use Storyboard to plan scenes visually
7. Commit your structure
8. Move to Tier 1 for writing
```

### Tools Used
- **Dashboard** — Project overview, Knowledge Graph visualization
- **Schema Builder** — Define custom bucket types (e.g., "Magic System", "Faction")
- **Character/World Dialogs** — Create structured entities
- **Storyboard** — Visual planning with panels and camera angles
- **Chat** — Ask questions, refine decisions
- **Timeline** — View story structure, alternate branches

### Key Commands
```bash
# Create a character
POST /api/v1/containers/
  body: { container_type: "character", name: "Zara", attributes: {...} }

# Create a location
POST /api/v1/containers/
  body: { container_type: "location", name: "College", ... }

# View knowledge graph
GET http://localhost:3000/dashboard

# Plan scenes
GET http://localhost:3000/storyboard
```

### IDE Agent Decision
✅ **Use Web UI + Chat** (NOT CLI for CRUD, CLI only for context)

Why? Because:
- Visual feedback
- Drag-drop for storyboard
- Easier to browse existing data
- Chat refines your choices

---

## Tier 3: Advanced Automation 🚀 (Expert)

**Use When:** You want to automate multi-step workflows (outline → draft → review) or integrate AI pipelines.

### The Workflow

```
1. Define a custom Pipeline in Pipeline Studio (/pipelines)
2. Set approval gates and model overrides per step
3. Choose your models (Claude for prose, Gemini for images)
4. Run the pipeline
5. Review at each gate
6. Chat to refine intent
7. Approve and execute next steps
8. Commit the results
```

### Tools Used
- **Pipeline Studio** — Visual DAG builder with approval gates
- **Model Config** — Per-step, per-agent, or project-level model selection
- **Chat** — Refine prompts at approval gates
- **Storyboard** — Preview generated panels
- **Research Agent** — Deep-dive research for factual accuracy

### Example: Scene Generation Pipeline

```
1. Context → Load scene context (character, location, previous scene)
2. Research → (Optional) Research real-world facts
3. Outline → Generate scene outline via Claude
4. ⏸️ Review Outline Gate → Approve, edit, or chat to refine
5. Draft → Generate full scene prose
6. ⏸️ Review Draft Gate → Approve or iterate
7. Continuity Check → Validate against established rules
8. Export → Save to fragment/
```

### Key Commands
```bash
# Define a pipeline
POST /api/v1/pipeline/definitions
  body: { steps: [...], edges: [...] }

# Run pipeline with approval gates
POST /api/v1/pipeline/run
  body: { definition_id: "...", context: {...} }

# At approval gate, use Chat
POST /api/v1/chat/message
  body: { content: "Refine the outline to emphasize the climax" }

# Resume after approval
POST /api/v1/pipeline/{run_id}/resume
  body: { approved: true, edits: {...} }
```

### IDE Agent Decision
✅ **Use Pipeline Studio + Chat** (CLI only for setup/debugging)

Why? Because:
- Visual approval gates
- Better feedback on each step
- Easier to modify mid-workflow
- Chat handles refinement requests

---

## Tier 4: IDE Integration 🧑‍💻 (Development)

**Use When:** You're developing the Showrunner tool, testing new features, or doing bulk operations.

### The Workflow

```
1. Open Showrunner CLI in terminal
2. showrunner status — See project state
3. showrunner <command> — Issue a command
4. CLI prints a detailed prompt with context
5. Claude Code reads the prompt
6. Claude Code generates YAML/code
7. Write output to file
8. FileWatcher auto-syncs to web UI
9. Commit to git
```

### Tools Used
- **CLI** — Command-line interface for all Showrunner operations
- **Claude Code** — Editor integration for AI-assisted generation
- **Git** — Version control
- **YAML files** — Direct file editing for precision

### All Available Commands

```bash
# Project
showrunner status                          # Show project state
showrunner project list                    # List registered projects
showrunner project set <id>                # Switch active project
showrunner project register /path          # Register new project

# Characters
showrunner character create "Name"         # Generate character prompt
showrunner character list
showrunner character get <id>

# World
showrunner world build                     # Generate world building
showrunner world list-locations
showrunner world add-rule "Rule text"

# Story
showrunner story outline                   # Generate story structure
showrunner story list-chapters

# Scenes
showrunner scene write --chapter 1 --scene 1  # Generate scene prompt
showrunner scene list

# Pipeline
showrunner pipeline run <definition-id>    # Execute pipeline
showrunner pipeline list

# Research
showrunner research "Topic"                # Research + generate knowledge bucket

# Evaluate
showrunner evaluate continuity             # Check for plot holes
showrunner evaluate pacing                 # Analyze pacing

# Sessions
showrunner session start "Description"     # Start work session
showrunner session end "Summary"           # End session + save context

# Decisions
showrunner decide add "Decision text"      # Record decision
showrunner decide list

# Brief
showrunner brief show                      # Show current project brief
showrunner brief update                    # Update CLAUDE.md
```

### IDE Agent Decision
✅ **Use CLI for context/prompts, Claude Code for generation** (NOT web UI)

Why? Because:
- Transparent prompts
- Precise control
- Tool development context
- File-native (YAML is source of truth)

---

## Decision Tree: Which Tier Should I Use?

```
┌─ Are you writing a scene?
│  └─ YES → Use Tier 1 (Zen Mode + Chat)
│  └─ NO  → Continue below
│
├─ Do you need visual planning/creation?
│  └─ YES → Use Tier 2 (Dashboard + UI)
│  └─ NO  → Continue below
│
├─ Do you want to automate a multi-step workflow?
│  └─ YES → Use Tier 3 (Pipelines)
│  └─ NO  → Use Tier 1/2 or move to below
│
├─ Are you developing Showrunner or testing the CLI?
│  └─ YES → Use Tier 4 (CLI + Code)
│  └─ NO  → Use appropriate tier above
│
└─ Confused?
   └─ Default: Tier 1 (Zen Mode + Chat) — most users start here
```

---

## Context Flow Diagram

```
┌──────────────────────────────────────┐
│       Project State (YAML)           │
│  characters/, world/, story/, etc.   │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│    Knowledge Graph + Vector Store    │
│   (SQLite + ChromaDB indexing)       │
└──────────────────────────────────────┘
              ↓
    ┌─────────┬─────────┬──────────┐
    ↓         ↓         ↓          ↓
 TIER 1    TIER 2    TIER 3    TIER 4
 Zen       Dashboard Pipelines  CLI
 Mode      + UI      + Chat     + Code
    ↓         ↓         ↓          ↓
    └─────────┴─────────┴──────────┘
              ↓
┌──────────────────────────────────────┐
│     Chat Sidebar (All Tiers)        │
│   Multi-turn agent assistance       │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│    Approval Gates + Human Review    │
│  (Tier 2/3 feature, optional Tier 1) │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│       Git Commit (All Tiers)        │
│   Version control for all changes   │
└──────────────────────────────────────┘
```

---

## FAQ: When Should I Switch Tiers?

**Q: I'm writing in Tier 1 but need a new character.**
A: Create the character in Tier 2 UI first (quick), then return to Tier 1 writing. Chat can help reference the new character.

**Q: Can I use Tier 3 pipelines without Tier 1/2?**
A: Yes, but you'll miss context. Start with Tier 2 to populate your world, then use Tier 3 to automate.

**Q: Is Tier 4 (CLI) only for developers?**
A: Mostly. Power users might use CLI for bulk operations or precise YAML editing, but Tier 1-3 is the intended path.

**Q: Can I use multiple tiers in one session?**
A: Absolutely! Example:
1. Use Tier 2 to create a character (Dashboard)
2. Use Tier 1 to write a scene with that character (Zen Mode)
3. Use Tier 3 to generate panels (Pipeline)
4. Use Tier 1 again to refine the scene

---

## Performance Tips by Tier

### Tier 1 (Zen Mode)
- Keep scene length <5000 words for faster processing
- Use `/research` command for unknown facts
- @mention characters to load their full context
- Save frequently (Ctrl+S)

### Tier 2 (Dashboard)
- Load Knowledge Graph once per session (auto-cached)
- Narrow schema builder selections for faster creation
- Use tags to organize custom buckets
- Batch creation (create all characters before building world)

### Tier 3 (Pipelines)
- Use approval gates to save token budget
- Set model overrides at the step level (not project)
- Use /compact in chat to summarize context
- Test pipeline with small context first

### Tier 4 (CLI)
- Use `showrunner brief show` to load context once
- Use `--output` flags to save directly to YAML
- Batch CLI commands (`&&` chaining) to avoid repeated context loading
- Check `showrunner status` before running commands

---

## Transitioning Between Tiers

### Tier 1 → Tier 2
When you need to **add** something:
```
1. Switch to Dashboard (/dashboard)
2. Create new entity (character, location, etc.)
3. Return to Zen Mode (/zen)
4. Chat loads the new entity context automatically
```

### Tier 2 → Tier 3
When you want to **automate** something:
```
1. Visit Pipeline Studio (/pipelines)
2. Create a new pipeline definition
3. Add the entities you created in Tier 2 as inputs
4. Run the pipeline and approve at gates
```

### Tier 3 → Tier 1
When you want to **write** the results:
```
1. Export pipeline results (or use /export in chat)
2. Review in Storyboard (/storyboard)
3. Switch to Zen Mode (/zen)
4. Refine the generated content by hand
```

### Tier 4 → Tier 1/2/3
When you've **tested** a CLI feature:
```
1. File is auto-synced by FileWatcher
2. Switch to browser (UI)
3. View the result in Dashboard or Zen Mode
4. Proceed with Tier 1/2/3 workflow
```

---

## Summary

Use **Showrunner Tiers** to match your current task:

| I want to... | Use Tier |
|---|---|
| Write a scene | 1 (Zen Mode) |
| Create characters/locations | 2 (Dashboard) |
| Plan visually (storyboard) | 2 (Dashboard) |
| Generate and refine with AI | 3 (Pipelines) |
| Automate workflows | 3 (Pipelines) |
| Test the tool | 4 (CLI) |
| Ask for help | 1-3 (Chat Sidebar) |
| Control version history | All (Git) |

**Default:** Start with **Tier 1** (Zen Mode + Chat). Branch to other tiers as needed.

---

*Document prepared by: Comprehensive Architecture Review*
*Last Updated: 2026-03-08*
