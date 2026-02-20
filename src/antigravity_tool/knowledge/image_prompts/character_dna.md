# Writing Character DNA Blocks

## What Is a Character DNA Block?

A Character DNA block is a standardized, reusable text description that defines a character's **visual identity** for AI image generation. It serves as the "source of truth" for a character's appearance, ensuring consistency across dozens or hundreds of generated images.

Think of it as a visual fingerprint: compact enough to include in every prompt, detailed enough to produce recognizable results, and stable enough to resist prompt drift across different scenes and compositions.

---

## The Face-First Ordering Principle

AI image generation models process prompts with **front-loading bias** -- tokens appearing earlier in the prompt receive stronger weight. This means the order of descriptors in your DNA block directly affects which features remain consistent.

**Prioritize features in this order:**

1. **Face and head** (highest priority for recognition)
2. **Hair** (second strongest recognition signal)
3. **Body type and build**
4. **Skin tone and distinguishing marks**
5. **Default expression or affect**
6. **Clothing defaults** (lowest priority, most likely to change per scene)

### Why Face-First?

Readers identify characters primarily by face and hair. If the model sacrifices detail due to prompt length or competing instructions, you want it to sacrifice clothing accuracy before face accuracy. A character in the wrong outfit is still recognizable. A character with the wrong face is not.

### Example DNA Block (Face-First Ordering)

```
[CHARACTER: Kael]
Sharp angular face, narrow jaw, high cheekbones, deep-set dark brown eyes with
heavy brow ridge, thin straight nose, slight scar across left eyebrow. Short
black hair, undercut, swept back with two loose strands over forehead. Tall
lean muscular build, 185cm. Light brown skin. Resting serious expression,
slight downward turn at mouth corners. Default outfit: black fitted long coat
over dark grey combat vest, armored shoulder plates.
```

Notice:
- Face geometry comes first (angular, narrow jaw, cheekbones)
- Eyes are described with multiple attributes (deep-set, dark brown, heavy brow)
- Hair is immediately after face
- Build follows hair
- Clothing is last and labeled as "default" since it may change

---

## Stable Tokens: Building Blocks of Consistency

### What Makes a Token "Stable"?

A stable token is a descriptor that reliably produces the same visual result across different prompts, models, and contexts. Stability comes from:

1. **Specificity:** "Platinum blonde" is more stable than "light hair"
2. **Concreteness:** "Scar across left cheek" is more stable than "battle-worn face"
3. **Standard vocabulary:** Descriptors the model has seen frequently in training data
4. **Non-contradiction:** Tokens that do not fight with other tokens in the prompt

### Stable vs. Unstable Descriptors

| Unstable | Stable | Why |
|----------|--------|-----|
| "Beautiful" | "Heart-shaped face, large almond eyes, full lips" | "Beautiful" is subjective; specific geometry is objective |
| "Looks dangerous" | "Sharp eyes, angular brow, thin-lipped slight smirk" | Mood-based descriptions are interpreted inconsistently |
| "Young" | "Soft rounded jaw, smooth skin, wide eyes, 17 years old" | "Young" spans a huge range; specific features narrow it |
| "Strong" | "Broad shoulders, thick neck, defined forearm muscles" | "Strong" is vague; anatomical specifics are concrete |
| "Cool hairstyle" | "Asymmetric bob, left side chin-length, right side shaved to 3mm" | Style judgments vary; measurements do not |

### The Descriptor Stack

Build each feature from a stack of stable descriptors:

**Eyes:**
`[shape] + [size] + [color] + [distinctive quality]`
Example: "Narrow upturned almond eyes, slightly large, dark amber, with long lower lashes"

**Hair:**
`[color] + [length] + [texture] + [style] + [distinctive detail]`
Example: "Jet black hair, waist-length, straight and silky, center-parted, with blunt-cut bangs at eyebrow level"

**Face:**
`[shape] + [jaw] + [cheekbones] + [nose] + [lips] + [distinctive marks]`
Example: "Oval face, soft jawline, subtle cheekbones, small button nose, thin pale lips, beauty mark below right eye"

---

## Avoiding Prompt Drift

Prompt drift occurs when a character's appearance gradually shifts across multiple generations. Over dozens of images, small inconsistencies compound until the character is no longer recognizable. This is the primary enemy of visual consistency.

### Causes of Drift

1. **Inconsistent DNA placement:** Putting the DNA block in different positions within the prompt. Always place it in the same position (recommended: immediately after the scene/action description).

2. **Competing descriptors:** Scene descriptions that override DNA tokens. "A dark, shadowy figure" might override "light brown skin." Be explicit: "Kael (light brown skin) stands in deep shadow."

3. **Model reinterpretation:** The model "averages" features across its training data. Repeated generation without strong anchors gradually pulls features toward generic means.

4. **Emotional descriptor bleeding:** "Angry Kael" might change his face shape if the model associates anger with different facial structures. Use behavioral descriptors ("Kael shouting, brow furrowed, teeth bared") rather than emotional labels.

5. **Style variations:** Different art styles in the same prompt series pull features differently. Lock the style token (see style_tokens.md) alongside the DNA block.

### Anti-Drift Techniques

**1. The Anchor Token System**
Identify 3-5 tokens that are the *most* distinctive and non-negotiable for the character. These are your anchors. They appear in every single prompt, unmodified:

```
ANCHORS for Kael: "scar across left eyebrow, deep-set dark brown eyes,
undercut black hair swept back"
```

Even if you abbreviate the DNA block for a particular prompt, anchors are never removed.

**2. Negative Reinforcement**
Use negative prompts to explicitly exclude drift directions:

```
Negative: blonde hair, blue eyes, round face, short stature, beard
```

This creates "guardrails" that prevent the model from drifting toward common defaults.

**3. Consistent Seed References**
If your generation tool supports image references or seeds:
- Generate 2-3 "canonical" reference images that perfectly match the DNA
- Use these as reference/influence images in subsequent generations
- Update references only when intentional design changes occur

**4. DNA Block Versioning**
Keep the DNA block in a single, centralized location. Never edit it for individual scenes -- instead, append scene-specific modifications:

```
[DNA BLOCK -- do not modify]
Sharp angular face, narrow jaw, high cheekbones, deep-set dark brown eyes...

[SCENE MODIFICATIONS]
Wearing formal white dress shirt, sleeves rolled to elbows. Hair slightly
disheveled. Bruise forming on right cheekbone.
```

This maintains the core identity while allowing scene-appropriate variations.

**5. Periodic Consistency Checks**
Every 10-15 generated images, compare the latest output against the canonical references. If drift is occurring:
- Strengthen the drifting feature's descriptor (add more specific tokens)
- Add the drifting direction to the negative prompt
- Consider regenerating with stricter adherence to the DNA block

---

## DNA Block Templates

### Template: Male Character (Action/Shonen)

```
[CHARACTER: {Name}]
{face_shape} face, {jaw_type} jaw, {cheekbone_description}, {eye_shape}
{eye_color} eyes {eye_distinctive}, {nose_description}, {lip_description},
{facial_marks_if_any}. {hair_color} {hair_length} hair, {hair_texture},
{hair_style}, {hair_distinctive}. {height_descriptor} {build_type} build.
{skin_tone} skin. {default_expression}. Default: {clothing_description}.
```

### Template: Female Character (General)

```
[CHARACTER: {Name}]
{face_shape} face, {jaw_type} jawline, {cheekbone_description}, {eye_shape}
{eye_size} {eye_color} eyes {eye_distinctive}, {eyebrow_description},
{nose_description}, {lip_description}, {facial_marks_if_any}. {hair_color}
{hair_length} hair, {hair_texture}, {hair_style}, {hair_distinctive}.
{height_descriptor} {build_type} figure. {skin_tone} skin.
{default_expression}. Default: {clothing_description}.
```

### Template: Non-Human/Fantasy Character

```
[CHARACTER: {Name}]
{species_identifier}. {face_shape} face, {key_non_human_features},
{eye_shape} {eye_color} eyes {eye_distinctive}, {nose_description},
{mouth_description}, {additional_non_human_facial_features}. {hair_or_equivalent}.
{body_type}, {height_descriptor}, {non_human_body_features}. {skin_or_surface}.
{default_expression_or_affect}. Default: {clothing_or_adornment}.
```

---

## Clothing and Outfit Variants

Characters change outfits. Handle this with a modular approach:

### Base DNA (Always Included)
The character's physical appearance -- face, hair, body. This never changes (except for deliberate story events like injury or aging).

### Outfit Modules (Swappable)

```
[OUTFIT: Kael - Combat]
Black fitted long coat, dark grey combat vest underneath, armored shoulder
plates, black tactical pants, knee-high boots with metal shin guards.

[OUTFIT: Kael - Casual]
Dark green henley shirt with sleeves pushed up, black jeans, simple leather
belt, worn brown boots.

[OUTFIT: Kael - Formal]
Charcoal three-piece suit, white dress shirt, black tie, silver cufflinks,
polished black dress shoes.
```

Combine by appending the relevant outfit module to the base DNA:

```
[DNA BLOCK] + [OUTFIT: Kael - Formal] + [SCENE DESCRIPTION]
```

---

## Age and Temporal Variants

For stories with time skips or flashbacks, create DNA variants:

```
[CHARACTER: Kael - Age 12]
Round soft face, narrow jaw not yet defined, wide dark brown eyes, small
straight nose, slight gap in front teeth. Short messy black hair, falling
over forehead. Thin small build, 145cm. Light brown skin. Default expression:
curious, slightly anxious. Oversized worn school uniform.

[CHARACTER: Kael - Age 17]
Face lengthening, jaw becoming angular, cheekbones emerging, deep-set dark
brown eyes, thin straight nose, slight scar forming across left eyebrow.
Short black hair, beginning to grow out, swept back loosely. Lean athletic
build, 175cm. Light brown skin. Default expression: guarded, alert. Dark
training clothes.

[CHARACTER: Kael - Age 25 (Primary)]
Sharp angular face, narrow jaw, high cheekbones, deep-set dark brown eyes
with heavy brow ridge, thin straight nose, scar across left eyebrow. Short
black hair, undercut, swept back. Tall lean muscular build, 185cm. Light
brown skin. Resting serious expression. Black fitted long coat, combat vest.
```

Each variant maintains recognizable continuity (same eyes, same skin, same scar progression) while showing appropriate age differences.

---

## Common Mistakes

### Over-Description
DNA blocks that exceed 100 words become unreliable. The model cannot hold too many specific instructions simultaneously. Prioritize ruthlessly. Cut anything that is not essential for recognition.

### Poetic Language
"Eyes like molten amber catching the dying sun" is beautiful prose and terrible prompt language. Use: "Warm amber eyes, slightly downturned." Models interpret literal, concrete language more consistently than metaphor.

### Contradictory Features
"Innocent wide eyes" combined with "intimidating sharp gaze" creates conflict. The model will average them, producing neither. Choose one dominant quality and reinforce it.

### Neglecting Side/Back Views
DNA blocks often describe only the front-facing character. For scenes requiring profile or three-quarter views, add profile-specific notes:

```
Profile notes: Strong brow ridge visible in profile, nose has slight
aquiline curve, jaw angles sharply below ear, undercut visible from side
showing shaved section above ear.
```

### Ignoring Model Biases
Different AI image models have different biases and tendencies. Test your DNA block on your specific model and adjust. If the model consistently makes a character's hair lighter than described, strengthen the hair color token or add it to the negative prompt ("NOT light brown hair, NOT auburn hair").

---

## DNA Block Quality Checklist

Before finalizing a character DNA block, verify:

1. **Is the face described with at least 5 specific geometric features?** (shape, jaw, cheekbones, nose, eyes)
2. **Are the eyes described with shape, color, and at least one distinctive quality?**
3. **Is the hair described with color, length, texture, and style?**
4. **Is there at least one unique distinguishing feature?** (scar, mole, heterochromia, unusual feature)
5. **Is the block under 80 words for the core physical description?** (excluding outfit)
6. **Are all descriptors concrete and literal, not poetic or metaphorical?**
7. **Does the block avoid contradictory descriptors?**
8. **Have you identified 3-5 anchor tokens for anti-drift?**
9. **Have you tested the block and verified it produces consistent results?**
10. **Have you created negative prompt guardrails for the most common drift directions?**
