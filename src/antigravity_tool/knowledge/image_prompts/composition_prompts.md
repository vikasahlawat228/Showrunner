# Translating Composition to Prompts

This guide covers how to convert panel composition decisions (shot type, camera angle, character placement) into effective image generation prompts. The goal is a reliable mapping from your screenplay/panel blueprint to visual output.

## The Composition-to-Prompt Pipeline

```
Panel Blueprint → Shot Type Tokens → Angle Tokens → Subject Placement → Environment → Mood → Final Prompt
```

Each composition decision translates into specific prompt language. Consistency in this translation is what makes your manhwa look professionally directed.

## Shot Type Translation

### Extreme Wide Shot (EWS)
```
Composition intent: Establish scale, show environment dominance
Prompt tokens: "extreme wide shot, vast landscape, tiny figure in distance, establishing shot"
Subject ratio: Character occupies <10% of frame
Key detail: Emphasize environment details over character features
```

### Wide Shot (WS)
```
Composition intent: Show full body in context
Prompt tokens: "wide shot, full body visible, character in environment, full figure"
Subject ratio: Character occupies 30-50% of frame height
Key detail: Full costume/outfit visible, environment clearly defined
```

### Medium Wide Shot (MWS)
```
Composition intent: Show body language with some environment
Prompt tokens: "medium wide shot, knee-up framing, three-quarter body shot"
Subject ratio: Character from knees up
Key detail: Good for action poses and gesture
```

### Medium Shot (MS)
```
Composition intent: Conversational, natural framing
Prompt tokens: "medium shot, waist-up, upper body framing"
Subject ratio: Character from waist up
Key detail: Default for dialogue scenes, shows hand gestures
```

### Medium Close-Up (MCU)
```
Composition intent: Emotional focus while maintaining context
Prompt tokens: "medium close-up, chest-up framing, portrait with shoulders"
Subject ratio: Character from chest up
Key detail: Bridges conversation and emotional intensity
```

### Close-Up (CU)
```
Composition intent: Emotional intensity, facial expression focus
Prompt tokens: "close-up, face focus, detailed expression, portrait shot"
Subject ratio: Face fills most of frame
Key detail: Character DNA facial features must be very precise here
```

### Extreme Close-Up (ECU)
```
Composition intent: Maximum intensity, detail emphasis
Prompt tokens: "extreme close-up, eye detail, macro shot, tight crop on [feature]"
Subject ratio: Single feature fills frame
Key detail: Use for dramatic reveals, emotional peaks
```

### Over-the-Shoulder (OTS)
```
Composition intent: POV connection, dialogue framing
Prompt tokens: "over the shoulder shot, foreground character back/shoulder blurred, facing [character]"
Subject ratio: Foreground character 20-30%, background character 40-50%
Key detail: Specify which character is in foreground vs background
```

### Two-Shot
```
Composition intent: Relationship dynamics, confrontation
Prompt tokens: "two shot, two characters facing each other, side by side, dual portrait"
Subject ratio: Both characters roughly equal in frame
Key detail: Include both characters' DNA blocks
```

## Camera Angle Translation

### Eye Level
```
Prompt tokens: "eye level angle, straight-on perspective, neutral camera angle"
Effect: Neutral, natural, relatable
Use: Default for most panels
```

### Low Angle
```
Prompt tokens: "low angle shot, looking up at subject, dramatic perspective from below, worm's eye view"
Effect: Subject appears powerful, imposing, heroic
Use: Power moments, villain reveals, heroic poses
```

### High Angle
```
Prompt tokens: "high angle shot, looking down at subject, bird's eye perspective, overhead view"
Effect: Subject appears vulnerable, small, overwhelmed
Use: Defeat, isolation, emotional vulnerability
```

### Dutch Angle (Tilted)
```
Prompt tokens: "dutch angle, tilted camera, diagonal composition, canted angle"
Effect: Unease, tension, disorientation
Use: Horror, psychological tension, world-shifting moments
```

### Bird's Eye View
```
Prompt tokens: "bird's eye view, top-down perspective, aerial view, looking straight down"
Effect: Strategic overview, detachment, scale
Use: Battle maps, city establishing shots, isolation in space
```

### Worm's Eye View
```
Prompt tokens: "worm's eye view, extreme low angle, ground level perspective, looking straight up"
Effect: Maximum intimidation, grandeur
Use: Towering buildings, powerful figures, scale emphasis
```

## Combining Shot + Angle

The most effective prompts combine shot type and angle clearly:

```
# Powerful villain introduction
"low angle medium shot, looking up at [character], imposing stance, dramatic lighting from behind"

# Vulnerable protagonist moment
"high angle close-up, looking down at [character], tears in eyes, isolated in empty space"

# Tense confrontation
"eye level two-shot, [character A] facing [character B], tension between them, narrow space"

# Epic battle reveal
"extreme low angle extreme wide shot, massive [creature/army] towering above, tiny figures below"
```

## Subject Placement Tokens

### Rule of Thirds
```
"character positioned off-center, rule of thirds composition"
"subject in left third of frame, looking right"
"subject in right third, negative space on left"
```

### Center Composition
```
"centered composition, symmetrical framing, character in center"
Use: Power poses, confrontations, formal moments
```

### Foreground/Background Layering
```
"foreground elements framing shot, [object] in foreground blur"
"depth of field, sharp focus on subject, blurred background"
"layered composition, foreground/midground/background elements"
```

### Leading Lines
```
"leading lines drawing eye to subject, [architectural element] creating visual path"
"converging lines toward vanishing point, perspective depth"
```

## Environment Integration

### Interior Scenes
```
"indoor scene, [room type], [lighting source], architectural details"
"dim interior, window light casting shadows, cluttered room"
"grand hall, high ceiling, ornate pillars, ambient candlelight"
```

### Exterior Scenes
```
"outdoor scene, [location type], [sky condition], [vegetation/architecture]"
"urban street, neon signs, wet pavement, night scene"
"open field, vast sky, distant mountains, golden hour"
```

### Atmosphere and Depth
```
"atmospheric perspective, distant objects faded"
"particles in air, dust motes in light beam"
"fog rolling in, obscured background, sense of mystery"
```

## Panel-Specific Considerations for Manhwa/Webtoon

### Vertical Scroll Composition
Webtoon panels are viewed vertically. This affects composition:

```
# Tall vertical panel (for dramatic reveals)
"vertical composition, tall narrow frame, looking up at towering [subject]"

# Wide horizontal panel (for landscape establishing)
"wide panoramic composition, horizontal landscape, expansive view"

# Standard webtoon panel (9:16 section)
"vertical portrait composition, 9:16 aspect ratio, [subject] in upper/lower portion"
```

### Scroll Transitions
Consider how panels connect in vertical scroll:

```
# Panel ending on tension (reader scrolls to see resolution)
"cropped composition, partial face visible, suspenseful framing, cut off at edge"

# Reveal panel (what reader sees after scrolling)
"dramatic reveal composition, full subject visible, impactful framing, splash panel feel"
```

## Assembling the Final Prompt

### Template Structure
```
[Character DNA block]
[Shot type] + [Camera angle] + [Subject placement]
[Character action/pose/expression]
[Environment description]
[Style tokens from style guide]
[Mood/lighting tokens]
[Quality tokens]
```

### Example: Complete Panel Prompt

Panel blueprint:
- Shot: Medium close-up
- Angle: Slightly low
- Character: Kai, determined expression
- Setting: Rooftop, sunset
- Mood: Hopeful but uncertain

Assembled prompt:
```
young man with silver-white messy hair, sharp blue eyes, angular jaw,
wearing black fitted jacket with silver clasps,
medium close-up, slightly low angle, off-center right composition,
determined expression, jaw set, eyes looking toward horizon,
standing on rooftop edge, city skyline background, sunset sky,
manhwa style, full color, cel shading, clean lines,
golden hour lighting, warm orange backlight, rim light on hair,
masterpiece, best quality, sharp detail
```

## Common Mistakes

1. **Contradictory composition**: "extreme close-up, full body visible" - pick one
2. **Missing character DNA**: Style is set but character looks different each panel
3. **Vague placement**: "character standing" - specify where in frame and what pose
4. **Ignoring the cut**: Not considering what's cropped out vs shown
5. **Over-describing**: Too many composition tokens can confuse the generator. Be specific and concise.
6. **Forgetting negative prompts**: Always pair composition prompts with relevant negatives
7. **Inconsistent style tokens**: Changing base style between panels breaks visual continuity
