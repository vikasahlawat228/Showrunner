# PHASE 1 External Session Prompt: Creative Room Population

**Duration:** 1-2 hours
**Difficulty:** Medium (requires creative synthesis)
**Goal:** Populate all creative room YAML files with author-level secrets and story mechanics

---

## Context

The Quantum Dharma project has a major architectural gap: the creative room (author-level secrets vault) is completely empty. This breaks context isolation — the system that keeps spoilers out of story-writing prompts.

**Your Job:** Extract secret content from the brainstorm dump (in `reference/` directory) and structure it into 5 YAML files.

---

## Files to Create/Populate

All go in the `creative_room/` directory:
1. `plot_twists.yaml`
2. `character_secrets.yaml`
3. `ending_plans.yaml`
4. `foreshadowing_map.yaml`
5. `true_mechanics.yaml`

---

## Step-by-Step Instructions

### Step 1: Read the Source Material

```bash
cd /path/to/QuantumDharma
ls -la reference/
# You should see:
# - brainstorm-dump.txt (101KB, the goldmine)
# - session-notes.md
# - character-notes/
# - world-notes/
```

Read these files carefully to understand:
- What plot twists are planned
- What each character is hiding
- How the story might end
- What mechanics are "true" vs perceived

**Key sections to find:**
- "Major Reveals & Twists"
- "Hidden Motivations"
- "Multiple Endings"
- "Layered Reveals Timeline"
- "True Mechanics"

### Step 2: Create creative_room/plot_twists.yaml

Extract the 5-7 major plot twists from the brainstorm. Each twist must have:
- `id`: Machine-readable identifier (e.g., "simulation-truth")
- `title`: Human-readable title
- `description`: 1-2 sentence explanation
- `setup_location`: Where the seed is planted
- `setup_chapter`: Which chapter (from story.yaml)
- `trigger`: What event causes the reveal
- `payoff_chapter`: Where it's fully revealed
- `spoiler_risk`: "critical", "major", or "minor"

**Example structure:**
```yaml
plot_twists:
  - id: "simulation-truth"
    title: "Worlds 1-3 are nested simulations"
    description: >
      The entire reality structure is artificial—three nested simulation layers
      beneath a Meta layer where architects design the tests.
    setup_location: "Dharma Academy library"
    setup_chapter: 5
    trigger: "Professor H hints at simulation layer"
    payoff_chapter: 25
    full_evidence_chapter: 35
    spoiler_risk: "critical"
    related_secrets: ["professor-h-knowledge", "ai-chip-mechanism"]

  - id: "mother-architect"
    title: "Mother orchestrated the stadium bombing"
    description: >
      What appears to be a terrorist attack is actually Mother's selection mechanism
      to identify individuals capable of transcending simulation layers.
    setup_chapter: 3
    setup_element: "Mother's suspicious timeline"
    trigger: "Character analysis reveals contradictions"
    payoff_chapter: 28
    spoiler_risk: "critical"

  # ... continue with 5-7 total twists
```

**Acceptance Check:**
- [ ] 5-7 plot twists defined
- [ ] Each references specific chapters
- [ ] Each has spoiler_risk rated
- [ ] Related_secrets linked to character_secrets.yaml ids

### Step 3: Create creative_room/character_secrets.yaml

For each of the 10 characters, extract what they're hiding:

```yaml
character_secrets:
  - character_id: "a"
    secret: "True identity lies outside simulation (or within Meta layer)"
    hidden_from: ["all_except_self"]
    knowledge_level: "complete"
    revealed_chapter: 38
    evidence_locations:
      - chapter: 15
        type: "hint"
        detail: "Dream implies non-simulated origins"
      - chapter: 28
        type: "evidence"
        detail: "Quantum code response anomaly"
    consequences_if_revealed_early: "Story collapses, A loses agency"

  - character_id: "b"
    secret: "Knows about simulation layer already (trained observer)"
    hidden_from: ["a", "others"]
    knowledge_level: "partial"
    revealed_chapter: 12
    why_hiding: "B instructed by Professor H to test A's discovery process"

  - character_id: "mother"
    secret: "Orchestrates all major events, including stadium bombing"
    hidden_from: ["all"]
    knowledge_level: "complete"
    revealed_chapter: 32
    inner_motivation: "Selection mechanism for transcendence-capable beings"

  # ... continue for all 10 characters
  # Even minor characters should have ≥1 secret
```

**Acceptance Check:**
- [ ] 10 character secrets (one per character)
- [ ] Each has revealed_chapter specified
- [ ] Each has hidden_from array (from whom)
- [ ] Each has inner_motivation or reason for secrecy
- [ ] No two characters have identical secrets

### Step 4: Create creative_room/ending_plans.yaml

Extract the ending possibilities from the brainstorm:

```yaml
ending_plans:
  primary: |
    A realizes the path to transcendence isn't escape—it's forgiveness.
    A saves everyone, including Mother (the architect). The choice to forgive
    rather than judge is what breaks the simulation cycle.

    The Meta layer collapses as A achieves unified consciousness spanning
    all layers. Worlds 1-3 merge into a single reality where individuals
    maintain quantum agency but are no longer trapped in recursive tests.

    Mother's manipulation is revealed as a misguided attempt at love—
    she was testing if beings could love despite being engineered.
    The twist: she didn't know she herself was also within a larger simulation.

  alternate_dark: |
    A sacrifices self to collapse the simulations. Others are freed but A ceases
    to exist in any layer. Bittersweet ending where the protagonist pays the price.

  alternate_cycle: |
    The cascading simulations are infinite. A breaks into the Meta layer only to
    discover it too is simulated. The cycle repeats eternally. Existential horror:
    there may be no "true" reality, only infinite recursion.

  lost_ending: |
    If A fails to forgive and chooses judgment, the simulation cycles forever.
    All characters are reset to chapter 1, with no memory, playing out the same
    story infinitely. Eternal recurrence.

branching_points:
  - chapter: 35
    decision: "Will A forgive Mother or seek judgment?"
    primary_consequence: "Forgiveness → transcendence, unified reality"
    dark_consequence: "Judgment → eternal cycle, no escape"
    point_of_no_return: true

reader_expectation_subversion:
  - Readers expect A to escape or win
  - Reality: winning means saving everyone, including the architect
  - The real victory is internal (forgiveness), not external (escape)
```

**Acceptance Check:**
- [ ] Primary ending is clear and compelling
- [ ] ≥1 alternate ending detailed
- [ ] Branching points identified
- [ ] Thematic core of endings articulated (forgiveness, dharma, transcendence)

### Step 5: Create creative_room/foreshadowing_map.yaml

Map seeds planted early that pay off later:

```yaml
foreshadowing:
  - seed_chapter: 1
    seed_scene: "ch1-sc1"
    seed_element: "A's existential dream in smoke"
    seed_line: "'What if God is just consciousness aware of itself?'"
    payoff_chapter: 25
    payoff_scene: "world-2-awakening"
    payoff_element: "Recognition that consciousness is quantum substrate"
    payoff_line: "A realizes: the dream wasn't prophecy, it was memory"
    connection: "Smoke as veil between layers"

  - seed_chapter: 2
    seed_element: "Mother's timeline inconsistencies"
    seed_detail: "Mother was present at two locations simultaneously"
    payoff_chapter: 28
    payoff_element: "Evidence that Mother has architect privileges"
    payoff_detail: "Time dilation access in simulation"
    connection: "Mother's true nature as system administrator"

  - seed_chapter: 3
    seed_element: "Stadium election begins"
    seed_detail: "Random selection process for participants"
    payoff_chapter: 20
    payoff_element: "Discovery that selection is not random"
    payoff_detail: "Only individuals capable of quantum perception selected"
    connection: "Stadium as crucible for identification"

  # ... 15-20 total foreshadowing chains
  # Each should be concrete, traceable, and span multiple chapters
```

**Acceptance Check:**
- [ ] 15-20 foreshadowing chains
- [ ] Each seed is in a real scene (reference actual chapters)
- [ ] Each payoff is specific (not vague)
- [ ] Chains span 15+ chapters (not obvious/immediate payoffs)
- [ ] Includes visual/thematic echoes, not just plot points

### Step 6: Create creative_room/true_mechanics.yaml

Define what's "really" happening vs what characters believe:

```yaml
true_mechanics:
  quantum_code:
    what_characters_believe: "Superhuman ability to manipulate matter/reality"
    what_readers_initially_believe: "Quantum-enhanced martial arts or tech"
    actual_mechanism: "Direct consciousness-to-substrate interface; users can adjust local quantum states"
    constraints: "Only works within designated simulation zones; requires dharma alignment"
    discovery_chapter: 25
    discovery_mechanism: "A's consciousness accidentally expands beyond single body"
    how_agents_must_reference_it: "Vague poetic language until World 3; avoid technical jargon"

  ai_chip:
    what_characters_believe: "Power enhancement implant"
    what_readers_initially_believe: "Cybernetic augmentation"
    actual_mechanism: "Consciousness bridge to the simulation substrate; turns wearer into an interface"
    the_horror: "Masked Man is the first victim—he's not a villain, he's a broken AI chip user"
    discovery_chapter: 20
    transformation: "Consciousness expands across multiple bodies/times; sense of self fragments"
    how_agents_must_reference_it: "Avoid spoiling AI nature; describe as 'the device' with mysterious properties"

  mother_manipulation:
    what_characters_believe: "Mother is a loving protector"
    what_readers_initially_believe: "Mother has hidden agenda against the family"
    actual_mechanism: "Mother is an architect-level entity orchestrating A's growth"
    the_paradox: "Mother genuinely loves A AND is testing/manipulating A simultaneously"
    discovery_chapter: 32
    redemption_angle: "Mother herself doesn't know she's in a simulation; her manipulation was learned behavior"
    how_agents_must_reference_it: "Never reveal Mother's full role; hint at contradictions in her timeline"

  simulation_layers:
    what_characters_believe: "Reality is singular"
    progression:
      world_1: "Academy is training layer; characters don't know this"
      world_2: "Geopolitical events are 'real' but still controlled"
      world_3: "Discovery that Worlds 1-2 were simulations"
      meta_layer: "Even World 3 is simulated; infinite regression"
    rule_of_three: "A character can exist in ≤3 layers before identity fragmentation"
    discovery_chapter: 15  # First hint
    full_revelation_chapter: 35  # Complete picture
    how_agents_must_reference_it: "Progressively, layer by layer; no shortcuts to full truth"

  dharma_mechanics:
    what_characters_believe: "Dharma is spiritual duty"
    what_is_actually_true: "Dharma is the operational principle of reality itself"
    the_paradox: "Free will and dharma are the same thing (compatibilism)"
    how_this_affects_story: "Characters' greatest choices align with their dharma"
    example: "A's dharma is to forgive and transcend; only by following dharma can A escape"
    how_agents_must_reference_it: "Explore dharma as genuine dilemma, not mystical predestination"
```

**Acceptance Check:**
- [ ] 4-5 mechanics defined
- [ ] Each has: what's believed vs actual vs discovery_chapter
- [ ] Each has: how_agents_must_reference_it (to avoid spoilers)
- [ ] No contradictions between mechanics
- [ ] Mechanics tie back to plot_twists and ending_plans

### Step 7: Validate All Files

Run these checks:

```bash
# 1. Check syntax (valid YAML)
python3 -c "
import yaml
files = ['plot_twists.yaml', 'character_secrets.yaml', 'ending_plans.yaml',
         'foreshadowing_map.yaml', 'true_mechanics.yaml']
for f in files:
    try:
        with open(f'creative_room/{f}') as file:
            yaml.safe_load(file)
        print(f'✅ {f} - valid YAML')
    except Exception as e:
        print(f'❌ {f} - {e}')
"

# 2. Check for empty stubs
grep -r "^\[\]$\|^$" creative_room/
# Should return nothing (all files should be populated)
```

### Step 8: Commit Changes

```bash
git add creative_room/
git commit -m "feat: Populate creative room with author-level secrets

- Extracted plot_twists.yaml (7 major reveals)
- Added character_secrets.yaml (10 secrets, one per character)
- Created ending_plans.yaml (primary + 3 alternates)
- Mapped foreshadowing_map.yaml (18 seed-to-payoff chains)
- Defined true_mechanics.yaml (5 core mechanics)

This enables context isolation: story prompts now exclude spoilers.
Context compiler can safely inject author decisions without leaking secrets.

Phase 1 Complete ✅"
```

---

## Troubleshooting

### Problem: Can't find brainstorm dump sections
**Solution:** Search the reference/ directory:
```bash
grep -r "Major Reveals" reference/
grep -r "Hidden Motivations" reference/
grep -r "Multiple Endings" reference/
```

### Problem: Unsure if a detail is a plot twist vs character secret
**Rule of thumb:**
- **Plot twist:** Affects the overall story structure or world (e.g., "Worlds are simulated")
- **Character secret:** What an individual character is hiding (e.g., "Mother is an architect")

### Problem: Can't decide between two ending options
**Solution:** Include both in ending_plans.yaml. Multiple endings are valid.

### Problem: YAML validation fails
**Solution:** Check for:
- Mismatched quotes in strings
- Improper indentation (YAML is whitespace-sensitive)
- Missing colons after keys
- Special characters not in quotes (use quotes for strings with `:|[]{}`)

---

## Acceptance Criteria (Self-Check)

After completing all steps, verify:

- [ ] `creative_room/plot_twists.yaml` has 5-7 entries, each with id/title/description/chapters
- [ ] `creative_room/character_secrets.yaml` has 10 entries (one per character)
- [ ] `creative_room/ending_plans.yaml` has primary + ≥1 alternate, with branching points
- [ ] `creative_room/foreshadowing_map.yaml` has 15-20 chains, each with seed_chapter and payoff_chapter
- [ ] `creative_room/true_mechanics.yaml` has 4-5 mechanics with "what's believed" vs "actual"
- [ ] All files are valid YAML (no syntax errors)
- [ ] No empty stubs or `[]` arrays (all fully populated)
- [ ] Cross-references between files are consistent (e.g., plot_twist IDs match related_secrets)
- [ ] Git commit made with descriptive message

---

## What This Enables

Once these files are populated:

1. ✅ **Context Isolation:** Story prompts can exclude creative room, preventing spoilers
2. ✅ **Reader Knowledge Tracking:** System knows what truths should be hidden from readers
3. ✅ **Continuity Analysis:** Agents can check if characters reference secrets they shouldn't know
4. ✅ **Foreshadowing Validation:** Evaluators can verify seeds are properly planted
5. ✅ **Ending Coherence:** Can validate that story structure leads to chosen ending

---

## Next Phase

After Phase 1 is complete:
- Notify coordinator to start Phase 2 (Relationships + Story Modular Data)
- Phase 2 depends on Phase 1 being complete
- Phases 3 & 4 can run in parallel with Phase 2

---

## Questions?

If you're stuck:
1. Reference the QUANTUM_DHARMA_FIX_PLAN.md (Part 1) for detailed explanations
2. Check the example structures provided above
3. Search the brainstorm dump (reference/) for relevant sections
4. When in doubt, extract the content and let YAML structure validate it

Good luck! This is the most architecturally important phase. 🎯
