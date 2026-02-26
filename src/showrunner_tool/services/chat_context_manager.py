"""Chat Context Manager — 3-layer context model for agentic chat (Phase J-2).

Layers:
  1. Project Memory — persistent, auto-injected
  2. Session History — recent messages within context budget
  3. On-Demand Retrieval — @-mention entity injection via ContextAssembler

Handles token budgeting across all layers and /compact operations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from showrunner_tool.schemas.chat import (
    ChatCompactionResult,
    ChatMessage,
)
from showrunner_tool.services.chat_session_service import ChatSessionService
from showrunner_tool.services.project_memory_service import ProjectMemoryService

logger = logging.getLogger(__name__)

# Budget allocation ratios
MEMORY_BUDGET_RATIO = 0.1    # 10% for project memory
HISTORY_BUDGET_RATIO = 0.6   # 60% for session history
RETRIEVAL_BUDGET_RATIO = 0.3  # 30% for on-demand retrieval


class ChatContextManager:
    """Assembles 3-layer context for the chat orchestrator.

    Layer 1: Project Memory (persistent rules, decisions, preferences)
    Layer 2: Session History (recent messages, within budget)
    Layer 3: On-Demand Retrieval (@-mentions → entity context)
    """

    def __init__(
        self,
        session_service: ChatSessionService,
        memory_service: ProjectMemoryService,
        context_assembler=None,  # Optional ContextAssembler for entity retrieval
    ):
        self._session_service = session_service
        self._memory_service = memory_service
        self._context_assembler = context_assembler

    def build_context(
        self,
        session_id: str,
        mentioned_entity_ids: Optional[List[str]] = None,
        token_budget: int = 100_000,
        context_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the 3-layer context for an LLM call.

        Returns a dict with:
          - "system_context": project memory + history text + active editor context
          - "messages": trimmed message history for chat format
          - "entity_context": on-demand entity data
          - "token_usage": estimated tokens used across layers
          - "layers": breakdown by layer for Glass Box
        """
        # Make sure context_assembler is available to pull Tier 1
        if not self._context_assembler:
            logger.warning("ChatContextManager isolated - no ContextAssembler provided")
        layers: Dict[str, int] = {}

        # Layer 1: Project Memory
        memory_budget = int(token_budget * MEMORY_BUDGET_RATIO)
        
        # Legacy local project_memory.json (keep for backwards compat)
        memory_text = self._memory_service.to_context_string()

        # Add Tier 1 Auto-Memory from Knowledge Graph
        if self._context_assembler and hasattr(self._context_assembler, "get_tier1_memory"):
            active_era = context_payload.get("era_id") if context_payload else None
            tier1 = self._context_assembler.get_tier1_memory(max_tokens=memory_budget // 2, active_era_id=active_era)
            if tier1:
                memory_text = tier1 + "\n\n" + memory_text
        
        # Inject Active Editor Context (CUJ 14 - Zen Mode side-by-side)
        if context_payload:
            payload_lines = ["\n\n## Active Editor Context"]
            for k, v in context_payload.items():
                # Truncate very long content (e.g. huge text buffers)
                if isinstance(v, str) and len(v) > 10000:
                    v = v[:10000] + "... [truncated]"
                payload_lines.append(f"**{k}**: {v}")
            memory_text += "\n".join(payload_lines)

        memory_tokens = self._estimate_tokens(memory_text)
        if memory_tokens > memory_budget:
            memory_text = memory_text[: memory_budget * 4]
            memory_tokens = memory_budget
        layers["project_memory"] = memory_tokens

        # Layer 2: Session History
        history_budget = int(token_budget * HISTORY_BUDGET_RATIO)
        messages = self._session_service.get_messages(session_id)
        trimmed_messages, history_tokens = self._trim_messages(messages, history_budget)
        layers["session_history"] = history_tokens

        # Layer 3: On-Demand Retrieval
        entity_context = ""
        retrieval_tokens = 0
        if mentioned_entity_ids and self._context_assembler:
            retrieval_budget = int(token_budget * RETRIEVAL_BUDGET_RATIO)
            entity_context = self._resolve_mentions(
                mentioned_entity_ids, retrieval_budget
            )
            retrieval_tokens = self._estimate_tokens(entity_context)
        layers["on_demand_retrieval"] = retrieval_tokens

        total_tokens = sum(layers.values())

        return {
            "system_context": memory_text,
            "messages": [
                {"role": m.role, "content": m.content} for m in trimmed_messages
            ],
            "entity_context": entity_context,
            "token_usage": total_tokens,
            "layers": layers,
        }

    def compact(
        self,
        session_id: str,
        keep_recent: int = 10,
    ) -> ChatCompactionResult:
        """Compact a session's history by summarizing old messages.

        Keeps the most recent `keep_recent` messages and replaces older
        ones with a summary digest.
        """
        messages = self._session_service.get_messages(session_id)

        if len(messages) <= keep_recent:
            return ChatCompactionResult(
                digest="",
                original_message_count=len(messages),
                token_reduction=0,
                compaction_number=0,
            )

        # Split into old (to summarize) and recent (to keep)
        old_messages = messages[:-keep_recent]
        kept_messages = messages[-keep_recent:]

        # Build digest from old messages
        digest_lines = []
        for msg in old_messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            content_preview = msg.content[:200]
            digest_lines.append(f"[{prefix}]: {content_preview}")

        digest = "## Conversation Summary\n" + "\n".join(digest_lines)

        # Estimate token reduction
        old_tokens = sum(self._estimate_tokens(m.content) for m in old_messages)
        digest_tokens = self._estimate_tokens(digest)
        reduction = old_tokens - digest_tokens

        # Get session and update compaction state
        session = self._session_service.get_session(session_id)
        compaction_number = 0
        if session:
            compaction_number = session.compaction_count + 1

        # Persist digest as a system message
        self._session_service.add_message(
            session_id=session_id,
            role="system",
            content=digest,
        )

        # Extract entity IDs mentioned across compacted messages
        preserved = set()
        for msg in kept_messages:
            preserved.update(msg.mentioned_entity_ids)

        return ChatCompactionResult(
            digest=digest,
            original_message_count=len(messages),
            token_reduction=max(0, reduction),
            preserved_entities=list(preserved),
            compaction_number=compaction_number,
        )

    def _trim_messages(
        self, messages: List[ChatMessage], budget: int
    ) -> tuple[List[ChatMessage], int]:
        """Trim messages from oldest to fit within token budget."""
        if not messages:
            return [], 0

        # Keep messages from most recent, working backwards
        kept: List[ChatMessage] = []
        total_tokens = 0

        for msg in reversed(messages):
            msg_tokens = self._estimate_tokens(msg.content)
            if total_tokens + msg_tokens > budget:
                break
            kept.insert(0, msg)
            total_tokens += msg_tokens

        return kept, total_tokens

    def _resolve_mentions(
        self, entity_ids: List[str], budget: int
    ) -> str:
        """Resolve @-mentioned entities into context text.

        Uses ContextAssembler for entity retrieval when available.
        """
        if not self._context_assembler:
            return ""

        # For now, return a simple placeholder
        # Full implementation will use ContextAssembler.compile() with entity scope
        lines = [f"## Referenced Entities ({len(entity_ids)})"]
        for eid in entity_ids:
            lines.append(f"- Entity: {eid}")
        text = "\n".join(lines)

        # Trim to budget
        max_chars = budget * 4
        if len(text) > max_chars:
            text = text[:max_chars] + "\n..."

        return text

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count: ~4 chars per token."""
        return len(text) // 4
