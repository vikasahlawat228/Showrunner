"""Core service logic for the composable SSE pipeline engine.

Supports both:
1. Legacy hardcoded pipeline (when definition_id is None)
2. Composable definition-driven pipelines (DAG execution)

Pipeline definitions are persisted via ContainerRepository.
Pipeline runs are ephemeral in-memory state.

Phase G Track 1 adds logic nodes (IF_ELSE, LOOP, MERGE_OUTPUTS)
which turn the executor from a simple topological traversal into
a state-machine that can branch and loop.
"""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import operator
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

import ulid

from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.schemas.container import GenericContainer
from showrunner_tool.schemas.pipeline import PipelineState, PipelineRun
from showrunner_tool.schemas.pipeline_steps import (
    PipelineDefinition,
    PipelineStepDef,
    PipelineEdge,
    StepType,
    STEP_CATEGORIES,
    StepCategory,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Safe Expression Evaluator for Logic Nodes
# ---------------------------------------------------------------------------

# Allowed comparison / arithmetic operators in condition expressions
_SAFE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
}


def evaluate_condition(expression: str, payload: Dict[str, Any]) -> bool:
    """Safely evaluate a simple condition expression against the pipeline payload.

    Supports:
      - Bare identifiers resolved against payload keys (e.g. ``word_count``)
      - Dotted paths resolved via nested dict lookup (e.g. ``result.ready``)
      - Numeric and string literals, booleans, None
      - Comparisons: ==, !=, <, <=, >, >=
      - Boolean operators: and, or, not
      - Arithmetic: +, -, *

    Examples::

        evaluate_condition("word_count > 500", {"word_count": 600})  # True
        evaluate_condition("ready == true", {"ready": True})         # True
        evaluate_condition("status == 'done'", {"status": "done"})   # True

    Raises ``ValueError`` on disallowed AST nodes (no function calls, no
    attribute access beyond payload lookup, etc.).
    """
    if not expression or not expression.strip():
        return False

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid condition expression: {exc}") from exc

    def _resolve(node: ast.AST) -> Any:  # noqa: C901 — small recursive evaluator
        if isinstance(node, ast.Expression):
            return _resolve(node.body)

        # --- literals ---
        if isinstance(node, ast.Constant):
            return node.value

        # --- identifiers (payload keys) ---
        if isinstance(node, ast.Name):
            key = node.id
            # Accept Python-style boolean keywords
            if key == "true":
                return True
            if key == "false":
                return False
            if key in payload:
                return payload[key]
            return None

        # --- dotted attribute lookup → nested dict access ---
        if isinstance(node, ast.Attribute):
            parts = _dotted_parts(node)
            value = payload
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value

        # --- comparisons ---
        if isinstance(node, ast.Compare):
            left = _resolve(node.left)
            for op_node, comparator in zip(node.ops, node.comparators):
                op_fn = _SAFE_OPS.get(type(op_node))
                if op_fn is None:
                    raise ValueError(f"Unsupported comparison: {type(op_node).__name__}")
                right = _resolve(comparator)
                if not op_fn(left, right):
                    return False
                left = right
            return True

        # --- boolean ops ---
        if isinstance(node, ast.BoolOp):
            op_fn = _SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported boolean op: {type(node.op).__name__}")
            result = _resolve(node.values[0])
            for val in node.values[1:]:
                result = op_fn(result, _resolve(val))
            return result

        # --- unary not ---
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not _resolve(node.operand)

        # --- binary arithmetic ---
        if isinstance(node, ast.BinOp):
            op_fn = _SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported binary op: {type(node.op).__name__}")
            return op_fn(_resolve(node.left), _resolve(node.right))

        raise ValueError(f"Disallowed expression node: {type(node).__name__}")

    def _dotted_parts(node: ast.Attribute) -> List[str]:
        """Flatten ``a.b.c`` into ``['a', 'b', 'c']``."""
        parts: List[str] = [node.attr]
        current = node.value
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()
        return parts

    return bool(_resolve(tree))


class PipelineService:
    """Manages composable state-machine pipelines with SSE streaming.

    Pipeline definitions are persisted via ContainerRepository as
    GenericContainer with container_type="pipeline_def".
    Pipeline runs are ephemeral in-memory state (lost on restart).
    """

    # In-memory stores for ephemeral run state (shared across instances)
    _runs: Dict[str, PipelineRun] = {}
    _events: Dict[str, asyncio.Event] = {}

    # Optional context engine for intelligent context assembly (Track 2)
    _context_engine: Optional[Any] = None
    # Optional model config registry for model resolution cascade (Phase F)
    _model_config_registry: Optional[Any] = None
    # Optional agent dispatcher for research step handlers (Phase G)
    _agent_dispatcher: Optional[Any] = None

    @classmethod
    def set_context_engine(cls, engine: Any) -> None:
        """Inject a ContextEngine instance for use by context-gathering step handlers."""
        cls._context_engine = engine

    @classmethod
    def set_model_config_registry(cls, registry: Any) -> None:
        """Inject a ModelConfigRegistry for model resolution cascade."""
        cls._model_config_registry = registry

    @classmethod
    def set_agent_dispatcher(cls, dispatcher: Any) -> None:
        """Inject an AgentDispatcher for research deep-dive step handlers."""
        cls._agent_dispatcher = dispatcher

    def __init__(
        self,
        container_repo: ContainerRepository,
        event_service: EventService,
    ):
        self.container_repo = container_repo
        self.event_service = event_service

    # ------------------------------------------------------------------
    # Definition <-> GenericContainer conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _definition_to_container(definition: PipelineDefinition) -> GenericContainer:
        """Convert a PipelineDefinition to a GenericContainer for storage."""
        return GenericContainer(
            id=definition.id,
            container_type="pipeline_def",
            name=definition.name,
            attributes={
                "description": definition.description,
                "steps": [s.model_dump(mode="json") for s in definition.steps],
                "edges": [e.model_dump(mode="json") for e in definition.edges],
            },
            relationships=[],
            created_at=definition.created_at,
            updated_at=definition.updated_at,
        )

    @staticmethod
    def _container_to_definition(container: GenericContainer) -> PipelineDefinition:
        """Reconstruct a PipelineDefinition from a GenericContainer."""
        attrs = container.attributes
        steps = [PipelineStepDef(**s) for s in attrs.get("steps", [])]
        edges = [PipelineEdge(**e) for e in attrs.get("edges", [])]
        return PipelineDefinition(
            id=container.id,
            name=container.name,
            description=attrs.get("description", ""),
            steps=steps,
            edges=edges,
            created_at=container.created_at,
            updated_at=container.updated_at,
        )

    # ------------------------------------------------------------------
    # Definition CRUD (persisted via ContainerRepository)
    # ------------------------------------------------------------------

    def save_definition(self, definition: PipelineDefinition) -> PipelineDefinition:
        """Save or update a pipeline definition."""
        existing = self.get_definition(definition.id)
        event_type = "UPDATE" if existing else "CREATE"

        container = self._definition_to_container(definition)
        self.container_repo.save_container(container)

        # Emit event to EventService
        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type=event_type,
                container_id=definition.id,
                payload=container.attributes,
            )
        except Exception as e:
            logger.warning(
                "Failed to emit %s event for pipeline def %s: %s",
                event_type, definition.id, e,
            )

        return definition

    def get_definition(self, definition_id: str) -> Optional[PipelineDefinition]:
        """Get a pipeline definition by ID."""
        all_defs = self.list_definitions()
        for d in all_defs:
            if d.id == definition_id:
                return d
        return None

    def list_definitions(self) -> List[PipelineDefinition]:
        """List all saved pipeline definitions."""
        containers = self.container_repo.list_by_type("pipeline_def")
        definitions = []
        for c in containers:
            try:
                definitions.append(self._container_to_definition(c))
            except Exception as e:
                logger.warning(
                    "Failed to load pipeline definition from container %s: %s",
                    c.id, e,
                )
        return definitions

    def delete_definition(self, definition_id: str) -> bool:
        """Delete a pipeline definition. Returns True if found and deleted."""
        definition = self.get_definition(definition_id)
        if not definition:
            return False

        # Delete the YAML file from the pipeline_def subdirectory
        file_stem = definition.name.lower().replace(" ", "_")
        def_dir = self.container_repo.base_dir / "pipeline_def"
        if def_dir.exists():
            original_base = self.container_repo.base_dir
            self.container_repo.base_dir = def_dir
            try:
                self.container_repo.delete(file_stem)
            finally:
                self.container_repo.base_dir = original_base

        # Emit DELETE event
        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type="DELETE",
                container_id=definition_id,
                payload={"deleted": True},
            )
        except Exception as e:
            logger.warning(
                "Failed to emit DELETE event for pipeline def %s: %s",
                definition_id, e,
            )

        return True

    # ------------------------------------------------------------------
    # Pipeline Execution
    # ------------------------------------------------------------------

    async def start_pipeline(self, initial_payload: dict, definition_id: Optional[str] = None) -> str:
        """Initialize a run and start the background task."""
        run_id = str(ulid.ULID())

        definition = self.get_definition(definition_id) if definition_id else None

        run = PipelineRun(
            id=run_id,
            current_state=PipelineState.CONTEXT_GATHERING,
            payload=initial_payload,
            definition_id=definition_id,
            total_steps=len(definition.steps) if definition else 4,
        )
        PipelineService._runs[run_id] = run
        PipelineService._events[run_id] = asyncio.Event()

        if definition:
            asyncio.create_task(self._run_composable_pipeline(run_id, definition))
        else:
            asyncio.create_task(self._run_legacy_pipeline(run_id))

        return run_id

    # ------------------------------------------------------------------
    # Composable Pipeline Executor
    # ------------------------------------------------------------------

    async def _run_composable_pipeline(
        self, run_id: str, definition: PipelineDefinition
    ) -> None:
        """Execute a pipeline definition as a state machine.

        For pipelines without logic nodes this behaves identically to the
        previous topological-order loop.  When logic nodes (IF_ELSE, LOOP,
        MERGE_OUTPUTS) are present the executor follows explicit jump
        targets instead of the default topological successor.
        """
        run = PipelineService._runs.get(run_id)
        if not run:
            return

        try:
            step_map: Dict[str, PipelineStepDef] = {s.id: s for s in definition.steps}

            # Build adjacency for default "next step" resolution.
            # For non-logic nodes we use the *first* outgoing edge as
            # the default successor.  For logic nodes the handler picks
            # the target explicitly so default_next is only a fallback.
            execution_order = self._topological_sort(definition)

            # Map source → list of targets from edges
            edge_targets: Dict[str, List[str]] = {s.id: [] for s in definition.steps}
            for edge in definition.edges:
                if edge.source in edge_targets:
                    edge_targets[edge.source].append(edge.target)

            default_next: Dict[str, Optional[str]] = {}
            for step in execution_order:
                targets = edge_targets.get(step.id, [])
                if targets:
                    # Use the first outgoing edge as default next
                    default_next[step.id] = targets[0]
                else:
                    # Terminal node — no outgoing edges
                    default_next[step.id] = None

            # Loop iteration counters (keyed by step ID)
            loop_counters: Dict[str, int] = {}

            current_step_id: Optional[str] = execution_order[0].id if execution_order else None

            while current_step_id is not None:
                if run_id not in PipelineService._runs:
                    break

                step = step_map.get(current_step_id)
                if step is None:
                    logger.error("Step %s not found in definition", current_step_id)
                    break

                # Update run state to reflect current step
                run.current_step_id = step.id
                run.current_step_type = step.step_type.value
                run.current_step_label = step.label
                run.current_agent_id = step.config.get("agent_id") or None

                category = STEP_CATEGORIES.get(step.step_type, StepCategory.EXECUTE)

                if category == StepCategory.HUMAN:
                    # Check auto-approval conditions
                    auto_approve = False
                    confidence = run.payload.get("confidence_score", 0)
                    errors = run.payload.get("continuity_errors", [])
                    
                    if step.step_type == StepType.APPROVE_OUTPUT and isinstance(confidence, (int, float)) and confidence > 90 and len(errors) == 0:
                        auto_approve = True

                    if not auto_approve:
                        # Human checkpoint — pause for user
                        run.current_state = PipelineState.PAUSED_FOR_USER
                        run.payload = {
                            **run.payload,
                            "step_name": step.label,
                            "step_type": step.step_type.value,
                            "step_config": step.config,
                        }
                        event = PipelineService._events.get(run_id)
                        if event:
                            event.clear()
                            await event.wait()

                        # Phase G Track 4: "Chat-to-Refine" Loop-back
                        refine_text = run.payload.get("refine_instructions")
                        is_regenerate = run.payload.get("regenerate", False)
                        
                        if refine_text or is_regenerate:
                            if refine_text:
                                # Append instructions to the existing prompt
                                current_prompt = run.payload.get("prompt_text", "")
                                run.payload["prompt_text"] = f"{current_prompt}\n\n[Refined Instructions: {refine_text}]"
                                # Clear instructions so we don't infinitely loop
                                run.payload.pop("refine_instructions", None)
                            
                            # Find the preceding LLM_GENERATE step
                            last_llm_step_id = None
                            for sid in reversed(run.steps_completed):
                                s = step_map.get(sid)
                                if s is not None and s.step_type == StepType.LLM_GENERATE:
                                    last_llm_step_id = sid
                                    break
                            
                            if last_llm_step_id:
                                # Do not mark this HUMAN step as completed, just loop back
                                current_step_id = last_llm_step_id
                                continue
                    else:
                        auto_approved_list = run.payload.get("auto_approved_steps", [])
                        auto_approved_list.append({
                            "step_id": step.id,
                            "step_name": step.label,
                            "prompt_text": run.payload.get("prompt_text"),
                            "model": run.payload.get("resolved_model"),
                            "confidence_score": confidence,
                            "continuity_errors": errors,
                            "generated_text": run.payload.get("generated_text"),
                        })
                        run.payload["auto_approved_steps"] = auto_approved_list
                        logger.info(f"Auto-approved step {step.id} due to high confidence ({confidence})")

                    # Mark completed and advance to default next
                    run.steps_completed.append(step.id)
                    current_step_id = default_next.get(step.id)

                elif category == StepCategory.LOGIC:
                    # Logic nodes determine the next step themselves
                    next_id = await self._execute_logic_step(run, step, loop_counters, default_next)
                    run.steps_completed.append(step.id)
                    current_step_id = next_id

                else:
                    # Auto-executing step
                    run.current_state = PipelineState.EXECUTING
                    await self._execute_step(run, step)
                    run.steps_completed.append(step.id)
                    current_step_id = default_next.get(step.id)

            # All steps done
            run.current_state = PipelineState.COMPLETED
            run.current_step_id = None

        except Exception as e:
            logger.error("Pipeline %s failed: %s", run_id, e)
            run.current_state = PipelineState.FAILED
            run.error = str(e)
        finally:
            PipelineService._events.pop(run_id, None)
            # Persist completed/failed runs (Phase F)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                self._persist_completed_run(run)

    def _persist_completed_run(self, run: PipelineRun) -> None:
        """Save a finalized pipeline run as a GenericContainer and emit event.

        Active runs stay in-memory for SSE streaming performance.
        Completed/failed runs are persisted so they survive restarts.
        """
        try:
            container = GenericContainer(
                id=run.id,
                container_type="pipeline_run",
                name=f"Run {run.id[:8]}",
                attributes={
                    "state": run.current_state.value,
                    "definition_id": run.definition_id,
                    "steps_completed": run.steps_completed,
                    "total_steps": run.total_steps,
                    "error": run.error,
                    "created_at": run.created_at.isoformat(),
                },
            )
            self.container_repo.save_container(container)

            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type="CREATE",
                container_id=run.id,
                payload={
                    "container_type": "pipeline_run",
                    "state": run.current_state.value,
                    "definition_id": run.definition_id,
                },
            )
            logger.info("Persisted completed pipeline run %s", run.id)
        except Exception as e:
            logger.warning("Failed to persist pipeline run %s: %s", run.id, e)

    def set_step_model_override(self, run_id: str, step_id: str, model_name: str):
        """Override config (e.g. model) for a specific step at runtime."""
        run = self._runs.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if not hasattr(run, 'step_overrides') or run.step_overrides is None:
            run.step_overrides = {}
        if step_id not in run.step_overrides:
            run.step_overrides[step_id] = {}
        run.step_overrides[step_id]["model"] = model_name

    async def _execute_step(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Dispatch a single step to its handler."""
        # Apply runtime overrides if any exist for this step
        if getattr(run, 'step_overrides', None) and step.id in run.step_overrides:
            override = run.step_overrides[step.id]
            if "model" in override:
                step.config["target_model"] = override["model"]

        handler = self._step_handlers.get(step.step_type)
        if handler:
            await handler(self, run, step)
        else:
            logger.warning("No handler for step type %s, skipping", step.step_type)
            await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    # Logic Step Execution (Phase G Track 1)
    # ------------------------------------------------------------------

    async def _execute_logic_step(
        self,
        run: PipelineRun,
        step: PipelineStepDef,
        loop_counters: Dict[str, int],
        default_next: Dict[str, Optional[str]],
    ) -> Optional[str]:
        """Execute a logic node and return the next step ID to jump to."""
        run.current_state = PipelineState.EXECUTING

        if step.step_type == StepType.IF_ELSE:
            return await self._handle_if_else(run, step, default_next)
        elif step.step_type == StepType.LOOP:
            return await self._handle_loop(run, step, loop_counters, default_next)
        elif step.step_type == StepType.MERGE_OUTPUTS:
            return await self._handle_merge_outputs(run, step, default_next)
        else:
            logger.warning("Unknown logic step type %s", step.step_type)
            return default_next.get(step.id)

    async def _handle_if_else(
        self,
        run: PipelineRun,
        step: PipelineStepDef,
        default_next: Dict[str, Optional[str]],
    ) -> Optional[str]:
        """Evaluate condition and route to true_target or false_target."""
        condition = step.config.get("condition", "")
        true_target = step.config.get("true_target")
        false_target = step.config.get("false_target")

        try:
            result = evaluate_condition(condition, run.payload)
        except ValueError as e:
            logger.error("IF_ELSE condition eval failed for step %s: %s", step.id, e)
            result = False

        run.payload["_logic"] = {
            **run.payload.get("_logic", {}),
            step.id: {"condition": condition, "result": result},
        }

        if result:
            return true_target or default_next.get(step.id)
        else:
            return false_target or default_next.get(step.id)

    async def _handle_loop(
        self,
        run: PipelineRun,
        step: PipelineStepDef,
        loop_counters: Dict[str, int],
        default_next: Dict[str, Optional[str]],
    ) -> Optional[str]:
        """Check exit condition; if not met, loop back. Otherwise advance."""
        condition = step.config.get("condition", "")
        loop_back_to = step.config.get("loop_back_to")
        max_iterations = step.config.get("max_iterations", 10)

        # Increment iteration counter for this loop step
        loop_counters[step.id] = loop_counters.get(step.id, 0) + 1
        current_iter = loop_counters[step.id]

        try:
            exit_met = evaluate_condition(condition, run.payload)
        except ValueError as e:
            logger.error("LOOP condition eval failed for step %s: %s", step.id, e)
            exit_met = True  # Bail out on bad expressions

        run.payload["_logic"] = {
            **run.payload.get("_logic", {}),
            step.id: {
                "condition": condition,
                "exit_met": exit_met,
                "iteration": current_iter,
                "max_iterations": max_iterations,
            },
        }

        if exit_met or current_iter >= max_iterations:
            # Exit the loop — proceed to default next step
            return default_next.get(step.id)
        else:
            # Loop back
            return loop_back_to or default_next.get(step.id)

    async def _handle_merge_outputs(
        self,
        run: PipelineRun,
        step: PipelineStepDef,
        default_next: Dict[str, Optional[str]],
    ) -> Optional[str]:
        """Merge specified payload keys into a single 'merged' dict."""
        source_keys = step.config.get("source_keys", [])
        merge_strategy = step.config.get("merge_strategy", "shallow")

        merged: Dict[str, Any] = {}
        for key in source_keys:
            value = run.payload.get(key)
            if isinstance(value, dict) and merge_strategy == "deep":
                merged = self._deep_merge(merged, value)
            elif isinstance(value, dict):
                merged.update(value)
            elif value is not None:
                merged[key] = value

        run.payload["merged"] = merged
        return default_next.get(step.id)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge *override* into *base*."""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = PipelineService._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------
    # Step Handlers
    # ------------------------------------------------------------------

    async def _handle_gather_buckets(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Gather containers matching the configured types.

        When a ContextEngine is available, assembles real context from the
        knowledge graph with token budgeting. Otherwise falls back to metadata-only.
        """
        run.current_state = PipelineState.CONTEXT_GATHERING
        container_types = step.config.get("container_types", [])
        max_items = step.config.get("max_items", 10)

        if PipelineService._context_engine is not None:
            try:
                # Use the context engine for real context assembly
                query = run.payload.get("text", run.payload.get("prompt_text", ""))
                # Estimate a per-item token budget, with a reasonable total cap
                max_tokens = step.config.get("max_tokens", max_items * 400)
                result = PipelineService._context_engine.assemble_context(
                    query=query,
                    container_types=container_types if container_types else None,
                    max_tokens=max_tokens,
                    include_relationships=step.config.get("include_relationships", True),
                )
                run.payload["gathered_context"] = result.text
                run.payload["gathered_context_meta"] = {
                    "container_types": container_types,
                    "max_items": max_items,
                    "containers_included": result.containers_included,
                    "containers_truncated": result.containers_truncated,
                    "token_estimate": result.token_estimate,
                    "status": "gathered",
                    "buckets": [
                        {"id": b.id, "name": b.name, "type": b.container_type, "summary": b.summary}
                        for b in result.buckets
                    ],
                }
                logger.info(
                    "Gathered context: %d containers (%d truncated), ~%d tokens",
                    result.containers_included,
                    result.containers_truncated,
                    result.token_estimate,
                )
            except Exception as e:
                logger.error("ContextEngine gather failed, falling back: %s", e)
                run.payload["gathered_context"] = {
                    "container_types": container_types,
                    "max_items": max_items,
                    "status": "gathered",
                    "error": str(e),
                }
        else:
            # Fallback: metadata-only (original stub behavior)
            run.payload["gathered_context"] = {
                "container_types": container_types,
                "max_items": max_items,
                "status": "gathered",
            }

        await asyncio.sleep(0.3)

    async def _handle_semantic_search(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Search for related content.

        When a ContextEngine is available, uses it to assemble relevant context
        from the knowledge graph based on the query. Otherwise falls back to metadata-only.
        """
        run.current_state = PipelineState.CONTEXT_GATHERING
        query_source = step.config.get("query_source", "payload.text")
        limit = step.config.get("limit", 5)

        # Extract query from payload
        query = run.payload.get("text", run.payload.get("prompt_text", ""))

        if PipelineService._context_engine is not None and query:
            try:
                max_tokens = step.config.get("max_tokens", limit * 400)
                result = PipelineService._context_engine.assemble_context(
                    query=query,
                    max_tokens=max_tokens,
                    include_relationships=step.config.get("include_relationships", True),
                )
                run.payload["search_results"] = result.text
                run.payload["search_results_meta"] = {
                    "query": query,
                    "limit": limit,
                    "containers_included": result.containers_included,
                    "containers_truncated": result.containers_truncated,
                    "token_estimate": result.token_estimate,
                    "status": "searched",
                }
                logger.info(
                    "Semantic search: %d containers matched for query '%s' (~%d tokens)",
                    result.containers_included,
                    query[:50],
                    result.token_estimate,
                )
            except Exception as e:
                logger.error("ContextEngine search failed, falling back: %s", e)
                run.payload["search_results"] = {
                    "query": query,
                    "limit": limit,
                    "status": "searched",
                    "error": str(e),
                }
        else:
            # Fallback: metadata-only (original stub behavior)
            run.payload["search_results"] = {
                "query": query,
                "limit": limit,
                "status": "searched",
            }

        await asyncio.sleep(0.3)

    async def _handle_prompt_template(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Assemble a prompt from template + context."""
        run.current_state = PipelineState.PROMPT_ASSEMBLY
        template = step.config.get("template_inline", "")

        if template:
            # Simple slot replacement from payload
            prompt = template
            for key, value in run.payload.items():
                placeholder = "{{" + key + "}}"
                if isinstance(value, str):
                    prompt = prompt.replace(placeholder, value)
            run.payload["prompt_text"] = prompt
        else:
            run.payload["prompt_text"] = run.payload.get(
                "prompt_text",
                f"[Auto-assembled prompt from step {step.id}]",
            )

        run.payload["step_name"] = step.label
        await asyncio.sleep(0.5)

    async def _handle_multi_variant(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Mark for multi-variant generation."""
        count = step.config.get("count", 3)
        run.payload["variant_count"] = count
        await asyncio.sleep(0.3)

    async def _handle_llm_generate(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Call the LLM to generate content.

        Uses ModelConfigRegistry cascade when available:
          Step config > Bucket preference > Agent default > Project default.
        """
        run.current_state = PipelineState.EXECUTING

        # Resolve model via the cascade (Phase F)
        agent_id = run.current_agent_id
        override_model = run.payload.get("model")

        if override_model:
            model = override_model
            temperature = run.payload.get("temperature", step.config.get("temperature", 0.7))
            run.payload.pop("model", None)  # Consume the override
        elif PipelineService._model_config_registry is not None:
            resolved = PipelineService._model_config_registry.resolve(
                step_config=step.config,
                bucket_model_preference=None,
                agent_id=agent_id,
            )
            model = resolved.model
            temperature = run.payload.get("temperature", step.config.get("temperature", resolved.temperature))
        else:
            model = step.config.get("model", "gemini/gemini-2.0-flash")
            temperature = run.payload.get("temperature", step.config.get("temperature", 0.7))

        # Clear override so it doesn't leak into future steps
        run.payload.pop("temperature", None)

        prompt_text = run.payload.get("prompt_text", "")

        if not prompt_text:
            run.payload["generated_text"] = "[No prompt was provided to the LLM]"
            return

        # Handle pinned context
        pinned_ids = run.payload.get("pinned_context_ids", [])
        if pinned_ids:
            pinned_context = []
            for cid in pinned_ids:
                container = self.container_repo.get_container(cid)
                if container:
                    content = container.attributes.get("text", container.attributes.get("summary", ""))
                    pinned_context.append(f"[{container.name} ({container.container_type})]: {content}")
            if pinned_context:
                prompt_text += "\n\n## Pinned Context\n" + "\n\n".join(pinned_context)

        # Handle regenerate flag looping
        if run.payload.get("regenerate"):
            run.payload.pop("regenerate", None)
            
        # Append instructions for Confidence-Based Auto-Execution
        prompt_text += (
            "\n\n[SYSTEM INSTRUCTION: You MUST output your response as a valid JSON object containing exactly three keys: "
            "'generated_text' (string) containing your actual response to the prompt above, "
            "'confidence_score' (number 0-100) estimating your confidence in meeting the prompt requirements and preserving continuity, "
            "and 'continuity_errors' (array of strings) listing any detected logical or continuity errors. Do NOT wrap in markdown blocks if possible.]"
        )

        # Store resolved model in payload for Glass Box transparency
        run.payload["resolved_model"] = model

        try:
            from litellm import completion

            api_key = os.getenv("GEMINI_API_KEY")
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a creative writing assistant."},
                    {"role": "user", "content": prompt_text},
                ],
                api_key=api_key,
                temperature=temperature,
            )
            content = response.choices[0].message.content.strip()
            
            # Clean possible markdown block
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            try:
                import json
                parsed = json.loads(content)
                run.payload["generated_text"] = parsed.get("generated_text", content)
                run.payload["confidence_score"] = parsed.get("confidence_score", 0)
                run.payload["continuity_errors"] = parsed.get("continuity_errors", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM structured JSON output. Proceeding with raw text.")
                run.payload["generated_text"] = content
                run.payload["confidence_score"] = 0
                run.payload["continuity_errors"] = ["Failed to parse structured output"]
                
        except Exception as e:
            logger.error("LLM generation failed: %s", e)
            run.payload["generated_text"] = f"[LLM Error: {e}]"

    async def _handle_image_generate(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Queue an image generation request."""
        run.current_state = PipelineState.EXECUTING
        run.payload["image_status"] = "queued"
        run.payload["image_prompt"] = run.payload.get("prompt_text", "")
        await asyncio.sleep(1)

    async def _handle_save_to_bucket(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Save generated content to a container."""
        container_type = step.config.get("container_type", "fragment")
        run.payload["saved"] = {
            "container_type": container_type,
            "status": "saved",
        }
        await asyncio.sleep(0.3)

    async def _handle_http_request(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Make an external HTTP request."""
        url = step.config.get("url", "")
        method = step.config.get("method", "POST")

        if not url:
            run.payload["http_response"] = {"error": "No URL configured"}
            return

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    json=run.payload,
                    headers=step.config.get("headers", {}),
                    timeout=30,
                )
                run.payload["http_response"] = {
                    "status": resp.status_code,
                    "body": resp.text[:2000],
                }
        except Exception as e:
            run.payload["http_response"] = {"error": str(e)}

    async def _handle_research_deep_dive(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Execute a research query via the research agent skill."""
        run.current_state = PipelineState.EXECUTING

        query = run.payload.get("text", run.payload.get("prompt_text", ""))
        if not query:
            run.payload["research_result"] = {"error": "No research query provided"}
            return

        if PipelineService._agent_dispatcher is None:
            run.payload["research_result"] = {"error": "AgentDispatcher not available"}
            return

        skill = PipelineService._agent_dispatcher.skills.get("research_agent")
        if skill is None:
            run.payload["research_result"] = {"error": "research_agent skill not loaded"}
            return

        result = await PipelineService._agent_dispatcher.execute(skill, query)

        if result.success and result.actions:
            research_data = result.actions[0]
            run.payload["research_result"] = research_data
            run.payload["research_summary"] = research_data.get("summary", "")
        else:
            run.payload["research_result"] = {
                "response": result.response[:500] if result.response else "",
                "error": result.error,
            }

        # Optionally persist to research library
        save_to_library = step.config.get("save_to_library", True)
        if save_to_library and result.success and result.actions:
            data = result.actions[0]
            container = GenericContainer(
                container_type="research_topic",
                name=f"Research: {query[:50]}",
                attributes={
                    "original_query": query,
                    "summary": data.get("summary", ""),
                    "confidence_score": data.get("confidence_score", 0.0),
                    "sources": data.get("sources", []),
                    "key_facts": data.get("key_facts", {}),
                },
            )
            try:
                self.container_repo.save_container(container)
                self.event_service.append_event(
                    parent_event_id=None,
                    branch_id="main",
                    event_type="CREATE",
                    container_id=container.id,
                    payload=container.attributes,
                )
                run.payload["research_container_id"] = container.id
                logger.info("Persisted research result as container %s", container.id)
            except Exception as e:
                logger.warning("Failed to persist research result: %s", e)

    # Step handler registry (instance methods, dispatched via self)
    _step_handlers: Dict[StepType, Any] = {}

    # ------------------------------------------------------------------
    # Legacy Pipeline (backward compatible)
    # ------------------------------------------------------------------

    async def _run_legacy_pipeline(self, run_id: str) -> None:
        """The original hardcoded pipeline logic — kept for backward compat."""
        run = PipelineService._runs.get(run_id)
        if not run:
            return

        try:
            # CONTEXT_GATHERING
            run.current_step_label = "Gathering Context"
            run.current_agent_id = "pipeline_director"
            await asyncio.sleep(1)

            # PROMPT_ASSEMBLY
            run.current_state = PipelineState.PROMPT_ASSEMBLY
            run.current_step_label = "Assembling Prompt"
            await asyncio.sleep(1)

            run.payload = {
                **run.payload,
                "prompt_text": (
                    f"[Assembled prompt for pipeline run {run_id}]\n\n"
                    "You are a creative writing assistant working on a manga/manhwa story.\n\n"
                    "## Gathered Context\n"
                    "- Characters, scenes, and world data have been compiled.\n\n"
                    "## Instructions\n"
                    "Review and edit this prompt before AI execution begins."
                ),
                "step_name": "Prompt Assembly",
            }

            # PAUSED_FOR_USER
            run.current_state = PipelineState.PAUSED_FOR_USER
            event = PipelineService._events.get(run_id)
            if event:
                await event.wait()

            # EXECUTING
            run.current_state = PipelineState.EXECUTING
            run.current_step_label = "Executing AI"
            await asyncio.sleep(2)

            # COMPLETED
            run.current_state = PipelineState.COMPLETED

        except Exception as e:
            run.current_state = PipelineState.FAILED
            run.error = str(e)
        finally:
            PipelineService._events.pop(run_id, None)
            # Persist completed/failed legacy runs (Phase F)
            if run and run.current_state in (PipelineState.COMPLETED, PipelineState.FAILED):
                self._persist_completed_run(run)

    # ------------------------------------------------------------------
    # SSE Streaming (unchanged — class method, operates on shared _runs)
    # ------------------------------------------------------------------

    @classmethod
    async def stream_pipeline(cls, run_id: str) -> AsyncGenerator[str, None]:
        """Provides SSE stream for the given run_id's state changes."""
        run = cls._runs.get(run_id)
        if not run:
            yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
            return

        last_state = None
        last_step_id = None
        while True:
            run = cls._runs.get(run_id)
            if not run:
                break

            # Emit on state change OR step change
            if run.current_state != last_state or run.current_step_id != last_step_id:
                last_state = run.current_state
                last_step_id = run.current_step_id

                data = run.model_dump_json()
                yield f"data: {data}\n\n"

                if run.current_state in [PipelineState.COMPLETED, PipelineState.FAILED]:
                    break

            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Resume (unchanged — class method, operates on shared _runs)
    # ------------------------------------------------------------------

    @classmethod
    async def resume_pipeline(cls, run_id: str, new_payload: dict) -> None:
        """Resume a paused pipeline run with user edits/updates."""
        run = cls._runs.get(run_id)
        if not run:
            raise ValueError(f"Pipeline Run {run_id} not found")

        if run.current_state != PipelineState.PAUSED_FOR_USER:
            raise ValueError(
                f"Pipeline Run {run_id} is not paused (currently {run.current_state})"
            )

        run.payload = {**run.payload, **new_payload}

        event = cls._events.get(run_id)
        if event:
            event.set()

    # ------------------------------------------------------------------
    # Deterministic Recorded Action Distillation
    # ------------------------------------------------------------------

    # Maps known slash commands to descriptive prompt templates
    _COMMAND_PROMPT_MAP: Dict[str, str] = {
        "brainstorm": "Brainstorm creative ideas and directions for the given text. Provide varied, imaginative suggestions.\n\nInput text:\n{{input_text}}",
        "expand": "Expand and develop the following text with richer detail, deeper characterization, and enhanced prose.\n\nInput text:\n{{input_text}}",
        "compress": "Condense the following text while preserving its core meaning, voice, and key plot points.\n\nInput text:\n{{input_text}}",
        "rewrite": "Rewrite the following text with improved prose quality, pacing, and emotional impact.\n\nInput text:\n{{input_text}}",
        "continue": "Continue the narrative from where the following text ends, maintaining consistent voice and pacing.\n\nInput text:\n{{input_text}}",
        "dialogue": "Generate natural dialogue for the characters in this scene, maintaining their distinct voices.\n\nScene context:\n{{input_text}}",
        "critique": "Provide a constructive critique of the following text, focusing on prose quality, pacing, character voice, and story coherence.\n\nInput text:\n{{input_text}}",
        "research": "Research the topics and setting elements referenced in the following text. Provide factual context and creative implications.\n\nInput text:\n{{input_text}}",
    }

    def distill_recorded_actions(
        self,
        actions: List[Dict[str, Any]],
        title: str,
    ) -> "PipelineDefinition":
        """Convert recorded user actions into a pipeline definition deterministically.

        Unlike NL-to-DAG which relies on an LLM, this method uses a rule-based
        mapping that translates each known action type into the correct pipeline
        step(s), then wires them together sequentially.

        Specific text values from the recording are generalized into
        ``{{input_text}}`` template variables so the resulting pipeline is
        reusable on different content.

        Args:
            actions: List of recorded action dicts (type, description, payload).
            title: Display name for the generated pipeline definition.

        Returns:
            A validated ``PipelineDefinition``.

        Raises:
            ValueError: If actions list is empty.
        """
        if not actions:
            raise ValueError("Cannot distill an empty action list")

        steps: List[PipelineStepDef] = []
        edges: List[PipelineEdge] = []
        step_counter = 0
        x_pos = 100

        # Track whether the original session included approvals so we know
        # whether to auto-insert checkpoint steps after LLM nodes.
        has_approvals = any(a.get("type") == "approval" for a in actions)

        for action in actions:
            action_type = action.get("type", "")
            payload = action.get("payload", {})
            description = action.get("description", "")

            if action_type == "slash_command":
                command = payload.get("command", "unknown")
                prompt_template = self._COMMAND_PROMPT_MAP.get(
                    command,
                    f"Execute /{command} on the following content.\n\nInput text:\n{{{{input_text}}}}",
                )

                # Step 1: Prompt assembly
                step_counter += 1
                prompt_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.PROMPT_TEMPLATE,
                    label=f"Prepare /{command} Prompt",
                    config={"template_inline": prompt_template},
                    position={"x": x_pos, "y": 200},
                )
                steps.append(prompt_step)
                x_pos += 300

                # Step 2: LLM generation
                step_counter += 1
                gen_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.LLM_GENERATE,
                    label=f"Generate /{command} Output",
                    config={"temperature": 0.7, "max_tokens": 2048},
                    position={"x": x_pos, "y": 200},
                )
                steps.append(gen_step)
                edges.append(PipelineEdge(source=prompt_step.id, target=gen_step.id))
                x_pos += 300

                # Wire to previous step if exists
                if len(steps) > 2:
                    prev_step = steps[-3]
                    edges.append(PipelineEdge(source=prev_step.id, target=prompt_step.id))

            elif action_type == "chat_message":
                message = payload.get("message", description)
                # Generalize the chat message into a template
                step_counter += 1
                chat_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.LLM_GENERATE,
                    label=f"Chat: {message[:40]}..." if len(message) > 40 else f"Chat: {message}",
                    config={
                        "prompt_override": "{{chat_instruction}}\n\nContext:\n{{input_text}}",
                        "temperature": 0.7,
                        "max_tokens": 2048,
                    },
                    position={"x": x_pos, "y": 200},
                )
                steps.append(chat_step)
                x_pos += 300

                # Wire to previous
                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=chat_step.id))

            elif action_type == "approval":
                step_counter += 1
                approval_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.APPROVE_OUTPUT,
                    label="Review & Approve Output",
                    config={"allow_edit": True},
                    position={"x": x_pos, "y": 200},
                )
                steps.append(approval_step)
                x_pos += 300

                # Wire to previous
                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=approval_step.id))

            elif action_type == "text_selection":
                step_counter += 1
                gather_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.GATHER_BUCKETS,
                    label="Gather Context",
                    config={
                        "container_types": payload.get("container_types", ["scene", "character"]),
                        "max_items": 10,
                    },
                    position={"x": x_pos, "y": 200},
                )
                steps.append(gather_step)
                x_pos += 300

                # Wire to previous
                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=gather_step.id))

            elif action_type == "save":
                step_counter += 1
                save_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.SAVE_TO_BUCKET,
                    label="Save Output",
                    config={
                        "container_type": payload.get("container_type", "fragment"),
                    },
                    position={"x": x_pos, "y": 200},
                )
                steps.append(save_step)
                x_pos += 300

                # Wire to previous
                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=save_step.id))

            elif action_type == "option_select":
                # Option selection (e.g. picking a brainstorm result) maps to
                # a review checkpoint
                step_counter += 1
                review_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.REVIEW_PROMPT,
                    label="Review & Select Option",
                    config={},
                    position={"x": x_pos, "y": 200},
                )
                steps.append(review_step)
                x_pos += 300

                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=review_step.id))

            elif action_type == "entity_mention":
                # Entity mentions enrich context — add a semantic search step
                step_counter += 1
                search_step = PipelineStepDef(
                    id=f"step_{step_counter}",
                    step_type=StepType.SEMANTIC_SEARCH,
                    label=f"Lookup: {payload.get('entity_name', 'entity')}",
                    config={"limit": 5},
                    position={"x": x_pos, "y": 200},
                )
                steps.append(search_step)
                x_pos += 300

                if len(steps) > 1:
                    edges.append(PipelineEdge(source=steps[-2].id, target=search_step.id))
            else:
                logger.warning("Unknown recorded action type '%s', skipping", action_type)
                continue

        # If the original session had approvals but the last step isn't an
        # approval, add a final checkpoint
        if has_approvals and steps and steps[-1].step_type not in (
            StepType.APPROVE_OUTPUT, StepType.REVIEW_PROMPT
        ):
            step_counter += 1
            final_approve = PipelineStepDef(
                id=f"step_{step_counter}",
                step_type=StepType.APPROVE_OUTPUT,
                label="Final Review",
                config={"allow_edit": True},
                position={"x": x_pos, "y": 200},
            )
            steps.append(final_approve)
            edges.append(PipelineEdge(source=steps[-2].id, target=final_approve.id))

        definition = PipelineDefinition(
            name=title,
            description=f"Recorded workflow distilled into reusable pipeline ({len(steps)} steps)",
            steps=steps,
            edges=edges,
        )

        return definition

    # ------------------------------------------------------------------
    # NL-to-DAG Pipeline Generation (Phase H Track 3)
    # ------------------------------------------------------------------

    async def generate_pipeline_from_nl(
        self,
        intent: str,
        title: str,
        agent_dispatcher: "AgentDispatcher",
    ) -> PipelineDefinition:
        """Convert a natural-language intent into a PipelineDefinition DAG.

        Uses the ``pipeline_director`` agent skill to generate a structured
        JSON response that is parsed into valid ``PipelineStepDef`` and
        ``PipelineEdge`` objects.

        Args:
            intent: Natural-language description of the desired workflow.
            title: Display name for the generated pipeline definition.
            agent_dispatcher: An ``AgentDispatcher`` instance for LLM calls.

        Returns:
            A validated ``PipelineDefinition`` ready to be saved and executed.

        Raises:
            ValueError: If the agent's response cannot be parsed into a
                valid ``PipelineDefinition``.
        """
        import re as _re

        # Resolve the pipeline_director skill
        skill = agent_dispatcher.skills.get("pipeline_director")
        if skill is None:
            raise ValueError(
                "pipeline_director skill not found. "
                "Ensure agents/skills/pipeline_director.md exists."
            )

        # Build a context payload that tells the LLM the exact Pydantic
        # schema it must produce.
        valid_step_types = [st.value for st in StepType]
        schema_context = {
            "output_format": "strict_json",
            "json_schema": {
                "steps": [
                    {
                        "id": "string (unique, e.g. 'step_1')",
                        "step_type": f"one of {valid_step_types}",
                        "label": "string (human-readable name for this step)",
                        "config": "dict (step-specific configuration, see config_schema per type)",
                    }
                ],
                "edges": [
                    {
                        "source": "string (source step id)",
                        "target": "string (target step id)",
                    }
                ],
            },
            "valid_step_types": valid_step_types,
            "instructions": (
                "Respond ONLY with a JSON object containing 'steps' and 'edges' arrays. "
                "Do NOT include any explanation outside the JSON. "
                "Each step must have a unique 'id', a valid 'step_type' from the list above, "
                "a human-readable 'label', and a 'config' dict. "
                "Edges define the DAG connections (source -> target). "
                "Ensure the DAG is valid — no orphan nodes, at least one path from start to end."
            ),
        }

        result = await agent_dispatcher.execute(skill, intent, context=schema_context)

        if not result.success:
            raise ValueError(
                f"Pipeline generation failed: {result.error or 'unknown error'}"
            )

        # Extract JSON from the response (handle markdown code fences)
        response_text = result.response.strip()
        fence_pattern = _re.compile(r"```(?:json)?\s*\n(.*?)\n```", _re.DOTALL)
        fence_matches = fence_pattern.findall(response_text)
        json_text = fence_matches[0] if fence_matches else response_text

        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Failed to parse pipeline JSON from LLM response: {exc}"
            ) from exc

        # Validate and construct Pydantic models
        raw_steps = parsed.get("steps", [])
        raw_edges = parsed.get("edges", [])

        if not raw_steps:
            raise ValueError("LLM response contained no pipeline steps")

        steps: List[PipelineStepDef] = []
        for raw_step in raw_steps:
            # Normalise step_type to handle case variations
            raw_type = raw_step.get("step_type", "")
            try:
                step_type = StepType(raw_type)
            except ValueError:
                logger.warning(
                    "Unknown step_type '%s' from LLM, defaulting to llm_generate",
                    raw_type,
                )
                step_type = StepType.LLM_GENERATE

            steps.append(
                PipelineStepDef(
                    id=raw_step.get("id", f"step_{len(steps)+1}"),
                    step_type=step_type,
                    label=raw_step.get("label", f"Step {len(steps)+1}"),
                    config=raw_step.get("config", {}),
                )
            )

        edges: List[PipelineEdge] = []
        step_ids = {s.id for s in steps}
        for raw_edge in raw_edges:
            src = raw_edge.get("source", "")
            tgt = raw_edge.get("target", "")
            if src in step_ids and tgt in step_ids:
                edges.append(PipelineEdge(source=src, target=tgt))
            else:
                logger.warning(
                    "Skipping edge %s->%s: references unknown step(s)", src, tgt
                )

        definition = PipelineDefinition(
            name=title,
            description=f"Auto-generated from intent: {intent}",
            steps=steps,
            edges=edges,
        )

        return definition

    # ------------------------------------------------------------------
    # Topological Sort
    # ------------------------------------------------------------------

    async def _handle_style_enforce_dialogue(self, run: PipelineRun, step: PipelineStepDef) -> None:
        """Enforce character style on dialogue in the text payload."""
        run.current_state = PipelineState.EXECUTING
        speaker_name = step.config.get("speaker_name", "")
        voice_profile_bucket_id = step.config.get("voice_profile_bucket_id", "")
        
        if not speaker_name or not voice_profile_bucket_id:
            logger.warning("Missing speaker_name or voice_profile_bucket_id for style enforce node")
            return
            
        # Get voice profile container
        profile_container = self.container_repo.get_container(voice_profile_bucket_id)
        if not profile_container:
            logger.warning(f"Voice profile container {voice_profile_bucket_id} not found")
            return
            
        voice_profile_attrs = profile_container.attributes
        
        # Get text from payload
        text = run.payload.get("text", run.payload.get("prompt_text", ""))
        if not text:
            return
            
        # Use style service locally
        from showrunner_tool.services.style_service import StyleService
        style_service = StyleService(None, None, None)
        
        new_text = await style_service.enforce_style_on_dialogue(text, speaker_name, voice_profile_attrs)
        
        run.payload["text"] = new_text
        run.payload["style_enforced_for"] = speaker_name
        
    @staticmethod
    def _topological_sort(definition: PipelineDefinition) -> List[PipelineStepDef]:
        """Sort pipeline steps in topological order (respects edges)."""
        step_map = {s.id: s for s in definition.steps}
        adj: Dict[str, List[str]] = {s.id: [] for s in definition.steps}
        in_degree: Dict[str, int] = {s.id: 0 for s in definition.steps}

        for edge in definition.edges:
            if edge.source in adj and edge.target in in_degree:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        # Kahn's algorithm
        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        result: List[PipelineStepDef] = []

        while queue:
            current = queue.pop(0)
            result.append(step_map[current])
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we didn't process all steps, fall back to definition order
        if len(result) < len(definition.steps):
            processed = {s.id for s in result}
            for step in definition.steps:
                if step.id not in processed:
                    result.append(step)

        return result


# Initialize step handlers after class definition
PipelineService._step_handlers = {
    StepType.GATHER_BUCKETS: PipelineService._handle_gather_buckets,
    StepType.SEMANTIC_SEARCH: PipelineService._handle_semantic_search,
    StepType.PROMPT_TEMPLATE: PipelineService._handle_prompt_template,
    StepType.MULTI_VARIANT: PipelineService._handle_multi_variant,
    StepType.LLM_GENERATE: PipelineService._handle_llm_generate,
    StepType.IMAGE_GENERATE: PipelineService._handle_image_generate,
    StepType.SAVE_TO_BUCKET: PipelineService._handle_save_to_bucket,
    StepType.HTTP_REQUEST: PipelineService._handle_http_request,
    StepType.RESEARCH_DEEP_DIVE: PipelineService._handle_research_deep_dive,
    StepType.STYLE_ENFORCE_DIALOGUE: PipelineService._handle_style_enforce_dialogue,
}
