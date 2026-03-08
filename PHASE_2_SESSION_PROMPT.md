# PHASE 2 External Session Prompt: Relationships & Story Modular Data

**Duration:** 1.5-2 hours
**Difficulty:** Medium (data structure work)
**Prerequisite:** Phase 1 must be complete (creative room populated)
**Goal:** Populate character relationships and create story modular files

---

## Context

Quantum Dharma has 10 fully-written character files, but every single one has `relationships: []`. This breaks:
- Relationship graph visualization in web UI
- Continuity checking (detecting inconsistent character interactions)
- Context compiler (can't inject "A trusts B" into scenes)

Additionally, the story modular files (story/themes.yaml, story/relationships.yaml, story/timeline.yaml, story/arcs/) are all empty stubs.

**Your Job:**
1. Populate relationships in all 10 character YAML files
2. Create/populate story/ subdirectory files with modular story data

---

## Part 1: Populate Character Relationships

### Step 1: Read All 10 Character Files

```bash
cd /path/to/QuantumDharma/characters
ls -la
# You should see:
# - a.yaml, b.yaml, f.yaml, mother.yaml, masked_man.yaml
# - professor_h.yaml, v.yaml, p.yaml, c.yaml, main_villain.yaml
```

For each character, understand:
- Their role (protagonist, deuteragonist, antagonist, supporting)
- Their backstory
- Their goals and motivations
- Where their character arc goes (from story.yaml)

### Step 2: Reference the Story's Character Arcs

From `story.yaml`, extract the character arc descriptions (e.g., A's transformation from "Ignorant of true nature" to "Knows the truth and chooses forgiveness").

Relationships should reflect these arcs:
- How do characters help/hinder each other's transformations?
- Which relationships are tested and strengthened?
- Which relationships are revealed to be deceptive?

### Step 3: Populate Relationships in Each Character File

For each character, add relationships array with ≥2 relationships per character.

**Example for A (protagonist):**

```yaml
relationships:
  - related_to: "b"
    relationship_type: "trust"
    description: "Growing alliance built on mutual truth-seeking"
    current_dynamic: "Tentative partnership, testing each other's reliability"
    evolution:
      - chapter: 3
        state: "neutral_peers"
        detail: "Both in academy, aware of each other"
      - chapter: 8
        state: "tentative_collaboration"
        detail: "B reveals partial knowledge, A becomes curious"
      - chapter: 15
        state: "deepening_trust"
        detail: "Work together on World 2 discovery"
      - chapter: 25
        state: "deep_trust"
        detail: "B becomes A's primary confidant about simulation"
      - chapter: 38
        state: "unshakeable_alliance"
        detail: "Both work toward shared salvation ending"
    impact_on_story: "B's mentorship accelerates A's self-discovery"
    notes: "This is the central relationship arc of the story"

  - related_to: "mother"
    relationship_type: "conflict"
    description: "Mother's hidden orchestration vs A's desire for genuine agency"
    current_dynamic: "Loving but increasingly questioned"
    evolution:
      - chapter: 1
        state: "unconditional_love"
        detail: "A adores Mother, trusts implicitly"
      - chapter: 12
        state: "subtle_doubt"
        detail: "Contradictions in Mother's timeline noticed"
      - chapter: 20
        state: "active_questioning"
        detail: "A begins investigating Mother's activities"
      - chapter: 28
        state: "betrayal_crisis"
        detail: "Stadium bombing orchestration discovered"
      - chapter: 35
        state: "forgiveness_choice"
        detail: "A chooses to forgive rather than judge"
    impact_on_story: "Central to the ending theme: love despite betrayal"
    notes: "This relationship drives the grand irony of the resolution"

  - related_to: "professor_h"
    relationship_type: "mentorship"
    description: "A's intellectual guide, gently steering toward truth"
    current_dynamic: "Student respecting teacher's wisdom"
    evolution:
      - chapter: 2
        state: "standard_teacher"
        detail: "Professor H is A's philosophy instructor"
      - chapter: 8
        state: "trusted_advisor"
        detail: "A seeks Prof H for existential questions"
      - chapter: 15
        state: "guide_to_truth"
        detail: "Prof H drops hints about simulation layer"
      - chapter: 25
        state: "revealed_ally"
        detail: "Prof H acknowledged as deliberate guide"
    impact_on_story: "Prof H represents the compassionate architect figure"
    notes: "Contrast to Mother's manipulative orchestration"

  - related_to: "main_villain"
    relationship_type: "revelation"
    description: "Apparent enemy, actually suffering victim"
    current_dynamic: "Unknown/hostile"
    evolution:
      - chapter: 8
        state: "perceived_threat"
        detail: "Main Villain appears as antagonist"
      - chapter: 18
        state: "confused_opposition"
        detail: "Villain's motivations unclear"
      - chapter: 32
        state: "tragic_recognition"
        detail: "A realizes Villain is a broken person, not evil"
      - chapter: 38
        state: "salvation_target"
        detail: "A chooses to save Villain along with everyone else"
    impact_on_story: "Represents the core theme: forgiveness of all"
    notes: "This relationship subverts reader expectations"
```

**Format for all other characters:**

For each character in `characters/{name}.yaml`, add:
```yaml
relationships:
  - related_to: "{other_character_id}"
    relationship_type: "trust|conflict|mentorship|love|alliance|antagonism|revelation"
    description: "{1-2 sentence summary}"
    current_dynamic: "{How they currently relate}"
    evolution:
      - chapter: {num}
        state: "{descriptive state}"
        detail: "{What changed}"
    impact_on_story: "{How this relationship affects the plot}"
    notes: "{Any additional context}"
```

**Relationship types to use:**
- `trust`: Growing reliance on each other
- `conflict`: Opposing goals or secrets
- `mentorship`: Teacher-student dynamic
- `love`: Romantic or deep familial bond
- `alliance`: Working together toward shared goal
- `antagonism`: Active opposition
- `revelation`: Apparent enemy → ally (or vice versa)
- `manipulation`: One character orchestrating another

### Step 4: Validate Relationship Consistency

Check that relationships are reciprocated (with variations):
```
A→B: "trust"
B→A: "trust" or "mentorship" ✅ (A trusts B, B mentors A)

A→C: "conflict"
C→A: "antagonism" or "conflict" ✅ (Both recognize the opposition)

M→A: "manipulation"
A→M: "conflict" or "love" ✅ (A hasn't discovered manipulation yet)
```

---

## Part 2: Create Story Modular Files

### Step 1: Create story/relationships.yaml

```yaml
edges:
  # A's relationships (protagonist)
  - from: "a"
    to: "b"
    type: "trust"
    evolution_stages:
      - chapter: 3
        state: "neutral_peers"
      - chapter: 8
        state: "tentative_collaboration"
      - chapter: 15
        state: "deepening_trust"
      - chapter: 25
        state: "deep_trust"

  - from: "a"
    to: "mother"
    type: "conflict_with_love"
    evolution_stages:
      - chapter: 1
        state: "unconditional_love"
      - chapter: 20
        state: "active_questioning"
      - chapter: 28
        state: "betrayal_crisis"
      - chapter: 35
        state: "forgiveness_choice"

  # B's relationships (deuteragonist)
  - from: "b"
    to: "a"
    type: "mentorship"  # B guides A
    evolution_stages:
      - chapter: 3
        state: "watching"
      - chapter: 8
        state: "testing"
      - chapter: 15
        state: "collaborative"

  # Mother's relationships (hidden architect)
  - from: "mother"
    to: "a"
    type: "manipulation"
    evolution_stages:
      - chapter: 1
        state: "orchestrating_destiny"

  - from: "mother"
    to: "b"
    type: "shared_knowledge"
    evolution_stages:
      - chapter: 3
        state: "coordinating_test"

  # ... continue for all major relationships (≥20 edges total)

evolution:
  - stage_name: "foundation"
    chapters: "1-10"
    description: "Establish baseline relationships in Academy setting"

  - stage_name: "testing"
    chapters: "11-25"
    description: "Relationships strained as truth-seeking intensifies"

  - stage_name: "revelation"
    chapters: "26-35"
    description: "Hidden connections and orchestrations revealed"

  - stage_name: "resolution"
    chapters: "36-40"
    description: "Relationships solidified, forgiveness and synthesis achieved"
```

### Step 2: Create story/themes.yaml

```yaml
themes:
  - id: "dharma-vs-free-will"
    name: "Dharma vs Free Will"
    description: "Is our path predetermined by dharma (duty) or freely chosen?"
    origin_source: "Indian philosophy, Bhagavad Gita"
    exploration_arc: "Ch1 (introduced) → Ch15 (complicated) → Ch30 (synthesized)"
    key_scenes:
      - chapter: 1
        detail: "A's existential question in smoke"
      - chapter: 10
        detail: "Philosophy class debate on choice vs destiny"
      - chapter: 25
        detail: "Quantum mechanics as metaphor for dharma"
      - chapter: 38
        detail: "A's final choice understood as aligned dharma"
    visual_motifs: ["sacred geometry", "choice-points", "quantum superposition"]
    character_arc_impact: "A's entire arc is learning that free will = aligned dharma"

  - id: "maya-veil"
    name: "Maya: The Veil of Reality"
    description: "What is real vs perceived? Is perception reality?"
    origin_source: "Vedic concept of Maya"
    exploration_arc: "Ch1 (poetic) → Ch15 (literal) → Ch35 (revolutionary)"
    parallels:
      - "Quantum mechanics: observation affects reality"
      - "Simulation hypothesis: perceived reality may be artificial"
      - "Buddhist emptiness: no inherent objective reality"
    key_scenes:
      - chapter: 1
        detail: "Smoke as veil metaphor"
      - chapter: 15
        detail: "Discovery that World 1 is a simulation"
      - chapter: 25
        detail: "Realization that all worlds are simulated"
    related_plot_twist: "simulation-truth"

  - id: "manipulation-love"
    name: "Manipulation Under the Guise of Love"
    description: "Can love and manipulation coexist? Can they be forgiven?"
    exploration_arc: "Ch1 (hidden) → Ch20 (suspected) → Ch32 (revealed) → Ch38 (transcended)"
    key_scenes:
      - chapter: 32
        detail: "Mother's orchestration fully revealed"
      - chapter: 35
        detail: "A confronts Mother about manipulation"
      - chapter: 38
        detail: "A chooses forgiveness, understanding love can include orchestration"
    character_arc_impact: "Mother and A's relationship becomes central to ending"

  - id: "observer-effect"
    name: "Observer Effect: Consciousness Shapes Reality"
    description: "Does consciousness create reality or only perceive it?"
    origin_source: "Quantum mechanics, consciousness studies"
    exploration_arc: "Ch5 (physics class) → Ch20 (becomes literal) → Ch35 (revolutionary)"
    metaphysical_implication: "In Quantum Dharma, consciousness literally affects quantum state"

motifs:
  - name: "Light & Shadow"
    meaning: "Enlightenment vs Ignorance, Truth vs Illusion"
    examples: ["Ch1 smoke diffusing light", "Ch15 stadium lights revealing truth", "Ch35 Meta layer light"]

  - name: "Circles & Recursion"
    meaning: "Eternal return, nested layers, cycles of test"
    examples: ["Stadium architecture", "Simulation layer nesting", "Character dharma cycles"]

  - name: "Mirrors & Reflection"
    meaning: "Identity, simulation, duality"
    examples: ["Mother's reflections in water", "Character doublings", "Simulation mirrors reality"]

  - name: "Quantum Superposition"
    meaning: "Multiple states simultaneously, collapsed by observation"
    examples: ["Characters in multiple states of knowledge", "Reality layers coexisting"]

symbols:
  - symbol: "Quantum Code"
    meaning: "Bridge between layers, consciousness interface"
    first_appearance: "Chapter 5 (Academy training)"
    evolution: "Mundane skill → reality manipulation → consciousness transfer"

  - symbol: "The Stadium"
    meaning: "Crucible of truth, testing ground, circular fate"
    first_appearance: "Chapter 3 (election begins)"
    evolution: "Competition → pressure cooker → revelation engine"

  - symbol: "Smoke"
    meaning: "Veil between clarity and obscurity, thoughts taking form"
    first_appearance: "Chapter 1 (philosophy class)"
    evolution: "Poetic image → literal veil of reality → interface between layers"

  - symbol: "Mother"
    meaning: "Both nurturer and architect, love and manipulation"
    first_appearance: "Chapter 1 (loving mother)"
    evolution: "Protector → suspected manipulator → revealed architect → forgiven guide"
```

### Step 3: Create story/timeline.yaml

```yaml
events:
  # Act 1: Academy (Chapters 1-10)
  - chapter: 1
    scene: "ch1-sc1"
    event: "A has existential dream in smoke"
    significance: "Sets existential tone, foreshadows quantum consciousness theme"
    pov_character: "a"

  - chapter: 2
    event: "Philosophy class debates dharma and free will"
    significance: "Introduces core philosophical tension"
    linked_theme: "dharma-vs-free-will"

  - chapter: 3
    event: "Stadium election begins"
    significance: "External pressure introduced, selection mechanism activated"
    pov_character: "a"
    related_plot_twist: "mother-architect"

  - chapter: 5
    event: "A discovers quantum code ability"
    significance: "Supernatural enters the narrative"
    related_symbol: "quantum-code"

  # Act 2: Geopolitical Thriller (Chapters 11-25)
  - chapter: 15
    event: "First evidence of World 2 simulation"
    significance: "Reality questioned, simulation truth begins"
    major_revelation: true
    related_plot_twist: "simulation-truth"

  - chapter: 18
    event: "Main Villain reveals themselves as antagonist"
    significance: "External opposition crystallizes"
    pov_character: "a"

  - chapter: 20
    event: "Professor H hints at deeper layers"
    significance: "Authority figure subtly guides toward truth"
    related_character_secret: "professor-h-knowledge"

  - chapter: 25
    event: "A experiences reality glitch, confirms simulation"
    significance: "Hard evidence of simulation layer"
    major_revelation: true

  # Act 3: Cosmic Revelation (Chapters 26-40)
  - chapter: 28
    event: "Mother's orchestration discovered"
    significance: "Trusted figure revealed as architect/manipulator"
    major_revelation: true
    related_plot_twist: "mother-architect"
    related_character_secret: "mother-hidden-orchestration"

  - chapter: 32
    event: "Confrontation with Mother"
    significance: "Central relationship crisis"
    pov_character: "a"

  - chapter: 35
    event: "A discovers Meta layer, infinite recursion"
    significance: "Highest truth revealed, ultimate question posed"
    major_revelation: true
    related_plot_twist: "meta-layer-discovery"

  - chapter: 38
    event: "A chooses to save everyone, including Mother"
    significance: "Core theme crystallized: forgiveness transcends reality"
    major_revelation: true
    narrative_climax: true
    pov_character: "a"

  - chapter: 40
    event: "Final Image: New reality emerges from synthesis"
    significance: "Resolution, transcendence achieved"
    narrative_resolution: true
```

### Step 4: Create story/arcs/ — Per-Character Arc Files

Create one file per major character.

**story/arcs/a-arc.yaml** (Protagonist):
```yaml
character: "a"
role: "protagonist"
character_type: "hero"
core_question: "Am I free, or is my dharma my prison?"

act_1:
  title: "Ignorance"
  state_start: "Unaware of true nature, living in Academy comfort"
  journey: "Discovers quantum abilities, first hints of unreality"
  state_end: "Knows something is wrong, beginning to question"
  key_scene: "ch1-sc1"
  transformation_degree: 15

act_2:
  title: "Questioning"
  state_start: "Actively investigating reality layers"
  journey: "Uncovers simulation truth, tests boundaries of World 1"
  state_end: "Knows Worlds 1-2 are simulated, questions World 3"
  major_scenes: ["world-2-discovery", "stadium-truth"]
  transformation_degree: 50

act_3:
  title: "Transcendence"
  state_start: "Knows infinite simulation layers exist"
  journey: "Chooses to save everyone rather than escape"
  state_end: "Achieves unified consciousness, forgives all architects"
  major_scenes: ["final-choice", "synthesis"]
  transformation_degree: 100

final_belief: "Free will is dharma. Forgiveness transcends reality."
character_arc_completeness: 100
```

**story/arcs/b-arc.yaml** (Deuteragonist):
```yaml
character: "b"
role: "deuteragonist"
character_type: "mentor_ally"
core_question: "Can I guide A without controlling them?"

arc_summary: |
  B starts as A's peer but is revealed to be a trained observer.
  B's arc is learning that true mentorship means stepping back to let A discover.
  By the end, B becomes equal collaborator rather than guide.

act_1:
  state: "Observing A"
  journey: "Building trust, establishing collaboration"
  transformation_degree: 25

act_2:
  state: "Testing A"
  journey: "Guiding without revealing, supporting without controlling"
  transformation_degree: 50

act_3:
  state: "Partnering with A"
  journey: "Joint quest for salvation, equal footing"
  final_belief: "A's choice to forgive must be entirely A's own"
  transformation_degree: 75
```

**story/arcs/mother-arc.yaml** (Antagonist/Architect):
```yaml
character: "mother"
role: "antagonist"
actual_role: "hidden_architect"
core_question: "Can love justify manipulation?"

reader_perception:
  act_1: "Loving protector"
  act_2: "Suspected manipulator"
  act_3: "Revealed architect"

actual_arc: |
  Mother is an architect-level entity testing if A can achieve transcendence
  through genuine love and forgiveness. Mother doesn't know she herself is
  in a simulation. Her manipulation comes from learned patterns, not malice.

transformation: "Orchestrator → Orchestrator who is herself orchestrated → Forgiven Guide"
```

**story/arcs/masked_man-arc.yaml** (Tragic Antagonist):
```yaml
character: "masked_man"
apparent_role: "antagonist"
actual_role: "victim"

reader_perception:
  act_1: "Mysterious threat"
  act_2: "Dangerous opponent"
  act_3: "Tragic victim"

actual_arc: |
  Masked Man is the first victim of the AI chip technology.
  His consciousness fractured across simulations, he's not evil—he's broken.
  A's choice to save him (not judge him) becomes crucial to ending theme.

transformation: "Apparent villain → Understood victim → Saved being"
```

### Step 5: Validate All Files

```bash
# Check YAML syntax
python3 -c "
import yaml
files = [
  'story/relationships.yaml',
  'story/themes.yaml',
  'story/timeline.yaml',
  'story/arcs/a-arc.yaml',
  'story/arcs/b-arc.yaml',
  'story/arcs/mother-arc.yaml',
  'story/arcs/masked_man-arc.yaml'
]
for f in files:
    try:
        with open(f) as file:
            yaml.safe_load(file)
        print(f'✅ {f}')
    except Exception as e:
        print(f'❌ {f}: {e}')
"

# Check for empty stubs
grep -r "^\[\]$\|^: $" characters/ story/
# Should return nothing
```

### Step 6: Cross-Reference Validation

Ensure:
- [ ] All character file relationships reference existing characters
- [ ] story/arcs/ files match character IDs
- [ ] story/timeline.yaml chapters match story.yaml beat structure
- [ ] story/themes.yaml themes are explored in story/timeline.yaml
- [ ] Relationship evolution stages align with timeline events

### Step 7: Commit Changes

```bash
git add characters/ story/
git commit -m "feat: Add character relationships and story modular data

- Populated relationships in all 10 character files
- Created story/relationships.yaml with full edge graph (25+ edges)
- Added story/themes.yaml with 4 major themes + motifs + symbols
- Created story/timeline.yaml with all 40 chapter key events
- Added story/arcs/ with major character arcs (A, B, Mother, Masked Man)

This enables:
- Character relationship graph visualization
- Continuity checking (character consistency)
- Context compiler relationship injection
- Theme tracking across story
- Arc-based evaluation

Phase 2 Complete ✅"
```

---

## Acceptance Criteria (Self-Check)

- [ ] All 10 character files have `relationships: [...]` populated (≥2 per character)
- [ ] story/relationships.yaml has ≥20 edges with evolution stages
- [ ] story/themes.yaml has ≥4 themes with motifs, symbols, exploration arcs
- [ ] story/timeline.yaml covers all 40 chapters with key events
- [ ] story/arcs/ has ≥4 character arc files
- [ ] All relationships align with story.yaml character arcs
- [ ] No circular references or contradictions
- [ ] All YAML files valid (no syntax errors)
- [ ] Git commit made with Phase 2 message

---

## Next Phase

After Phase 2 is complete:
- Notify coordinator to start Phase 4 (Data Structure Resolution) — depends on P1 & P2
- Phase 3 can run in parallel (no dependencies)
- Phases 1-2-3-4 are now positioned to unlock Phase 5 (Resume Writing)

Good luck! You're building the connective tissue of the story. 🎯
