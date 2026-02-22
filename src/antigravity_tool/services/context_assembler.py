"""Unified Context Assembler -- merges CLI ContextCompiler + Web ContextEngine.

Single entry point for ALL context assembly:
  - CLI path: renders Jinja2 templates
  - Chat/Web path: structured markdown text
  - API path: raw entity dicts

Pipeline:
  1. ProjectSnapshotFactory.load(scope)
  2. Build context dict from snapshot
  3. Inject decisions from DecisionLog
  4. Apply token budget
  5. Render output format (template/structured/raw)
  6. Return ContextResult with Glass Box metadata
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from antigravity_tool.schemas.dal import ContextScope, ProjectSnapshot

logger = logging.getLogger(__name__)

# Maps workflow step -> Jinja2 template path (relative to prompts/)
STEP_TEMPLATE_MAP: Dict[str, str] = {
    "world_building": "world/build.md.j2",
    "character_creation": "character/create.md.j2",
    "story_outline": "story/outline.md.j2",
    "scene_writing": "scene/write.md.j2",
    "screenplay": "scene/screenplay.md.j2",
    "panel_composition": "panel/compose.md.j2",
    "evaluation": "evaluate/scene.md.j2",
    "brainstorm": "brainstorm/generate.md.j2",
    "research": "research/query.md.j2",
}


@dataclass
class ContextBucketInfo:
    """Metadata about a single context bucket (Glass Box)."""

    name: str
    entity_type: str
    tokens: int
    truncated: bool = False


@dataclass
class ContextResult:
    """Result from context assembly."""

    text: str
    token_estimate: int
    snapshot: Optional[ProjectSnapshot] = None
    glass_box: List[ContextBucketInfo] = field(default_factory=list)
    cache_hit_rate: float = 0.0
    load_time_ms: int = 0


class ContextAssembler:
    """Unified context assembly for CLI, Web, and Chat paths."""

    def __init__(
        self,
        snapshot_factory,  # ProjectSnapshotFactory
        template_engine=None,  # Optional Jinja2 TemplateEngine for CLI path
        decision_log=None,  # Optional DecisionLog for injecting decisions
        kg_service=None,  # Optional KnowledgeGraphService for relationships
    ):
        self._snapshot_factory = snapshot_factory
        self._template_engine = template_engine
        self._decision_log = decision_log
        self._kg_service = kg_service

    def compile(self, scope: ContextScope) -> ContextResult:
        """Assemble context for the given scope.

        Output format controlled by scope.output_format:
          - "template": Jinja2 render (CLI path)
          - "structured": Markdown with headers (Chat/Web path)
          - "raw": Dict of entities (API path)
        """
        # Step 1: Load snapshot
        snapshot = self._snapshot_factory.load(scope)

        # Step 2: Build context dict
        context = self._build_context_dict(snapshot, scope)

        # Step 3: Inject decisions
        if self._decision_log:
            decisions = self._get_scoped_decisions(scope)
            if decisions:
                context["decisions"] = decisions
                snapshot.decisions = [{"decision": d} for d in decisions]

        # Step 4: Apply token budget
        budgeted_context, glass_box = self._apply_token_budget(
            context, scope.token_budget
        )

        # Step 5: Render output
        if scope.output_format == "template" and self._template_engine:
            text = self._render_template(scope.step, budgeted_context)
        elif scope.output_format == "raw":
            text = json.dumps(budgeted_context, indent=2, default=str)
        else:
            # "structured" -- markdown format
            text = self._render_structured(budgeted_context, scope.step)

        token_estimate = self._estimate_tokens(text)
        total = snapshot.cache_hits + snapshot.cache_misses
        hit_rate = snapshot.cache_hits / total if total > 0 else 0.0

        return ContextResult(
            text=text,
            token_estimate=token_estimate,
            snapshot=snapshot,
            glass_box=glass_box,
            cache_hit_rate=hit_rate,
            load_time_ms=snapshot.load_time_ms,
        )

    def _build_context_dict(
        self, snapshot: ProjectSnapshot, scope: ContextScope
    ) -> Dict[str, Any]:
        """Convert a ProjectSnapshot into a step-specific context dictionary."""
        ctx: Dict[str, Any] = {}

        if snapshot.world:
            ctx["world"] = snapshot.world
        if snapshot.characters:
            ctx["characters"] = snapshot.characters
        if snapshot.story_structure:
            ctx["story_structure"] = snapshot.story_structure
        if snapshot.scenes:
            ctx["scenes"] = snapshot.scenes
            if len(snapshot.scenes) == 1:
                ctx["current_scene"] = snapshot.scenes[0]
        if snapshot.screenplays:
            ctx["screenplays"] = snapshot.screenplays
        if snapshot.panels:
            ctx["panels"] = snapshot.panels
        if snapshot.style_guides:
            ctx["style_guide"] = snapshot.style_guides
        if snapshot.creative_room and scope.access_level == "author":
            ctx["creative_room"] = snapshot.creative_room

        return ctx

    def _get_scoped_decisions(self, scope: ContextScope) -> List[str]:
        """Get decisions matching the current scope.

        Adapts to DecisionLog.query() API -- returns list of decision strings.
        """
        try:
            decisions = self._decision_log.query(
                chapter=scope.chapter,
                scene=scope.scene,
                character=scope.character_name,
                active_only=True,
            )
            return [d.decision for d in decisions]
        except Exception as e:
            logger.warning("Failed to load decisions: %s", e)
            return []

    def _apply_token_budget(
        self, context: Dict[str, Any], budget: int
    ) -> tuple[Dict[str, Any], List[ContextBucketInfo]]:
        """Rank context buckets by priority and truncate if over budget."""
        # Priority order for token budget allocation
        priority = [
            "current_scene",
            "characters",
            "world",
            "story_structure",
            "style_guide",
            "scenes",
            "decisions",
            "screenplays",
            "panels",
            "creative_room",
        ]

        glass_box: List[ContextBucketInfo] = []
        budgeted: Dict[str, Any] = {}
        running_tokens = 0

        for key in priority:
            if key not in context:
                continue

            value = context[key]
            text_repr = str(value)
            bucket_tokens = self._estimate_tokens(text_repr)

            truncated = False
            if running_tokens + bucket_tokens > budget:
                # Truncate this bucket
                remaining = budget - running_tokens
                if remaining > 100:  # Only include if meaningful
                    budgeted[key] = value  # Keep original, truncation at render
                    bucket_tokens = remaining
                    truncated = True
                else:
                    truncated = True
                    glass_box.append(
                        ContextBucketInfo(
                            name=key,
                            entity_type=key,
                            tokens=bucket_tokens,
                            truncated=True,
                        )
                    )
                    continue
            else:
                budgeted[key] = value

            running_tokens += bucket_tokens
            glass_box.append(
                ContextBucketInfo(
                    name=key,
                    entity_type=key,
                    tokens=bucket_tokens,
                    truncated=truncated,
                )
            )

        # Include any keys not in priority list
        for key in context:
            if key not in budgeted and key not in [g.name for g in glass_box]:
                budgeted[key] = context[key]

        return budgeted, glass_box

    def _render_template(self, step: str, context: Dict[str, Any]) -> str:
        """Render context through Jinja2 template."""
        template_path = STEP_TEMPLATE_MAP.get(step)
        if not template_path or not self._template_engine:
            return self._render_structured(context, step)
        try:
            return self._template_engine.render(template_path, **context)
        except Exception as e:
            logger.warning("Template render failed for %s: %s", step, e)
            return self._render_structured(context, step)

    def _render_structured(self, context: Dict[str, Any], step: str) -> str:
        """Render context as structured markdown (Chat/Web path)."""
        lines = [f"# Context for {step.replace('_', ' ').title()}\n"]

        for key, value in context.items():
            header = key.replace("_", " ").title()

            if isinstance(value, dict):
                lines.append(f"## {header}")
                for k, v in value.items():
                    if not str(k).startswith("_"):
                        str_v = str(v)
                        if len(str_v) > 500:
                            str_v = str_v[:500] + "..."
                        lines.append(f"- **{k}**: {str_v}")
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"## {header} ({len(value)} items)")
                for item in value:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("title", "unnamed"))
                        lines.append(f"### {name}")
                        for k, v in item.items():
                            if not str(k).startswith("_") and k not in (
                                "name",
                                "title",
                            ):
                                str_v = str(v)
                                if len(str_v) > 300:
                                    str_v = str_v[:300] + "..."
                                lines.append(f"- **{k}**: {str_v}")
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"## {header}")
                lines.append(str(value))
                lines.append("")

        return "\n".join(lines)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count: ~4 chars per token."""
        return len(text) // 4
