# Claude Code as Director Agent — Showrunner IDE Guide

**For writers using Claude Code (the IDE integration) to develop stories in Showrunner.**

This guide explains how to use Claude Code to work directly with your story files, bypassing the web UI entirely. It's a completely zero-token workflow: Claude Code reads/writes YAML files, and the FileWatcher in the backend automatically syncs everything to the web UI.

---

## ⚡ CRITICAL: The Two-Step Mechanic

**This is the most important concept to understand.**

Showrunner CLI commands don't create files directly. They **print prompts** that Claude Code reads and acts on.

### How It Works

```
You → showrunner character create "Zara"
      ↓
CLI → Prints a formatted prompt with character schema + all needed context
      ↓
You (Claude Code) → Read that prompt carefully
      ↓
Claude Code → Generate the YAML content following the prompt's schema
      ↓
You → Write the YAML to characters/zara.yaml
```

### Why This Design?

- **Free**: Claude Code generates content (no API tokens)
- **Transparent**: You see exactly what context is being used
- **Flexible**: You can customize or reject the generated content
- **Reliable**: The prompt guides you to write valid YAML

### Every showrunner Command Follows This Pattern

```bash
showrunner scene write --chapter 1 --scene 1
# Prints: A prompt with scene schema, character context, previous scene, pacing guide, etc.
# You (Claude Code) read this prompt, understand what to write, generate the scene YAML
# You write it to: fragment/ch1-sc1.yaml

showrunner character create "Miko"
# Prints: A prompt with character template, world context, genre guidance, etc.
# You read it, generate character YAML, write to: characters/miko.yaml

showrunner research "Feudal Japanese armor"
# Prints: A prompt asking for research structure, sources, confidence scoring
# You read it, research and write result to: containers/research_topic/...
```

---

## 🗺️ Path Concordance Table

When you read the guide or skill files, you'll see references to story files. Here's where they actually live:

| When You See... | The File Actually Lives At | Use Case |
|---|---|---|
| "Save to `fragment/`" | `fragment/ch4-sc3.yaml` | Scene prose (what you write) |
| "Save to `containers/`" | `containers/<type>/<name>.yaml` | Research, notes, custom data |
| "Save to `idea_card/`" | `idea_card/<idea>.yaml` | Brainstorm ideas, plot twists |
| "A character" | `characters/<name>.yaml` | Character profiles (or `containers/character/`) |
| "A location" | `world/locations/<name>.yaml` | World locations |
| "A scene" | `fragment/<id>.yaml` OR `chapters/s1/chapter-01/scenes/` | Story prose |
| "A panel" | `chapters/s1/chapter-01/panels/<id>.yaml` | Storyboard panels |
| "A screenplay" | `chapters/s1/chapter-01/screenplay/<id>.yaml` | Scene breakdowns |
| "A decision" | `.showrunner/decisions.yaml` | Persistent author preferences |
| "Brain dump inbox" | `.showrunner/inbox.yaml` | Captured ideas (before processing) |
| "Research" | `containers/research_topic/<topic>.yaml` | Fact-checked information |

---

## Quick Start

### 1. Load Your Project Context

At the start of each writing session, ask Claude Code:

```
Read CLAUDE.md for project state, then show me the current brief.
```

Claude will read your `CLAUDE.md` file (which has a dynamic section updated by the backend) and give you:
- Current chapter and scene position
- Character names and file paths
- Recent plot events
- Active decisions
- Remaining token budget

### 2. Navigate to Your Story Files

The YAML files are the **source of truth**. Everything lives here:

```
characters/              # Character profiles (name.yaml)
world/                   # World, locations, factions
containers/              # Research, ideas, notes
fragment/                # Story scenes (what you write)
idea_card/               # Brainstorm ideas
pipeline_def/            # Multi-step workflows
```

Example:
```
"Read characters/zara.yaml to understand Zara's current state"
"Show me fragment/ch3-sc2.yaml (the previous scene)"
"What research is available? (list containers/)"
```

### 3. Write Your Story

Claude Code can write directly to fragment files:

```
"Read the research from containers/samurai-armor.yaml and the character context
from characters/zara.yaml. Now write the prose for fragment/ch4-sc3.yaml where
Zara discovers the artifact. Save to the file when done."
```

The FileWatcher detects the change → syncs to knowledge graph → broadcasts to web UI via SSE. **The web UI auto-updates in real-time.**

---

## How Context Works

### Loading Project State

**Command 1: Brief Context**
```
showrunner brief show
```
Outputs a markdown summary of:
- Project name, current chapter/scene
- Character roster with descriptions
- World summary
- Recent session notes
- Git status
- Token usage

**Command 2: Load Specific Files**

Ask Claude Code:
```
"Read characters/*.yaml to show me all characters"
"Read containers/ to show research topics"
"Read fragment/ch3-sc1.yaml"
```

Claude Code reads the YAML directly. No API calls. All local.

**Command 3: Check CLAUDE.md**

```
"Read CLAUDE.md and extract the DYNAMIC section"
```

This file has:
- Current project state (regenerated by `showrunner brief update`)
- Character names + file paths (for quick navigation)
- Last 3 session summaries
- Active decisions/preferences
- Git status

### Understanding the YAML Schema

All story entities use the same **GenericContainer** format:

```yaml
id: "01ARZ3NDEKTSV4RRFFQ69G5FAV"  # ULID (unique identifier)
name: "Zara"
container_type: "character"  # Type: character, location, scene, fragment, research_topic, etc.
schema_version: 1
created_at: 2026-03-07T...
updated_at: 2026-03-07T...
attributes:  # Flexible key-value store (varies by type)
  role: "protagonist"
  age: 28
  location: "The Fortress"
  emotional_state: "Determined"
  relationships:
    miko: "rival"
    sensei: "mentor"
```

**For characters:** `attributes` contains role, age, location, emotional_state, relationships, skills, secrets, etc.

**For scenes/fragments:** `attributes` contains prose, word_count, characters_present, plot_events, etc.

**For research:** `attributes` contains research_text, sources, confidence_score, key_facts.

### Entity IDs

Every entity has a unique ULID. When you @-mention an entity in chat, or need to reference it in code, use the `id` field from the YAML:

```yaml
# characters/zara.yaml
id: "zara-001"  # or full ULID
```

---

## Using Agent Skills

Claude Code can act as any of the 10 Showrunner agents by reading their skill files. The skill files are your **system prompts** for Claude Code to interpret and execute.

### Available Agents

Located in `agents/skills/`:

1. **research_agent.md** — Investigates topics, finds sources, fact-checks
2. **story_architect.md** — Designs story structure, outlines chapters, plans arcs
3. **brainstorm_agent.md** — Generates creative ideas, plot twists, character dynamics
4. **writing_agent.md** — Drafts prose, maintains voice consistency
5. **continuity_analyst.md** — Checks for plot holes, timeline conflicts, character consistency
6. **style_enforcer.md** — Maintains tone, pacing, formatting conventions
7. **translator_agent.md** — Adapts writing for different genres/audiences
8. **prompt_composer.md** — Writes image generation prompts for panels
9. **schema_architect.md** — Designs container schemas for custom entities
10. **graph_arranger.md** — Manages knowledge graph relationships

### How to Use Them

**Pattern 1: Direct Skill Reference**

```
"Read agents/skills/research_agent.md.
Now act as the Research Agent and research the history of samurai armor.
Save the result to containers/samurai-armor-research.yaml with container_type: research_topic."
```

Claude Code reads the skill file, understands the agent's role and approach, and executes it.

**Pattern 2: Skill-Guided Task**

```
"You are the Story Architect (see agents/skills/story_architect.md).
The current plot is: [description].
Generate a 3-act outline for the next chapter.
Use markdown format and save to containers/chapter-4-outline.yaml."
```

**Pattern 3: Cascade of Agents**

```
"1. Read agents/skills/research_agent.md and research [topic], save to containers/.
2. Read agents/skills/story_architect.md and create a scene outline using that research.
3. Read characters/zara.yaml and make sure the outline fits her character.
4. Write the scene prose to fragment/ch4-sc3.yaml respecting all constraints."
```

Each agent skill file contains:
- **Role description** — what the agent does
- **Approach** — how they think and work
- **Input/Output** — what they expect and produce
- **Constraints** — guardrails (genre, tone, length, etc.)

---

## Writing a Scene (Complete Workflow)

Here's a full example of how to write a scene using Claude Code:

### Step 1: Load Context

```
"I'm about to write Scene 3 of Chapter 4.
1. Read CLAUDE.md for current project state.
2. Read characters/zara.yaml (protagonist).
3. Read characters/miko.yaml (antagonist).
4. Read fragment/ch4-sc2.yaml (the previous scene).
5. Check containers/ for any research relevant to feudal Japan.
Summarize the context so I can write the next scene."
```

### Step 2: Research (Optional)

If you need new information:

```
"Read agents/skills/research_agent.md.
Now research the layout of a traditional Japanese fortress.
Save the result to containers/japanese-fortress-research.yaml with container_type: research_topic."
```

### Step 3: Brainstorm (Optional)

If you need ideas:

```
"Read agents/skills/brainstorm_agent.md.
Zara and Miko are about to have a tense conversation where Zara reveals a secret.
Generate 5 different ways this scene could play out dramatically.
Save to containers/ch4-sc3-brainstorm.yaml."
```

### Step 4: Write the Scene

```
"You have all the context. Now read agents/skills/writing_agent.md.

Write a scene (800-1200 words) where:
- Zara discovers the hidden artifact in the fortress
- Miko is present, creating tension
- The discovery changes Zara's understanding of the plot
- Maintain the dark, introspective tone established in previous scenes
- Include sensory details and dialogue

Save the scene to fragment/ch4-sc3.yaml with container_type: fragment, and include:
- prose: [the text you wrote]
- word_count: [actual count]
- characters_present: [zara, miko]
- plot_events: [what happens]
- emotional_tone: [the mood]"
```

### Step 5: Verify Continuity

```
"Read agents/skills/continuity_analyst.md.
Now check if the scene at fragment/ch4-sc3.yaml is consistent with:
- Zara's character (characters/zara.yaml)
- Miko's character (characters/miko.yaml)
- The timeline (when did previous events happen?)
- Plot logic (does this event make sense?)

Report any issues found and suggest fixes."
```

### Step 6: Update Related Entities (Optional)

After writing, you may need to update character states:

```
"Based on the scene in fragment/ch4-sc3.yaml:
1. Zara discovered the artifact and her emotional state changed.
2. Update characters/zara.yaml to reflect her new emotional_state: 'Conflicted'.
3. Update her 'location' to 'The Artifact Chamber'.
4. Don't change anything else."
```

### Step 7: Commit to Git

```
showrunner git stage-story
showrunner git commit-message
```

Or manually:
```
git add characters/ fragment/ && git commit -m "Chapter 4 Scene 3: Zara discovers the artifact"
```

---

## Cascade Updates (Keeping Entities in Sync)

**Problem:** When you write a scene where a character develops, their YAML file doesn't automatically update. They become out of sync.

**Solution:** Use the Cascade Update Service to detect entity changes and update related files.

### Manual Cascade Update

After writing a scene:

```
showrunner cascade update fragment/ch4-sc3.yaml
```

This will:
1. Analyze the scene file
2. Detect which characters were affected
3. Update `characters/[name].yaml` with new states (emotional state, location, relationships, etc.)
4. Update `world/[location].yaml` if the scene took place somewhere new
5. Show you what was changed

Output example:
```
✓ Updated characters/zara.yaml:
  - emotional_state: "Conflicted" (was "Determined")
  - location: "The Artifact Chamber" (was "The Fortress")

✓ Updated world/the-fortress.yaml:
  - new_discovery: "Ancient artifact in chamber C3"

✓ No changes needed: characters/miko.yaml (not present in scene)
```

### Auto-Cascade (Optional)

You can enable auto-cascade updates in the FileWatcher so that whenever a fragment changes, related entities update automatically. This requires LLM tokens, so it's disabled by default.

To enable:
```bash
showrunner config set cascade_updates auto
```

To disable:
```bash
showrunner config set cascade_updates manual
```

---

## Git Workflow

### For Story Files Only

All story work goes through git. But don't commit database files or cache:

```bash
# Stage only story files
showrunner git stage-story
# Equivalent to: git add characters/ world/ containers/ fragment/ idea_card/ pipeline_def/

# Generate AI-powered commit message
showrunner git commit-message
# Shows preview, then commits if you confirm

# View story history
showrunner git history
# Shows: git log --oneline -- characters/ world/ containers/ fragment/
```

### Branching Strategy

**Per-arc branches:** Create a branch for each story arc or major decision:

```bash
git checkout -b arc-2-the-descent
# Write scenes exploring this arc...
# If you like it: git merge back to main
# If you don't: git checkout main (branches are preserved in .git)
```

**Per-session branches (optional):** If experimenting:

```bash
git checkout -b session-2026-03-07-brainstorm
# Explore wildly...
# Cherry-pick what you like back to main
```

### Viewing Changes

```bash
# What's changed since last commit?
git diff -- characters/ world/ containers/ fragment/

# What's staged?
git diff --staged -- characters/ world/ containers/ fragment/

# Full history of a character
git log --oneline -- characters/zara.yaml

# See what changed in a specific commit
git show <commit-hash>
```

---

## Key Commands Reference

### Brief & Context

```bash
showrunner brief show           # Full project summary
showrunner brief context        # Current working state
showrunner brief update         # Regenerate CLAUDE.md dynamic section
showrunner brief context --format json  # Machine-readable format (for Claude Code parsing)
```

### Session Management

```bash
showrunner session start "Working on Chapter 4"     # Log the session start
showrunner session end "Wrote scenes 1-3, revised pacing"  # Log session summary
showrunner session history      # See past session notes
```

### Decisions (Persistent Preferences)

```bash
showrunner decide add "Always use third-person POV" --category style
showrunner decide list           # See all decisions
showrunner decide remove <id>    # Remove a decision
```

Decisions are scoped: global, chapter, scene, or character. They persist across sessions.

### Cascade Updates

```bash
showrunner cascade update fragment/ch4-sc3.yaml  # Auto-update related entities
```

### Git

```bash
showrunner git stage-story       # Stage all story files
showrunner git commit-message    # AI-generated message (preview + confirm)
showrunner git history           # Story commit log
```

### Status & Info

```bash
showrunner status                # Current project state
showrunner info                  # Project details
```

---

## Switching Between Web UI and Claude Code

**The beauty of this system:** Both workflows use the same YAML files. They're completely interoperable.

| Action | Web UI | Claude Code |
|--------|--------|-------------|
| **Read character** | Click in Characters panel | `read characters/zara.yaml` |
| **Write scene** | Open Zen Editor, type | `read context, write fragment/ch4-sc3.yaml` |
| **Research topic** | Chat: "research X" | `act as research_agent, research X, save containers/` |
| **Brainstorm ideas** | Chat: "brainstorm X" | `act as brainstorm_agent, brainstorm X` |
| **Check consistency** | Chat: "evaluate X" | `act as continuity_analyst, check fragment/ch4-sc3.yaml` |
| **Update character** | Click edit, modify, save | `edit characters/zara.yaml` |
| **Version control** | Git Panel button | `git add ... && git commit ...` |

### Real-Time Sync

When you write a scene using Claude Code:
1. Claude Code writes to `fragment/ch4-sc3.yaml`
2. FileWatcher detects the change (instant)
3. Knowledge Graph updates (instant)
4. Web UI receives SSE broadcast (instant)
5. Scene appears in Web UI panels without refresh

**Zero manual sync needed.** Everything flows through the FileWatcher.

---

## Example Sessions

### Session: Write Chapter 4, Scenes 1-3

```
# Start of session
read CLAUDE.md
showrunner brief show

# Load context
read characters/*.yaml
read fragment/ch3-sc2.yaml  (previous scene)
check containers/ for research on "fortress architecture"

# Write Scene 1
[Use research + character context to write scene]
write to fragment/ch4-sc1.yaml

# Update cascade
showrunner cascade update fragment/ch4-sc1.yaml

# Continue with Scenes 2-3 similarly...

# End of session
showrunner session end "Wrote Chapter 4 Scenes 1-3. Zara and Miko's tension escalating."
showrunner git stage-story
showrunner git commit-message
```

### Session: Research & Brainstorm (No Writing Yet)

```
# Load project
read CLAUDE.md

# Research phase
act as research_agent (agents/skills/research_agent.md)
research "ancient Japanese alchemy practices"
save to containers/alchemy-research.yaml

act as research_agent
research "feudal fortress defense mechanisms"
save to containers/fortress-research.yaml

# Brainstorm phase
act as brainstorm_agent (agents/skills/brainstorm_agent.md)
read characters/zara.yaml and characters/miko.yaml
generate 5 ways their relationship could develop
save to containers/zara-miko-brainstorm.yaml

# End session
showrunner session end "Researched alchemy and fortress design. Generated 5 brainstorm ideas."
```

### Session: Continuity Check & Revise

```
# Load project
read CLAUDE.md

# Check a scene
act as continuity_analyst (agents/skills/continuity_analyst.md)
read fragment/ch3-sc5.yaml
check for:
  - character consistency vs characters/zara.yaml, characters/miko.yaml
  - timeline conflicts with previous scenes
  - plot logic
  - tone consistency with style_enforcer.md

# If issues found:
read characters/zara.yaml
re-write fragment/ch3-sc5.yaml fixing the issues

# Verify fix
showrunner cascade update fragment/ch3-sc5.yaml

# Commit
showrunner git stage-story && showrunner git commit-message
```

---

## Token Economy (Zero Cost for IDE Work)

### Free Operations (No Tokens)
- Reading YAML files with Claude Code
- Using `showrunner` CLI commands (`brief`, `status`, `cascade update` is optional)
- Writing YAML files with Claude Code
- Git operations
- FileWatcher sync
- Web UI rendering

### Paid Operations (Minimal Tokens)
- `showrunner cascade update` — ~500 tokens per scene (optional, can be manual)
- `showrunner git commit-message` — ~200 tokens (generates commit message)
- Agent skills when called manually (research, brainstorm, etc.) — varies

**Pro tip:** Do most work in Claude Code (free). Only use agent skills when you need creative input or verification.

---

## Troubleshooting

### "File changes aren't appearing in the web UI"

**Cause:** FileWatcher might not be running or detected the change.

**Fix:**
```bash
# Restart the backend
bash start_studio.sh

# Or manually trigger sync
showrunner brief update
```

### "Character updates aren't showing in the scene"

**Cause:** Cascade updates are manual by default.

**Fix:**
```bash
showrunner cascade update fragment/ch4-sc3.yaml
```

### "Git history is cluttered with system files"

**Cause:** You committed `.showrunner/`, `knowledge_graph.db`, etc.

**Fix:**
```bash
# Always use
showrunner git stage-story

# Never use
git add .
```

### "Claude Code can't find a file"

**Cause:** Incorrect file path.

**Fix:**
```
# Claude Code should use absolute paths from project root:
read /Users/vikasahlawat/Documents/Showrunner/characters/zara.yaml
# Or relative from project root:
read characters/zara.yaml
```

---

## Philosophy: The IDE Becomes Your Director

Think of Claude Code + this workflow as **your Director Agent**:
- It reads your YAML files (like a director reading a script)
- It understands character arcs, plot structure, tone
- It writes scenes, brainstorms ideas, researches topics
- It keeps track of what's changing (cascade updates)
- It commits to git (version control)

The web UI is your **preview screen**:
- You can see all your work live
- Chat sidebar for quick advice
- Visual panels for graphical writing (storyboard, timeline, panels)
- But the real work happens in the YAML files

Both are the same story. Both are always in sync. Switch between them whenever you want.

---

## Next Steps

1. **Start a session:** `showrunner session start "Writing Chapter 4"`
2. **Load context:** `read CLAUDE.md` and `showrunner brief show`
3. **Read character files:** `read characters/*.yaml`
4. **Write your first scene:** Follow the "Complete Workflow" example above
5. **Cascade update:** `showrunner cascade update fragment/ch4-sc3.yaml`
6. **Commit:** `showrunner git stage-story && showrunner git commit-message`

Happy writing! 🎬
