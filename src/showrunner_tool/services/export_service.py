"""Export Service for Showrunner.

Provides three export formats:
  - Markdown manuscript (Season → Chapter → Scene headings + fragment prose)
  - JSON bundle (full project snapshot)
  - Fountain screenplay format
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from showrunner_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class ExportService:
    """Orchestrates export of story data into various output formats."""

    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        container_repo: ContainerRepository,
        schema_repo: SchemaRepository,
        event_service: EventService,
    ):
        self.kg_service = kg_service
        self.container_repo = container_repo
        self.schema_repo = schema_repo
        self.event_service = event_service

    # ── helpers ────────────────────────────────────────────────────

    def _get_fragments_for_scene(self, scene_id: str) -> List[Dict[str, Any]]:
        """Return fragment children of a scene, ordered by sort_order."""
        children = self.kg_service.get_children(scene_id)
        fragments = [c for c in children if c.get("container_type") == "fragment"]
        fragments.sort(key=lambda f: f.get("sort_order", 0))
        return fragments

    def _fragment_text(self, fragment: Dict[str, Any]) -> str:
        """Extract the prose text from a fragment row."""
        attrs = fragment.get("attributes_json", "{}")
        if isinstance(attrs, str):
            try:
                attrs = json.loads(attrs)
            except (json.JSONDecodeError, TypeError):
                attrs = {}
        # Also check top-level 'attributes' (used when dict is already parsed)
        if isinstance(attrs, dict):
            return attrs.get("text", "")
        # Fallback: check if raw dict has 'attributes'
        raw_attrs = fragment.get("attributes", {})
        if isinstance(raw_attrs, dict):
            return raw_attrs.get("text", "")
        return ""

    def _fragment_attributes(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the full attributes dict from a fragment."""
        attrs = fragment.get("attributes_json", "{}")
        if isinstance(attrs, str):
            try:
                return json.loads(attrs)
            except (json.JSONDecodeError, TypeError):
                return {}
        if isinstance(attrs, dict):
            return attrs
        raw = fragment.get("attributes", {})
        return raw if isinstance(raw, dict) else {}

    # ── heading depth map ─────────────────────────────────────────

    _HEADING_LEVELS = {
        "season": 1,
        "arc": 2,
        "act": 2,
        "chapter": 2,
        "scene": 3,
    }

    # ══════════════════════════════════════════════════════════════
    # 1. Markdown export
    # ══════════════════════════════════════════════════════════════

    def export_markdown(self) -> str:
        """Render the full manuscript as Markdown.

        Heading hierarchy:
          # Season
          ## Chapter (or Arc / Act)
          ### Scene
          <fragment prose>
        """
        tree = self.kg_service.get_structure_tree("")
        lines: list[str] = []
        self._render_md_node(tree, lines)
        return "\n".join(lines)

    def _render_md_node(
        self, nodes: List[Dict[str, Any]], lines: list[str]
    ) -> None:
        for node in nodes:
            ctype = node.get("container_type", "")
            name = node.get("name", "Untitled")
            level = self._HEADING_LEVELS.get(ctype, 2)
            heading = "#" * level
            lines.append(f"{heading} {name}")
            lines.append("")

            # If this is a scene, collect fragments
            if ctype == "scene":
                fragments = self._get_fragments_for_scene(node["id"])
                for frag in fragments:
                    text = self._fragment_text(frag)
                    if text:
                        lines.append(text)
                        lines.append("")

            # Recurse into children
            children = node.get("children", [])
            if children:
                self._render_md_node(children, lines)

    # ══════════════════════════════════════════════════════════════
    # 2. JSON bundle export
    # ══════════════════════════════════════════════════════════════

    def export_json_bundle(self) -> dict:
        """Return the full project state as a JSON-serialisable dict.

        Keys: containers, schemas, relationships, events.
        """
        containers = self.kg_service.find_containers()
        relationships = self.kg_service.get_all_relationships()
        events = self.event_service.get_all_events()

        # Schemas — read all from the schema repo
        schemas: list[dict] = []
        try:
            for schema in self.schema_repo.list_all():
                schemas.append(
                    schema.model_dump(mode="json")
                    if hasattr(schema, "model_dump")
                    else schema
                )
        except Exception:
            logger.debug("Could not load schemas for bundle export", exc_info=True)

        return {
            "containers": containers,
            "schemas": schemas,
            "relationships": relationships,
            "events": events,
        }

    # ══════════════════════════════════════════════════════════════
    # 3. Fountain screenplay export
    # ══════════════════════════════════════════════════════════════

    def export_fountain(self) -> str:
        """Render the manuscript in Fountain screenplay format.

        Uses fragment attributes ``scene_heading``, ``action``,
        ``character``, and ``dialogue`` when available.
        Falls back to plain prose otherwise.
        """
        tree = self.kg_service.get_structure_tree("")
        lines: list[str] = []
        self._render_fountain_node(tree, lines)
        return "\n".join(lines)

    def _render_fountain_node(
        self, nodes: List[Dict[str, Any]], lines: list[str]
    ) -> None:
        for node in nodes:
            ctype = node.get("container_type", "")

            if ctype == "scene":
                self._render_fountain_scene(node, lines)
            else:
                # Recurse into children (seasons, chapters, arcs, acts)
                children = node.get("children", [])
                if children:
                    self._render_fountain_node(children, lines)

    def _render_fountain_scene(
        self, scene_node: Dict[str, Any], lines: list[str]
    ) -> None:
        fragments = self._get_fragments_for_scene(scene_node["id"])

        for frag in fragments:
            attrs = self._fragment_attributes(frag)

            scene_heading = attrs.get("scene_heading")
            character = attrs.get("character")
            dialogue = attrs.get("dialogue")
            action = attrs.get("action")

            has_screenplay_attrs = any([scene_heading, character, dialogue, action])

            if has_screenplay_attrs:
                if scene_heading:
                    lines.append(scene_heading.upper())
                    lines.append("")
                if action:
                    lines.append(action)
                    lines.append("")
                if character:
                    lines.append(character.upper())
                if dialogue:
                    lines.append(dialogue)
                    lines.append("")
            else:
                # Fallback: plain prose
                text = attrs.get("text", "")
                if text:
                    lines.append(text)
                    lines.append("")

    # ══════════════════════════════════════════════════════════════
    # 4. HTML export
    # ══════════════════════════════════════════════════════════════

    def export_html(self) -> str:
        """Render the manuscript as a styled HTML document suitable for printing to PDF."""
        tree = self.kg_service.get_structure_tree("")
        body_lines: list[str] = []
        self._render_html_node(tree, body_lines)
        body_html = "\n".join(body_lines)
        return self._wrap_html(body_html)

    def _render_html_node(
        self, nodes: List[Dict[str, Any]], lines: list[str]
    ) -> None:
        for node in nodes:
            ctype = node.get("container_type", "")
            name = node.get("name", "Untitled")
            
            if ctype == "season":
                lines.append(f'<h1 class="season">{name}</h1>')
            elif ctype in ("chapter", "arc", "act"):
                lines.append(f'<h2 class="{ctype}">{name}</h2>')
            elif ctype == "scene":
                lines.append(f'<h3 class="scene">{name}</h3>')
                lines.append('<div class="scene-divider"></div>')
                
                fragments = self._get_fragments_for_scene(node["id"])
                for frag in fragments:
                    text = self._fragment_text(frag)
                    if text:
                        paragraphs = text.strip().split("\n\n")
                        for p in paragraphs:
                            if p.strip():
                                lines.append(f'<p class="prose">{p.strip()}</p>')
            
            # Recurse into children
            children = node.get("children", [])
            if children:
                self._render_html_node(children, lines)

    def _wrap_html(self, body: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Manuscript Export</title>
    <style>
        @media print {{
            body {{ font-size: 12pt; }}
            .scene-divider {{ page-break-before: auto; }}
        }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            max-width: 700px;
            margin: 2rem auto;
            padding: 0 1rem;
            line-height: 1.8;
            color: #1a1a1a;
            background: #fff;
        }}
        h1 {{ font-size: 2em; margin-top: 3em; border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; margin-top: 2em; color: #333; }}
        h3 {{ font-size: 1.2em; margin-top: 1.5em; color: #555; font-style: italic; }}
        .prose {{ text-indent: 2em; margin: 0.8em 0; }}
        .scene-divider {{ margin: 2em 0; border-top: 1px solid #ddd; }}
        .export-meta {{ color: #999; font-size: 0.8em; text-align: center; margin-bottom: 3em; }}
    </style>
</head>
<body>
    <div class="export-meta">Exported from Showrunner</div>
    {body}
</body>
</html>"""
