# Repository Structure & Organization Guide

**Date**: 2026-03-08
**Status**: Two-repository split complete ✅

---

## 🎯 Overview: Two Separate Repositories

The Quantum Dharma project now lives in **two separate git repositories**, each with a distinct purpose:

### Repository 1: **Showrunner** (Tool + Reference)
```
📍 Location: /Users/vikasahlawat/Documents/Showrunner/
🎯 Purpose: Showrunner CLI tool development, shared resources
📦 What's tracked: Tool code, documentation, brainstorm notes (reference)
🔗 Repository: https://github.com/[your-org]/showrunner
```

### Repository 2: **Quantum Dharma** (Story Project)
```
📍 Location: /Users/vikasahlawat/Documents/QuantumDharma/
🎯 Purpose: Story creative work (characters, scenes, world building)
📦 What's tracked: YAML story content, decisions, creative room, sessions
🔗 Repository: Create as https://github.com/[your-org]/quantum-dharma (optional)
```

---

## 📋 What Lives Where

### **Showrunner Repo** (`/Documents/Showrunner/`)

| Type | Location | Purpose |
|------|----------|---------|
| **Tool Source** | `src/showrunner_tool/` | Python CLI implementation |
| **Web Frontend** | `src/web/` | Next.js UI (optional UI studio) |
| **Documentation** | `docs/` | IDE_GUIDE.md, QUICKSTART.md, etc. |
| **Brainstorm Notes** | `My Story Notes Dump/Keep/` | 65 original Google Keep exports (HTML+JSON) |
| **Compiled Notes** | `COMPILED_STORY_NOTES.txt` | Master reference (all 65 notes) |
| **Story Development** | `agents/tasks/` | Mission docs, friction logs, recommendations |
| **Project Config** | `CLAUDE.md` | Development guide & project instructions |

**Committed in latest commit** (7a9405c):
- 65 Google Keep notes with metadata
- Compiled story notes (61KB)
- Story kickoff mission document
- Story brainstorm dump (101KB)
- Friction log, optimization recommendations
- Development task documentation

### **Quantum Dharma Repo** (`/Documents/QuantumDharma/`)

| Type | Location | Purpose |
|------|----------|---------|
| **Characters** | `characters/*.yaml` | 10 character profiles with DNA blocks |
| **World** | `world.yaml` + `world/` | 4 reality layers, 7 rules, 6 locations |
| **Story Structure** | `story.yaml` + `story/` | 15 beats, 40 chapters, arcs, themes |
| **Written Scenes** | `fragment/*.yaml` | Actual story prose (Chapter 1 Scene 1 written) |
| **Story Decisions** | `.showrunner/decisions.yaml` | 12 persistent author preferences |
| **Creative Room** | `.showrunner/creative_room.yaml` | 10 hidden truths, secrets, revelations |
| **Sessions** | `.showrunner/sessions/` | Session logs and context |
| **Reference** | `reference/` | Brain dump, Keep notes, dev tasks (local copies) |
| **Project Config** | `CLAUDE.md` | Story-specific briefing |
| **Project Manifest** | `showrunner.yaml` | Showrunner config for this story |

**Committed in initial commit** (a1d77de):
- Complete world building (4 layers, 6 locations, 7 rules)
- 10 character profiles with full DNA blocks
- 15 save-the-cat story beats covering 40 chapters
- Opening scene written (2500+ words)
- 12 author decisions
- 10 creative room secrets
- Reference materials (copies from Showrunner)

---

## 🔄 Workflow: How They Work Together

### **For Writing Scenes**

```
1. Open QuantumDharma repo in IDE
2. Reference: Read reference/brain-dump/story-brainstorm-dump.md (Section 0)
3. Check: Review characters/*.yaml for current scene characters
4. Write: Add prose to fragment/ch1-sc2.yaml
5. Commit: git commit -m "feat: Write Chapter 1 Scene 2"
```

**Git Status**: QuantumDharma repo only
**Showrunner Repo**: Not affected (stays clean)

### **For Brainstorm Note Updates**

```
1. Update reference/brain-dump/story-brainstorm-dump.md locally
2. Commit: git commit -m "docs: Update [section] with [new insights]"
3. Optional: Sync back to /Documents/Showrunner/agents/tasks/
   - Copy updated file
   - Commit in Showrunner repo
   - This keeps reference materials in sync
```

**Git Status**: Both repos can be updated (independent commits)

### **For Tool Testing Against Story Project**

```
1. cd /Documents/Showrunner
2. showrunner status  (checks QuantumDharma project)
3. showrunner character create "NewChar" (generates prompt)
4. Read prompt, generate YAML in QuantumDharma/characters/
5. git add -A in QuantumDharma repo
6. git commit in QuantumDharma repo
```

**Git Status**: Separate commits in each repo

### **For Syncing Decisions or Creative Room**

```
1. Update .showrunner/decisions.yaml in QuantumDharma
2. git commit in QuantumDharma repo
3. Optional: Document change in Showrunner/agents/tasks/ for reference
```

---

## 🛠️ Git Commands Reference

### Showrunner Repo
```bash
cd /Users/vikasahlawat/Documents/Showrunner

# Check status
git status

# View commits
git log --oneline | head -10

# Commit reference materials updates
git add agents/tasks/
git commit -m "docs: Update [doc] with [changes]"
```

### Quantum Dharma Repo
```bash
cd /Users/vikasahlawat/Documents/QuantumDharma

# Check status
git status

# View commits
git log --oneline | head -10

# Commit story work
git add characters/
git commit -m "feat: Create character [name]"

# Or commit scenes
git add fragment/
git commit -m "feat: Write Chapter X Scene Y"
```

---

## 📂 File Tree Overview

```
~/Documents/
│
├── Showrunner/                              (Tool + Reference)
│   ├── src/
│   │   ├── showrunner_tool/                (CLI implementation)
│   │   └── web/                             (Web UI - optional)
│   ├── docs/
│   │   ├── IDE_GUIDE.md
│   │   ├── QUICKSTART.md
│   │   └── SCHEMA_REFERENCE.md
│   ├── My Story Notes Dump/Keep/            (65 original Keep exports)
│   ├── COMPILED_STORY_NOTES.txt             (Master reference)
│   ├── agents/tasks/                        (Mission docs, friction logs)
│   ├── CLAUDE.md                            (Tool development guide)
│   └── REPO_STRUCTURE.md                    (This file)
│
└── QuantumDharma/                           (Story Project)
    ├── characters/                          (10 YAML character profiles)
    │   ├── a.yaml
    │   ├── b.yaml
    │   ├── f.yaml
    │   ├── mother.yaml
    │   ├── masked_man.yaml
    │   ├── professor_h.yaml
    │   ├── v.yaml
    │   ├── p.yaml
    │   ├── c.yaml
    │   └── main_villain.yaml
    ├── world.yaml                           (World building YAML)
    ├── world/                               (World components)
    │   ├── rules.yaml
    │   ├── settings.yaml
    │   └── history.yaml
    ├── story.yaml                           (Story structure YAML)
    ├── story/                               (Story components)
    │   ├── relationships.yaml
    │   ├── structure.yaml
    │   ├── themes.yaml
    │   └── timeline.yaml
    ├── fragment/                            (Written scenes)
    │   ├── ch1-sc1.yaml                     (Opening scene - 2500+ words)
    │   └── [future scenes]
    ├── .showrunner/                         (Showrunner metadata)
    │   ├── decisions.yaml                   (12 author decisions)
    │   ├── creative_room.yaml               (10 hidden truths)
    │   ├── sessions/
    │   │   └── session-2026-03-08-001.yaml
    │   └── workflow_state.yaml
    ├── reference/                           (Local copies of brainstorm)
    │   ├── brain-dump/
    │   │   ├── story-brainstorm-dump.md
    │   │   └── compiled-keep-notes.txt
    │   ├── keep-notes/                      (65 Keep exports)
    │   └── dev-tasks/
    ├── chapters/                            (Chapter organization)
    │   └── chapter-01/
    │       └── meta.yaml
    ├── CLAUDE.md                            (Story project briefing)
    ├── showrunner.yaml                      (Showrunner project config)
    └── reference/README.md                  (This repo's guide)
```

---

## 🚀 Getting Started: Next Steps

### Step 1: Understand Your Setup
```bash
# You have two repos now:
ls -la ~/Documents/Showrunner/        # Tool repo
ls -la ~/Documents/QuantumDharma/     # Story repo

# Each has its own git history:
cd ~/Documents/Showrunner && git log --oneline | head -3
cd ~/Documents/QuantumDharma && git log --oneline | head -3
```

### Step 2: Begin Writing Session
```bash
# Go to story project
cd ~/Documents/QuantumDharma

# Read brainstorm for context
cat reference/brain-dump/story-brainstorm-dump.md | head -100

# Check next scene to write
cat story.yaml | grep -A5 "next_chapter"

# Write the next scene
vim fragment/ch1-sc2.yaml

# Commit your work
git add fragment/
git commit -m "feat: Write Chapter 1 Scene 2 - the college balcony"
```

### Step 3: Use Showrunner Tool Against Story
```bash
# Go to Showrunner (tool repo)
cd ~/Documents/Showrunner

# The tool automatically detects your story project
showrunner status

# Use tool commands, results save to QuantumDharma
showrunner character create "SecondaryChar" --role supporting

# Then go back and commit in QuantumDharma
cd ~/Documents/QuantumDharma
git add characters/secondarychar.yaml
git commit -m "feat: Create secondary character from brainstorm"
```

---

## 📌 Key Principles

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | Showrunner = tool, QuantumDharma = story |
| **Separate Git Histories** | Each repo tracks only its own domain |
| **Reference Materials** | Brainstorm notes in both (sync as needed) |
| **Canonical Story Data** | QuantumDharma is source of truth for YAML |
| **Tool Development** | Showrunner repo is source of truth for code |
| **Session Persistence** | .showrunner/ folder in QuantumDharma tracks sessions |
| **Creative Context** | reference/brain-dump/ available locally during writing |

---

## ✅ Verification Checklist

- [x] Showrunner repo contains brainstorm notes & documentation
- [x] Quantum Dharma repo contains complete story project
- [x] Each repo has independent git history
- [x] Both repos properly initialized and committed
- [x] Reference README updated in QuantumDharma
- [x] No merge conflicts or duplicate tracking
- [x] quantum-dharma/ removed from Showrunner working directory
- [x] Workflows documented for common tasks

---

## 🔗 Quick Links

| What | Where |
|------|-------|
| **Story brainstorm** | `~/Documents/QuantumDharma/reference/brain-dump/story-brainstorm-dump.md` |
| **Character profiles** | `~/Documents/QuantumDharma/characters/` |
| **Written scenes** | `~/Documents/QuantumDharma/fragment/` |
| **Story outline** | `~/Documents/QuantumDharma/story.yaml` |
| **Author decisions** | `~/Documents/QuantumDharma/.showrunner/decisions.yaml` |
| **Creative room secrets** | `~/Documents/QuantumDharma/.showrunner/creative_room.yaml` |
| **Tool source code** | `~/Documents/Showrunner/src/showrunner_tool/` |
| **Tool documentation** | `~/Documents/Showrunner/docs/` |
| **Development notes** | `~/Documents/Showrunner/agents/tasks/` |

---

## 📞 Need Help?

- **For story questions**: See `~/Documents/QuantumDharma/reference/brain-dump/story-brainstorm-dump.md`
- **For character info**: Check `~/Documents/QuantumDharma/characters/[name].yaml`
- **For tool usage**: See `~/Documents/Showrunner/docs/IDE_GUIDE.md`
- **For workflow issues**: Check `~/Documents/QuantumDharma/agents/tasks/friction-log-story-kickoff.md`

---

**Setup Date**: 2026-03-08
**Status**: ✅ Complete and ready for story development
**Next Action**: Continue writing Chapter 1 Scenes 2-5
