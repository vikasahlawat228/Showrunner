# Showrunner Quick Start: Zero to First Scene in 10 Minutes

Welcome! This guide takes you from nothing to your first written story scene in under 10 minutes. No experience required.

## The One Thing You Must Understand: The Two-Step Mechanic

**Showrunner CLI commands don't create files directly. They print prompts.**

Here's what happens:

```
You → showrunner character create "Zara"
      ↓
CLI → Prints a formatted prompt with character schema + context
      ↓
You (Claude Code) → Reads the prompt, understands what to write
      ↓
Claude Code → Generates the character YAML directly
      ↓
You → The YAML appears in characters/zara.yaml
```

**This is intentional:** Claude Code generates the content (free). The CLI provides structure and context.

---

## 10-Step Quick Start

### Step 1: Install the Tool (2 minutes)

```bash
# Navigate to the project directory
cd /path/to/Showrunner

# Create Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install as development package
pip install -e .

# Verify installation
showrunner --help
```

### Step 2: Create Your Project (1 minute)

```bash
# Create a new story project
showrunner init "My First Manga" --template manhwa --structure save_the_cat

# Navigate into it
cd my-first-manga

# Check what was created
ls -la
# You should see: fragment/, containers/, idea_card/, characters/, world/, chapters/, CLAUDE.md, etc.
```

### Step 3: Open Claude Code (1 minute)

Open Claude Code (this tool you're using now):

```
# In Claude Code, tell me:
"I just created a Showrunner project. Read CLAUDE.md to understand the state and next steps."
```

I'll read your CLAUDE.md and understand the project structure, the two-step mechanic, and your current state.

### Step 4: Check Project State (1 minute)

```bash
# In your terminal (not in Claude Code):
showrunner brief show
```

This shows:
- Current step (World Building)
- How many characters (0)
- How many story beats (0/0 filled)
- What to do next

Output will look like:
```
Project: My First Manga
Status: New Project
Current Step: World Building
  ✗ World settings
  ✗ Characters
  ✗ Story structure
Next: Build the world with: showrunner world build
```

### Step 5: Build Your World (2 minutes)

In Claude Code:

```
"Run: showrunner world build
Then read the prompt output and generate the world settings YAML for a dark fantasy manga.
Include: genre, tone, time period, magic system, and one key location.
Save the result to world/settings.yaml"
```

I'll run the command, read the prompt, and generate your world settings.

### Step 6: Create Your First Character (2 minutes)

In Claude Code:

```
"Run: showrunner character create "Zara" --role protagonist
Read the character schema prompt and generate a detailed character profile.
Zara is the main character: a young swordswoman with a mysterious past.
Save to characters/zara.yaml"
```

I'll create Zara's complete profile including:
- Personality, backstory, relationships
- DNA block (for visual consistency in images)
- Character arc framework

### Step 7: Brain Dump an Idea (1 minute)

```bash
# In your terminal:
showrunner capture "Zara discovers her sword has a hidden inscription"
showrunner capture "What if her mentor is actually the villain?"
showrunner inbox show
```

These ideas go to `.showrunner/inbox.yaml` and show up as unprocessed captures.

In Claude Code:

```
"Show me all unprocessed ideas in .showrunner/inbox.yaml
Convert interesting ones to idea_card/*.yaml files for later development."
```

### Step 8: Outline Your Story (2 minutes)

In Claude Code:

```
"Run: showrunner story outline --structure save_the_cat
Read the outline prompt and generate a basic story structure for my manga.
Follow the Save the Cat framework: Hook → Catalyst → B Story → Midpoint → Final Battle → Resolution.
Make it about Zara discovering the truth about her sword and her mentor.
Save to story/structure.yaml"
```

### Step 9: Write Your First Scene (3 minutes)

In Claude Code:

```
"Run: showrunner scene write --chapter 1 --scene 1
Read the scene writing prompt carefully.
Write the opening scene of my manga: Zara enters the Forge District for the first time.
POV: Zara. Mood: tense, awe-struck. Length: ~800 words.
Save the prose to fragment/ch1-sc1.yaml"
```

### Step 10: Commit Your Work (1 minute)

```bash
# In your terminal:
showrunner git stage-story
showrunner git commit-message
# Git will commit your story files

# Check what was committed:
git log --oneline -- fragment/ characters/
```

---

## What You Just Did

✅ Created a structured story project
✅ Built a cohesive world
✅ Created your main character
✅ Brain-dumped ideas for later
✅ Outlined your story arc
✅ Wrote your opening scene
✅ Committed everything to version control

**All of this using Claude Code as your Director Agent.**

---

## Key Files You Interact With

| File/Directory | What It Is | How to Use |
|---|---|---|
| `CLAUDE.md` | Project briefing + state | Read at start of session for context |
| `fragment/` | Your story scenes | Read before writing, write new scenes here |
| `characters/` | Character profiles | Read before writing, update after scenes |
| `world/` | World settings + locations | Read for world context, reference in scenes |
| `containers/` | Research + notes | Create via `showrunner capture`, reference when writing |
| `idea_card/` | Brainstorm ideas | Create via capture, develop into scenes |
| `.showrunner/inbox.yaml` | Brain dump capture list | Process regularly to convert ideas to containers |

---

## The Pattern You'll Repeat

Each writing session follows this pattern:

```
1. Read CLAUDE.md for current state
2. Read context YAMLs (characters, world, previous scenes)
3. Run a showrunner command to get a prompt
4. Ask me (Claude Code) to:
   - Read the prompt
   - Generate YAML following the schema
   - Write to the correct file path
5. Run: showrunner cascade update <file>
   (auto-syncs character states if needed)
6. Run: showrunner git stage-story && showrunner git commit-message
   (commit your work)
7. End session: showrunner session end "summary" --next "next steps"
```

**Repeat this for every scene, and your manga grows.**

---

## Where to Go Next

### To Understand Everything

Read: **[docs/IDE_GUIDE.md](IDE_GUIDE.md)**
- Full reference for how Claude Code workflows work
- All CLI commands explained
- Detailed examples
- Agent skills reference

### To See Your Story Visually

```bash
# Start the web UI
showrunner server start --reload    # Backend (port 8000)

# In another terminal:
cd src/web
npm run dev                         # Frontend (port 3000)
```

Then visit `http://localhost:3000` to see your story in the dashboard.

### To Ask for Help

Inside Claude Code, just ask me! Examples:

- "Help me outline Chapter 2"
- "What's the best way to write a fight scene?"
- "Check the continuity of this scene"
- "What research do I need for X?"

---

## Troubleshooting

### "File not found" Error

Make sure you're using the right paths:
- **Scenes**: `fragment/ch1-sc1.yaml` ✅ (NOT `chapters/chapter-01/scenes/...`)
- **Characters**: `characters/zara.yaml` ✅
- **Research**: `containers/research_topic/something.yaml` ✅
- **Ideas**: `idea_card/something.yaml` ✅

(See [Path Concordance Table](IDE_GUIDE.md#paths-and-directories-concordance-table) for full reference)

### "CLAUDE.md is empty"

After `showrunner init`, the DYNAMIC section fills after you make edits. It will populate more once you run:
```bash
showrunner brief update
```

### "I wrote something but I don't see it in the web UI"

Give the FileWatcher 2 seconds to sync, then refresh the browser. If still not there:
```bash
showrunner index rebuild
```

This rebuilds the knowledge graph from your YAML files.

---

## You're Ready!

You have everything you need to write a complete manga story:

- ✅ Claude Code (this tool) as your Director Agent
- ✅ Local YAML files as your source of truth (git-friendly)
- ✅ The two-step mechanic (CLI → prompt → you → YAML)
- ✅ Agent skills for research, writing, brainstorming, evaluation
- ✅ Web UI to see your story visually as you build it
- ✅ Git version control for all your work

**Start writing. Ask me for help. Enjoy the process.**

Next: [Read the Full IDE Guide →](IDE_GUIDE.md)
