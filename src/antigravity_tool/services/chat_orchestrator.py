"""ChatOrchestrator — central brain for the agentic chat system (Phase J).

Handles message processing, intent classification, tool execution,
plan/execute mode, and pipeline control via chat.

Yields ChatEvent SSE stream for real-time frontend updates.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from antigravity_tool.schemas.chat import (
    ChatActionTrace,
    ChatArtifact,
    ChatEvent,
    ChatMessage,
)
from antigravity_tool.services.chat_session_service import ChatSessionService

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """Central orchestrator for agentic chat message processing.

    Pipeline per message:
      1. Check for /commands (plan, compact, etc.)
      2. Classify intent via IntentClassifier
      3. Assemble context via ChatContextManager
      4. Execute tool actions or generate chat response
      5. Persist message + traces
      6. Yield ChatEvent stream

    Plan/Execute Mode (J-6):
      /plan <goal> — propose N steps, yield as numbered plan
      /approve [step_numbers] — approve steps for execution
      /execute — run all approved steps sequentially

    Pipeline Control (J-7):
      "run pipeline <name>" — resolve definition, preview, launch background
      Pipeline SSE events multiplexed into chat stream
    """

    def __init__(
        self,
        session_service: ChatSessionService,
        context_assembler=None,
        intent_classifier=None,
        context_manager=None,
        tool_registry: Optional[Dict[str, Callable]] = None,
        pipeline_service=None,
        model_config_registry=None,
    ):
        self._session_service = session_service
        self._context_assembler = context_assembler
        self._intent_classifier = intent_classifier
        self._context_manager = context_manager
        self._tools = tool_registry or {}
        self._pipeline_service = pipeline_service
        self._model_config_registry = model_config_registry
        # Per-session plan state (session_id -> list of plan steps)
        self._plans: Dict[str, List[Dict[str, Any]]] = {}

    async def handle_message(
        self,
        session_id: str,
        content: str,
        mentioned_entity_ids: Optional[List[str]] = None,
        context_payload: Optional[dict] = None,
    ) -> AsyncGenerator[ChatEvent, None]:
        """Process a user message and yield SSE events."""
        start = time.monotonic()

        try:
            # Persist user message
            self._session_service.add_message(
                session_id=session_id,
                role="user",
                content=content,
                mentioned_entity_ids=mentioned_entity_ids,
            )

            # Check for /commands
            if content.strip().startswith("/"):
                async for event in self._handle_command(session_id, content.strip(), start):
                    yield event
                return

            # Intent classification
            intent = "CHAT"
            if self._intent_classifier:
                tool_intent = self._intent_classifier.classify(content)
                intent = tool_intent.tool

                # Check approval gate
                if tool_intent.requires_approval:
                    yield ChatEvent(
                        event_type="approval_needed",
                        data={"tool": intent, "params": tool_intent.params},
                    )
                    return

            trace1 = ChatActionTrace(
                tool_name="intent_classifier",
                context_summary=f"Classified as {intent}",
            ).model_dump()
            yield ChatEvent(
                event_type="action_trace",
                data=trace1,
            )

            # Execute tool if registered
            if intent != "CHAT" and intent.lower() in self._tools:
                async for event in self._execute_tool(
                    session_id, intent, content, mentioned_entity_ids, start, context_payload
                ):
                    yield event
                return

            # Default chat response via LLM
            response_text = ""
            try:
                # Pass context payload to the LLM generation explicitly
                async for chunk in self._generate_llm_response(session_id, content, intent, context_payload):
                    response_text += chunk
                    yield ChatEvent(event_type="token", data={"text": chunk})
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to shell response: {e}", exc_info=True)
                response_text = self._generate_shell_response(content, intent)
                # Stream tokens preserving em-dashes and spaces using regex
                words = re.findall(r'\S+\s*', response_text)
                for word in words:
                    yield ChatEvent(event_type="token", data={"text": word})

            elapsed_ms = int((time.monotonic() - start) * 1000)
            trace2 = ChatActionTrace(
                tool_name="chat_response",
                context_summary=f"Processed as {intent}",
                duration_ms=elapsed_ms,
            ).model_dump()

            assistant_msg = self._session_service.add_message(
                session_id=session_id,
                role="assistant",
                content=response_text,
                action_traces=[trace1, trace2],
            )
            est_tokens = len(content.split()) + len(response_text.split())
            self._session_service.update_token_usage(session_id, est_tokens)

            yield ChatEvent(
                event_type="complete",
                data={
                    "message_id": assistant_msg.id,
                    "session_id": session_id,
                    "duration_ms": elapsed_ms,
                    "trace": trace2,
                },
            )

        except Exception as e:
            logger.error("ChatOrchestrator error: %s", e)
            yield ChatEvent(
                event_type="error",
                data={"error": str(e), "session_id": session_id},
            )

    # ── /command handlers ─────────────────────────────────────────

    async def _handle_command(
        self, session_id: str, content: str, start: float
    ) -> AsyncGenerator[ChatEvent, None]:
        """Handle /slash commands."""
        parts = content.split(None, 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "/plan":
            async for event in self._handle_plan(session_id, args, start):
                yield event
        elif command == "/approve":
            async for event in self._handle_approve(session_id, args, start):
                yield event
        elif command == "/execute":
            async for event in self._handle_execute(session_id, start):
                yield event
        elif command == "/compact":
            async for event in self._handle_compact(session_id, start):
                yield event
        else:
            response = f"Unknown command: {command}. Available: /plan, /approve, /execute, /compact"
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(content.split()) + len(response.split()))
            yield ChatEvent(
                event_type="complete",
                data={"message_id": msg.id, "session_id": session_id},
            )

    async def _handle_plan(
        self, session_id: str, goal: str, start: float
    ) -> AsyncGenerator[ChatEvent, None]:
        """Create a multi-step plan for a goal."""
        if not goal:
            response = "Usage: /plan <goal description>"
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(goal.split()) + len(response.split()))
            yield ChatEvent(event_type="complete", data={"message_id": msg.id, "session_id": session_id})
            return

        trace = ChatActionTrace(
            tool_name="plan_generator",
            context_summary=f"Generating plan for: {goal}",
        ).model_dump()
        yield ChatEvent(
            event_type="action_trace",
            data=trace,
        )

        import litellm
        import json

        # LLM Plan Generation
        system_prompt = (
            "You are an expert project manager and writer's assistant. "
            "Given a goal, generate a concise, sequential 4-5 step execution plan. "
            "Return ONLY a JSON array of objects. Each object must have: "
            "'step' (integer), 'action' (string, max 10 words), and 'status' (always 'pending')."
        )
        
        try:
            response = await litellm.acompletion(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Goal: {goal}"}
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content.strip()
            # Clean possible markdown block
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            steps = json.loads(content)
        except Exception as e:
            # Fallback
            steps = [
                {"step": 1, "action": f"Analyze requirements for: {goal}", "status": "pending"},
                {"step": 2, "action": f"Gather context and entities related to: {goal}", "status": "pending"},
                {"step": 3, "action": f"Execute primary action for: {goal}", "status": "pending"},
                {"step": 4, "action": "Review and validate results", "status": "pending"},
            ]

        self._plans[session_id] = steps

        # Format plan as response
        lines = [f"## Plan: {goal}\n"]
        for s in steps:
            lines.append(f"  {s['step']}. {s['action']}")
        lines.append("\nUse `/approve 1,2,3,4` to approve steps, then `/execute` to run.")
        response = "\n".join(lines)

        for word in response.split():
            yield ChatEvent(event_type="token", data={"text": word + " "})

        msg = self._session_service.add_message(session_id, "assistant", response, action_traces=[trace])
        self._session_service.update_token_usage(session_id, len(goal.split()) + len(response.split()) + 50)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        yield ChatEvent(
            event_type="complete",
            data={"message_id": msg.id, "session_id": session_id, "duration_ms": elapsed_ms},
        )

    async def _handle_approve(
        self, session_id: str, args: str, start: float
    ) -> AsyncGenerator[ChatEvent, None]:
        """Approve specific steps in the current plan."""
        plan = self._plans.get(session_id)
        if not plan:
            response = "No active plan. Use /plan <goal> first."
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(args.split()) + len(response.split()))
            yield ChatEvent(event_type="complete", data={"message_id": msg.id, "session_id": session_id})
            return

        # Parse step numbers
        if args.strip().lower() == "all":
            step_nums = [s["step"] for s in plan]
        else:
            step_nums = [int(x.strip()) for x in re.split(r"[,\s]+", args) if x.strip().isdigit()]

        approved = []
        for step in plan:
            if step["step"] in step_nums:
                step["status"] = "approved"
                approved.append(step["step"])

        response = f"Approved steps: {', '.join(map(str, approved))}. Use /execute to run."
        yield ChatEvent(event_type="token", data={"text": response})
        msg = self._session_service.add_message(session_id, "assistant", response)
        self._session_service.update_token_usage(session_id, len(args.split()) + len(response.split()) + 10)
        yield ChatEvent(
            event_type="complete",
            data={"message_id": msg.id, "session_id": session_id},
        )

    async def _handle_execute(
        self, session_id: str, start: float
    ) -> AsyncGenerator[ChatEvent, None]:
        """Execute all approved steps in the current plan."""
        plan = self._plans.get(session_id)
        if not plan:
            response = "No active plan. Use /plan <goal> first."
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(response.split()))
            yield ChatEvent(event_type="complete", data={"message_id": msg.id, "session_id": session_id})
            return

        approved = [s for s in plan if s["status"] == "approved"]
        if not approved:
            response = "No approved steps. Use /approve <step_numbers> first."
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(response.split()))
            yield ChatEvent(event_type="complete", data={"message_id": msg.id, "session_id": session_id})
            return

        results = []
        action_traces = []
        for step in approved:
            step["status"] = "executing"
            trace = ChatActionTrace(
                tool_name=f"plan_step_{step['step']}",
                context_summary=step["action"],
            ).model_dump()
            action_traces.append(trace)
            yield ChatEvent(
                event_type="action_trace",
                data=trace,
            )

            # Shell mode: mark as complete
            step["status"] = "completed"
            results.append(f"Step {step['step']}: {step['action']} — completed (shell mode)")

            yield ChatEvent(
                event_type="background_update",
                data={"step": step["step"], "status": "completed"},
            )

        response = "## Execution Complete\n\n" + "\n".join(results)
        for word in response.split():
            yield ChatEvent(event_type="token", data={"text": word + " "})

        # Clean up plan
        del self._plans[session_id]

        msg = self._session_service.add_message(session_id, "assistant", response, action_traces=action_traces)
        self._session_service.update_token_usage(session_id, len(response.split()) + len(approved) * 50)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        yield ChatEvent(
            event_type="complete",
            data={"message_id": msg.id, "session_id": session_id, "duration_ms": elapsed_ms},
        )

    async def _handle_compact(
        self, session_id: str, start: float
    ) -> AsyncGenerator[ChatEvent, None]:
        """Compact session history."""
        if self._context_manager:
            result = self._context_manager.compact(session_id)
            response = (
                f"Compacted: {result.original_message_count} messages → "
                f"digest ({result.token_reduction} tokens saved)."
            )
        else:
            response = "Context manager not configured. Compaction unavailable."

        yield ChatEvent(event_type="token", data={"text": response})
        msg = self._session_service.add_message(session_id, "assistant", response)
        self._session_service.update_token_usage(session_id, len(response.split()))
        yield ChatEvent(
            event_type="complete",
            data={"message_id": msg.id, "session_id": session_id},
        )

    # ── Tool execution ────────────────────────────────────────────

    async def _execute_tool(
        self,
        session_id: str,
        intent: str,
        content: str,
        mentioned_entity_ids: Optional[List[str]],
        start: float,
        context_payload: Optional[dict] = None,
    ) -> AsyncGenerator[ChatEvent, None]:
        """Execute a registered tool and yield events."""
        tool_fn = self._tools.get(intent.lower())
        if not tool_fn:
            response = f"Tool '{intent}' is registered but not yet implemented."
            yield ChatEvent(event_type="token", data={"text": response})
            msg = self._session_service.add_message(session_id, "assistant", response)
            self._session_service.update_token_usage(session_id, len(content.split()) + len(response.split()))
            yield ChatEvent(event_type="complete", data={"message_id": msg.id, "session_id": session_id})
            return

        trace1 = ChatActionTrace(
            tool_name=intent,
            context_summary=f"Executing tool: {intent}",
        ).model_dump()
        yield ChatEvent(
            event_type="action_trace",
            data=trace1,
        )

        try:
            import inspect
            response = ""
            result = None
            if inspect.isasyncgenfunction(tool_fn):
                result_chunks = []
                async for chunk in tool_fn(
                    content,
                    mentioned_entity_ids or [],
                    session_id=session_id,
                    context_manager=self._context_manager,
                    context_payload=context_payload,
                ):
                    if isinstance(chunk, ChatEvent):
                        yield chunk
                    elif isinstance(chunk, str):
                        result_chunks.append(chunk)
                        for word in re.findall(r'\S+\s*', chunk):
                            yield ChatEvent(event_type="token", data={"text": word})
                response = "".join(result_chunks) or f"Tool '{intent}' completed."
                result = response
            elif inspect.iscoroutinefunction(tool_fn):
                result = await tool_fn(
                    content,
                    mentioned_entity_ids or [],
                    session_id=session_id,
                    context_manager=self._context_manager,
                    context_payload=context_payload,
                )
                response = str(result) if result else f"Tool '{intent}' executed successfully."
            else:
                result = tool_fn(
                    content, 
                    mentioned_entity_ids or [],
                    session_id=session_id,
                    context_manager=self._context_manager,
                    context_payload=context_payload,
                )
                response = str(result) if result else f"Tool '{intent}' executed successfully."
            
            # Emit artifact if result is significant enough
            if not inspect.isasyncgenfunction(tool_fn) and result and intent.lower() in ("search", "create", "evaluate", "pipeline"):
                artifact = ChatArtifact(
                    artifact_type=self._intent_to_artifact_type(intent),
                    title=f"{intent.title()} Results",
                    content=str(result),
                )
                yield ChatEvent(
                    event_type="artifact",
                    data=artifact.model_dump(),
                )
        except Exception as e:
            response = f"Tool '{intent}' failed: {e}"
            logger.warning("Tool execution failed: %s", e)

        if not str(tool_fn).startswith("<function") or not inspect.isasyncgenfunction(tool_fn):
            for word in re.findall(r'\S+\s*', response):
                yield ChatEvent(event_type="token", data={"text": word})

        elapsed_ms = int((time.monotonic() - start) * 1000)
        trace2 = ChatActionTrace(
            tool_name=intent,
            context_summary=f"Executed tool: {intent}",
            duration_ms=elapsed_ms,
        ).model_dump()
        msg = self._session_service.add_message(session_id, "assistant", response, action_traces=[trace1, trace2])
        self._session_service.update_token_usage(session_id, len(content.split()) + len(response.split()) + 40)

        yield ChatEvent(
            event_type="complete",
            data={
                "message_id": msg.id,
                "session_id": session_id,
                "duration_ms": elapsed_ms,
                "trace": trace2,
            },
        )

    # ── Response generation ───────────────────────────────────────

    async def _generate_llm_response(
        self, session_id: str, user_content: str, intent: str, context_payload: Optional[dict] = None
    ) -> AsyncGenerator[str, None]:
        """Stream an LLM response using ChatContextManager + LiteLLM."""
        try:
            import litellm
        except ImportError:
            raise RuntimeError("litellm is not installed, falling back")

        context = {}
        if self._context_manager:
            context = self._context_manager.build_context(session_id, context_payload=context_payload)

        system_context = context.get("system_context", "")
        system_prompt = self._build_system_prompt(system_context, intent)
        messages = context.get("messages", [])
        messages.append({"role": "user", "content": user_content})

        model_name = "gemini/gemini-2.5-flash"
        if self._model_config_registry:
            config = self._model_config_registry.resolve(agent_id="chat")
            if config and hasattr(config, "model"):
                model_name = config.model

        response = await litellm.acompletion(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            stream=True,
            max_tokens=8192,
        )

        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _build_system_prompt(self, system_context: str, intent: str) -> str:
        """Assemble the system prompt."""
        base_prompt = "You are the Showrunner story co-pilot for a manga/manhwa creation tool."
        
        intent_instructions = ""
        if intent == "CHAT":
            intent_instructions = "The user is engaging in general conversation. Be helpful, brainstorm and respond to their queries."
        else:
            intent_instructions = f"The intent was classified as {intent}, but fell through to the chat handler. Explain your capabilities if needed."

        parts = filter(None, [base_prompt, intent_instructions, system_context])
        return "\n\n".join(parts)

    def _intent_to_artifact_type(self, intent: str) -> str:
        """Map tool intent to artifact type."""
        mapping = {
            "search": "table",
            "create": "yaml",
            "evaluate": "outline",
            "pipeline": "outline",
            "research": "prose",
        }
        return mapping.get(intent.lower(), "prose")

    def _generate_shell_response(self, user_content: str, intent: str) -> str:
        """Generate a simple shell response (placeholder).

        Will be replaced by LLM call when context_manager is wired.
        """
        if intent == "CHAT":
            return (
                "I received your message. The chat orchestrator is running in "
                "shell mode (Phase J-1). LLM integration, tool execution, and "
                "context assembly will be available in subsequent phases."
            )
        return f"Intent '{intent}' is not yet implemented."
