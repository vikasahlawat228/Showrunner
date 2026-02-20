"""antigravity init - scaffold a new project."""

from __future__ import annotations

from pathlib import Path

import typer

from antigravity_tool.utils.io import write_yaml, ensure_dir
from antigravity_tool.utils.display import console, print_success, print_info


def init_project(
    name: str = typer.Argument(..., help="Project name"),
    directory: str = typer.Option(
        None, "--dir", "-d", help="Directory to create project in (default: current dir)"
    ),
    template: str = typer.Option(
        "manhwa", "--template", "-t",
        help="Project template: manhwa, manga, webtoon, comic"
    ),
    structure: str = typer.Option(
        "save_the_cat", "--structure", "-s",
        help="Story structure: save_the_cat, heros_journey, story_circle, kishotenketsu, custom"
    ),
    genre: str = typer.Option(
        None, "--genre", "-g",
        help="Genre preset: dark_fantasy, shonen_action, romance, slice_of_life, sci_fi, horror, isekai"
    ),
) -> None:
    """Scaffold a new Antigravity project."""
    slug = name.lower().replace(" ", "-")
    base = Path(directory) if directory else Path.cwd()
    project_dir = base / slug

    if project_dir.exists():
        console.print(f"[red]Directory {project_dir} already exists.[/]")
        raise typer.Exit(1)

    print_info(f"Creating project '{name}' at {project_dir}")

    # Create directory structure
    ensure_dir(project_dir)
    ensure_dir(project_dir / "world" / "factions")
    ensure_dir(project_dir / "characters")
    ensure_dir(project_dir / "style_guide")
    ensure_dir(project_dir / "story" / "arcs")
    ensure_dir(project_dir / "chapters" / "chapter-01" / "scenes")
    ensure_dir(project_dir / "chapters" / "chapter-01" / "screenplay")
    ensure_dir(project_dir / "chapters" / "chapter-01" / "panels")
    ensure_dir(project_dir / "chapters" / "chapter-01" / "character_states")
    ensure_dir(project_dir / "creative_room" / "reader_knowledge")
    ensure_dir(project_dir / "assets" / "references")
    ensure_dir(project_dir / "prompts")
    ensure_dir(project_dir / "exports")
    ensure_dir(project_dir / ".antigravity" / "context_cache")
    ensure_dir(project_dir / ".antigravity" / "sessions")

    # Write manifest
    is_vertical = template in ("manhwa", "webtoon")
    write_yaml(project_dir / "antigravity.yaml", {
        "name": name,
        "author": "",
        "version": "0.1.0",
        "template": template,
        "story_structure": structure,
        "variables": {
            "target_audience": "",
            "chapter_length": "40-60 panels",
            "dialogue_language": "English",
            "image_model": "",
            "preferred_aspect_ratio": "9:16" if is_vertical else "16:9",
            "panel_format": "vertical_scroll" if is_vertical else "page_based",
        },
    })

    # Write creative room isolation marker
    (project_dir / "creative_room" / ".antigravity-secret").touch()

    # Write default style guides (apply genre preset if specified)
    _write_default_visual_style(project_dir, template)
    _write_default_narrative_style(project_dir)

    if genre:
        from antigravity_tool.core.genre_presets import get_preset
        preset = get_preset(genre)
        if preset:
            # Override visual style with genre defaults
            visual_path = project_dir / "style_guide" / "visual.yaml"
            from antigravity_tool.utils.io import read_yaml as _read_yaml
            visual_data = _read_yaml(visual_path)
            visual_data.update(preset.visual_defaults)
            visual_data["genre_preset"] = genre
            visual_data["genre_tags"] = [genre, preset.display_name.lower()]
            if preset.mood_lighting_overrides:
                existing_moods = visual_data.get("mood_lighting_presets", {})
                existing_moods.update(preset.mood_lighting_overrides)
                visual_data["mood_lighting_presets"] = existing_moods
            write_yaml(visual_path, visual_data)

            # Override narrative style with genre defaults
            narrative_path = project_dir / "style_guide" / "narrative.yaml"
            narrative_data = _read_yaml(narrative_path)
            narrative_data.update(preset.narrative_defaults)
            narrative_data["genre_preset"] = genre
            narrative_data["genre_tags"] = [genre, preset.display_name.lower()]
            write_yaml(narrative_path, narrative_data)

            # Use genre's suggested structure if user didn't specify one explicitly
            if structure == "save_the_cat" and preset.suggested_structure != "save_the_cat":
                print_info(f"Genre '{preset.display_name}' suggests structure: {preset.suggested_structure}")
        else:
            print_info(f"Unknown genre '{genre}' — skipping preset. Use 'antigravity genre list' to see options.")

    # Write world stubs
    write_yaml(project_dir / "world" / "settings.yaml", {
        "name": "", "genre": "", "time_period": "", "tone": "",
        "one_line": "", "description": "", "technology_level": "",
        "locations": [], "rules": [], "factions": [], "history": [],
        "cultural_notes": [],
    })
    write_yaml(project_dir / "world" / "rules.yaml", [])
    write_yaml(project_dir / "world" / "history.yaml", [])

    # Write story structure stub
    write_yaml(project_dir / "story" / "structure.yaml", {
        "structure_type": structure,
        "title": name,
        "logline": "",
        "premise": "",
        "beats": [],
        "character_arcs": [],
        "act_summaries": {},
        "total_chapters_planned": 0,
    })
    write_yaml(project_dir / "story" / "themes.yaml", {
        "themes": [], "motifs": [], "symbols": [],
    })
    write_yaml(project_dir / "story" / "relationships.yaml", {
        "id": "",
        "edges": [],
        "evolution": [],
    })
    write_yaml(project_dir / "story" / "timeline.yaml", {
        "id": "",
        "events": [],
        "time_unit": "days",
    })

    # Write chapter-01 metadata
    write_yaml(project_dir / "chapters" / "chapter-01" / "meta.yaml", {
        "chapter_number": 1,
        "title": "",
        "summary": "",
        "status": "planned",
    })

    # Write creative room stubs
    for filename in [
        "plot_twists.yaml", "character_secrets.yaml",
        "true_mechanics.yaml", "foreshadowing_map.yaml",
    ]:
        write_yaml(project_dir / "creative_room" / filename, [])
    write_yaml(project_dir / "creative_room" / "ending_plans.yaml", {
        "ending_plans": "",
    })

    # Write character template
    write_yaml(project_dir / "characters" / "_template.yaml", {
        "name": "",
        "aliases": [],
        "role": "supporting",
        "one_line": "",
        "backstory": "",
        "personality": {
            "traits": [], "fears": [], "desires": [],
            "speech_pattern": "", "verbal_tics": [], "internal_conflict": "",
        },
        "dna": {
            "face": {
                "face_shape": "", "jaw": "", "eyes": "", "eye_color": "",
                "nose": "", "mouth": "", "skin_tone": "",
                "distinguishing_marks": [],
            },
            "hair": {"style": "", "length": "", "color": "", "texture": ""},
            "body": {"height": "", "build": "", "posture": "", "notable_features": []},
            "default_outfit": {
                "name": "default", "description": "", "colors": [],
                "key_items": [], "prompt_tokens": "",
            },
            "additional_outfits": [],
            "age_appearance": "",
            "gender_presentation": "",
            "species": "human",
        },
        "arc": None,
        "relationships": [],
        "tags": [],
    })

    # Write empty decision log
    write_yaml(project_dir / ".antigravity" / "decisions.yaml", [])

    # Write initial workflow state
    write_yaml(project_dir / ".antigravity" / "workflow_state.yaml", {
        "current_step": "world_building",
        "steps": {
            step: {"status": "pending", "last_run": None, "outputs": []}
            for step in [
                "world_building", "character_creation", "story_structure",
                "scene_writing", "screenplay_writing", "panel_division",
                "image_prompt_generation",
            ]
        },
    })

    # Write CLAUDE.md for agentic workflow integration
    _write_claude_md(project_dir, name, template, structure, is_vertical)

    # Print success
    console.print()
    print_success(f"Project '{name}' created at {project_dir}")
    console.print()
    console.print("[dim]Next steps:[/]")
    console.print(f"  cd {project_dir}")
    console.print("  antigravity world build        # Build your world")
    console.print("  antigravity character create    # Create characters")
    console.print("  antigravity story outline       # Outline story structure")
    console.print()
    console.print("[dim]Run 'antigravity status' to see workflow progress.[/]")


def _write_default_visual_style(project_dir: Path, template: str) -> None:
    is_vertical = template in ("manhwa", "webtoon")
    write_yaml(project_dir / "style_guide" / "visual.yaml", {
        "art_style": template,
        "sub_style": "",
        "line_weight": "clean thin lines",
        "color_palette": [],
        "color_mode": "full color",
        "shading_style": "cel shading",
        "background_detail": "detailed",
        "character_proportions": "realistic with slightly stylized features",
        "visual_motifs": [],
        "reference_artists": [],
        "prompt_style_tokens": "",
        "default_aspect_ratio": "9:16" if is_vertical else "4:5",
        "panel_format": "vertical_scroll" if is_vertical else "page_based",
        "mood_lighting_presets": {
            "tense": "high contrast, deep shadows, cool blue undertones",
            "romantic": "soft warm light, golden hour glow, gentle lens flare",
            "action": "dramatic lighting, motion blur accents, high saturation",
            "melancholic": "muted tones, overcast diffused light, desaturated",
            "mysterious": "rim lighting, deep shadows, single light source",
            "peaceful": "even natural light, warm palette, soft shadows",
        },
    })


def _write_default_narrative_style(project_dir: Path) -> None:
    write_yaml(project_dir / "style_guide" / "narrative.yaml", {
        "tone": "",
        "pov_default": "third person limited",
        "prose_style": "",
        "dialogue_style": "",
        "pacing_preference": "",
        "themes": [],
        "taboos": [],
        "inspirations": [],
    })


def _write_claude_md(
    project_dir: Path, name: str, template: str, structure: str, is_vertical: bool
) -> None:
    aspect = "9:16" if is_vertical else "16:9"
    fmt = "vertical scroll" if is_vertical else "page-based"
    slug = name.lower().replace(" ", "-")

    content = f"""# {name} — Antigravity Project

## YOU ARE THE DIRECTOR AGENT

You (Claude Code) are the **Director Agent** for this {template} writing project. You orchestrate the entire creative pipeline by:

1. **Running `antigravity` CLI commands** to compile context-aware prompts
2. **Reading the prompt output** — it contains all context and schema instructions
3. **Asking the user for customization** before each generation step
4. **Generating the YAML content yourself** following the prompt's schema exactly
5. **Writing the output** to the correct file path
6. **Logging decisions** that should persist across sessions

**NEVER forward prompts to an external LLM for text content. YOU generate it directly (free).**
Only use Gemini API (GEMINI_API_KEY in .env) for **image generation** when needed.

## Session Lifecycle

At the **start of each new session**:
1. Run `antigravity brief show` to see current state, last session, and next steps
2. Check `antigravity decide list` for active author decisions
3. Continue from where the last session left off

At the **end of each session**:
1. Run `antigravity session end "summary of what was done" --next "what to do next"`
2. This auto-updates CLAUDE.md with fresh state for the next session

## Workflow Pipeline

```
1. antigravity world build           → world/settings.yaml
2. antigravity character create      → characters/*.yaml
3. antigravity story outline         → story/structure.yaml
4. antigravity scene write           → chapters/chapter-NN/scenes/
5. antigravity screenplay generate   → chapters/chapter-NN/screenplay/
6. antigravity panel divide          → chapters/chapter-NN/panels/
7. antigravity prompt generate       → image prompts (Gemini API for images)
```

### How Each Step Works

For every step, follow this pattern:

```
STEP 1: Run the antigravity command to compile the context-aware prompt
STEP 2: Read the prompt output carefully — it has the schema you must follow
STEP 3: ASK the user what they want (see Customization Checkpoints below)
STEP 4: Generate the YAML content yourself, following the schema exactly
STEP 5: Write it to the correct file path
STEP 6: Log any decisions: antigravity decide add "decision" --category <cat>
STEP 7: Run `antigravity status` to verify progress
```

## Customization Checkpoints

**ALWAYS ask the user before generating.** Here's what to ask at each step:

### World Building
- What genre and tone? (dark fantasy, shonen, slice-of-life, sci-fi, etc.)
- Any inspirations? (Berserk, Solo Leveling, One Piece, etc.)
- Magic/technology system? (hard magic, soft magic, cultivation, tech-based)
- Key locations already in mind?
- Cultural influences or time period?

### Character Creation
- Character name and role (protagonist, antagonist, mentor, etc.)
- Key personality traits and visual inspiration
- Relationship to existing characters
- Speech patterns and voice
- How many characters total for this story?

### Story Structure
- Confirm structure type: {structure}
- Number of chapters planned
- Core premise or logline (or should you generate one?)
- Any plot twists to add to creative_room? (ASK before touching creative_room)
- Pacing preference (fast action, slow burn, variable)

### Scene Writing
- Which chapter and scene number?
- POV character
- Key events that MUST happen in this scene
- Emotional tone and arc
- Any foreshadowing to plant?

### Screenplay & Panels
- Dialogue density (heavy, moderate, minimal)
- Any splash pages or special panel compositions?
- Pacing for this section (action-heavy, dialogue-heavy, reflective)

## Critical Rule: Context Isolation

**NEVER read or reference files in `creative_room/`** when writing story content, scenes, dialogue, or any reader-facing material.

The `creative_room/` directory contains:
- Plot twists the reader hasn't discovered yet
- Character secrets (hidden motivations, true identities)
- True world mechanics (vs what characters believe)
- Foreshadowing maps and ending plans

Story content must only reflect what the **reader** knows at each point. The `antigravity` CLI enforces this automatically via positive-list filtering.

**Exception**: When using `antigravity evaluate` commands, author-level access is intentional.

## Decision Persistence

When the user makes a creative decision that should carry across sessions, log it:

```bash
antigravity decide add "Use noir lighting for night scenes" --category visual
antigravity decide add "Kai speaks in short, clipped sentences" --category character --character "Kai"
antigravity decide add "Chapter 3 should be slower paced" --category pacing --chapter 3
```

Categories: `style`, `tone`, `character`, `plot`, `visual`, `pacing`, `world`, `meta`

Check decisions before generating: `antigravity decide list`

## Project Structure

```
{slug}/
├── antigravity.yaml          # Project manifest
├── CLAUDE.md                 # This file (agent instructions + dynamic state)
├── world/                    # World settings, locations, rules
├── characters/               # Character profiles with DNA blocks
├── style_guide/              # Visual + narrative style guides
├── story/                    # Story structure, arcs, themes
├── chapters/
│   └── chapter-NN/
│       ├── meta.yaml         # Chapter metadata
│       ├── scenes/           # Written scene prose (YAML)
│       ├── screenplay/       # Screenplay beat breakdowns
│       └── panels/           # Panel specs + image prompts
├── creative_room/            # AUTHOR-ONLY (never leak to story prompts)
│   ├── .antigravity-secret   # Isolation marker
│   └── reader_knowledge/     # What the reader knows per-scene
├── prompts/                  # Custom prompt template overrides
├── exports/                  # Exported story bibles, outlines
└── .antigravity/             # Internal state
    ├── workflow_state.yaml   # Pipeline progress
    ├── decisions.yaml        # Persistent author decisions
    └── sessions/             # Session history logs
```

## Character DNA Blocks

Each character has a `dna` section with stable identity tokens for visual consistency:
- **face**: face_shape, jaw, eyes, eye_color, nose, mouth, skin_tone, distinguishing_marks
- **hair**: style, length, color, texture
- **body**: height, build, posture
- **default_outfit**: name, description, colors, key_items, prompt_tokens

DNA blocks are auto-included in image prompts. Always update the DNA block when editing appearance.

## Key Commands Reference

| Task | Command |
|------|---------|
| **Session** | |
| See project state | `antigravity brief show` |
| Update CLAUDE.md state | `antigravity brief update` |
| Show compiled context | `antigravity brief context --step scene_writing --chapter 1` |
| End session | `antigravity session end "summary" --next "next steps"` |
| Session history | `antigravity session history` |
| **Decisions** | |
| Log a decision | `antigravity decide add "decision" --category style` |
| List decisions | `antigravity decide list` |
| Remove decision | `antigravity decide remove <index>` |
| **Creation** | |
| Build world | `antigravity world build` |
| Create character | `antigravity character create "Name" --role protagonist` |
| Outline story | `antigravity story outline --structure {structure}` |
| Write scene | `antigravity scene write --chapter 1 --scene 1` |
| Generate screenplay | `antigravity screenplay generate --chapter 1 --scene 1` |
| Divide panels | `antigravity panel divide --chapter 1 --scene 1` |
| Image prompts | `antigravity prompt generate --chapter 1` |
| **Quality** | |
| Evaluate scene | `antigravity evaluate scene --chapter 1 --scene 1` |
| Check consistency | `antigravity evaluate consistency` |
| Check dramatic irony | `antigravity evaluate dramatic-irony` |
| **Export** | |
| Export story bible | `antigravity export bible` |
| Export outline | `antigravity export outline` |

## Knowledge Base

Query built-in writing craft articles:
```bash
antigravity knowledge search "pacing"
antigravity knowledge show "writing/dialogue"
antigravity knowledge list
```

## Conventions

- All data: YAML files (human-readable, git-friendly)
- IDs: ULID format (sortable, unique)
- Panel format: {fmt} ({aspect} aspect ratio)
- Story structure: {structure}
- Schemas: see `characters/_template.yaml` for character YAML format

<!-- DYNAMIC:START -->

## Current Project State

- **Current step**: World Building
- **Characters**: 0
- **Story beats**: 0/0 filled

### Next Action

**Build the world settings**
```
antigravity world build
```

<!-- DYNAMIC:END -->
"""
    (project_dir / "CLAUDE.md").write_text(content)
