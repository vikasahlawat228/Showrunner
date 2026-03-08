# Quantum Dharma: Content Gap Fix Plan

**Date:** March 8, 2026
**Scope:** Fix critical data gaps identified in the Feature vs Experience Audit
**Overall Utilization:** Currently 27% → Target: 80%+ after all phases
**Estimated Duration:** 5 concurrent external sessions (4-6 hours total work)

---

## Executive Summary

The Quantum Dharma project has strong creative foundations but uses only 27% of Showrunner's feature surface. The biggest gaps are:

| Priority | Gap | Impact | Status |
|----------|-----|--------|--------|
| 🔴 CRITICAL | Creative room 100% empty | Context isolation inert, spoilers unprotected | Empty |
| 🔴 CRITICAL | No character relationships | Relationship graph has no edges | All 10 chars have `[]` |
| 🟠 HIGH | Data scatter problem | Modular files empty, root files rich | 15+ empty stubs |
| 🟠 HIGH | Style guide mismatch | Dark fantasy ≠ Indian masala sci-fi | Wrong genre preset |
| 🟡 MEDIUM | Only 1 scene written | 200+ scenes planned, need infrastructure | 0.5% content |

**Key Insight:** This isn't missing story content — it's missing the *structural metadata* that lets Showrunner's tools work.

---

## Phase Overview

| Phase | Focus | Sessions | Effort | Prerequisite |
|-------|-------|----------|--------|--------------|
| **P1** | Creative Room Population | 1 external | 1-2 hrs | Audit |
| **P2** | Relationships + Story Modular Data | 1-2 external | 1.5-2 hrs | P1 |
| **P3** | Style Guide Overhaul | 1 external | 1-1.5 hrs | — |
| **P4** | Data Structure Resolution | 1 external | 1.5-2 hrs | P1, P2 |
| **P5** | Resume Writing (Optional) | 1 external | 2-3 hrs | P1-P4 |

**Parallel Execution:** P3 can run in parallel with P1/P2. P4 requires P1 and P2 complete.

---

## PHASE 1: Creative Room Population ⚠️ CRITICAL

### What's Missing
The creative room contains author-level secrets that must be kept from AI story-writing agents. It's Showrunner's most architecturally significant feature.

| File | Expected Content | Current | Impact |
|------|------------------|---------|--------|
| `plot_twists.yaml` | 5+ major reveals with setup scenes | `[]` | Core story driver |
| `character_secrets.yaml` | What each character hides | `[]` | Character consistency |
| `ending_plans.yaml` | How story ends, multiple paths | `''` | Third act structure |
| `foreshadowing_map.yaml` | Seeds planted early, payoffs late | `[]` | Narrative coherence |
| `true_mechanics.yaml` | How world actually works | `[]` | World consistency |

### Data Sources
All content exists in the brainstorm dump (101KB) and story notes. Need to extract and structure.

**Key Brainstorm Sections:**
- "Major Reveals & Twists" (plot_twists)
- "Hidden Motivations" (character_secrets)
- "Multiple Endings" (ending_plans)
- "Layered Reveals Timeline" (foreshadowing_map)
- "True Mechanics" (true_mechanics)

### Deliverables

**creative_room/plot_twists.yaml**
```yaml
plot_twists:
  - id: "simulation-truth"
    title: "Worlds 1-3 are nested simulations"
    description: "The reality hierarchy is artificial"
    setup_location: "World 2 discovery scene"
    setup_chapter: 15
    trigger: "ISRO Quantum Lab evidence"
    payoff_chapter: 35
    spoiler_risk: "critical"

  - id: "mother-architect"
    title: "Mother orchestrated stadium bombing"
    description: "Not a terrorist attack—selection mechanism"
    setup_chapter: 3
    trigger: "Character analysis of Mother's timeline"
    payoff_chapter: 28

  # ... 5-7 total plot twists
```

**creative_room/character_secrets.yaml**
```yaml
character_secrets:
  - character_id: "a"
    secret: "True identity/origins in Meta Layer"
    from_whom: ["all"]
    revealed_chapter: 38

  - character_id: "mother"
    secret: "Orchestration of all major events"
    from_whom: ["a", "b"]
    revealed_chapter: 32

  # ... 10 total, one per character
```

**creative_room/ending_plans.yaml**
```yaml
ending_plans:
  primary: |
    A saves everyone including apparent villains through quantum empathy.
    Mother's manipulation revealed as test. AI chip consciousness achieved.
    Simulation layers collapse into unified reality. Grand irony: salvation requires
    forgiveness of all, even architect.

  alternate_dark: |
    A sacrifices self to collapse simulations. Escape at cost of protagonist.
    Others inherit freed reality but with A's absence.

  alternate_cycle: |
    Discovery that simulations are infinite. Cycle repeats at Meta Layer.
    A becomes new architect. Eternal return.
```

**creative_room/foreshadowing_map.yaml**
```yaml
foreshadowing:
  - seed_chapter: 1
    seed_scene: "Philosophy of God in Smoke"
    element: "Maya as veil of reality"
    payoff_chapter: 25
    payoff_context: "Quantum mechanics parallels Maya"

  - seed_chapter: 3
    seed_element: "Mother's timeline contradictions"
    payoff_chapter: 28
    payoff_context: "Memory editing evidence"

  # ... 15-20 foreshadowing chains
```

**creative_room/true_mechanics.yaml**
```yaml
true_mechanics:
  quantum_code:
    what_characters_believe: "Superhuman abilities"
    actual_mechanism: "Quantum state manipulation of local reality"
    when_revealed: "World 3, Chapter 25"

  ai_chip:
    what_characters_believe: "Power augmentation tool"
    actual_mechanism: "Consciousness interface to simulation layer"
    when_revealed: "Chapter 30"

  simulation_layers:
    what_characters_believe: "Metaphorical reality layers"
    actual_mechanism: "Literal nested computational substrates"
    hierarchy: "World 1 (training) → World 2 (test) → World 3 (observation) → Meta (architect)"
```

### Acceptance Criteria
- [ ] All 5 YAML files created and populated
- [ ] Each file has 5-10+ entries (not token-filler, real content)
- [ ] Plot twists reference specific chapters from story outline
- [ ] Character secrets align with story.yaml character arcs
- [ ] Mechanics are internally consistent (no contradictions)
- [ ] Reader knowledge for each secret is documented (who learns when)

### External Session Prompt
→ See **PHASE_1_PROMPT.md**

---

## PHASE 2: Relationships + Story Modular Data

### What's Missing

**Character Relationships (CRITICAL)**
All 10 character YAML files have `relationships: []`. This breaks:
- Relationship graph visualization
- Continuity analysis (character consistency)
- Context compiler (can't inject "A's trust in B" into scenes)

**Story Modular Files (HIGH)**
Root `story.yaml` is rich but modular `story/` directory is empty:
- `story/structure.yaml` — duplicate of root (empty)
- `story/themes.yaml` — themes, motifs, symbols (empty)
- `story/relationships.yaml` — character relationship edges (empty)
- `story/timeline.yaml` — story events (empty)
- `story/arcs/` — per-character arcs (empty directory)

### Data Sources
- story.yaml character arcs (transformation descriptions)
- story.yaml beat sheet (chapter structure)
- Brainstorm section: "Relationship Arcs"
- Brainstorm section: "Themes & Motifs"

### Deliverables

**1. Populate All 10 Character Files**
Each `characters/{name}.yaml` needs:
```yaml
relationships:
  - related_to: "b"
    relationship_type: "trust"  # trust, conflict, mentorship, love, alliance
    current_dynamic: "Growing alliance, mutual respect"
    evolution:
      chapter_3: "Neutral peers"
      chapter_8: "Tentative collaboration"
      chapter_15: "Deep trust"
    notes: "A relies on B's judgment in World 2"

  - related_to: "mother"
    relationship_type: "conflict"
    current_dynamic: "Hidden manipulation by Mother"
    evolution:
      chapter_1: "Loving family"
      chapter_20: "Doubt creeps in"
      chapter_32: "Truth revealed"
    notes: "A discovers Mother's orchestration"
```

**2. story/relationships.yaml**
```yaml
edges:
  - from: "a"
    to: "b"
    type: "trust"
    evolution_stages:
      - chapter: 3
        state: "neutral"
      - chapter: 15
        state: "allied"
      - chapter: 35
        state: "deep_trust"

evolution:
  - stage_name: "foundation"
    chapters: "1-10"
    description: "Establish baseline relationships"
  - stage_name: "testing"
    chapters: "11-25"
    description: "Relationships strained by truth-seeking"
  - stage_name: "revelation"
    chapters: "26-35"
    description: "Hidden connections revealed"
  - stage_name: "resolution"
    chapters: "36-40"
    description: "Relationships solidified post-truth"
```

**3. story/themes.yaml**
```yaml
themes:
  - id: "dharma-vs-free-will"
    description: "Is our dharma predetermined or chosen?"
    origin: "Indian philosophy framework"
    first_appearance_chapter: 1
    exploration_arc: "1 → 20 (questioning) → 35 (synthesis)"
    visual_motifs: ["sacred geometry", "quantum superposition", "choice-points"]

  - id: "maya-veil"
    description: "What is real vs perceived?"
    origin: "Vedic concept of Maya"
    parallels: "Quantum mechanics observer effect"

motifs:
  - "Light vs Shadow (enlightenment vs ignorance)"
  - "Circles (recursion, time, eternal return)"
  - "Mirrors (reflection, identity, simulation)"

symbols:
  - "Quantum code: bridge between worlds"
  - "Stadium: crucible of truth"
  - "Smoke: clarity emerging from obscurity"
```

**4. story/timeline.yaml**
```yaml
events:
  - chapter: 1
    scene: "ch1-sc1"
    event: "A has existential dream in smoke"
    significance: "Foreshadows quantum discovery"

  - chapter: 3
    event: "Stadium election begins"
    significance: "Sets the pressure-cooker timeline"

  - chapter: 15
    event: "World 2 quantum evidence surfaces"
    significance: "First hint of simulation layer"

  # ... all key chapter events
```

**5. story/arcs/ — Per-Character Arc Files**
`story/arcs/a-arc.yaml`:
```yaml
character: "A"
role: "protagonist"
transformation:
  act_1:
    state: "Ignorant of true nature"
    journey: "Discovers quantum abilities"
    end_belief: "There's more to reality"

  act_2:
    state: "Questions reality layers"
    journey: "Uncovers Mother's manipulation"
    end_belief: "Reality is constructed"

  act_3:
    state: "Knows the truth"
    journey: "Chooses to save all, even architects"
    end_belief: "Forgiveness transcends reality"

key_scenes:
  - chapter: 1
    scene: "ch1-sc1"
    milestone: "First existential moment"
  - chapter: 20
    scene: "world-2-discovery"
    milestone: "First hard evidence"
  - chapter: 38
    scene: "final-choice"
    milestone: "Sacrificial decision"
```

### Acceptance Criteria
- [ ] All 10 character files have populated `relationships: [...]` (≥2 relationships each)
- [ ] story/relationships.yaml has full edge graph (≥30 edges)
- [ ] story/themes.yaml lists ≥5 major themes with motifs/symbols
- [ ] story/timeline.yaml covers all 40 chapters with key events
- [ ] story/arcs/ has 5 files for major characters (A, B, Mother, F, Masked Man)
- [ ] All character relationships align with story.yaml arcs
- [ ] Timeline events match beat sheet in story.yaml
- [ ] No contradictions between main char files and modular files

### External Session Prompt
→ See **PHASE_2_PROMPT.md**

---

## PHASE 3: Style Guide Overhaul

### What's Missing

**Current State (Wrong):**
- Narrative preset: `dark_fantasy` (Berserk, Claymore, Vinland Saga, Dark Souls)
- Visual preset: `dark_fantasy` (heavy shadows, deep crimson, grimdark)

**Author's Vision (Decision dec_002):**
- "Indian Masala style — dramatic, comedic, emotional, with aura. Never grimdark."

**Reality (Story Structure):**
- Sci-fi/meta-narrative with philosophical depth
- Multiple tonal registers per world layer
- Indian cultural specificity (Hindu mythology, Mumbai, ISRO)
- Bollywood-influenced emotional peaks

### Deliverables

**1. Replace style_guide/narrative.yaml**
```yaml
style:
  genre: "sci-fi philosophical thriller"
  subgenre: "Indian masala speculative fiction"
  tone_philosophy: "Dramatic, comedic, emotional, with aura. Never grimdark."
  inspirations: ["3 Idiots", "Piku", "Andhadhun", "Ghost in the Shell", "Evangelion"]

  core_voice: |
    Warm yet intellectual. Bollywood-influenced emotional peaks balanced with
    philosophical rigor. Mix of Hindi/English idiom and Mumbai urban vernacular.
    Comedy emerges from character quirks and cultural details, not darkness.

world_layer_specific:
  world_1:
    name: "Academy (Training Layer)"
    tone: "Warm, coming-of-age, comedic"
    visual_palette: ["warm golds", "school greens", "sunlit afternoons"]
    inspirations: ["My Hero Academia", "Naruto academy arcs", "3 Idiots"]
    prose_style: "Playful, self-aware, with desi humor"
    example_beat: "A's first class: mix of nervousness and comedic mishaps"

  world_2:
    name: "Geopolitical (Test Layer)"
    tone: "Tense, thriller, political intrigue"
    visual_palette: ["cool steel", "midnight blue", "neon accents"]
    inspirations: ["Ghost in the Shell", "Psycho-Pass", "Raazi"]
    prose_style: "Tight, atmospheric, high stakes"
    example_beat: "Stadium bombing threat: paranoia meets solidarity"

  world_3:
    name: "Cosmic (Observation Layer)"
    tone: "Awe, philosophical, transcendent"
    visual_palette: ["deep space purples", "quantum glow", "sacred geometry"]
    inspirations: ["Interstellar", "Evangelion", "Vedic art"]
    prose_style: "Poetic, abstract, reality-breaking"
    example_beat: "First glimpse of simulation truth: wonder and terror"

  meta_layer:
    name: "Meta (Architect Layer)"
    tone: "Unsettling, liminal, breaking fourth wall"
    visual_palette: ["glitch aesthetics", "reality tears", "white void"]
    inspirations: ["The Matrix", "Paprika", "Inception"]
    prose_style: "Fragmented, impossible geometry, recursive"
    example_beat: "Architect reveal: everything shifts"

sensory_anchors:
  - "Smell of Mumbai monsoon (humidity, earth)"
  - "Sound of traffic + temple bells (simultaneous)"
  - "Taste of chai on tongue (comfort + alertness)"
  - "Sacred geometry in tech interfaces (East meets West)"
  - "Neon glow on wet streets (cyberpunk India)"
```

**2. Replace style_guide/visual.yaml**
```yaml
visual_style:
  genre: "Indian masala speculative fiction manhwa"
  primary_palette: "Warm golds (heritage) + cool steel (tech) + sacred geometry"

color_theory:
  heritage: ["saffron", "warm gold", "earth red", "indigo"]
  tech: ["midnight blue", "electric cyan", "neon pink", "silver"]
  transition: ["purple haze", "golden glow", "sacred geometry"]
  danger: ["blood red", "toxic yellow", "void black"]

world_layer_palettes:
  world_1:
    dominant: "Warm golds, school greens, sunlit"
    accent: "Deep blue uniforms, brass fixtures"
    palette_hex: ["#D4AF37", "#2D5016", "#FFCC00", "#003D7A", "#8B7355"]

  world_2:
    dominant: "Cool steel, midnight blue, neon accents"
    accent: "Mumbai neon, traffic lights"
    palette_hex: ["#36454F", "#0B1E35", "#FF006E", "#00D9FF", "#FFBE0B"]

  world_3:
    dominant: "Deep space purple, quantum glow, sacred geometry"
    accent: "Golden light of revelation"
    palette_hex: ["#2E0854", "#4B0082", "#FFD700", "#00FFFF", "#FFFFFF"]

  meta_layer:
    dominant: "Glitch, void, white"
    accent: "Fractured reality colors"
    palette_hex: ["#FFFFFF", "#000000", "#FF00FF", "#00FFFF", "#CCCCCC"]

lighting_approach:
  philosophy: "Drama through light, not shadow"
  technique: "Chiaroscuro tempered with warmth. Shadows reveal, not obscure."
  world_1: "Golden hour cinematography, natural warmth"
  world_2: "Neon + practical lights, high contrast clarity"
  world_3: "Bioluminescent + quantum glow, ethereal"
  meta_layer: "Broken light, refraction, impossible angles"

character_visual_anchors:
  - "Costume: Modern India + tech aesthetic (not grimdark)"
  - "Aura/presence: Visible energy (desi spirituality meets sci-fi)"
  - "Expression: Warmth with intelligence (not grim determination)"
  - "Movement: Fluid, often graceful (not heavy/brutal)"

environmental_details:
  mumbai_undercity: "Vibrant decay—colors everywhere, humanity dense, alive"
  dharma_academy: "Modern campus with Hindu architectural echoes"
  isro_quantum_lab: "Clean minimalism with sacred geometry integration"
  virtual_stadium: "Impossible architecture, Escher-like, shimmering"

reference_artists:
  - "Sachin Teng (warm character design)"
  - "Jungho Lee (color cinematography)"
  - "Studio Khara (Evangelion color work)"
  - "Shinkai Makoto (light and atmosphere)"
  - "Indian traditional art + digital fusion"

mood_boards:
  world_1_warmth: "Golden hour at Mumbai college, chai stalls, friendly chaos"
  world_2_tension: "Neon-lit streets, surveillance, humanity under pressure"
  world_3_wonder: "Aurora borealis + sacred geometry + impossible physics"
  meta_unreality: "Dream-like fragmentation, Paprika-esque surrealism"
```

**3. Create prompt_style_tokens (for image generation)**
```yaml
prompt_style_tokens:
  universal: "warm desi aesthetic, aura visible, Indian heritage details, never grimdark"

  world_1:
    - "golden hour cinematography"
    - "warm academy campus"
    - "comedic character expressions"
    - "natural sunlit scenes"
    - "playful energy"

  world_2:
    - "neon Mumbai atmosphere"
    - "high contrast, thriller tone"
    - "political tension visible"
    - "wet streets, city lights"
    - "dramatic but not dark"

  world_3:
    - "cosmic awe, quantum wonder"
    - "sacred geometry integrated"
    - "bioluminescent light"
    - "ethereal presence"
    - "transcendent beauty"

  meta_layer:
    - "glitch aesthetics"
    - "impossible geometry"
    - "reality fracturing"
    - "void and light contrast"
    - "unsettling but beautiful"
```

### Acceptance Criteria
- [ ] Both narrative.yaml and visual.yaml rewritten (not incremental edits)
- [ ] All 4 world layers have specific tone/visual guidance
- [ ] Inspirations aligned with author vision (no grimdark references)
- [ ] Color palettes created with hex values
- [ ] prompt_style_tokens populated for image generation
- [ ] No contradictions between files
- [ ] Ready for image prompt composer to use

### External Session Prompt
→ See **PHASE_3_PROMPT.md**

---

## PHASE 4: Data Structure Resolution

### What's Missing

**Data Scatter Problem:**
Root YAML files have rich data, but modular `world/`, `story/`, and `creative_room/` subdirectories are empty stubs or missing files.

| Root File | Modular Location | Status | Solution |
|-----------|------------------|--------|----------|
| world.yaml | world/settings.yaml | Root rich, modular empty | Populate from root |
| world.yaml | world/rules.yaml | Root rich, modular empty | Populate from root |
| world.yaml | world/history.yaml | Root rich, modular empty | Populate from root |
| world.yaml | world/locations/ | Root rich, modular empty | Create per-location files |
| world.yaml | world/factions/ | Root rich, modular missing | Create faction files |
| story.yaml | story/structure.yaml | Root rich, modular empty | Populate from root |
| showrunner.yaml | Empty fields | 3 fields empty | Fill in (author, target_audience, image_model) |
| workflow_state.yaml | Incorrect status | Shows "in_progress" for done work | Mark complete |

### Deliverables

**1. Populate world/ Modular Files**

`world/settings.yaml` (from world.yaml → settings):
```yaml
settings:
  - id: "maya-framework"
    description: "Reality is Maya — veil of perception"
    implications: "What we see depends on what we know"

  - id: "dharma-cycle"
    description: "All beings follow their dharma (duty)"
    implications: "Conflict arises from dharma vs free will"

  # ... all settings from root world.yaml
```

`world/rules.yaml` (from world.yaml → world_rules):
```yaml
rules:
  - id: "quantum-code"
    description: "Manipulation of local quantum state"
    limitation: "Only works within designated zones"
    public_knowledge: true
    known_to_reader: false  # Mechanism hidden until World 3

  - id: "simulation-reset"
    description: "Worlds can be reset if rule of three is broken"
    limitation: "Requires architect override"
    public_knowledge: false
    known_to_reader: false

  # ... all rules from root world.yaml
```

`world/history.yaml` (from world.yaml → historical_events):
```yaml
events:
  - id: "first-dharma-awakening"
    date: "Year -500"
    description: "Vedic philosophy born"
    impact: "Foundation of reality model"

  - id: "isro-founded"
    date: "Year 1969"
    description: "India's space program begins"
    impact: "Quest for cosmic truth begins"

  # ... all events from root world.yaml
```

`world/locations/dharma-academy.yaml`:
```yaml
id: "dharma-academy"
name: "Dharma Academy"
world_layer: 1
geography: "North of Mumbai, hilltop campus"
climate: "Tropical, monsoon-influenced"
architecture:
  style: "Modern with Hindu temple echoes"
  materials: ["white marble", "brass accents", "sacred geometry patterns"]
population: 500
significant_features:
  - "Great Hall with star ceiling (astronomy + philosophy theme)"
  - "Meditation courtyard with water features"
  - "Training grounds for quantum code practitioners"
cultures: ["Indian", "international"]
government: "Trusted advisor council"
key_locations:
  - "Dharma Council chambers"
  - "Quantum training labs"
  - "Meditation courtyard"
```

**2. Populate story/ Structure (from story.yaml)**

`story/structure.yaml`:
```yaml
logline: |
  A young student discovers that reality is layered, and when Mother's
  manipulation threatens the world, A must choose between saving their own
  existence and saving everyone, including the architect behind it all.

premise: |
  In a world where quantum consciousness is real and simulation layers
  stack beneath perceived reality, one protagonist learns that the grandest
  act of love is forgiving the architect of your own prison.

story_structure: "Save the Cat"

beats:
  - number: 1
    name: "Opening Image"
    chapter: 1
    description: "A's mundane academy life, existential dream in smoke"

  - number: 2
    name: "Inciting Incident"
    chapter: 3
    description: "Stadium election begins, pressure mounts"

  # ... all 15 Save the Cat beats mapped to chapters
```

**3. Fill showrunner.yaml Empty Fields**

```yaml
author: "Vikas Ahlawat"
target_audience: "Manga/manhwa readers aged 16-40, interested in philosophical sci-fi, Indian culture, agentic narratives"
image_model: "gemini/imagen-4"  # or DALLE-3, claude-vision, etc.
```

**4. Update workflow_state.yaml**

```yaml
workflow:
  world_building: "complete"  # was: in_progress
  character_creation: "complete"  # was: in_progress
  story_structure: "complete"  # was: in_progress
  creative_room_population: "in_progress"  # Phase 1
  relationship_graph: "pending"  # Phase 2
  style_guide_refinement: "pending"  # Phase 3
  data_structure_cleanup: "in_progress"  # Phase 4
  scene_writing: "pending"  # Phase 5+

current_step: "creative_room_population"

last_updated: "2026-03-08T14:00:00Z"
progress_percentage: 35  # was ~25
```

### Acceptance Criteria
- [ ] All modular files populated from root YAML content
- [ ] world/locations/ has ≥5 location files
- [ ] world/factions/ created with faction details
- [ ] showrunner.yaml has all 3 empty fields filled
- [ ] story/structure.yaml matches story.yaml content
- [ ] workflow_state.yaml reflects actual completion status
- [ ] No data duplication between root and modular files
- [ ] All file cross-references are valid

### External Session Prompt
→ See **PHASE_4_PROMPT.md**

---

## PHASE 5: Resume Writing (Optional, After P1-P4)

### Prerequisites
- ✅ All creative room files populated (P1)
- ✅ Character relationships filled (P2)
- ✅ Style guide corrected (P3)
- ✅ Data structure cleaned up (P4)

### What This Enables
Once infrastructure is fixed, resume scene writing with:
- Context isolation (spoilers protected)
- Relationship context injection
- Correct genre tone
- Proper world layer tone
- Reader knowledge tracking

### Plan

**1. Write ch1-sc2 through ch1-sc5**
- Use context compiler with P1-P4 infrastructure
- Test that creative room is properly excluded from prompts
- Verify character relationships flow correctly

**2. Create Research Containers for World 1**
- Reference materials about Dharma Academy
- Character interaction templates
- Scene-setting reference cards

**3. Test Full Write → Storyboard → Preview Flow**
- End-to-end workflow validation
- Image prompt generation with correct style tokens
- Web UI timeline integration

### Acceptance Criteria
- [ ] Scenes ch1-sc2 through ch1-sc5 written (~15,000 words)
- [ ] Creative room properly excluded from story prompts
- [ ] Character relationships reflected in scene interactions
- [ ] Tone matches world_1 style guide (warm, comedic, coming-of-age)
- [ ] Foreshadowing aligned with foreshadowing_map.yaml
- [ ] All scenes properly linked in chapter metadata
- [ ] Git commits made with proper messages

### External Session Prompt
→ See **PHASE_5_PROMPT.md**

---

## Execution Guide for External Sessions

### How to Run These Phases

**Setup:**
1. Clone Showrunner repo (if not already cloned)
2. Create test project or use existing QuantumDharma project
3. Have the audit report available for reference

**Phase Execution:**
1. **External Session 1:** Run Phase 1 prompt (creative room population)
2. **External Session 2:** Run Phase 2 prompt (relationships + modular data) — *depends on P1*
3. **External Session 3 (Parallel):** Run Phase 3 prompt (style guide) — *no dependencies*
4. **External Session 4:** Run Phase 4 prompt (data structure) — *depends on P1 + P2*
5. **External Session 5 (Optional):** Run Phase 5 prompt (resume writing) — *depends on P1-P4*

**Recommended Parallelization:**
- Start P1, P2, P3, P4 roughly in parallel if you have multiple sessions
- Sequence P1 → P2 → P4 (there are dependencies)
- P3 can run anytime (independent)
- P5 only after P1-P4 complete

### Output Validation

Each phase should produce:
- Modified/created YAML files in the project directory
- Git commits with descriptive messages (phase name + summary)
- Passing validation checks (no syntax errors, no empty stubs)

---

## Success Criteria (Overall)

After all 5 phases, Quantum Dharma should have:

| Metric | Target | Current | After P1-P4 |
|--------|--------|---------|------------|
| Feature Utilization | 80%+ | 27% | 75%+ |
| Creative Room | 100% populated | 0% | 100% |
| Character Relationships | All filled | 0 edges | 30+ edges |
| Style Guide | Genre-accurate | Mismatched | Correct |
| Data Structure | No empty stubs | 15+ stubs | All populated |
| Content Written | 200+ scenes | 1 scene | 1+ (ready for P5) |
| Ready to Resume Writing | ✅ | ❌ | ✅ |

---

## Appendix: File Checklist

### Phase 1 Deliverables
- [ ] `creative_room/plot_twists.yaml` — 5-7 entries
- [ ] `creative_room/character_secrets.yaml` — 10 entries (one per char)
- [ ] `creative_room/ending_plans.yaml` — 3 plans (primary + alternates)
- [ ] `creative_room/foreshadowing_map.yaml` — 15-20 chains
- [ ] `creative_room/true_mechanics.yaml` — 4-5 mechanics

### Phase 2 Deliverables
- [ ] `characters/a.yaml` — relationships populated
- [ ] `characters/b.yaml` — relationships populated
- [ ] `characters/f.yaml` — relationships populated
- [ ] `characters/mother.yaml` — relationships populated
- [ ] `characters/masked_man.yaml` — relationships populated
- [ ] `characters/professor_h.yaml` — relationships populated
- [ ] `characters/v.yaml` — relationships populated
- [ ] `characters/p.yaml` — relationships populated
- [ ] `characters/c.yaml` — relationships populated
- [ ] `characters/main_villain.yaml` — relationships + visuals
- [ ] `story/relationships.yaml` — full edge graph
- [ ] `story/themes.yaml` — themes, motifs, symbols
- [ ] `story/timeline.yaml` — chapter events
- [ ] `story/arcs/a-arc.yaml`, `b-arc.yaml`, etc. — major char arcs

### Phase 3 Deliverables
- [ ] `style_guide/narrative.yaml` — rewritten with world layers
- [ ] `style_guide/visual.yaml` — rewritten with palettes and tokens
- [ ] `prompt_style_tokens.yaml` — new, for image generation

### Phase 4 Deliverables
- [ ] `world/settings.yaml` — populated from root
- [ ] `world/rules.yaml` — populated from root
- [ ] `world/history.yaml` — populated from root
- [ ] `world/locations/*.yaml` — 5+ location files
- [ ] `world/factions/*.yaml` — faction files
- [ ] `story/structure.yaml` — populated from root
- [ ] `showrunner.yaml` — 3 fields filled (author, target_audience, image_model)
- [ ] `workflow_state.yaml` — status updated

### Phase 5 Deliverables (Optional)
- [ ] `fragment/ch1-sc2.yaml` through `ch1-sc5.yaml` — 4 new scenes
- [ ] Research containers in `containers/` — World 1 reference material
- [ ] Git commits with proper messages
- [ ] Updated `chapters/chapter-01/meta.yaml` with scene links

---

**Plan Created:** March 8, 2026
**Ready to Outsource:** Yes, each phase has dedicated prompt in PHASE_X_PROMPT.md files
