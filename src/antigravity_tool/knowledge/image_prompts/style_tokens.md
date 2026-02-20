# Style Tokens and Modifiers

Style tokens are short, reusable text fragments that control the aesthetic of AI-generated images. Placing consistent style tokens across all image prompts ensures visual coherence throughout your manga/manhwa project.

## Core Concepts

### What Are Style Tokens?
Style tokens are descriptive phrases that guide AI image generators toward a specific look. They operate at multiple levels:

- **Medium tokens**: Define the fundamental art type (e.g., "digital painting", "ink drawing")
- **Style tokens**: Define the aesthetic school (e.g., "manhwa style", "shonen manga")
- **Quality tokens**: Control detail and rendering quality (e.g., "highly detailed", "sharp lines")
- **Mood tokens**: Set the emotional tone of the image (e.g., "dramatic lighting", "soft glow")

### Token Ordering
Place tokens in order of importance. Most AI models weight earlier tokens more heavily:

```
[subject] + [action/pose] + [style tokens] + [quality tokens] + [mood/atmosphere]
```

## Art Style Categories

### Manga Styles

| Style | Tokens | Characteristics |
|-------|--------|-----------------|
| Shonen | `shonen manga style, dynamic lines, high energy, bold inking` | Action-oriented, exaggerated poses, speed lines |
| Shojo | `shojo manga style, delicate lines, soft tones, floral accents` | Emotional focus, decorative elements, sparkles |
| Seinen | `seinen manga style, detailed rendering, realistic proportions, heavy shadows` | Mature, detailed backgrounds, gritty |
| Josei | `josei manga style, elegant lines, muted tones, realistic faces` | Realistic proportions, subtle expressions |

### Manhwa/Webtoon Styles

| Style | Tokens | Characteristics |
|-------|--------|-----------------|
| Modern Manhwa | `manhwa style, full color, clean cel shading, digital art` | Clean lines, vibrant colors, digital look |
| Fantasy Manhwa | `manhwa style, detailed fantasy, rich colors, ornate details` | Elaborate costumes, magical effects |
| Romance Manhwa | `manhwa style, soft coloring, gentle gradients, warm palette` | Soft lighting, pastel accents, expressive eyes |
| Action Manhwa | `manhwa style, dynamic composition, saturated colors, impact effects` | Bold contrasts, motion effects, dramatic angles |

### Hybrid and Specialty

| Style | Tokens | Characteristics |
|-------|--------|-----------------|
| Semi-Realistic | `semi-realistic anime, detailed faces, realistic lighting, digital painting` | Blend of anime and realism |
| Watercolor | `watercolor manga style, soft edges, color bleed, paper texture` | Painted look, organic feel |
| Noir | `manga noir, high contrast, deep shadows, monochrome with accent color` | Film noir influence, dramatic |
| Chibi | `chibi style, super deformed, cute proportions, simple features` | Comic relief, simplified |

## Quality Modifiers

### Resolution and Detail
```
masterpiece, best quality, highly detailed     # Maximum quality
clean lines, sharp edges, professional          # Clean production look
rough sketch, loose lines, gestural             # Draft/sketch feel
```

### Line Work
```
thin precise lines, fine inking                 # Delicate style
bold thick outlines, heavy inking               # Bold style
variable line weight, dynamic inking            # Expressive style
no outlines, painterly, soft edges              # Lineless style
```

### Coloring Approach
```
flat colors, cel shading, minimal gradients     # Clean manhwa look
soft gradients, airbrush shading                # Smooth blended look
crosshatching, screen tones, halftone dots      # Traditional manga look
full color, rich palette, vibrant               # Full color production
grayscale, monochrome, ink wash                 # Black and white
limited palette, two-tone, duotone              # Restricted color
```

## Mood and Atmosphere Tokens

### Lighting

| Mood | Tokens |
|------|--------|
| Dramatic | `dramatic lighting, strong shadows, chiaroscuro, rim light` |
| Warm | `warm golden light, sunset glow, amber tones, soft warmth` |
| Cold | `cool blue light, moonlight, pale luminescence, cold tones` |
| Mysterious | `dim lighting, fog, obscured details, silhouette` |
| Hopeful | `bright backlighting, lens flare, radiant glow, light rays` |
| Ominous | `low key lighting, deep shadows, underlit, eerie glow` |

### Time of Day
```
sunrise, dawn light, pink and gold sky          # Early morning
bright daylight, clear sky, midday sun          # Daytime
golden hour, long shadows, warm orange light    # Late afternoon
twilight, purple sky, fading light              # Dusk
night scene, moonlit, starry sky, dark          # Night
```

### Weather
```
rainy, wet surfaces, reflections, puddles       # Rain
snowing, frost, cold breath, white landscape    # Snow
foggy, misty, low visibility, diffused light    # Fog
stormy, dark clouds, lightning, wind effects    # Storm
cherry blossoms falling, spring breeze          # Sakura (common in manga)
```

## Building a Style Guide Token Set

For a consistent project, define a **base style block** that goes into every prompt:

```yaml
# Example: Modern Fantasy Manhwa
style_guide:
  base_tokens: "manhwa style, full color, digital art, detailed rendering"
  quality_tokens: "masterpiece, best quality, sharp lines"
  coloring: "cel shading with soft gradients, vibrant saturated colors"
  line_work: "clean variable-weight lines, precise inking"
```

### Scene-Specific Overrides

Layer mood tokens on top of your base style:

```yaml
# Tense confrontation scene
mood_override: "dramatic lighting, high contrast, intense atmosphere"

# Peaceful slice-of-life scene
mood_override: "soft warm lighting, gentle colors, relaxed atmosphere"

# Flashback
mood_override: "desaturated colors, vignette, soft focus, faded"
```

## Negative Tokens

Many image generators support negative prompts. Common negatives for manga/manhwa:

```
# Quality negatives
low quality, blurry, jpeg artifacts, deformed

# Style consistency negatives
3d render, photorealistic, western comic style  # If you want anime/manga
chibi, super deformed                           # If you want realistic proportions
oversaturated, neon colors                      # If you want muted palette

# Anatomy negatives
extra fingers, extra limbs, deformed hands, bad anatomy
```

## Token Consistency Rules

1. **Define once, use everywhere**: Create your style block at project start
2. **Layer, don't replace**: Add mood tokens on top of base tokens per-scene
3. **Character DNA tokens override style tokens**: If a character has specific features, those take priority
4. **Test early**: Generate a few test images with your token set before committing to full production
5. **Document variations**: If certain scenes need different styles (flashbacks, dreams), document those overrides explicitly in your style guide

## Common Pitfalls

- **Token soup**: Too many conflicting tokens cancel each other out. Keep it focused.
- **Inconsistent ordering**: Maintain the same token order across prompts for predictability.
- **Missing negatives**: Always include quality negatives at minimum.
- **Style drift**: If you change tokens mid-project, all subsequent images may look different from earlier ones.
- **Forgetting character DNA**: Style tokens set the mood, but character DNA blocks maintain identity. Always include both.
