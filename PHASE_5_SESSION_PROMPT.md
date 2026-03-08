# PHASE 5 External Session Prompt: Resume Writing

**Duration:** 2-3 hours
**Difficulty:** High (creative + technical)
**Prerequisite:** Phases 1-4 complete (all infrastructure ready)
**Goal:** Resume writing scenes with proper infrastructure in place

---

## Context

Phases 1-4 have built the scaffolding. Now it's time to write new scenes using all that infrastructure.

**Currently Written:**
- `fragment/ch1-sc1.yaml` — "The Philosophy of God in Smoke" (~4000 words)

**To Write (Phase 5):**
- `fragment/ch1-sc2.yaml` through `ch1-sc5.yaml` — Chapter 1 completion (~15,000 words total)

**Key Differences from ch1-sc1:**
- Uses creative room (spoilers excluded)
- Character relationships properly injected
- World layer 1 style guide (warm, comedic, coming-of-age)
- Proper scene structure: setup → conflict → revelation
- Reader knowledge tracking

---

## Step 1: Understand Chapter 1 Structure

From `story.yaml`, Chapter 1 covers:

| Scene | Beat | Focus | Tone |
|-------|------|-------|------|
| ch1-sc1 | Opening Image | A's mundane life + existential dream | Warm, philosophical |
| ch1-sc2 | Inciting Incident | Stadium election begins | Excitement, pressure |
| ch1-sc3 | — | A's first quantum code discovery | Wonder, discovery |
| ch1-sc4 | — | Mother's suspicious behavior hinted | Warmth with doubt |
| ch1-sc5 | Break into Act 1 | B invites A to something secretive | Trust building, mystery |

### Key World Layer Elements
- **Setting**: Dharma Academy (hilltop campus north of Mumbai)
- **Time**: Modern day, monsoon season
- **Characters**: A (protagonist), B (peer/mentor), Mother (loving but suspicious), Professor H (wise guide)
- **Tone**: Warm Academy vibes, philosophical depth, comedic relief

---

## Step 2: Prepare Scene Template

Create `fragment/ch1-sc2-TEMPLATE.yaml` to understand the structure:

```yaml
id: "ch1-sc2"
chapter: 1
scene_number: 2
title: "The Elections Begin"
word_count: 3000

# Context from Phase 1-4 work:
world_layer: 1
setting: "Dharma Academy - Main Assembly Hall"
pov_character: "a"
characters_present: ["a", "b", "professor_h", "mother"]

# Reader knowledge at this point:
reader_knows:
  - "A is a philosophy-loving Academy student"
  - "A has vivid existential dreams"
  - "Quantum code abilities exist and are trained"
  - "Something feels off about reality"

reader_does_not_know:
  - "That simulation layers exist"
  - "That Mother is orchestrating events"
  - "That this election is a selection mechanism"
  - "That quantum code is consciousness interface"

# Relationships to reflect:
# - A ↔ B: Neutral peers, building awareness
# - A ↔ Mother: Deep love, growing subtle doubt
# - A ↔ Professor H: Respectful student, sensing hidden depths

# Foreshadowing to plant:
# - Mother's timeline oddities (she knew about election before announcement)
# - B's careful observation of A
# - Professor H dropping hints about "special students"

# Style guide compliance:
narrative_tone: "warm Academy, exciting pressure, philosophical undertone"
visual_palette: ["warm golds", "school greens", "sunlit assembly hall", "excited student energy"]
prose_style: "Warm, dialogue-driven, quick-paced with philosophical asides"

# Scene beats:
beats:
  - "A enters assembly, notices unusual energy"
  - "Principal announces stadium election for 50 students"
  - "A's heart races with excitement and fear"
  - "Mother's foreknowledge revealed through careful observation"
  - "B whispers something cryptic about the election"
  - "Scene ends with A resolved to compete"

plot_function: "Introduces external pressure, activates A's agency"
character_arc_impact: "A chooses to participate, first active choice"

# Creative room context (excluded from prompt):
# This scene plants seeds for plot_twist: mother-architect
# Foreshadowing: Mother knows too much
# Reader learns: Selection is not random
```

---

## Step 3: Write Scene ch1-sc2

Now write the actual scene prose.

**Approach:**
1. Read ch1-sc1 to understand the writing style and voice
2. Use the template above as structural guide
3. Follow the world layer 1 style guide: warm, comedic, philosophical
4. Plant foreshadowing (but don't reveal)
5. Deepen character relationships

**Scene Structure:**

```
Opening (500 words):
- Establish setting: Assembly hall, afternoon light, Academy vibes
- A's sensory experience entering
- Energy in the room (students talking, speculation)

Incident (1000 words):
- Principal's announcement of stadium election
- A's reaction: excitement, fear, ambition
- Mother's presence and reaction (she seems to know)
- B's mysterious behavior

Development (1000 words):
- Conversations with peers about the election
- Mother pulls A aside (warm but tinged with knowledge?)
- B gives A cryptic advice
- A's internal monologue about dharma vs ambition

Climax (300 words):
- A decides to compete
- Mother supports (but with strange knowing)
- B smiles, satisfied

Resolution (200 words):
- A exits assembly feeling chosen, uncertain why

Total: ~3000 words
```

**Key Writing Notes:**

- **Tone**: Match ch1-sc1's philosophical warmth
- **Dialogue**: Use Hindi/English code-mixing where natural
- **Foreshadowing**: Plant Mother's knowledge subtly (she "happened to know" the election date, she's "always been interested in selection")
- **Relationships**: Show A's trust in B growing, A's love for Mother complicated by doubt
- **Style Guide**: Use senses from style_guide (chai smell if in cafe, monsoon humidity, temple bells in distance)

**Example Opening:**

```
The assembly hall is built like a cathedral, all high arched ceilings and old
wood that creaks with history. It's monsoon season—the open windows let in
the smell of wet earth and the distant sound of traffic from Mumbai below.
A thousand kilometers away and the city still intrudes.

A slides into a seat next to B, who's been at the Academy a year longer and
somehow always knows where the interesting parts of gatherings will be.

"You can feel it, right?" B whispers. "Something's different today."

A can. There's an electricity in the air that's not about the weather.
```

---

## Step 4: Write Scenes ch1-sc3 through ch1-sc5

Repeat Step 3 for remaining scenes:

**ch1-sc3: "First Light"** (2500 words)
- A discovers their first quantum code ability
- Happens during training session with mentor
- Wonder and discovery tone
- Foreshadowing: Ability is limited, controlled

**ch1-sc4: "The Question"** (2000 words)
- A returns home, Mother is there with unusual presence
- Subtle hints that Mother knows more than she should
- A feels loved but also observed
- Sets up Mother's dual nature

**ch1-sc5: "The Secret"** (3000 words)
- B pulls A aside with a proposition
- B hints at deeper knowledge
- Proposal to help A prepare for election
- Scene ends with alliance formed, mystery deepened

**Combined Word Count:** 3000 + 2500 + 2000 + 3000 = 10,500 words (+ ch1-sc1's 4000 = 14,500 total for Chapter 1)

---

## Step 5: Create Scene YAML Files

For each scene, create a YAML file with:

```yaml
id: "ch1-sc{n}"
chapter: 1
scene_number: {n}
title: "{Scene Title}"
word_count: {actual}
prose: |
  {Full scene text, 2000-3000 words}

metadata:
  world_layer: 1
  setting: "Dharma Academy"
  pov_character: "a"
  characters_present: [...]
  tone: "warm, comedic, philosophical"

reader_knowledge:
  learns:
    - "Key truth revealed in this scene"
  still_unaware:
    - "Things they don't know yet"

relationships_reflected:
  - "a-b: Building trust"
  - "a-mother: Love with growing doubt"

foreshadowing_planted:
  - "element": "description"

continuity_checks:
  - "A's feelings consistent with ch1-sc1"
  - "Mother's behavior hinted at but not revealed"
  - "B's knowledge level appropriate"

git_notes: "Scene ch1-sc{n}: {Scene purpose in story arc}"
```

---

## Step 6: Validate Scenes

### Continuity Check

```bash
# Ensure characters are consistent across scenes
python3 << 'EOF'
import yaml

# Load all chapter 1 scenes
scenes = []
for i in range(1, 6):
    try:
        with open(f'fragment/ch1-sc{i}.yaml') as f:
            scenes.append(yaml.safe_load(f))
    except FileNotFoundError:
        print(f"⚠️  ch1-sc{i}.yaml not found")

# Check continuity
for i, scene in enumerate(scenes[:-1]):
    current = scene['metadata'].get('end_state', {})
    next_scene = scenes[i+1]['metadata'].get('start_state', {})
    if current and next_scene:
        # Validate that end state of scene N matches start of scene N+1
        pass

print(f"✅ Loaded {len(scenes)} scenes")
EOF
```

### Reader Knowledge Consistency

```bash
# Verify reader knowledge progression
python3 << 'EOF'
import yaml

previous_knowledge = set()
for i in range(1, 6):
    with open(f'fragment/ch1-sc{i}.yaml') as f:
        scene = yaml.safe_load(f)

    learns = set(scene['reader_knowledge']['learns'])
    unaware = set(scene['reader_knowledge']['still_unaware'])

    # Check: Nothing learned in Scene N should be in "unaware" for Scene N+1
    if i < 5:
        with open(f'fragment/ch1-sc{i+1}.yaml') as f:
            next_scene = yaml.safe_load(f)
        next_unaware = set(next_scene['reader_knowledge']['still_unaware'])

        if learns & next_unaware:
            print(f"⚠️  Continuity issue: Scene {i} learns something Scene {i+1} claims reader doesn't know")
        else:
            print(f"✅ Scene {i} → {i+1} continuity OK")
EOF
```

### Creative Room Exclusion

Verify that creative room secrets are NOT revealed in Chapter 1:

```bash
# These should NOT appear in ch1-sc1 through ch1-sc5:
echo "Checking for early spoilers..."
grep -i "simulation\|architect\|manipulation\|meta.*layer" fragment/ch1-sc*.yaml && echo "⚠️  SPOILER FOUND!" || echo "✅ No major spoilers"
```

### Style Guide Compliance

Check that scenes follow world_1 style guide (warm, comedic, golden hour):

```bash
# Scenes should mention:
grep -l "warm\|golden\|monsoon\|chai\|comedy\|laugh" fragment/ch1-sc*.yaml
# Should find all 5 files

# Scenes should NOT mention:
grep -l "grimdark\|shadow\|dark\|grim" fragment/ch1-sc*.yaml
# Should find nothing
```

---

## Step 7: Integrate Into Chapter Metadata

Update `chapters/chapter-01/meta.yaml`:

```yaml
id: "chapter-01"
chapter_number: 1
title: "The Academy"
description: "A's introduction to quantum powers and the beginning of the election"

story_beat: "Opening Image → Inciting Incident"
act: 1

scenes:
  - scene_id: "ch1-sc1"
    title: "The Philosophy of God in Smoke"
    status: "written"
    word_count: 4000

  - scene_id: "ch1-sc2"
    title: "The Elections Begin"
    status: "written"
    word_count: 3000

  - scene_id: "ch1-sc3"
    title: "First Light"
    status: "written"
    word_count: 2500

  - scene_id: "ch1-sc4"
    title: "The Question"
    status: "written"
    word_count: 2000

  - scene_id: "ch1-sc5"
    title: "The Secret"
    status: "written"
    word_count: 3000

chapter_totals:
  scene_count: 5
  word_count: 14500
  status: "complete"

reader_knowledge_state:
  knows:
    - "A is a philosophy-loving student at Dharma Academy"
    - "Quantum code abilities exist and are trained"
    - "There's an election for stadium participation"
    - "Something feels off about reality"
    - "B is trustworthy and knows secrets"

  unaware:
    - "Simulation layers exist"
    - "Mother is an architect"
    - "The election is a selection mechanism"
    - "True nature of quantum code"

next_chapter: "chapter-02"
next_chapter_focus: "Stadium election competition begins"
```

---

## Step 8: Create Research Containers (Optional but Helpful)

Populate `containers/` with reference material for Chapter 1:

**containers/ch1-world-1-reference.yaml**
```yaml
id: "ch1-world-1-reference"
type: "research"
chapter_scope: "chapter-01"
purpose: "Reference material for World 1 Academy writing"

sections:
  dharma_academy_details:
    - "Campus layout and atmosphere"
    - "Daily schedule and rhythm"
    - "Character hangout spots"
    - "Monsoon season sensory details"

  character_interactions:
    - "A and B first meet (how?)"
    - "A and Mother's dynamic"
    - "Professor H's classroom style"

  quantum_code_training:
    - "How students learn it (classes vs practice)"
    - "What intermediate level looks like"
    - "Safety limits and restrictions"

  foreshadowing_opportunities:
    - "Mother knows too much"
    - "B observes carefully"
    - "Professor H hints at depths"
```

---

## Step 9: Commit Changes

```bash
git add fragment/ch1-sc*.yaml chapters/chapter-01/meta.yaml containers/
git commit -m "feat: Write Chapter 1 scenes (ch1-sc2 through ch1-sc5)

Added:
- ch1-sc2.yaml 'The Elections Begin' (3000 words)
- ch1-sc3.yaml 'First Light' (2500 words)
- ch1-sc4.yaml 'The Question' (2000 words)
- ch1-sc5.yaml 'The Secret' (3000 words)

Chapter 1 now complete with 5 scenes, 14,500 total words

Features:
- Creative room properly excluded (no spoilers)
- Character relationships properly reflected
- World layer 1 style guide applied (warm, comedic)
- Foreshadowing planted for later reveals
- Reader knowledge tracked progressively

Validated:
- Continuity across scenes
- No early spoilers
- Style guide compliance
- Character consistency

Next: Write Chapter 2 (stadium competition), or revise Chapter 1

Phase 5 Complete ✅"
```

---

## Step 10: Post-Writing Validation

After all scenes written and committed, run full validation:

```bash
python3 << 'EOF'
import yaml
import os

print("=" * 50)
print("CHAPTER 1 VALIDATION")
print("=" * 50)

# Check all files exist
for i in range(1, 6):
    path = f'fragment/ch1-sc{i}.yaml'
    if os.path.exists(path):
        with open(path) as f:
            scene = yaml.safe_load(f)
        wc = scene.get('word_count', 0)
        print(f"✅ ch1-sc{i}: {wc} words")
    else:
        print(f"❌ ch1-sc{i}: NOT FOUND")

# Total word count
total = sum([
    yaml.safe_load(open(f'fragment/ch1-sc{i}.yaml'))['word_count']
    for i in range(1, 6)
])
print(f"\n📊 Total Chapter 1: {total} words")
print(f"   Target: ~15,000 words")
print(f"   Status: {'✅ ON TARGET' if 13000 < total < 17000 else '⚠️  REVIEW'}")

print("\n" + "=" * 50)
EOF
```

---

## Acceptance Criteria (Self-Check)

- [ ] ch1-sc2.yaml written and valid YAML (~3000 words)
- [ ] ch1-sc3.yaml written and valid YAML (~2500 words)
- [ ] ch1-sc4.yaml written and valid YAML (~2000 words)
- [ ] ch1-sc5.yaml written and valid YAML (~3000 words)
- [ ] Total Chapter 1: 13,000-17,000 words
- [ ] Creative room secrets NOT revealed early
- [ ] Character relationships properly reflected
- [ ] World layer 1 style guide applied (warm, comedic)
- [ ] Foreshadowing planted (Mother's knowledge, B's secrets)
- [ ] Reader knowledge tracked in metadata
- [ ] Continuity across all 5 scenes verified
- [ ] chapters/chapter-01/meta.yaml updated with scene links
- [ ] Git commit made with Phase 5 message

---

## What This Enables

Once Phase 5 is complete:
- ✅ All infrastructure (Phases 1-4) tested in real writing
- ✅ Chapter 1 complete with 5 scenes
- ✅ Proof that creative room isolation works
- ✅ Proof that relationship injection works
- ✅ Proof that style guide produces coherent tone
- ✅ Ready to continue with Chapter 2
- ✅ Template established for remaining chapters

---

## Next Steps (Beyond Phase 5)

Once Chapter 1 is solid:
1. **Write Chapter 2** (stadium election competition)
   - World layer: Still 1, but more intense pressure
   - Tone: Excitement with underlying tension
   - Foreshadowing: B's knowledge, Mother's oversight

2. **Generate images for Chapter 1** using correct style tokens from Phase 3
   - Use prompt_style_tokens for image prompts
   - Ensure warm golden hour aesthetic
   - Validate character consistency across images

3. **Storyboard Chapter 1** in web UI
   - Divide scenes into panels
   - Layout for vertical scroll (9:16 manhwa format)
   - Assign character DNA to each panel

4. **Continue Chapter-by-Chapter** until all 40 chapters are drafted

---

## Tips for Success

1. **Read ch1-sc1 first** — understand the voice and style
2. **Keep creative room file open** — remember what NOT to reveal
3. **Reference style_guide constantly** — golden hour, warm tones, comedic relief
4. **Plant foreshadowing subtly** — hints, not exposition
5. **Use dialogue heavily** — Academy scenes are social
6. **Trust the character arcs** — they're already mapped, just execute them
7. **Validate as you go** — catch continuity issues early

---

## Questions?

- Unsure about a scene's tone? Check style_guide/narrative.yaml
- Not sure what A knows? Check reader_knowledge state in previous scene
- Confused about foreshadowing? Reference creative_room/foreshadowing_map.yaml
- Stuck on character interaction? Reference story/relationships.yaml

Good luck! You're bringing Quantum Dharma to life. 🎬
