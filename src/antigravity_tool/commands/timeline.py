"""antigravity timeline - chronological story timeline management."""

from __future__ import annotations

from typing import Optional

import typer
import yaml

from antigravity_tool.core.project import Project
from antigravity_tool.core.template_engine import TemplateEngine
from antigravity_tool.schemas.timeline import Timeline, TimelineEvent, TimelineIssue
from antigravity_tool.utils.display import (
    console, create_table, print_success, print_info, print_error, print_prompt_output,
)
from antigravity_tool.utils.io import read_yaml, write_yaml
from antigravity_tool.utils.ids import generate_id

app = typer.Typer(help="Story timeline management.")


def _load_timeline(project: Project) -> Timeline:
    p = project.story_dir / "timeline.yaml"
    if not p.exists():
        return Timeline()
    data = read_yaml(p)
    return Timeline(**data)


def _save_timeline(project: Project, timeline: Timeline) -> None:
    p = project.story_dir / "timeline.yaml"
    write_yaml(p, timeline.model_dump(mode="json"))


@app.command("add")
def add_event(
    description: str = typer.Argument(..., help="Event description"),
    time: str = typer.Option(..., "--time", "-t", help="Story time (e.g. 'Day 1, Morning')"),
    sort_order: float = typer.Option(..., "--order", help="Numeric sort key for chronological ordering"),
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Chapter number"),
    scene: Optional[int] = typer.Option(None, "--scene", "-s", help="Scene number"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Location"),
    flashback: bool = typer.Option(False, "--flashback", help="Mark as flashback"),
    parallel: Optional[str] = typer.Option(None, "--parallel", "-p", help="Parallel event group ID"),
    duration: Optional[str] = typer.Option(None, "--duration", help="Duration (e.g. '2 hours')"),
) -> None:
    """Add a timeline event."""
    project = Project.find()
    timeline = _load_timeline(project)

    event = TimelineEvent(
        event_id=generate_id(),
        description=description,
        story_time=time,
        sort_order=sort_order,
        chapter_num=chapter,
        scene_num=scene,
        location=location or "",
        is_flashback=flashback,
        parallel_group=parallel,
        duration=duration,
    )

    timeline.events.append(event)
    _save_timeline(project, timeline)
    print_success(f"Added timeline event: {description}")


@app.command("show")
def show_timeline(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Filter by chapter"),
    chronological: bool = typer.Option(False, "--chrono", help="Sort chronologically instead of by narrative order"),
) -> None:
    """Display the story timeline."""
    project = Project.find()
    timeline = _load_timeline(project)

    if not timeline.events:
        print_info("Timeline is empty. Add events with 'antigravity timeline add'.")
        return

    events = timeline.events
    if chapter:
        events = timeline.get_events_for_chapter(chapter)

    if chronological:
        events = sorted(events, key=lambda e: e.sort_order)
        title = "Story Timeline (Chronological)"
    else:
        events = sorted(events, key=lambda e: (e.chapter_num or 0, e.scene_num or 0))
        title = "Story Timeline (Narrative Order)"

    if chapter:
        title += f" — Chapter {chapter}"

    table = create_table(title, [
        ("Order", "dim"),
        ("Story Time", "cyan"),
        ("Ch/Sc", "magenta"),
        ("Description", ""),
        ("Location", "green"),
        ("Flags", "yellow"),
    ])

    for event in events:
        ch_sc = ""
        if event.chapter_num:
            ch_sc = f"Ch.{event.chapter_num}"
            if event.scene_num:
                ch_sc += f" Sc.{event.scene_num}"

        flags = []
        if event.is_flashback:
            flags.append("FLASHBACK")
        if event.parallel_group:
            flags.append(f"||{event.parallel_group}")
        if event.duration:
            flags.append(event.duration)

        table.add_row(
            f"{event.sort_order:.1f}",
            event.story_time,
            ch_sc,
            event.description,
            event.location,
            " ".join(flags) if flags else "",
        )

    console.print(table)
    console.print(f"\n[dim]{len(events)} events[/]")


@app.command("narrative")
def narrative_order() -> None:
    """Show timeline in narrative (reading) order."""
    project = Project.find()
    timeline = _load_timeline(project)

    events = timeline.get_narrative_order()
    if not events:
        print_info("Timeline is empty.")
        return

    console.print("\n[bold]Timeline — Narrative Order[/]\n")
    for event in events:
        ch_sc = ""
        if event.chapter_num:
            ch_sc = f"[magenta]Ch.{event.chapter_num}[/]"
            if event.scene_num:
                ch_sc += f" [magenta]Sc.{event.scene_num}[/]"

        flashback_tag = " [yellow][FLASHBACK][/]" if event.is_flashback else ""
        parallel_tag = f" [dim](parallel: {event.parallel_group})[/]" if event.parallel_group else ""

        console.print(f"  {ch_sc} [cyan]{event.story_time}[/] — {event.description}{flashback_tag}{parallel_tag}")

    console.print()


@app.command("check")
def check_timeline() -> None:
    """Check timeline for temporal inconsistencies."""
    project = Project.find()
    timeline = _load_timeline(project)

    if not timeline.events:
        print_info("Timeline is empty. Nothing to check.")
        return

    issues = _detect_timeline_issues(timeline)

    if not issues:
        print_success(f"Timeline is consistent! ({len(timeline.events)} events checked)")
        return

    console.print(f"\n[bold]Timeline Issues ({len(issues)} found)[/]\n")
    for issue in issues:
        console.print(f"  [yellow]WRN[/] {issue.description}")
        if issue.event_a:
            console.print(f"      Event A: {issue.event_a}")
        if issue.event_b:
            console.print(f"      Event B: {issue.event_b}")
        console.print()


@app.command("extract")
def extract_timeline(
    chapter: int = typer.Option(..., "--chapter", "-c", help="Chapter number"),
    scene: Optional[int] = typer.Option(None, "--scene", "-s", help="Scene number"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save prompt to file"),
) -> None:
    """Generate a prompt to extract timeline events from a scene."""
    project = Project.find()
    engine = TemplateEngine(project.user_prompts_dir)
    timeline = _load_timeline(project)

    scenes = project.load_scenes(chapter)
    target_scenes = scenes
    if scene:
        target_scenes = [s for s in scenes if s.scene_number == scene]

    ctx = {
        "project_name": project.name,
        "chapter_num": chapter,
        "scene_num": scene,
        "scenes": [s.model_dump(mode="json") for s in target_scenes],
        "existing_events": [e.model_dump(mode="json") for e in timeline.get_chronological_order()],
        "time_unit": timeline.time_unit.value,
    }

    prompt = engine.render("story/extract_timeline.md.j2", **ctx)

    if output:
        with open(output, "w") as f:
            f.write(prompt)
        print_success(f"Prompt saved to {output}")
    else:
        print_prompt_output(prompt, f"Extract Timeline: Ch.{chapter}" + (f" Sc.{scene}" if scene else ""))


def _detect_timeline_issues(timeline: Timeline) -> list[TimelineIssue]:
    """Detect temporal inconsistencies in the timeline."""
    issues: list[TimelineIssue] = []
    chrono = timeline.get_chronological_order()
    narrative = timeline.get_narrative_order()

    # Check for character bilocation (same character in two places at the same time)
    by_time: dict[float, list[TimelineEvent]] = {}
    for event in chrono:
        by_time.setdefault(event.sort_order, []).append(event)

    for sort_order, events in by_time.items():
        if len(events) < 2:
            continue
        # Check if any character appears in multiple non-parallel events
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                e1, e2 = events[i], events[j]
                # If they're in the same parallel group, that's fine
                if e1.parallel_group and e1.parallel_group == e2.parallel_group:
                    continue
                # Check character overlap
                chars_1 = set(e1.characters_involved)
                chars_2 = set(e2.characters_involved)
                overlap = chars_1 & chars_2
                if overlap and e1.location and e2.location and e1.location != e2.location:
                    issues.append(TimelineIssue(
                        description=f"Character bilocation: {', '.join(overlap)} at both '{e1.location}' and '{e2.location}' at the same time ({e1.story_time}).",
                        event_a=e1.description,
                        event_b=e2.description,
                        issue_type="character_bilocation",
                    ))

    # Check for flashback ordering: flashbacks in narrative order should reference earlier chronological times
    for event in narrative:
        if event.is_flashback:
            # Find surrounding non-flashback events
            non_fb_before = [
                e for e in narrative
                if not e.is_flashback
                and (e.chapter_num or 0, e.scene_num or 0) < (event.chapter_num or 0, event.scene_num or 0)
            ]
            if non_fb_before:
                last_before = non_fb_before[-1]
                if event.sort_order >= last_before.sort_order:
                    issues.append(TimelineIssue(
                        description=f"Flashback at Ch.{event.chapter_num} Sc.{event.scene_num} has sort_order {event.sort_order} >= surrounding events ({last_before.sort_order}). Should be earlier.",
                        event_a=event.description,
                        event_b=last_before.description,
                        issue_type="flashback_ordering",
                    ))

    return issues
