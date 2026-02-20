"""antigravity prompt - image prompt generation commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from antigravity_tool.core.project import Project
from antigravity_tool.core.context_compiler import ContextCompiler
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.core.workflow import WorkflowState
from antigravity_tool.utils.display import console, print_success, print_info, print_prompt_output
from antigravity_tool.utils.io import ensure_dir

app = typer.Typer(help="Image prompt generation commands.")


@app.command("generate")
def generate(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
) -> None:
    """Generate image prompts for all panels in a chapter."""
    project = Project.find()
    compiler = ContextCompiler(project)
    engine = TemplateEngine(project.user_prompts_dir)

    ctx = compiler.compile_for_step(
        "image_prompt_generation",
        chapter_num=chapter,
    )
    ctx["chapter_num"] = chapter
    prompt = engine.render("panel/panel_to_image_prompt.md.j2", **ctx)

    WorkflowState(project.path).mark_step_started("image_prompt_generation")

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Image Prompts: Chapter {chapter}")


@app.command("compile")
def compile_prompts(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
) -> None:
    """Compile and display assembled image prompts for panels that have DNA blocks."""
    project = Project.find()
    panels = project.load_panels(chapter)
    characters = project.load_all_characters(filter_secrets=False)
    style = project.load_visual_style_guide()

    if not panels:
        print_info(f"No panels found in chapter {chapter}.")
        return

    # Build DNA block map
    dna_blocks = {}
    for char in characters:
        if char.dna.face.face_shape:
            dna_blocks[char.id] = char.dna.to_prompt_block()
            dna_blocks[char.name] = char.dna.to_prompt_block()

    style_tokens = style.prompt_style_tokens if style else ""

    for panel in panels:
        compiled = panel.compile_image_prompt(dna_blocks, style_tokens)
        console.print(f"\n[bold cyan]Page {panel.page_number} Panel {panel.panel_number}[/]")
        console.print(f"[dim]Shot: {panel.shot_type.value} | Angle: {panel.camera_angle.value}[/]")
        console.print(compiled)
        console.print()


@app.command("export")
def export(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    format: str = typer.Option("txt", "--format", "-f", help="Export format: txt, json"),
) -> None:
    """Export image prompts to files."""
    project = Project.find()
    panels = project.load_panels(chapter)
    characters = project.load_all_characters(filter_secrets=False)
    style = project.load_visual_style_guide()

    if not panels:
        print_info(f"No panels found in chapter {chapter}.")
        return

    dna_blocks = {}
    for char in characters:
        if char.dna.face.face_shape:
            dna_blocks[char.id] = char.dna.to_prompt_block()
            dna_blocks[char.name] = char.dna.to_prompt_block()

    style_tokens = style.prompt_style_tokens if style else ""

    export_dir = ensure_dir(project.exports_dir / f"image_prompts" / f"chapter-{chapter:02d}")

    for panel in panels:
        compiled = panel.compile_image_prompt(dna_blocks, style_tokens)
        filename = f"page-{panel.page_number:02d}-panel-{panel.panel_number:02d}"

        if format == "json":
            import json
            data = {
                "page": panel.page_number,
                "panel": panel.panel_number,
                "shot_type": panel.shot_type.value,
                "camera_angle": panel.camera_angle.value,
                "prompt": compiled,
                "negative_prompt": panel.negative_prompt or "",
            }
            (export_dir / f"{filename}.json").write_text(json.dumps(data, indent=2))
        else:
            (export_dir / f"{filename}.txt").write_text(compiled)

    print_success(f"Exported {len(panels)} panel prompts to {export_dir}")
