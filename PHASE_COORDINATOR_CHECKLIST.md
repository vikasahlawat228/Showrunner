# Quantum Dharma Phase Coordinator Checklist

**Purpose:** Track execution of all 5 phases by external sessions
**Start Date:** March 8, 2026
**Coordinator:** [Your name]

---

## Pre-Launch Setup ✅

Before starting any external sessions:

- [ ] **Project backup created**
  ```bash
  cd /path/to/QuantumDharma
  git checkout -b backup-before-phases
  git push -u origin backup-before-phases
  git checkout main
  ```

- [ ] **Directories prepared**
  ```bash
  mkdir -p creative_room/
  mkdir -p story/arcs/
  mkdir -p world/locations/
  mkdir -p world/factions/
  ```

- [ ] **Git status verified**
  ```bash
  git status  # Should show "(clean)"
  ```

- [ ] **All 5 phase prompts reviewed**
  - [ ] PHASE_1_SESSION_PROMPT.md
  - [ ] PHASE_2_SESSION_PROMPT.md
  - [ ] PHASE_3_SESSION_PROMPT.md
  - [ ] PHASE_4_SESSION_PROMPT.md
  - [ ] PHASE_5_SESSION_PROMPT.md

- [ ] **PHASE_IMPLEMENTATION_REVIEW.md read** (this document explains the issues and recommendations)

---

## Phase Execution Timeline

### PHASE 1: Creative Room Population

**Status:** ⬜ Not started | 🔵 In Progress | ✅ Complete

**Start Date:** _____________
**End Date:** _____________
**Session ID:** _____________

**Checklist:**
- [ ] Assigned to external session
- [ ] Prompt copied: PHASE_1_SESSION_PROMPT.md
- [ ] Session confirmed receipt
- [ ] Session working on steps 1-7
- [ ] Session completed all 5 YAML files:
  - [ ] creative_room/plot_twists.yaml (5-7 entries)
  - [ ] creative_room/character_secrets.yaml (10 entries, one per char)
  - [ ] creative_room/ending_plans.yaml (primary + alternates)
  - [ ] creative_room/foreshadowing_map.yaml (15-20 chains)
  - [ ] creative_room/true_mechanics.yaml (4-5 mechanics)
- [ ] YAML validation passed (no syntax errors)
- [ ] No empty stubs remain
- [ ] Git commit made with Phase 1 message
- [ ] Session confirmed: "Phase 1 Complete ✅"

**Notes:**
```

```

**Issues Encountered:**
```

```

**Blockers:**
```

```

---

### PHASE 2: Relationships & Story Modular Data

**Status:** ⬜ Not started | 🔵 In Progress | ✅ Complete

**Start Date:** _____________
**End Date:** _____________
**Session ID:** _____________

**Prerequisites:**
- [x] Phase 1 complete

**Checklist:**
- [ ] Assigned to external session
- [ ] Prompt copied: PHASE_2_SESSION_PROMPT.md
- [ ] Session confirmed receipt
- [ ] Relationships populated in all 10 character files:
  - [ ] characters/a.yaml (≥2 relationships)
  - [ ] characters/b.yaml (≥2 relationships)
  - [ ] characters/f.yaml (≥2 relationships)
  - [ ] characters/mother.yaml (≥2 relationships)
  - [ ] characters/masked_man.yaml (≥2 relationships)
  - [ ] characters/professor_h.yaml (≥2 relationships)
  - [ ] characters/v.yaml (≥2 relationships)
  - [ ] characters/p.yaml (≥2 relationships)
  - [ ] characters/c.yaml (≥2 relationships)
  - [ ] characters/main_villain.yaml (≥2 relationships + visuals)
- [ ] Story modular files created:
  - [ ] story/relationships.yaml (≥20 edges, evolution stages)
  - [ ] story/themes.yaml (≥4 themes with motifs/symbols)
  - [ ] story/timeline.yaml (all 40 chapters with key events)
  - [ ] story/arcs/*.yaml (5 major character arcs)
- [ ] Cross-reference validation passed
- [ ] YAML validation passed
- [ ] Git commit made with Phase 2 message
- [ ] Session confirmed: "Phase 2 Complete ✅"

**Notes:**
```

```

**Issues Encountered:**
```

```

**Blockers:**
```

```

---

### PHASE 3: Style Guide Overhaul

**Status:** ⬜ Not started | 🔵 In Progress | ✅ Complete

**Start Date:** _____________
**End Date:** _____________
**Session ID:** _____________

**Prerequisites:**
- None (can run in parallel with P1-P2)

**Checklist:**
- [ ] Assigned to external session
- [ ] Prompt copied: PHASE_3_SESSION_PROMPT.md
- [ ] Session confirmed receipt
- [ ] Backup of existing style_guide files created
- [ ] style_guide/narrative.yaml rewritten:
  - [ ] Dark fantasy references removed
  - [ ] Indian masala sci-fi aesthetic applied
  - [ ] All 4 world layers have specific guidance
  - [ ] Sensory anchors included
- [ ] style_guide/visual.yaml rewritten:
  - [ ] Dark fantasy references removed
  - [ ] Color palettes created with hex codes
  - [ ] World-layer specific visuals defined
  - [ ] Reference artists listed
- [ ] prompt_style_tokens.yaml created:
  - [ ] Universal tokens defined
  - [ ] World-specific tokens for all 4 layers
  - [ ] Negative tokens listed (avoid)
- [ ] "Never grimdark" philosophy confirmed
- [ ] YAML validation passed
- [ ] "dark_fantasy" and "grimdark" grep check returns nothing
- [ ] Git commit made with Phase 3 message
- [ ] Session confirmed: "Phase 3 Complete ✅"

**Notes:**
```

```

**Issues Encountered:**
```

```

**Blockers:**
```

```

---

### PHASE 4: Data Structure Resolution

**Status:** ⬜ Not started | 🔵 In Progress | ✅ Complete

**Start Date:** _____________
**End Date:** _____________
**Session ID:** _____________

**Prerequisites:**
- [x] Phase 1 complete
- [x] Phase 2 complete

**Checklist:**
- [ ] Assigned to external session
- [ ] Prompt copied: PHASE_4_SESSION_PROMPT.md
- [ ] Session confirmed receipt
- [ ] Data extracted from root → modular files:
  - [ ] world/settings.yaml (≥3 settings)
  - [ ] world/rules.yaml (≥3 rules)
  - [ ] world/history.yaml (≥5 events)
  - [ ] world/locations/ directory populated (5 location files)
  - [ ] world/factions/ directory populated (if applicable)
  - [ ] story/structure.yaml created
- [ ] showrunner.yaml fields filled:
  - [ ] author: "Vikas Ahlawat" ✓
  - [ ] target_audience: "..." ✓
  - [ ] image_model: "gemini/imagen-4" ✓
- [ ] workflow_state.yaml updated:
  - [ ] current_step: "data_structure_cleanup" ✓
  - [ ] progress_percentage: 40 ✓
  - [ ] All previous work marked "complete" ✓
- [ ] Cross-reference validation passed
- [ ] YAML validation passed
- [ ] All files exist and not empty (no stubs)
- [ ] Git commit made with Phase 4 message
- [ ] Session confirmed: "Phase 4 Complete ✅"

**Notes:**
```

```

**Issues Encountered:**
```

```

**Blockers:**
```

```

---

### PHASE 5: Resume Writing

**Status:** ⬜ Not started | 🔵 In Progress | ✅ Complete

**Start Date:** _____________
**End Date:** _____________
**Session ID:** _____________

**Prerequisites:**
- [x] Phase 1 complete
- [x] Phase 2 complete
- [x] Phase 3 complete
- [x] Phase 4 complete

**Checklist:**
- [ ] Assigned to external session
- [ ] Prompt copied: PHASE_5_SESSION_PROMPT.md
- [ ] Session confirmed receipt
- [ ] Scenes written:
  - [ ] ch1-sc2.yaml "The Elections Begin" (~3000 words)
  - [ ] ch1-sc3.yaml "First Light" (~2500 words)
  - [ ] ch1-sc4.yaml "The Question" (~2000 words)
  - [ ] ch1-sc5.yaml "The Secret" (~3000 words)
- [ ] Total Chapter 1: 13,000-17,000 words
- [ ] Creative room properly excluded (no spoilers in scenes)
- [ ] Character relationships reflected
- [ ] World layer 1 style guide applied (warm, comedic)
- [ ] Foreshadowing planted appropriately
- [ ] Reader knowledge tracked
- [ ] chapters/chapter-01/meta.yaml updated with scene links
- [ ] Continuity check passed
- [ ] Reader knowledge consistency verified
- [ ] Style guide compliance confirmed
- [ ] YAML validation passed
- [ ] Git commit made with Phase 5 message
- [ ] Session confirmed: "Phase 5 Complete ✅"

**Notes:**
```

```

**Issues Encountered:**
```

```

**Blockers:**
```

```

---

## Summary Progress Tracking

### Timeline

```
Week 1:
  Day 1: Launch P1 + P3 (parallel, no dependencies)
  Day 2-3: P1 executing, P3 executing

Week 2:
  Day 1: P1 complete, launch P2
  Day 2: P3 complete (still working), P2 executing
  Day 3: P2 complete, launch P4

Week 3:
  Day 1: P4 executing
  Day 2: P4 complete, launch P5
  Day 3: P5 executing

Week 4:
  Day 1: P5 complete, all phases done
```

### Completion Status

| Phase | Status | Completion % | Next Action |
|-------|--------|--------------|-------------|
| P1: Creative Room | ⬜ | 0% | Launch to Session A |
| P2: Relationships | ⬜ | 0% | Wait for P1 |
| P3: Style Guide | ⬜ | 0% | Launch to Session B (parallel) |
| P4: Data Structure | ⬜ | 0% | Wait for P1+P2 |
| P5: Resume Writing | ⬜ | 0% | Wait for P1-P4 |
| **Overall** | ⬜ | 0% | Ready to launch |

---

## Critical Validations

### Before Phase 1 Starts
```bash
# Verify project structure
cd /path/to/QuantumDharma
[ -f showrunner.yaml ] && echo "✅ showrunner.yaml found" || echo "❌ Missing!"
[ -d characters ] && echo "✅ characters/ found" || echo "❌ Missing!"
[ -f story.yaml ] && echo "✅ story.yaml found" || echo "❌ Missing!"
[ -f world.yaml ] && echo "✅ world.yaml found" || echo "❌ Missing!"
[ -d reference ] && echo "✅ reference/ found" || echo "❌ Missing!"
```

### Between Phase 1 & 2
```bash
# Verify P1 output
[ -f creative_room/plot_twists.yaml ] && wc -l creative_room/*.yaml
# Should show ~100+ lines total for 5 files
```

### Before Phase 5 Starts
```bash
# Verify all previous work exists
find creative_room/ story/ world/ -name "*.yaml" | wc -l
# Should show 20+ files (not empty stubs)
```

---

## Communication Templates

### To Launch Session (Copy & Paste)

```
Subject: Quantum Dharma Phase [N] — External Session

Hi [Session Name],

I'm launching you on Phase [N]: [Phase Title] of the Quantum Dharma project.

Project Path: /path/to/QuantumDharma
Duration: [Time estimate]

Please follow the prompt: PHASE_[N]_SESSION_PROMPT.md

Key deliverables:
- [List the files/changes]

Acceptance criteria (all must pass):
- [ ] [Criterion 1]
- [ ] [Criterion 2]

When complete, reply with:
"Phase [N] Complete ✅" and I'll verify the output.

Thank you!
```

### Status Update Template

```
PHASE [N] STATUS UPDATE

✅ What's done:
- [Completed item 1]
- [Completed item 2]

🔵 Currently working on:
- [Current item]

⏱️ Estimated completion: [Time/Date]

⚠️ Issues: [Any blockers or questions]
```

### Completion Template

```
Phase [N] Complete ✅

All deliverables created:
- [File 1]: [Status]
- [File 2]: [Status]

Acceptance criteria: [All passing / Some issues]

Git commit: [Commit hash]

Notes:
[Any learnings or insights]

Ready for Phase [N+1]?
[Yes, waiting on / No, need to ...]
```

---

## Risk Mitigation

### If P1 Fails
- ❌ **Risk:** Creative room is empty, context isolation broken
- **Mitigation:** Assign to human-assisted session; provide brainstorm dump sections as reference
- **Escalation:** Manually extract 3-5 plot twists from brainstorm dump as seed data

### If P2 Fails
- ❌ **Risk:** No relationship graph, continuity checking broken
- **Mitigation:** Use character arc descriptions from story.yaml to infer basic relationships
- **Escalation:** Create minimal relationship stubs (at least 2 per character) and mark for review

### If P3 Fails
- ❌ **Risk:** Style guide still dark fantasy, image generation produces grimdark
- **Mitigation:** Style guide is cosmetic; doesn't block writing. Can fix after phases 1-4.
- **Escalation:** Not critical path; lower priority

### If P4 Fails
- ❌ **Risk:** Data structure still scattered, APIs can't find modular files
- **Mitigation:** Root YAML files still work; modular structure is optimization
- **Escalation:** Mark as "P5 can proceed with root-only data"

### If P5 Fails
- ❌ **Risk:** No new scenes written, can't validate infrastructure
- **Mitigation:** Optional phase; focus on P1-P4 infrastructure instead
- **Escalation:** Manual scene writing or assign to human + AI collaboration

---

## Signoff

- [ ] Coordinator review completed: _________________ (Date)
- [ ] Pre-launch checks passed: _________________ (Date)
- [ ] External sessions briefed: _________________ (Date)
- [ ] Phase 1 launched: _________________ (Date)
- [ ] All phases complete: _________________ (Date)

---

**Document Created:** March 8, 2026
**Last Updated:** March 8, 2026
**Coordinator:** [Your name]

For questions, refer to:
- QUANTUM_DHARMA_FIX_PLAN.md (master plan)
- PHASE_IMPLEMENTATION_REVIEW.md (analysis of each phase)
- PHASE_[N]_SESSION_PROMPT.md (for the specific phase)
