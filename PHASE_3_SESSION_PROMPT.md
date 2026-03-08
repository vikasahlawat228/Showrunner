# PHASE 3 External Session Prompt: Style Guide Overhaul

**Duration:** 1-1.5 hours
**Difficulty:** Low (creative, but straightforward replacement)
**Prerequisite:** None (can run in parallel with Phase 1-2)
**Goal:** Replace the incorrect dark_fantasy style with Indian masala sci-fi aesthetic

---

## Context

**Current Problem:**
- `style_guide/narrative.yaml` uses dark_fantasy preset (grimdark, Berserk, Dark Souls)
- `style_guide/visual.yaml` uses dark_fantasy visual palette (heavy shadows, crimson, grimdark)
- Author decision dec_002 explicitly states: "Indian Masala style — dramatic, comedic, emotional, with aura. **Never grimdark.**"

**Reality of the Story:**
- Sci-fi/meta-narrative with philosophical depth
- Multiple tonal registers (Academy warm, Geopolitical thriller, Cosmic awe, Meta unsettling)
- Indian cultural specificity (Hindu mythology, Mumbai, ISRO, Bollywood)
- Warm emotional peaks, not dark despair

**Your Job:** Replace both style files with correct Indian masala sci-fi aesthetics.

---

## Step 1: Backup Current Files

```bash
cd /path/to/QuantumDharma
cp style_guide/narrative.yaml style_guide/narrative.yaml.bak
cp style_guide/visual.yaml style_guide/visual.yaml.bak
```

## Step 2: Replace style_guide/narrative.yaml

Delete current content and replace with:

```yaml
# Quantum Dharma Narrative Style Guide
# Genre: Indian Masala Speculative Fiction (Sci-Fi Philosophical Thriller)

style:
  genre: "sci-fi philosophical thriller"
  subgenre: "Indian masala speculative fiction"
  tone_philosophy: |
    Dramatic, comedic, emotional, with aura. Never grimdark.
    Warm yet intellectual. Bollywood-influenced emotional peaks balanced with
    philosophical rigor. Mix of Hindi/English idiom and Mumbai urban vernacular.
    Comedy emerges from character quirks and cultural details, not darkness.

  core_voice: |
    The narrative voice is introspective but playful. Characters think deeply
    about existence but laugh at themselves. Dialogue is witty, sometimes code-mixed.
    Descriptions emphasize warmth and light, even in tense moments. Darkness is
    present, but never oppressive—it creates contrast, not domination.

  inspirations:
    - "3 Idiots (warm campus, philosophical, comedic heart)"
    - "Piku (family dynamics, Delhi/Mumbai life, humor in conflict)"
    - "Andhadhun (philosophical depth, unreliable reality, dark but not grimdark)"
    - "Ghost in the Shell (tech-philosophy blend, consciousness questions)"
    - "Evangelion (cosmic awe, psychological depth, spiritual themes)"

world_layer_specific:
  world_1_academy:
    name: "Academy (Training Layer)"
    tone: "Warm, coming-of-age, comedic, self-aware"
    visual_palette: ["warm golds", "school greens", "sunlit afternoons", "brass fixtures"]
    inspirations: ["My Hero Academia academy arcs", "Naruto school sequences", "3 Idiots"]
    prose_style: "Playful, self-aware, desi humor. Dialogue-driven, quick-paced."
    example_voice: |
      A sits in philosophy class, half-listening to Professor H's lecture on dharma.
      The afternoon sun cuts through the old windows, making dust motes visible—
      thousands of tiny decisions dancing in the light. How much of what A believes
      is chosen? How much is programmed into the very atoms?

      The kid next to A is asleep. A smiles. At least that's a choice.

  world_2_geopolitical:
    name: "Geopolitical (Test Layer)"
    tone: "Tense, thriller, political intrigue, high stakes clarity"
    visual_palette: ["cool steel", "midnight blue", "neon accents", "wet streets"]
    inspirations: ["Ghost in the Shell", "Psycho-Pass", "Raazi (tense political)"]
    prose_style: "Tight, atmospheric, information-dense. Every detail matters."
    example_voice: |
      The stadium's shadow stretches across the Mumbai rain-slicked street.
      Police presence is undeniable now—not aggressive, but watchful.
      A counts the surveillance cameras: seventeen visible from this angle.
      B appears beside A without A noticing. That's the second time this week.
      "They're going to make a move," B whispers. "Soon."

  world_3_cosmic:
    name: "Cosmic (Observation Layer)"
    tone: "Awe, philosophical, transcendent, reality-breaking"
    visual_palette: ["deep space purples", "quantum glow", "sacred geometry", "golden revelation"]
    inspirations: ["Interstellar", "Evangelion's cosmic moments", "Vedic art + digital fusion"]
    prose_style: "Poetic, abstract, sensory overload. Time and logic fracture."
    example_voice: |
      The simulation unravels not like cloth, but like thought.
      A's consciousness expands past the boundaries of A's skull, spreading through
      the quantum substrate like ink in water. For the first time, A understands:
      there is no "inside" or "outside." There is only the waveform, collapsing and
      uncollapsing across infinite layers.

      And in that collapse, A feels something like love.

  meta_layer:
    name: "Meta (Architect Layer)"
    tone: "Unsettling, liminal, fourth-wall breaking, impossible"
    visual_palette: ["void black", "glitch white", "impossible geometry", "fractal echoes"]
    inspirations: ["The Matrix red-pill scenes", "Paprika (dream logic)", "Inception folding"]
    prose_style: "Fragmented, recursive, non-linear. Sentences double back on themselves."
    example_voice: |
      This is not a place. It is the space between places.
      Mother stands in a room that has too many walls. Or zero walls.
      A's memories play out on screens that aren't screens.
      Time moves sideways.

      "You were always going to choose this," Mother says. She is right.
      She is also being told this by an architect one layer up.
      And that architect is being told the same by another.

      Infinite recursion. But A doesn't mind anymore.

sensory_anchors:
  smell: "Mumbai monsoon: humidity, earth after rain, incense from temples"
  sound: "Traffic + temple bells simultaneously; the city's holy chaos"
  taste: "Chai: comfort, alertness, home, warmth"
  touch: "Warm sun on skin after air-conditioned Academy; the city's breath"
  sight: "Neon glow on wet streets; sacred geometry in tech interfaces; East meets West"

emotional_beats:
  act_1: "Warmth mixed with creeping strangeness"
  act_2: "Mounting tension breaking into moments of tender character connection"
  act_3: "Awe and existential terror balanced with growing acceptance"

narrative_mechanics:
  foreshadowing: "Poetic and subtle; readers should feel haunted, not manipulated"
  dialogue: "Witty, code-mixed (Hindi/English), reveals character through word choice"
  pacing: "Fast in action, slow in reflection. Allow readers to sit with philosophical moments"
  humor: "Present throughout; darkens but never disappears, even in crisis"
  revelation: "Build gradually; readers discover alongside characters, not before"
```

## Step 3: Replace style_guide/visual.yaml

Delete current content and replace with:

```yaml
# Quantum Dharma Visual Style Guide
# Aesthetic: Indian Masala Speculative Fiction

visual_style:
  genre: "Indian masala speculative fiction manhwa/webcomic"
  philosophy: "Drama through light, not shadow. Warm golds + cool tech steels."

color_theory:
  heritage_colors: ["#D4AF37 (saffron gold)", "#C41E3A (warm red)", "#8B4513 (earth brown)", "#4B0082 (indigo)"]
  tech_colors: ["#0B1E35 (midnight blue)", "#00D9FF (cyber cyan)", "#FF006E (neon pink)", "#FFBE0B (warning yellow)"]
  transition_colors: ["#9400D3 (purple haze)", "#FFD700 (golden glow)", "#00FFFF (quantum cyan)"]
  danger_colors: ["#8B0000 (blood red)", "#FFD700 (corrupt gold)", "#000000 (void)"]

world_layer_specific:
  world_1_academy:
    name: "Academy Training Layer"
    dominant_colors: ["#D4AF37 (warm gold)", "#2D5016 (deep green)", "#FFCC00 (sunlight)", "#8B7355 (brick/earth)"]
    accent_colors: ["#003D7A (uniform blue)", "#CD853F (brass)"]
    hex_palette: ["#D4AF37", "#2D5016", "#FFCC00", "#003D7A", "#8B7355", "#CD853F"]
    lighting_approach: |
      Golden hour cinematography. Natural warmth dominates.
      Shadows are soft, diffused by dust and humidity.
      Sunlight through old windows creates romance, not mystery.
    atmosphere: "Day-lit, warm, inviting, slightly hazy (morning mist, afternoon heat)"
    character_visual_anchors:
      - "Modern Indian school uniforms with personal touches"
      - "Aura/presence visible as golden warmth around characters"
      - "Open, expressive faces with intelligent eyes"
      - "Graceful, fluid movement (not mechanical or heavy)"
    environment_details: |
      - Brick and marble campus with Hindu architectural echoes
      - Gardens with jasmine, neem trees, water features
      - Library with star-ceiling and philosophical quotes
      - Quantum training grounds (mixing sacred geometry with tech)
    reference_mood: "Warm campus life, chai stalls, friendly chaos, intellectual energy"

  world_2_geopolitical:
    name: "Geopolitical Test Layer"
    dominant_colors: ["#36454F (steel gray)", "#0B1E35 (midnight)", "#FF006E (neon pink)", "#00D9FF (cyber cyan)"]
    accent_colors: ["#FFBE0B (Mumbai neon)", "#1F77D2 (police blue)"]
    hex_palette: ["#36454F", "#0B1E35", "#FF006E", "#00D9FF", "#FFBE0B", "#1F77D2"]
    lighting_approach: |
      Neon + practical lights (streetlamps, car headlights, surveillance lights).
      High contrast. Shadows are sharp, defined. No diffusion.
      Wet surfaces reflect light in geometric patterns.
    atmosphere: "Night-dominated, tense, urban, high-surveillance"
    character_visual_anchors:
      - "Contemporary Mumbai style (modern + traditional mixed)"
      - "Aura/presence subdued, guarded, occasionally flaring with emotion"
      - "Faces show tension, calculation, hidden depth"
      - "Movement is efficient, controlled, purposeful"
    environment_details: |
      - Mumbai undercity: vibrant chaos, color everywhere despite gritty setting
      - Stadium: modern architecture with impossible geometry hints
      - Tech labs: minimalist, cold, functional aesthetic
      - Streets: neon signs, auto-rickshaws, crowds
    reference_mood: "Cyberpunk Mumbai, surveillance paranoia, human solidarity amid pressure"

  world_3_cosmic:
    name: "Cosmic Observation Layer"
    dominant_colors: ["#2E0854 (deep purple)", "#4B0082 (indigo)", "#FFD700 (golden revelation)", "#00FFFF (quantum glow)"]
    accent_colors: ["#FF00FF (magenta)", "#FFFFFF (stark white)"]
    hex_palette: ["#2E0854", "#4B0082", "#FFD700", "#00FFFF", "#FF00FF", "#FFFFFF"]
    lighting_approach: |
      Bioluminescent + quantum glow. Ethereal, otherworldly.
      Light sources are non-physical. Shadows have color (not just darkness).
      Sacred geometry illuminates from within.
    atmosphere: "Cosmic wonder, reality fragmentation, transcendent beauty"
    character_visual_anchors:
      - "Bodies partially translucent, showing internal light"
      - "Aura/presence visible as rainbow spectrum"
      - "Expressions show awe mixed with understanding"
      - "Movement is fluid, sometimes defying physics"
    environment_details: |
      - Impossible architecture (Escher-like, non-Euclidean)"
      - Quantum substrate visible as shimmering fields
      - Sacred geometry integrated into every structure
      - Time and space appear malleable
    reference_mood: "Aurora borealis meets sacred geometry, impossible beauty, cosmic awe"

  meta_layer:
    name: "Meta Architect Layer"
    dominant_colors: ["#FFFFFF (void white)", "#000000 (absolute black)", "#FF00FF (glitch magenta)", "#00FFFF (error cyan)"]
    accent_colors: ["#999999 (corruption gray)"]
    hex_palette: ["#FFFFFF", "#000000", "#FF00FF", "#00FFFF", "#999999"]
    lighting_approach: |
      Broken, fractured light. Glitch aesthetics.
      Light and shadow don't obey normal rules.
      Refraction and impossible angles dominate.
    atmosphere: "Unsettling, liminal, dream-like, reality-broken"
    character_visual_anchors:
      - "Bodies may have visual glitches, fractures"
      - "Presence is overwhelming, almost painful to perceive"
      - "Movement may stutter, repeat, or reverse"
      - "Faces show knowledge of higher orders of reality"
    environment_details: |
      - Rooms with impossible geometry
      - Surfaces that are and aren't there simultaneously
      - Time visible as texture
      - Reality appearing as code or mathematical equations
    reference_mood: "The Matrix, Paprika, Inception—dream logic made visible"

character_visual_approach:
  universal_principles:
    - "Visible aura/energy field indicating each character's quantum signature"
    - "Indian cultural details (jewelry, clothing, mannerisms) always present"
    - "Eyes convey intelligence and emotional depth"
    - "Beauty is defined broadly (not conformist)"
    - "Never grimdark or oppressive in appearance"

  costume_design:
    - "Modern India + tech aesthetic. Salwar kameez + hoodies, dhotis + sneakers."
    - "Jewelry that has meaning: family heirlooms mixed with tech devices."
    - "Colors match character personality and world layer."

  expression_and_movement:
    - "Warm with intelligence, not grim determination."
    - "Fluid and graceful, often dance-like in serious moments."
    - "Humor visible in expression even in tense scenes."

lighting_across_scenes:
  world_1_scenes: "Golden hour, natural warmth, soft shadows, dust motes visible"
  world_2_scenes: "Neon + streetlights, high contrast, sharp shadows, wet surfaces"
  world_3_scenes: "Quantum glow, non-physical light sources, sacred geometry"
  meta_scenes: "Fractured, glitchy, impossible angles, double-exposure effects"

reference_artists:
  - "Sachin Teng (warm character design, Indian specificity)"
  - "Jungho Lee (color cinematography, light mastery)"
  - "Studio Khara (Evangelion color work, spiritual depth)"
  - "Shinkai Makoto (light and atmosphere, beauty)"
  - "Indian traditional art (Warli, Madhubani) + digital fusion"
  - "Bollywood cinematography (warmth, emotional lighting)"

mood_boards:
  world_1_warmth: "Golden hour at Mumbai college, chai stalls, student energy, sunlit chaos"
  world_2_tension: "Neon-lit Mumbai streets, surveillance visible but human chaos persists"
  world_3_wonder: "Aurora + sacred geometry + impossible physics, transcendent beauty"
  meta_unreality: "Dream-like fragmentation, Paprika-esque surrealism, code made visible"

image_prompt_tokens:
  universal: "warm desi aesthetic, visible aura, Indian heritage details, never grimdark, cinematic"

  world_1:
    - "golden hour cinematography"
    - "warm academy campus"
    - "character expression: playful intelligence"
    - "natural sunlit scenes"
    - "comedic warmth present"
    - "dust motes in light"

  world_2:
    - "neon Mumbai atmosphere"
    - "high contrast clarity"
    - "political tension visible"
    - "wet streets, city lights"
    - "dramatic but not dark"
    - "human presence dominant"

  world_3:
    - "cosmic awe, quantum wonder"
    - "sacred geometry integrated"
    - "bioluminescent light"
    - "ethereal presence"
    - "transcendent beauty"
    - "reality fragmenting gently"

  meta_layer:
    - "glitch aesthetics"
    - "impossible geometry"
    - "reality fracturing"
    - "double-exposure effect"
    - "void and light contrast"
    - "unsettling but beautiful"
```

## Step 4: Create prompt_style_tokens.yaml (NEW FILE)

This file helps the image prompt composer insert correct style tokens into Gemini prompts.

```yaml
prompt_style_tokens:
  # Universal tokens applied to ALL prompts
  universal:
    - "warm desi aesthetic"
    - "visible aura/quantum signature"
    - "Indian heritage details"
    - "never grimdark"
    - "cinematic lighting"
    - "Bollywood-influenced emotional warmth"

  # World 1 - Academy Training Layer
  world_1:
    - "golden hour cinematography"
    - "warm academy campus setting"
    - "natural sunlit afternoon light"
    - "character expression: intelligent playfulness"
    - "comedic warmth present"
    - "dust motes in light, hazy atmosphere"
    - "Indian architectural echoes"
    - "Naruto academy energy"

  # World 2 - Geopolitical Test Layer
  world_2:
    - "neon Mumbai atmosphere"
    - "high contrast urban lighting"
    - "political thriller tension"
    - "wet streets reflecting neon"
    - "city lights dominant"
    - "dramatic but not dark"
    - "human presence and solidarity"
    - "surveillance visible but not oppressive"

  # World 3 - Cosmic Observation Layer
  world_3:
    - "cosmic awe and wonder"
    - "quantum glow bioluminescence"
    - "sacred geometry integrated"
    - "ethereal transcendent beauty"
    - "purple and gold color dominant"
    - "reality fragmenting gently"
    - "Evangelion-esque spiritual depth"
    - "impossible architecture, non-Euclidean"

  # Meta Layer - Architect Layer
  meta_layer:
    - "glitch aesthetics, digital artifacts"
    - "impossible geometry, Escher-like"
    - "reality fracturing visually"
    - "double-exposure effect"
    - "void black and white contrast"
    - "unsettling but beautiful"
    - "dream-logic made visible"
    - "Paprika-esque surrealism"

  # Negative tokens (NOT to include)
  avoid:
    - "grimdark"
    - "grim determination"
    - "heavy shadows dominating"
    - "dark fantasy"
    - "oppressive atmosphere"
    - "bleak"
    - "desaturated"
    - "Berserk-like"
    - "Dark Souls aesthetic"
    - "medieval grimdark"
```

## Step 5: Update prompt_style_tokens in existing files

If there's a `prompts/` directory with Jinja2 templates, update template headers to reference the new style guide:

```jinja2
{# Narrative generation prompt header #}
{# Style Guide: Indian Masala Sci-Fi (warm, never grimdark) #}
{# World Layer: {{ world_layer }} (see style_guide/narrative.yaml) #}
{# Visual Style: See style_guide/visual.yaml + prompt_style_tokens.yaml #}
```

## Step 6: Validate Changes

```bash
# Check YAML syntax
python3 -c "
import yaml
files = ['style_guide/narrative.yaml', 'style_guide/visual.yaml', 'prompt_style_tokens.yaml']
for f in files:
    try:
        with open(f) as file:
            yaml.safe_load(file)
        print(f'✅ {f} - valid')
    except Exception as e:
        print(f'❌ {f}: {e}')
"

# Check that dark_fantasy references are gone
grep -r "dark_fantasy\|grimdark\|Berserk\|Dark Souls" style_guide/
# Should return nothing
```

## Step 7: Commit Changes

```bash
git add style_guide/ prompt_style_tokens.yaml
git commit -m "style: Overhaul style guide to Indian masala sci-fi aesthetic

Replaced:
- style_guide/narrative.yaml: dark_fantasy → Indian masala sci-fi
- style_guide/visual.yaml: grimdark → warm aesthetic with tech steels

Added:
- prompt_style_tokens.yaml: style tokens for image generation

Changes:
- Narrative tone: warm, comedic, philosophical (never grimdark)
- Visual palette: warm golds + cool tech blues per world layer
- Lighting: golden hour (World 1), neon (World 2), quantum (World 3), glitch (Meta)
- Character design: Indian specificity, visible aura, fluid movement
- Inspirations: 3 Idiots, Ghost in the Shell, Evangelion (not Berserk)

Aligns with author decision dec_002: 'Indian Masala style — never grimdark'

Phase 3 Complete ✅"
```

---

## Acceptance Criteria (Self-Check)

- [ ] Both narrative.yaml and visual.yaml completely rewritten (not incremental edits)
- [ ] All dark_fantasy references removed
- [ ] All 4 world layers have specific guidance (narrative + visual + lighting)
- [ ] Color palettes include hex codes
- [ ] Inspirations changed from grimdark to Indian masala
- [ ] prompt_style_tokens.yaml created with all world layers
- [ ] "Never grimdark" philosophy appears multiple times
- [ ] Sensory anchors relate to Mumbai/India
- [ ] YAML files are valid (no syntax errors)
- [ ] Git commit made

---

## What This Unlocks

Once Phase 3 is complete:
- Image prompt generation will use correct style tokens
- Writing prompts will be guided by correct tone guidance
- Web UI style references will be updated
- All agents working on this project get clear Indian masala aesthetic direction

**Impact:** Writers won't accidentally generate dark, grimdark scenes. Image generation AI will produce warm, aura-filled, culturally-specific visuals.

---

## Phase Completion

Phase 3 is independent and can be done anytime. It doesn't depend on Phases 1-2, and Phases 4-5 don't depend on it (though they benefit from it).

Good luck! You're fixing the visual/tonal heart of the project. 🎨
