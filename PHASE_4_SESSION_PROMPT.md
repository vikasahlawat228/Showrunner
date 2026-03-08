# PHASE 4 External Session Prompt: Data Structure Resolution

**Duration:** 1.5-2 hours
**Difficulty:** Medium (data extraction and file organization)
**Prerequisite:** Phase 1 (creative room) and Phase 2 (relationships) complete
**Goal:** Resolve data scatter problem and fill empty stub files

---

## Context

**The Data Scatter Problem:**
Rich data lives in root YAML files, but modular subdirectory files are empty stubs. This breaks API queries and modular workflows.

| Root File | Modular Location | Status | Solution |
|-----------|------------------|--------|----------|
| world.yaml | world/settings.yaml | Empty stub | Extract settings, populate |
| world.yaml | world/rules.yaml | Empty stub | Extract world_rules, populate |
| world.yaml | world/history.yaml | Empty stub | Extract historical_events, populate |
| story.yaml | story/structure.yaml | Empty stub | Extract core structure, populate |
| showrunner.yaml | Multiple fields | 3 empty | Fill author, target_audience, image_model |
| workflow_state.yaml | Current status | Outdated | Update to reflect actual progress |

**Your Job:** Extract data from root files and populate modular files.

---

## Step 1: Extract From world.yaml → world/ Subdirectory

### 1a. Create world/settings.yaml

Read the `settings` field from root `world.yaml`.

```bash
grep -A 50 "^settings:" world.yaml | head -60
```

Create `world/settings.yaml`:

```yaml
# World Settings - Extracted from world.yaml
# These are fundamental constants of the world

settings:
  - id: "maya-framework"
    name: "Maya Framework"
    description: "Reality is Maya—a veil of perception. What we perceive depends on our consciousness level."
    implications: "Each world layer represents a different 'veil' level"
    philosophical_origin: "Vedantic concept of Maya"
    in_story_impact: "Characters gradually lift the veil through World layers"

  - id: "dharma-cycle"
    name: "Dharma Cycle"
    description: "All beings follow their dharma (essential nature/duty)"
    implications: "Conflict arises when dharma vs free will tension appears"
    philosophical_origin: "Bhagavad Gita teaching"
    in_story_impact: "A's ultimate choice is aligned with dharma"

  - id: "quantum-consciousness"
    name: "Quantum Consciousness"
    description: "Consciousness directly affects quantum states; observer = creator"
    implications: "Individuals with expanded consciousness can manipulate local reality"
    scientific_basis: "Quantum mechanics observer effect + consciousness studies"
    in_story_impact: "Quantum code ability is consciousness-state interface"

  # ... add all settings from root world.yaml
```

**Extraction Command:**
```bash
python3 << 'EOF'
import yaml

with open('world.yaml') as f:
    world_data = yaml.safe_load(f)

settings = world_data.get('settings', [])
if not settings:
    print("⚠️  No settings found in world.yaml")
else:
    with open('world/settings.yaml', 'w') as f:
        yaml.dump({'settings': settings}, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Extracted {len(settings)} settings to world/settings.yaml")
EOF
```

### 1b. Create world/rules.yaml

Extract `world_rules` from root `world.yaml`:

```yaml
# World Rules - Extracted from world.yaml
# Laws of reality in the world

rules:
  - id: "quantum-code"
    name: "Quantum Code"
    description: "Direct manipulation of local quantum states through concentrated consciousness"
    limitation: "Only works within designated simulation zones; requires dharma alignment"
    discovery_chapter: 5
    known_to_readers: false
    actual_mechanism: "Interface between consciousness and quantum substrate"
    spoiler_risk: "medium"

  - id: "rule-of-three"
    name: "Rule of Three"
    description: "A character can exist in maximum 3 reality layers before identity fragmentation"
    limitation: "Crossing layers requires quantum equilibrium"
    discovery_chapter: 25
    known_to_readers: false
    spoiler_risk: "high"

  # ... add all world_rules from root world.yaml
```

**Extraction Command:**
```bash
python3 << 'EOF'
import yaml

with open('world.yaml') as f:
    world_data = yaml.safe_load(f)

rules = world_data.get('world_rules', [])
if not rules:
    print("⚠️  No world_rules found in world.yaml")
else:
    with open('world/rules.yaml', 'w') as f:
        yaml.dump({'rules': rules}, f, default_flow_style=False, sort_keys=False)
    print(f"✅ Extracted {len(rules)} rules to world/rules.yaml")
EOF
```

### 1c. Create world/history.yaml

Extract `historical_events` from root `world.yaml`:

```yaml
# World History - Extracted from world.yaml
# Timeline of significant events that shaped the world

events:
  - id: "vedantic-awakening"
    date: "Year -500"
    event_name: "The Vedantic Awakening"
    description: "Development of Vedantic philosophy emphasizing Maya and Brahman"
    significance: "Foundation of philosophical framework underlying the world"
    cultural_impact: "Spread across Indian civilization"

  - id: "isro-founded"
    date: "Year 1969"
    event_name: "India's Space Program (ISRO) Founded"
    description: "India embarks on quest for cosmic truth through space exploration"
    significance: "Sets up ISRO Quantum Lab storyline"
    cultural_impact: "India pursues knowledge of the cosmos"

  - id: "dharma-academy-founded"
    date: "Year 2010"
    event_name: "Dharma Academy Founded"
    description: "Establishment of the Academy to train quantum consciousness practitioners"
    significance: "Creates World 1 setting"
    historical_context: "Following secret discoveries about simulation layers"

  # ... add all historical_events from root world.yaml
```

### 1d. Create world/locations/ Files

For each location in world.yaml, create a separate file:

**world/locations/dharma-academy.yaml**
```yaml
id: "dharma-academy"
name: "Dharma Academy"
world_layer: 1
geography: "Hilltop campus north of Mumbai"
climate: "Tropical monsoon"
architecture:
  style: "Modern with Hindu architectural echoes"
  materials: ["white marble", "brass", "sacred geometry patterns"]
population: 500
government: "Trusted advisor council"
culture: ["Indian", "international", "philosophical"]
key_facilities:
  - "Great Hall with star ceiling"
  - "Meditation courtyard"
  - "Quantum training grounds"
  - "Philosophy library"
significant_events: ["Opening ceremony", "Annual selection ceremony"]
```

Repeat for all 5 locations:
- dharma-academy.yaml
- mumbai-undercity.yaml
- isro-quantum-lab.yaml
- virtual-stadium.yaml
- void-between.yaml

### 1e. Create world/factions/ (if needed)

If world.yaml has faction data, create `world/factions/` directory with one file per faction:

**world/factions/dharma-council.yaml**
```yaml
id: "dharma-council"
name: "Dharma Council"
location: "Dharma Academy"
leadership: ["Professor H"]
goals: ["Preserve knowledge", "Guide consciousness evolution"]
methods: ["Teaching", "Mentorship", "Controlled revelation"]
```

---

## Step 2: Extract From story.yaml → story/ Subdirectory

### 2a. Create story/structure.yaml

Extract core story structure from root `story.yaml`:

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
word_count_target: 150000
estimated_panels: 800
target_chapters: 40

act_breakdown:
  act_1:
    chapters: "1-13"
    focus: "Academy, introduction to quantum powers"
    tone: "Warm, coming-of-age, philosophical"

  act_2:
    chapters: "14-27"
    focus: "World 2 geopolitical thriller, simulation hints"
    tone: "Tense, investigative, reality-questioning"

  act_3:
    chapters: "28-40"
    focus: "Cosmic revelation, forgiveness choice"
    tone: "Transcendent, existential, redemptive"

beats:
  # Extract all Save the Cat beats from story.yaml
  - number: 1
    name: "Opening Image"
    chapter: 1
    description: "A's mundane academy life contrasts with existential dream in smoke"

  - number: 2
    name: "Inciting Incident"
    chapter: 3
    description: "Stadium election begins; external pressure introduced"

  # ... continue for all 15 beats
```

**Extraction Command:**
```bash
python3 << 'EOF'
import yaml

with open('story.yaml') as f:
    story_data = yaml.safe_load(f)

structure = {
    'logline': story_data.get('logline', ''),
    'premise': story_data.get('premise', ''),
    'story_structure': story_data.get('story_structure', ''),
    'beats': story_data.get('beats', []),
}

with open('story/structure.yaml', 'w') as f:
    yaml.dump(structure, f, default_flow_style=False, sort_keys=False)
print("✅ Extracted story structure to story/structure.yaml")
EOF
```

---

## Step 3: Fill showrunner.yaml Empty Fields

### 3a. Edit showrunner.yaml

Open `showrunner.yaml` and fill in these three fields:

```yaml
# Current:
author:              # EMPTY
target_audience:     # EMPTY
image_model:         # EMPTY

# Fill with:
author: "Vikas Ahlawat"
target_audience: "Manga/manhwa readers aged 16-40 interested in philosophical sci-fi, Indian culture, agentic storytelling"
image_model: "gemini/imagen-4"
```

**Edit Command:**
```bash
# Replace empty fields
sed -i '' 's/^author:$/author: "Vikas Ahlawat"/g' showrunner.yaml
sed -i '' 's/^target_audience:$/target_audience: "Manga\/manhwa readers aged 16-40, philosophical sci-fi, Indian culture"/g' showrunner.yaml
sed -i '' 's/^image_model:$/image_model: "gemini\/imagen-4"/g' showrunner.yaml

# Verify
grep -A 1 "author:\|target_audience:\|image_model:" showrunner.yaml
```

---

## Step 4: Update workflow_state.yaml

### Current State (Outdated):
```yaml
current_step: story_structure
world_building: in_progress     # Actually complete!
character_creation: in_progress # Actually complete!
story_structure: in_progress    # Actually complete!
```

### Update to Actual Progress:
```yaml
workflow:
  world_building: "complete"
  character_creation: "complete"
  story_structure: "complete"
  creative_room_population: "in_progress"  # Phase 1
  relationship_graph: "complete"           # Phase 2
  style_guide_refinement: "complete"       # Phase 3
  data_structure_cleanup: "in_progress"    # Phase 4 (this phase)
  scene_writing: "pending"
  screenplay_writing: "pending"
  panel_division: "pending"
  image_prompt_generation: "pending"

current_step: "data_structure_cleanup"
progress_percentage: 40  # was ~25, now 35-40
last_updated: "2026-03-08T00:00:00Z"

next_milestone: "Resume writing with proper context isolation"
```

---

## Step 5: Validate All Changes

```bash
# Check YAML syntax for all files
python3 << 'EOF'
import yaml
import os

files_to_check = [
    'showrunner.yaml',
    'world/settings.yaml',
    'world/rules.yaml',
    'world/history.yaml',
    'story/structure.yaml',
    'workflow_state.yaml'
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        try:
            with open(filepath) as f:
                yaml.safe_load(f)
            print(f'✅ {filepath} - valid YAML')
        except Exception as e:
            print(f'❌ {filepath}: {e}')
    else:
        print(f'⚠️  {filepath} - not found')
EOF

# Check for remaining empty stubs
echo "Checking for empty stubs..."
grep -r "^\[\]$\|^: $\|^null$" world/ story/ showrunner.yaml 2>/dev/null || echo "✅ No empty stubs found"
```

### Cross-Reference Validation

```bash
# Check that story/structure.yaml chapters match story.yaml
echo "Validating chapter references..."
python3 << 'EOF'
import yaml

with open('story.yaml') as f:
    story_root = yaml.safe_load(f)

with open('story/structure.yaml') as f:
    story_modular = yaml.safe_load(f)

root_beats = {b.get('chapter') for b in story_root.get('beats', [])}
modular_beats = {b.get('chapter') for b in story_modular.get('beats', [])}

if root_beats == modular_beats:
    print("✅ Beat chapters match between story.yaml and story/structure.yaml")
else:
    print("⚠️  Beat chapters differ")
    print(f"   Root: {sorted(root_beats)}")
    print(f"   Modular: {sorted(modular_beats)}")
EOF
```

---

## Step 6: Commit Changes

```bash
git add showrunner.yaml workflow_state.yaml world/ story/
git commit -m "fix: Resolve data structure scatter problem

Extracted from root YAML files to modular subdirectories:
- world/settings.yaml: Extracted from world.yaml → settings
- world/rules.yaml: Extracted from world.yaml → world_rules
- world/history.yaml: Extracted from world.yaml → historical_events
- world/locations/*.yaml: 5 location files from world.yaml
- story/structure.yaml: Extracted from story.yaml core structure

Populated empty fields in showrunner.yaml:
- author: 'Vikas Ahlawat'
- target_audience: 'Manga readers aged 16-40, philosophical sci-fi'
- image_model: 'gemini/imagen-4'

Updated workflow_state.yaml:
- Marked world_building, character_creation, story_structure as complete
- Updated current_step to data_structure_cleanup
- Progress: 25% → 40%

Impact:
- APIs can now query world/settings, world/rules, etc.
- No more empty stub files
- Modular tools can find context in subdirectories
- Context compiler has data to work with
- Project metadata is complete

Phase 4 Complete ✅"
```

---

## Step 7: Verify Completeness

After commit, run this checklist:

```bash
# Files that should exist and NOT be empty:
ls -lah world/settings.yaml world/rules.yaml world/history.yaml
ls -lah story/structure.yaml story/relationships.yaml story/themes.yaml
ls -lah story/timeline.yaml

# Check file sizes (should all be > 1KB, not empty stubs)
du -h world/*.yaml story/*.yaml

# Verify all 10 character locations exist
ls -1 characters/ | wc -l  # Should be 10
```

---

## Acceptance Criteria (Self-Check)

- [ ] world/settings.yaml created and populated (≥3 settings)
- [ ] world/rules.yaml created and populated (≥3 rules)
- [ ] world/history.yaml created and populated (≥5 events)
- [ ] world/locations/ directory has 5 location files
- [ ] world/factions/ directory has faction files (if applicable)
- [ ] story/structure.yaml created and populated
- [ ] showrunner.yaml author field filled
- [ ] showrunner.yaml target_audience field filled
- [ ] showrunner.yaml image_model field filled
- [ ] workflow_state.yaml updated to reflect actual progress (current_step, progress_percentage)
- [ ] All YAML files are valid (no syntax errors)
- [ ] All previous phases' files still intact (story/relationships.yaml, story/themes.yaml, etc.)
- [ ] Git commit made with descriptive Phase 4 message

---

## What This Unlocks

Once Phase 4 is complete:
- ✅ Context compiler can query world/settings, world/rules, etc.
- ✅ Web API endpoints for /world/settings, /story/structure work
- ✅ No more empty stub files blocking workflows
- ✅ Modular architecture now functional
- ✅ All phases 1-4 infrastructure in place
- ✅ Ready for Phase 5 (resume writing)

---

## Troubleshooting

### Problem: Can't find field in root YAML
**Solution:** Use grep to locate:
```bash
grep -n "settings:\|world_rules:\|historical_events:" world.yaml
```

### Problem: YAML extraction commands fail
**Solution:** Ensure Python YAML module is installed:
```bash
pip install pyyaml
```

### Problem: Some modular files still empty
**Solution:** Double-check extraction worked:
```bash
wc -l world/settings.yaml  # Should be 20+ lines, not 2-3
```

---

## What's Next?

After Phase 4 completes:
- **All infrastructure complete** (Phases 1-4 done)
- **Ready for Phase 5** (Resume Writing)
- **Optional:** Phases 1-4 can be validated by running test scene write

Great work! You've built the scaffolding. 🔧
