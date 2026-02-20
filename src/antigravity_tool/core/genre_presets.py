"""Built-in genre presets for auto-configuring project style."""

from __future__ import annotations

from antigravity_tool.schemas.genre import GenrePreset

_PRESETS: dict[str, GenrePreset] = {
    "dark_fantasy": GenrePreset(
        genre_id="dark_fantasy",
        display_name="Dark Fantasy",
        description="Gritty, mature fantasy with moral ambiguity, high stakes, and visceral danger.",
        narrative_defaults={
            "tone": "grim, atmospheric, punctuated by moments of beauty",
            "pov_default": "third person limited",
            "prose_style": "stark, sensory, economical",
            "dialogue_style": "terse, loaded with subtext",
            "pacing_preference": "slow burn with explosive action peaks",
            "themes": ["cost of power", "moral ambiguity", "survival", "what makes a monster"],
            "taboos": [],
            "inspirations": ["Berserk", "Claymore", "Vinland Saga", "Dark Souls"],
        },
        visual_defaults={
            "art_style": "manhwa",
            "sub_style": "dark fantasy",
            "line_weight": "heavy ink lines, crosshatching in shadows",
            "color_palette": ["deep crimson", "charcoal", "muted gold", "steel blue", "bone white"],
            "color_mode": "muted palette with selective vivid accents",
            "shading_style": "heavy contrast, dramatic chiaroscuro",
            "background_detail": "atmospheric, decay and grandeur",
            "character_proportions": "realistic with imposing stature",
            "prompt_style_tokens": "dark fantasy manhwa, heavy shadows, dramatic lighting, detailed armor and weapons, atmospheric backgrounds",
        },
        suggested_structure="heros_journey",
        mood_lighting_overrides={
            "tense": "pitch darkness with a single flickering light source, deep red undertones",
            "action": "fire and blood-orange lighting, motion streaks, dust particles",
            "melancholic": "rain-soaked grey, muted everything, cold blue cast",
            "mysterious": "fog, moonlight silhouettes, long shadows",
            "peaceful": "dawn light through ruins, warm amber filtering through canopy",
        },
        common_tropes=[
            "chosen one with a dark cost", "corruption of power", "monster that was once human",
            "ancient evil awakening", "found family forged in battle", "the mentor's hidden sin",
        ],
        anti_tropes=[
            "power of friendship solves everything", "villain is purely evil with no depth",
            "consequence-free violence", "instant mastery of powers",
        ],
        reference_works=["Berserk", "Claymore", "Vinland Saga", "Chainsaw Man", "Made in Abyss"],
        panel_style_hints={
            "action": "wide panels, motion blur, speed lines, impact frames",
            "emotion": "extreme close-ups on eyes, negative space",
            "horror": "dutch angles, warped perspective, shadow-heavy compositions",
            "quiet": "wide establishing shots, small figures in vast landscapes",
        },
    ),
    "shonen_action": GenrePreset(
        genre_id="shonen_action",
        display_name="Shonen Action",
        description="High-energy action with escalating power systems, rivalries, and themes of growth.",
        narrative_defaults={
            "tone": "energetic, hopeful, dramatic with comedic beats",
            "pov_default": "third person limited",
            "prose_style": "punchy, kinetic, exclamatory",
            "dialogue_style": "bold declarations, battle banter, emotional speeches",
            "pacing_preference": "fast with training arcs as breathers",
            "themes": ["never giving up", "bonds of friendship", "surpassing limits", "protecting what matters"],
            "taboos": [],
            "inspirations": ["One Piece", "Naruto", "My Hero Academia", "Dragon Ball"],
        },
        visual_defaults={
            "art_style": "manga",
            "sub_style": "shonen action",
            "line_weight": "dynamic, thick for impact, thin for detail",
            "color_palette": ["vibrant orange", "electric blue", "hot red", "bright yellow", "deep black"],
            "color_mode": "high saturation for key moments, clean for dialogue",
            "shading_style": "screen tones with dynamic hatching",
            "background_detail": "detailed for establishing, speed lines for action",
            "character_proportions": "slightly exaggerated, expressive faces",
            "prompt_style_tokens": "shonen manga, dynamic poses, speed lines, dramatic angles, expressive faces, energy effects",
        },
        suggested_structure="save_the_cat",
        mood_lighting_overrides={
            "action": "high contrast, energy auras, explosive highlights",
            "training": "warm sunrise/sunset, sweat drops, determination glow",
            "rivalry": "split-screen lighting, opposing color temperatures",
            "emotional": "backlit silhouettes, tears catching light",
        },
        common_tropes=[
            "power-up through determination", "tournament arc", "training montage",
            "rival who becomes ally", "hidden potential awakening", "mentor sacrifice",
        ],
        anti_tropes=[
            "protagonist wins without effort", "static power levels",
            "stakes that never matter", "villain with no philosophy",
        ],
        reference_works=["One Piece", "Naruto", "My Hero Academia", "Jujutsu Kaisen", "Dragon Ball Z"],
        panel_style_hints={
            "action": "double-page spreads, extreme angles, impact frames with screentone explosions",
            "emotion": "chibi reactions for comedy, full-page for dramatic moments",
            "power_up": "aura effects, radiating lines, zoom on eyes",
            "quiet": "slice-of-life panels, 4-koma style gags",
        },
    ),
    "romance": GenrePreset(
        genre_id="romance",
        display_name="Romance / Shoujo",
        description="Character-driven romance with emotional depth, relationship dynamics, and heartfelt moments.",
        narrative_defaults={
            "tone": "warm, emotionally rich, bittersweet moments balanced with sweetness",
            "pov_default": "first person or close third person limited",
            "prose_style": "introspective, sensory, emotionally detailed",
            "dialogue_style": "natural, subtext-heavy, unfinished sentences convey tension",
            "pacing_preference": "slow burn with crescendo emotional peaks",
            "themes": ["vulnerability as strength", "miscommunication and growth", "what love actually means"],
            "taboos": [],
            "inspirations": ["Fruits Basket", "Kimi ni Todoke", "Horimiya", "True Beauty"],
        },
        visual_defaults={
            "art_style": "manhwa",
            "sub_style": "romance",
            "line_weight": "clean, delicate, flowing lines",
            "color_palette": ["blush pink", "soft lavender", "cream", "warm peach", "sky blue"],
            "color_mode": "soft watercolor palette with warm tones",
            "shading_style": "soft gradients, minimal harsh shadows",
            "background_detail": "sparkles and flowers for emotional moments, detailed for dates",
            "character_proportions": "elegant, fashion-forward, expressive eyes",
            "prompt_style_tokens": "romance manhwa, soft lighting, beautiful characters, sparkle effects, flower motifs, warm color palette",
        },
        suggested_structure="save_the_cat",
        mood_lighting_overrides={
            "romantic": "golden hour everything, lens flares, bokeh lights",
            "heartbreak": "rain, grey-blue tones, isolated figure",
            "tension": "close proximity, warm tones, shallow depth of field",
            "confession": "cherry blossoms, sunset backlight, wind in hair",
        },
        common_tropes=[
            "love triangle", "accidental proximity", "childhood friends to lovers",
            "fake dating becomes real", "the misunderstanding", "dramatic confession",
        ],
        anti_tropes=[
            "toxic behavior romanticized", "love at first sight without development",
            "female lead with no personality beyond love interest",
        ],
        reference_works=["True Beauty", "Fruits Basket", "Lovely Complex", "Horimiya", "My Love Story!!"],
        panel_style_hints={
            "romantic": "close-ups on hands almost touching, eye contact panels, sparkle backgrounds",
            "emotional": "full-page face with tears, flower overlay panels",
            "comedy": "chibi reactions, exaggerated expressions",
            "tension": "narrow panels stacking vertically, intense eye close-ups",
        },
    ),
    "slice_of_life": GenrePreset(
        genre_id="slice_of_life",
        display_name="Slice of Life",
        description="Quiet, character-driven stories about everyday life, small moments, and personal growth.",
        narrative_defaults={
            "tone": "gentle, contemplative, quietly humorous",
            "pov_default": "first person",
            "prose_style": "observational, warm, detail-oriented",
            "dialogue_style": "natural, conversational, comfortable silences",
            "pacing_preference": "leisurely, moment-driven rather than plot-driven",
            "themes": ["finding beauty in the mundane", "growing up", "community", "seasons of life"],
            "taboos": [],
            "inspirations": ["Yotsuba&!", "March Comes in Like a Lion", "Barakamon", "Silver Spoon"],
        },
        visual_defaults={
            "art_style": "manga",
            "sub_style": "slice of life",
            "line_weight": "light, clean, airy",
            "color_palette": ["warm cream", "sage green", "sky blue", "butter yellow", "soft brown"],
            "color_mode": "pastel palette, seasonal color shifts",
            "shading_style": "minimal, soft, natural lighting",
            "background_detail": "lovingly detailed everyday environments",
            "character_proportions": "natural, warm, expressive",
            "prompt_style_tokens": "slice of life manga, warm atmosphere, detailed everyday settings, natural lighting, gentle expressions",
        },
        suggested_structure="kishotenketsu",
        mood_lighting_overrides={
            "peaceful": "warm afternoon sun through windows, dappled light",
            "melancholic": "overcast sky, soft grey, rain on windows",
            "joyful": "bright sunny day, vivid seasonal colors",
            "nostalgic": "sunset golden hour, long shadows, warm tones",
        },
        common_tropes=[
            "seasonal festivals", "cooking scenes", "found family", "quiet epiphany",
            "the beauty of routine", "small act of kindness that resonates",
        ],
        anti_tropes=[
            "artificial drama for stakes", "world-ending threats",
            "characters who never change", "empty comedy without heart",
        ],
        reference_works=["Yotsuba&!", "March Comes in Like a Lion", "Barakamon", "A Silent Voice"],
        panel_style_hints={
            "peaceful": "wide landscape panels, characters small in frame",
            "comedy": "4-koma strips, reaction faces",
            "emotional": "wordless panel sequences, eyes and hands",
            "atmosphere": "full-width panels of food, weather, scenery",
        },
    ),
    "sci_fi": GenrePreset(
        genre_id="sci_fi",
        display_name="Sci-Fi / Cyberpunk",
        description="Technology-driven stories exploring humanity through the lens of future worlds.",
        narrative_defaults={
            "tone": "cerebral, atmospheric, philosophically provocative",
            "pov_default": "third person limited",
            "prose_style": "precise, technical, interspersed with poetic imagery",
            "dialogue_style": "clipped professional jargon mixed with street slang",
            "pacing_preference": "measured buildup with high-concept payoffs",
            "themes": ["what makes us human", "technology as double-edged sword", "freedom vs control"],
            "taboos": [],
            "inspirations": ["Ghost in the Shell", "Blame!", "Planetes", "Cyberpunk: Edgerunners"],
        },
        visual_defaults={
            "art_style": "manhwa",
            "sub_style": "cyberpunk sci-fi",
            "line_weight": "precise, technical, hard edges",
            "color_palette": ["neon cyan", "hot magenta", "deep purple", "chrome silver", "midnight black"],
            "color_mode": "neon accents against dark backgrounds",
            "shading_style": "hard-edge digital, rim lighting",
            "background_detail": "hyper-detailed cityscapes and tech interfaces",
            "character_proportions": "sleek, augmented, sharp silhouettes",
            "prompt_style_tokens": "cyberpunk manhwa, neon lighting, holographic effects, futuristic city, chrome and glass, rain-slicked streets",
        },
        suggested_structure="save_the_cat",
        mood_lighting_overrides={
            "tense": "flickering neon, surveillance camera grain, harsh fluorescent",
            "action": "neon streaks, bullet traces, holographic shattering",
            "melancholic": "rain in neon light, lone figure, reflection in puddles",
            "mysterious": "data streams, dark server rooms, single monitor glow",
        },
        common_tropes=[
            "augmentation vs humanity", "megacorp conspiracy", "rogue AI",
            "memory manipulation", "underground resistance", "the ghost in the machine",
        ],
        anti_tropes=[
            "technology is always evil", "AI villain with no nuance",
            "future without cultural diversity", "handwave hard science",
        ],
        reference_works=["Ghost in the Shell", "Blame!", "Akira", "Planetes", "Cyberpunk: Edgerunners"],
        panel_style_hints={
            "tech": "HUD overlays, data readouts in panel borders, wire-frame callouts",
            "action": "motion blur, neon trails, shattered glass",
            "atmosphere": "extreme wide shots of megastructures, tiny humans in vast spaces",
            "quiet": "close-up on human detail — fingerprint, eye, breath — contrasting with tech",
        },
    ),
    "horror": GenrePreset(
        genre_id="horror",
        display_name="Horror / Thriller",
        description="Fear-driven narratives with escalating dread, disturbing imagery, and psychological tension.",
        narrative_defaults={
            "tone": "dread-soaked, claustrophobic, punctuated by shock",
            "pov_default": "first person or tight third person limited",
            "prose_style": "sensory, paranoid, unreliable narration",
            "dialogue_style": "sparse, fragmented, what's unsaid is scarier",
            "pacing_preference": "slow dread escalation with sudden violence",
            "themes": ["the unknown", "loss of control", "what lurks beneath normalcy"],
            "taboos": [],
            "inspirations": ["Junji Ito", "Sweet Home", "Parasyte", "Uzumaki"],
        },
        visual_defaults={
            "art_style": "manga",
            "sub_style": "horror",
            "line_weight": "scratchy, uneven, increasingly distorted",
            "color_palette": ["blood red", "sickly yellow", "corpse grey", "void black", "bile green"],
            "color_mode": "desaturated with sudden color shocks",
            "shading_style": "heavy crosshatching, ink pooling in shadows",
            "background_detail": "detailed to uncanny, warping in horror moments",
            "character_proportions": "normal becoming distorted, subtle wrongness",
            "prompt_style_tokens": "horror manga, heavy shadows, grotesque detail, unsettling composition, distorted anatomy, ink-heavy art",
        },
        suggested_structure="save_the_cat",
        mood_lighting_overrides={
            "dread": "single dim light source, everything else in shadow",
            "shock": "sudden harsh white flash, overexposure",
            "paranoia": "surveillance feel, off-center framing, empty corners",
            "aftermath": "flat grey light, clinical, too-bright fluorescent",
        },
        common_tropes=[
            "the slow reveal", "body horror transformation", "isolation",
            "the thing that follows", "unreliable reality", "the door that shouldn't be opened",
        ],
        anti_tropes=[
            "jump scares without buildup", "gore for gore's sake",
            "victims who make impossibly stupid choices", "monster fully revealed too early",
        ],
        reference_works=["Uzumaki", "Sweet Home", "Parasyte", "The Drifting Classroom", "Hideout"],
        panel_style_hints={
            "dread": "increasingly narrow panels, claustrophobic layouts",
            "shock": "full-page reveal after sequence of small panels",
            "paranoia": "panels with too much empty space, figures at edges",
            "body_horror": "detailed anatomical distortion, texture-heavy rendering",
        },
    ),
    "isekai": GenrePreset(
        genre_id="isekai",
        display_name="Isekai / Progression Fantasy",
        description="Transported to another world with game-like systems, power progression, and world exploration.",
        narrative_defaults={
            "tone": "adventurous, strategic, satisfying power growth",
            "pov_default": "first person or close third person",
            "prose_style": "clear, systematic when describing powers, vivid for world discovery",
            "dialogue_style": "inner monologue heavy, strategic thinking, party banter",
            "pacing_preference": "steady progression with milestone payoffs",
            "themes": ["second chances", "using knowledge from past life", "building something from nothing"],
            "taboos": [],
            "inspirations": ["Solo Leveling", "Omniscient Reader's Viewpoint", "Mushoku Tensei", "Overlord"],
        },
        visual_defaults={
            "art_style": "manhwa",
            "sub_style": "isekai progression",
            "line_weight": "clean, sharp, detailed for status windows",
            "color_palette": ["royal purple", "gold", "ice blue", "forest green", "ember orange"],
            "color_mode": "vibrant full color with glowing effects for skills",
            "shading_style": "cel shading with glow effects for magic/skills",
            "background_detail": "detailed fantasy environments, dungeon atmosphere",
            "character_proportions": "stylish, slightly idealized, clear silhouettes",
            "prompt_style_tokens": "isekai manhwa, fantasy world, glowing skill effects, status window UI, vibrant colors, detailed environments",
        },
        suggested_structure="save_the_cat",
        mood_lighting_overrides={
            "dungeon": "torch and magic-glow lighting, deep shadows",
            "level_up": "radiant golden light, particle effects, divine glow",
            "town": "warm medieval marketplace lighting",
            "boss_fight": "dramatic backlighting, arena spotlight effect",
        },
        common_tropes=[
            "status windows and skill trees", "overpowered protagonist hiding strength",
            "dungeon crawling", "party formation", "guild registration scene",
            "the item nobody else wanted is actually the best",
        ],
        anti_tropes=[
            "harem collecting without character depth", "zero struggle power fantasy",
            "game system without narrative purpose", "world that exists only as backdrop",
        ],
        reference_works=["Solo Leveling", "Omniscient Reader's Viewpoint", "Tower of God", "Overlord"],
        panel_style_hints={
            "power_up": "full-page with radial effects, status window overlay",
            "action": "dynamic vertical panels for manhwa scroll, impact frames",
            "exploration": "wide panoramic shots of new environments",
            "system": "clean UI overlays, stat comparison panels",
        },
    ),
}


def get_preset(genre_id: str) -> GenrePreset | None:
    """Get a genre preset by ID."""
    return _PRESETS.get(genre_id)


def list_presets() -> list[GenrePreset]:
    """Return all available genre presets."""
    return list(_PRESETS.values())


def get_preset_ids() -> list[str]:
    """Return all genre preset IDs."""
    return list(_PRESETS.keys())
