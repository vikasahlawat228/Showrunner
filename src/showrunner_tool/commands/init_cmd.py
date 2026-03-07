"""showrunner init - scaffold a new project."""

from __future__ import annotations

from pathlib import Path

import typer

from showrunner_tool.utils.io import write_yaml, ensure_dir
from showrunner_tool.utils.display import console, print_success, print_info


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
    """Scaffold a new Showrunner project."""
    slug = name.lower().replace(" ", "-")
    base = Path(directory) if directory else Path.cwd()
    project_dir = base / slug

    if project_dir.exists():
        console.print(f"[red]Directory {project_dir} already exists.[/]")
        raise typer.Exit(1)

    print_info(f"Creating project '{name}' at {project_dir}")

    # Create directory structure
    ensure_dir(project_dir)

    # IDE-friendly flat structure (writers use these directly)
    ensure_dir(project_dir / "fragment")          # Scene prose
    ensure_dir(project_dir / "containers")        # Research, notes, generic data
    ensure_dir(project_dir / "idea_card")         # Brainstorm ideas
    ensure_dir(project_dir / "pipeline_def")      # Workflow definitions

    # Web UI structure (chapters/panels/screenplay for visual editing)
    ensure_dir(project_dir / "chapters" / "s1" / "chapter-01" / "scenes")
    ensure_dir(project_dir / "chapters" / "s1" / "chapter-01" / "screenplay")
    ensure_dir(project_dir / "chapters" / "s1" / "chapter-01" / "panels")
    ensure_dir(project_dir / "chapters" / "s1" / "chapter-01" / "character_states")

    # World building (locations as per-file YAMLs for scaling)
    ensure_dir(project_dir / "world" / "locations")
    ensure_dir(project_dir / "world" / "factions")

    # Character & style guides
    ensure_dir(project_dir / "characters")
    ensure_dir(project_dir / "style_guide")

    # Story planning
    ensure_dir(project_dir / "story" / "arcs")

    # Creative room (author-only secrets, never leak to story)
    ensure_dir(project_dir / "creative_room" / "reader_knowledge")

    # Assets & exports
    ensure_dir(project_dir / "assets" / "references")
    ensure_dir(project_dir / "prompts")
    ensure_dir(project_dir / "exports")

    # Internal state (databases, caches, sessions)
    ensure_dir(project_dir / ".showrunner" / "context_cache")
    ensure_dir(project_dir / ".showrunner" / "sessions")
    ensure_dir(project_dir / ".showrunner" / "trash")
    ensure_dir(project_dir / ".showrunner" / "inbox")

    # Write manifest
    is_vertical = template in ("manhwa", "webtoon")
    write_yaml(project_dir / "showrunner.yaml", {
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
    (project_dir / "creative_room" / ".showrunner-secret").touch()

    # Write default style guides (apply genre preset if specified)
    _write_default_visual_style(project_dir, template)
    _write_default_narrative_style(project_dir)

    if genre:
        from showrunner_tool.core.genre_presets import get_preset
        preset = get_preset(genre)
        if preset:
            # Override visual style with genre defaults
            visual_path = project_dir / "style_guide" / "visual.yaml"
            from showrunner_tool.utils.io import read_yaml as _read_yaml
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
            print_info(f"Unknown genre '{genre}' — skipping preset. Use 'showrunner genre list' to see options.")

    # Write world stubs
    write_yaml(project_dir / "world" / "settings.yaml", {
        "name": "", "genre": "", "time_period": "", "tone": "",
        "one_line": "", "description": "", "technology_level": "",
        "location_refs": [],  # Per-file locations in world/locations/ (avoid monolith)
        "rules": [], "factions": [], "history": [],
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

    # Write directory guide READMEs for IDE users
    _write_directory_guides(project_dir)

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
    write_yaml(project_dir / ".showrunner" / "decisions.yaml", [])

    # Write initial workflow state
    write_yaml(project_dir / ".showrunner" / "workflow_state.yaml", {
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

    # Write project-level .gitignore
    _write_gitignore(project_dir)

    # Auto-populate CLAUDE.md with initial briefing (P0.2)
    # This ensures the DYNAMIC section has useful state from day 1
    try:
        from showrunner_tool.core.briefing import BriefingGenerator
        from showrunner_tool.core.project import Project

        project = Project(project_dir)
        briefing_gen = BriefingGenerator(project)
        briefing_gen.update_claude_md()
        print_info("✅ Auto-populated CLAUDE.md with initial project state")
    except Exception as e:
        print_info(f"⚠️  Could not auto-populate briefing: {e}")
        print_info("   Run 'showrunner brief update' manually if needed")

    # Print success
    console.print()
    print_success(f"Project '{name}' created at {project_dir}")
    console.print()
    console.print("[dim]Next steps:[/]")
    console.print(f"  cd {project_dir}")
    console.print("  showrunner world build        # Build your world")
    console.print("  showrunner character create    # Create characters")
    console.print("  showrunner story outline       # Outline story structure")
    console.print()
    console.print("[dim]Run 'showrunner status' to see workflow progress.[/]")


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

    content = f"""# {name} — Showrunner Project

## YOU ARE THE DIRECTOR AGENT

You (Claude Code) are the **Director Agent** for this {template} writing project. You orchestrate the entire creative pipeline by:

1. **Running `showrunner` CLI commands** to compile context-aware prompts
2. **Reading the prompt output** — it contains all context and schema instructions
3. **Asking the user for customization** before each generation step
4. **Generating the YAML content yourself** following the prompt's schema exactly
5. **Writing the output** to the correct file path
6. **Logging decisions** that should persist across sessions

**NEVER forward prompts to an external LLM for text content. YOU generate it directly (free).**
Only use Gemini API (GEMINI_API_KEY in .env) for **image generation** when needed.

## Session Lifecycle

At the **start of each new session**:
1. Run `showrunner brief show` to see current state, last session, and next steps
2. Check `showrunner decide list` for active author decisions
3. Continue from where the last session left off

At the **end of each session**:
1. Run `showrunner session end "summary of what was done" --next "what to do next"`
2. This auto-updates CLAUDE.md with fresh state for the next session

## Workflow Pipeline

```
1. showrunner world build           → world/settings.yaml
2. showrunner character create      → characters/*.yaml
3. showrunner story outline         → story/structure.yaml
4. showrunner scene write           → fragment/*.yaml OR chapters/s1/chapter-NN/scenes/
5. showrunner screenplay generate   → chapters/s1/chapter-NN/screenplay/
6. showrunner panel divide          → chapters/s1/chapter-NN/panels/
7. showrunner prompt generate       → image prompts (Gemini API for images)
```

### How Each Step Works

For every step, follow this pattern:

```
STEP 1: Run the showrunner command to compile the context-aware prompt
STEP 2: Read the prompt output carefully — it has the schema you must follow
STEP 3: ASK the user what they want (see Customization Checkpoints below)
STEP 4: Generate the YAML content yourself, following the schema exactly
STEP 5: Write it to the correct file path
STEP 6: Log any decisions: showrunner decide add "decision" --category <cat>
STEP 7: Run `showrunner status` to verify progress
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

Story content must only reflect what the **reader** knows at each point. The `showrunner` CLI enforces this automatically via positive-list filtering.

**Exception**: When using `showrunner evaluate` commands, author-level access is intentional.

## Decision Persistence

When the user makes a creative decision that should carry across sessions, log it:

```bash
showrunner decide add "Use noir lighting for night scenes" --category visual
showrunner decide add "Kai speaks in short, clipped sentences" --category character --character "Kai"
showrunner decide add "Chapter 3 should be slower paced" --category pacing --chapter 3
```

Categories: `style`, `tone`, `character`, `plot`, `visual`, `pacing`, `world`, `meta`

Check decisions before generating: `showrunner decide list`

## Project Structure

```
{slug}/
├── showrunner.yaml          # Project manifest
├── CLAUDE.md                 # This file (agent instructions + dynamic state)
│
├── 📝 WRITING (IDE-friendly, use these directly)
├── fragment/                 # Scene prose — your main writing goes here
├── containers/               # Research, notes, character profiles
│   ├── research_topic/
│   └── ...
├── idea_card/                # Brainstorm ideas, plot twists, "what ifs"
├── pipeline_def/             # Custom workflow definitions
│
├── 🎨 WORLD BUILDING
├── world/
│   ├── settings.yaml         # Genre, tone, era, tech level
│   ├── locations/            # Per-file location YAMLs (scales well)
│   ├── factions/             # Factions and political structure
│   ├── rules.yaml            # Magic/tech/world rules
│   └── history.yaml          # Historical timeline
├── characters/               # Character profiles with DNA blocks
├── style_guide/              # Visual + narrative style guides
│
├── 📊 PLANNING & STRUCTURE
├── story/                    # Story arcs, beats, themes, timeline
├── chapters/
│   ├── s1/                   # Season 1
│   │   ├── chapter-01/
│   │   │   ├── meta.yaml     # Chapter metadata
│   │   │   ├── scenes/       # Scene breakdowns (alt: use fragment/)
│   │   │   ├── screenplay/   # Screenplay beat structures
│   │   │   └── panels/       # Panel specs + image prompts
│   │   └── ...
│   └── s2/                   # Season 2 (no collision with s1)
│
├── 🤫 AUTHOR-ONLY SECRETS (never leak to story!)
├── creative_room/
│   ├── .showrunner-secret    # Isolation marker
│   ├── plot_twists.yaml      # Surprises the reader hasn't learned
│   ├── character_secrets.yaml
│   ├── foreshadowing_map.yaml
│   ├── reader_knowledge/     # What reader knows per-scene
│   └── ending_plans.yaml
│
├── 🎬 ASSETS & EXPORTS
├── assets/
│   └── references/           # Reference images for consistency
├── prompts/                  # Custom prompt template overrides
├── exports/                  # Exported story bibles, outlines, EPUBs
│
├── 🛠️  INTERNAL STATE (auto-managed, usually git-ignored)
└── .showrunner/
    ├── workflow_state.yaml   # Pipeline progress tracking
    ├── decisions.yaml        # Persistent author decisions
    ├── inbox.yaml            # Brain dump capture inbox
    ├── sessions/             # Session history logs
    ├── trash/                # Soft-deleted files (recovery)
    └── context_cache/        # Pre-compiled context snapshots
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
| See project state | `showrunner brief show` |
| Update CLAUDE.md state | `showrunner brief update` |
| Show compiled context | `showrunner brief context --step scene_writing --chapter 1` |
| End session | `showrunner session end "summary" --next "next steps"` |
| Session history | `showrunner session history` |
| **Decisions** | |
| Log a decision | `showrunner decide add "decision" --category style` |
| List decisions | `showrunner decide list` |
| Remove decision | `showrunner decide remove <index>` |
| **Creation** | |
| Build world | `showrunner world build` |
| Create character | `showrunner character create "Name" --role protagonist` |
| Outline story | `showrunner story outline --structure {structure}` |
| Write scene | `showrunner scene write --chapter 1 --scene 1` |
| Generate screenplay | `showrunner screenplay generate --chapter 1 --scene 1` |
| Divide panels | `showrunner panel divide --chapter 1 --scene 1` |
| Image prompts | `showrunner prompt generate --chapter 1` |
| **Quality** | |
| Evaluate scene | `showrunner evaluate scene --chapter 1 --scene 1` |
| Check consistency | `showrunner evaluate consistency` |
| Check dramatic irony | `showrunner evaluate dramatic-irony` |
| **Export** | |
| Export story bible | `showrunner export bible` |
| Export outline | `showrunner export outline` |

## Knowledge Base

Query built-in writing craft articles:
```bash
showrunner knowledge search "pacing"
showrunner knowledge show "writing/dialogue"
showrunner knowledge list
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
showrunner world build
```

<!-- DYNAMIC:END -->
"""
    (project_dir / "CLAUDE.md").write_text(content)


def _write_directory_guides(project_dir: Path) -> None:
    """Write README files explaining what goes in each IDE directory."""
    guides = {
        "fragment": """# Fragment (Story Prose)

This directory contains your written story scenes. Each file is a complete scene or chapter fragment.

**Files**: `*.yaml` (one file per scene)
**Example**: `ch4-sc3.yaml` — Chapter 4, Scene 3

Each fragment should follow this structure:
```yaml
id: "<ULID>"
container_type: "fragment"
name: "Zara Enters the Forge"
attributes:
  prose: |
    The forge doors swung open. Zara could see the glow of molten metal...
  word_count: 850
  mood: "tense, dangerous"
  pov_character: "Zara"
  setting: "The Forge District"
timeline_positions:
  - "s1.arc1.ch4.sc3"
relationships: []
```

**To create**: Tell Claude Code to "write a scene" following the fragment schema.
**To cascade**: Run `showrunner cascade update fragment/ch4-sc3.yaml` after writing to auto-update character states.
""",
        "containers": """# Containers (Research, Notes, Ideas)

This directory holds structured research, notes, and reference material.

**Subdirectories**:
- `research_topic/` — Research results (feudal armor, physics, culture, etc.)
- `note/` — General notes and observations
- `character/` — Character profiles (created via CLI)
- `idea_card/` — Brainstorm ideas and plot concepts
- Other types as needed

**Files**: `*.yaml` (each container is a YAML file)
**Example**: `research_topic/feudal-armor.yaml` — Research on historical armor

**To create**: Either:
1. `showrunner capture "Research topic"` → IDE processes into a container
2. Tell Claude Code: "Research feudal armor. Save to containers/research_topic/..."

**To use**: Read containers and reference them when writing scenes. They're auto-included in context.
""",
        "idea_card": """# Idea Card (Brainstorm Storage)

This directory holds brainstorm ideas, plot twists, and "what if" scenarios.

**Files**: `*.yaml` (one file per idea)
**Example**: `what-if-zara-is-miko-sister.yaml`

Each idea card structure:
```yaml
id: "<ULID>"
container_type: "idea_card"
name: "What if Zara is Miko's long-lost sister?"
attributes:
  concept: "Zara discovers a birthmark matching Miko's..."
  novelty_score: 8
  feasibility_score: 7
  categories: ["plot-twist", "character-relationship", "season-2"]
  potential_impact: "High — completely reframes their dynamic"
relationships: []
```

**To create**: Either:
1. `showrunner capture "Zara discovers the pendant was her mother's"` → gets inbox, then process to idea_card
2. Tell Claude Code: "Brainstorm 5 plot twists for Chapter 6. Save as idea_card/..."

**To use**: Read these for brainstorm context. Mark favorites to develop further.
""",
        "pipeline_def": """# Pipeline Definitions (Workflow Automation)

This directory defines custom workflows that combine multiple steps.

**Files**: `*.yaml` (one file per pipeline)
**Example**: `research-then-write.yaml` — Pipeline that researches first, then writes a scene

**To create**: Tell Claude Code to create a custom pipeline using the schema (or `showrunner pipeline create ...`).

**To execute**: `showrunner pipeline run pipeline_def/research-then-write.yaml`
""",
    }

    for dirname, content in guides.items():
        readme_path = project_dir / dirname / "README.md"
        readme_path.write_text(content)


def _write_gitignore(project_dir: Path) -> None:
    content = """# Showrunner Story Project
# Story YAML files are tracked (they ARE the content)

# System databases (auto-rebuilt from YAML on startup)
*.db
*.db-journal
*.db-wal

# Vector store (rebuilt from YAML)
.chroma/

# Python/Node artifacts
__pycache__/
node_modules/
.next/
*.pyc

# IDE/OS artifacts
.DS_Store
.idea/
.vscode/

# Showrunner temp files
.showrunner/chat.db
.showrunner/sessions/*.tmp
"""
    (project_dir / ".gitignore").write_text(content)
