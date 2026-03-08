# Mission: Story Project Kickoff + Tool Optimization Loop

**Type**: Creative + Engineering (Dual Track)
**Priority**: Critical — This is the first real dogfooding session
**Context**: The author (Vikas) has exported 65 notes from Google Keep, organized into a master brainstorm dump. Now it's time to create an actual story project in Showrunner and start writing — while fixing every friction point encountered along the way.

**Key Reference Files**:
- `agents/tasks/story-brainstorm-dump.md` — Master story knowledge base (Section 0 has latest vision)
- `COMPILED_STORY_NOTES.txt` — Raw notes dump (65 notes)
- `CLAUDE.md` — Project development guide
- `docs/IDE_GUIDE.md` — How to use the two-step CLI mechanic
- `docs/QUICKSTART.md` — Zero to first scene flow
- `.agents/workflows/` — Formalized workflows (daily-session, write-scene, arc-planning, new-chapter)
- `.agents/skills/` or `agents/skills/` — 25 agent skill definitions

---

## IMPORTANT: How Showrunner Works (Two-Step Mechanic)

Showrunner CLI commands print **prompts** to stdout. You (Claude Code) read these prompts, then generate the YAML response following the schema. This is the core mechanic:

```
1. Run: showrunner <command>
2. Read the prompt output
3. Generate YAML following the prompt's schema
4. Save to the correct file path
```

Always read `docs/IDE_GUIDE.md` and `docs/QUICKSTART.md` first to understand this pattern.

---

## TRACK 1: Create the Story Project and Start Writing

### Phase 1: Initialize Project

```bash
source .venv/bin/activate

# Create the story project
showrunner init "Quantum Dharma" --template manhwa --structure save_the_cat --genre dark_fantasy
```

If the init command doesn't support all flags, use whatever it accepts and configure manually after.

After init:
1. Read `CLAUDE.md` for project state
2. Run `showrunner brief show` to see current status
3. Run `showrunner status` for health check

### Phase 2: World Building

Read `agents/tasks/story-brainstorm-dump.md` (especially Section 0: March 2026 Narrative Update) to understand the full story universe.

**The story has multiple nested reality layers:**

**Layer 0 — The Real World (deepest truth)**:
- Near-future Earth, post nuclear winter era
- AI chips embedded in humans, geopolitical tensions
- 3 college friends (A, B, F) building quantum simulation tech
- Professor H is their mentor
- A cricket stadium bombing (AI-orchestrated) kills everyone except A's mother
- The mother discovers and runs the quantum computer from her son's garage

**Layer 1 — World 1 (First Run / College World)**:
- Literature college setting
- Characters don't know they're in a simulation
- The Masked Man — victim of AI chip malfunction, not a true villain
- A discovers the Masked Man's truth, disguises himself as the Masked Man
- Infiltrates the main villain's gang
- Climax: College hijack at end of first run
- Tone: Indian college drama meets thriller, "Masala style"

**Layer 2 — World 2 (Tech Future)**:
- Advanced tech world with memory access, multiverse navigation
- Nuclear winter backdrop
- AI governance issues, geopolitical disasters
- Different physics rules from World 1

**Layer 3 — World 3 (The Creation / Meta World)**:
- A meta-universe for fictional consciousness
- Where the "powers" originate — agents manipulating quantum computer code
- Hindu mythology + quantum physics framework
- Maya = superposition, Observer Effect = consciousness, Brahman = quantum field

Build the world using:
```bash
showrunner world build
# Read the prompt, generate comprehensive world YAML covering all 4 layers
```

Then add locations, rules, and world-specific elements:
```bash
showrunner world add-location "The Stadium"
showrunner world add-location "A's Garage/Workshop"
showrunner world add-location "The Literature College"
showrunner world add-rule "AI Head Chips" --category technology
showrunner world add-rule "Quantum Code Manipulation" --category power_system
showrunner world add-rule "Simulation Layers" --category metaphysics
```

### Phase 3: Character Creation

Create the core cast from the brainstorm dump. For each character:
```bash
showrunner character create "<Name>" --role <role>
# Then read prompt and generate rich YAML backstory
showrunner character generate-dna "<Name>"
# Generate visual DNA block for consistent image generation
```

**Characters to create (in order of importance)**:

1. **A** (protagonist) — College student, quantum tech builder, becomes the Masked Man, eventually becomes an AI himself. The hero who was destroyed by AI and becomes AI to save everyone.

2. **B** (deuteragonist/rival) — A's best friend and challenger. Co-builder of the quantum tech. Present at the stadium.

3. **F** (love interest/partner) — The quantum mind. Third builder of the tech. Female lead. Present at the stadium.

4. **A's Mother** (hidden architect) — The most important character, deliberately kept minimal throughout the story. Sole survivor. Runs the quantum computer for years.

5. **The Masked Man** (tragic figure) — Victim of AI chip malfunction. His trauma was weaponized by corrupted AI. A disguises as him later. NOT a villain.

6. **Professor H** (mentor) — Their college professor/mentor. Present at stadium. Has a complex role across worlds.

7. **V** (antagonist) — Blind character. Antagonist with deep backstory.

8. **P** (A's father) — Security head at the stadium match. Dies in the bombing.

9. **C** (created character) — A character A created who becomes independent.

10. **The Main Villain** — Leader of the gang that hijacks the college. Identity to be developed.

### Phase 4: Story Architecture

```bash
# Create the overall story outline
showrunner story outline --structure save_the_cat

# Add arcs
showrunner story add-arc "First Run: College World" --type main --start-chapter 1 --end-chapter 13
showrunner story add-arc "The Masked Man's Truth" --type mystery --start-chapter 1 --end-chapter 6
showrunner story add-arc "A's Infiltration" --type thriller --start-chapter 7 --end-chapter 13
showrunner story add-arc "World 2: Tech Future" --type exploration --start-chapter 14 --end-chapter 26
showrunner story add-arc "The Mother's Secret" --type hidden --start-chapter 1 --end-chapter 40
showrunner story add-arc "The Survival Test" --type climax --start-chapter 35 --end-chapter 40
```

### Phase 5: Author Decisions (Persistent Preferences)

```bash
showrunner decide add "Manhwa/webtoon format, vertical scroll, 9:16 aspect" --category format
showrunner decide add "Indian Masala style — dramatic, comedic, emotional, with aura" --category tone
showrunner decide add "AI is not inherently evil — it reflects human trauma and intent" --category theme
showrunner decide add "Hindu mythology parallels quantum physics throughout" --category worldbuilding
showrunner decide add "Every character was present at the stadium — this is the unifying constraint" --category plot
showrunner decide add "The Mother is never prominently shown until the final reveal" --category narrative
showrunner decide add "Powers = quantum code manipulation, explained through both physics and mythology" --category power_system
showrunner decide add "Geopolitical scenarios are realistic extrapolations, not cartoonish" --category worldbuilding
showrunner decide add "Dark fantasy with comedic relief — never grimdark" --category tone
showrunner decide add "Third-person limited POV, shifting between characters per chapter" --category style
```

### Phase 6: Creative Room (Author-Only Secrets)

Set up the creative room with secrets the reader shouldn't know yet:
- The stadium bombing truth
- The Mother's role
- The simulation truth (all worlds are inside the quantum computer)
- The Masked Man's AI chip malfunction
- A's identity as the eventual orchestrator of humanity's future
- The survival test criteria

Use whatever creative_room commands are available, or manually create `.showrunner/creative-room.yaml`.

### Phase 7: Write the Opening

Start with Chapter 1, Scene 1 — the literature college. Use the write-scene workflow:

```bash
# Read the workflow
cat .agents/workflows/write-scene.md

# Execute
showrunner scene write --chapter 1 --scene 1
```

The opening scene from the brainstorm dump:
- Literature college setting
- A is in his own zone, saying: "Religion and God are good story tools for a writer that they use to basically portray themselves!"
- Lighting a bong, close but blurry shot
- Trippy music video in background
- Music fades as we move to the balcony where A hangs with friends
- Raid happens → bit of panic → A jumps down the balcony (surprisingly easily and neatly)
- Headmaster catches him at the last moment
- B (Head Boy) arrives to convince headmaster to exempt A

After writing:
```bash
showrunner cascade update fragment/ch1-sc1.yaml
showrunner git stage-story && showrunner git commit-message
```

### Phase 8: Session Management

```bash
# Start a proper session
showrunner session start "Project kickoff — world, characters, Chapter 1 Scene 1"

# ... do all the work above ...

# End session with summary
showrunner session end "Created project, built world across 4 layers, created 10 characters, outlined arc structure, wrote opening scene" --next "Write scenes 2-4 of Chapter 1, develop the Masked Man's introduction"

# Update the dynamic CLAUDE.md
showrunner brief update
```

---

## TRACK 2: Fix Every Friction Point Encountered

As you execute Track 1, you WILL hit friction. **Every time something breaks, is confusing, or could be better — fix it immediately.**

### Known Issues to Watch For and Fix:

**P0 — Fix If Encountered:**

1. **Entity detection 500 errors** — If @mentions or entity detection fails in the API, debug the endpoint in `src/showrunner_tool/server/routers/writing.py` or the entity detection service. Add proper error handling and debounce.

2. **NL Schema Wizard `[object Object]` errors** — If the schema wizard returns broken responses, fix the response parsing in the schema generation endpoint.

3. **Slash commands not wired** — If `/brainstorm`, `/research`, or `/continuity-check` don't work in Zen Mode, wire them. Check `src/web/src/app/zen/page.tsx` and the ZenEditor component for the slash command handler.

4. **Template doesn't create structure buckets** — If running a workflow template (like "Concept→Outline") generates text but doesn't create containers/buckets, fix the template execution to call the container creation API.

5. **Cascade update failures** — If `showrunner cascade update` errors or doesn't propagate changes, debug the cascade service.

**P1 — Improve If Noticed:**

6. **CLI command errors or missing flags** — If any showrunner command doesn't accept expected flags or errors out, fix the command handler in `src/showrunner_tool/commands/`.

7. **Context compilation gaps** — If generated content misses important context (e.g., world rules, character relationships), check the context compiler in `src/showrunner_tool/core/context_compiler.py`.

8. **Prompt template issues** — If prompts are poorly formatted or missing context, fix templates in `src/showrunner_tool/prompts/`.

9. **Session management bugs** — If session start/end doesn't persist properly, check `src/showrunner_tool/core/session_manager.py`.

10. **Git workflow issues** — If `stage-story` or `commit-message` fail, debug `src/showrunner_tool/commands/git_cmd.py`.

**P2 — Note for Later:**

11. **Missing workflows** — If you need a workflow that doesn't exist (e.g., `character-deep-dive`, `world-layer-build`), create it in `.agents/workflows/`.

12. **Missing agent skills** — If you need a skill that doesn't exist, create it in `agents/skills/` following the existing frontmatter format.

13. **UI improvements needed** — Note any UI/UX issues for the Zen editor, Storyboard, or Dashboard. Don't fix frontend during this session unless it's blocking writing.

### Friction Log

**IMPORTANT**: As you work through Track 1, maintain a friction log. After every significant step, append to `agents/tasks/friction-log-story-kickoff.md`:

```markdown
## [Timestamp] — [What you were trying to do]
**Command/Action**: `showrunner xyz`
**Expected**: [what should have happened]
**Actual**: [what actually happened]
**Fix Applied**: [what you changed, file paths]
**Status**: Fixed / Workaround / Deferred
```

This friction log is critical — it tells us exactly where the tool needs improvement for real writing workflows.

---

## TRACK 3: Optimization Recommendations

After completing Tracks 1 and 2, write a recommendations document to `agents/tasks/tool-optimization-recommendations.md` covering:

### IDE Workflow Optimizations
- Which commands should be combined into single workflows?
- Which two-step mechanic interactions were clunky?
- Where should context be auto-injected instead of requiring manual commands?
- Which agent skills need better prompts?
- What new workflows should be created for a story like this (multi-world, multi-layer)?

### UI Workflow Optimizations
- What should the Zen Mode sidebar show for a multi-world story?
- How should the Storyboard handle multiple worlds/layers?
- What Timeline view changes are needed for nested realities?
- How should the Knowledge Graph represent cross-world character connections?
- What new quick actions would help this specific story workflow?

### Story-Specific Tool Gaps
- Does the current container model support "nested worlds" well?
- Can the creative room properly hide multi-layer secrets?
- Does the reader knowledge state handle reality-reveal sequences?
- Can the continuity checker validate across different world layers?
- What custom schemas are needed for this story's unique elements?

---

## Completion Criteria

You are done when:
- [ ] Story project "Quantum Dharma" is initialized and functional
- [ ] World building covers all 4 reality layers
- [ ] 10 characters created with backstories
- [ ] Story arcs outlined (at least the First Run arc detailed)
- [ ] Author decisions logged (10+ persistent preferences)
- [ ] Creative room populated with author-only secrets
- [ ] Chapter 1 Scene 1 written (the college opening)
- [ ] Session properly started and ended with `showrunner session`
- [ ] Dynamic CLAUDE.md updated via `showrunner brief update`
- [ ] Git committed with story-specific commit message
- [ ] Friction log written with every issue encountered
- [ ] All P0 issues fixed during the session
- [ ] Optimization recommendations document written

## Output

Write final summary to `agents/tasks/story-kickoff-results.md` with:
- What was created (project structure, files)
- What was written (scenes, word count)
- What was fixed (friction items resolved)
- What needs follow-up (deferred items)
- Tool optimization recommendations
