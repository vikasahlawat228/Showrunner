"""Context Engine — centralized context assembly with token budgeting and summarization.

Provides a unified layer for assembling context from the Knowledge Graph,
estimating token counts, enforcing budgets, and summarizing when needed.
Used by PipelineService step handlers and DirectorService for LLM context management.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


@dataclass
class ContextBucketInfo:
    """Metadata about a single context bucket included in assembly."""

    id: str
    name: str
    container_type: str
    summary: str  # First ~100 chars of formatted text


@dataclass
class ContextResult:
    """Structured result from context assembly."""

    text: str                        # The assembled context string
    token_estimate: int              # Estimated token count
    containers_included: int         # How many containers were included
    containers_truncated: int        # How many were dropped due to budget
    was_summarized: bool             # Whether summarization was applied
    buckets: list[ContextBucketInfo] = field(default_factory=list)  # Glass Box: individual bucket metadata


class ContextEngine:
    """Centralized context assembly with token budgeting and summarization.

    Resolves containers from the KnowledgeGraphService, formats their attributes
    as structured text, enforces a token budget, and optionally summarizes via LLM
    when context exceeds limits.
    """

    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        container_repo: ContainerRepository,
    ):
        self.kg_service = kg_service
        self.container_repo = container_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble_context(
        self,
        query: str,
        container_ids: Optional[List[str]] = None,
        container_types: Optional[List[str]] = None,
        max_tokens: int = 4000,
        include_relationships: bool = True,
        active_era_id: Optional[str] = None,
    ) -> ContextResult:
        """Assemble context from the knowledge graph within a token budget.

        Steps:
        1. Resolve containers by IDs or types from KnowledgeGraphService
        2. For each container, format its attributes as structured text
        3. If include_relationships, also fetch 1-hop neighbors
        4. Estimate token count (4 chars ~ 1 token)
        5. If over budget, truncate least-relevant entries (by keyword overlap with query)
        6. Return structured ContextResult with the assembled text and metadata
        """
        # Step 1: Resolve explicitly requested containers
        raw_containers = self._resolve_containers(container_ids, container_types, active_era_id)

        # Step 1b (Phase H): Fetch semantically relevant containers
        semantic_ids: set[str] = set()
        try:
            semantic_hits = self.kg_service.semantic_search(query, limit=5)
            for hit in semantic_hits:
                hid = hit.get("id", "")
                if hid:
                    semantic_ids.add(hid)
        except Exception as exc:
            logger.debug("Semantic search unavailable: %s", exc)

        # Merge semantic hits (deduplicated)
        existing_ids = {c.get("id") for c in raw_containers}
        missing_ids = semantic_ids - existing_ids
        if missing_ids:
            for mid in missing_ids:
                rows = self.kg_service.find_containers(filters={"id": mid})
                raw_containers.extend(rows)

        if not raw_containers:
            return ContextResult(
                text="",
                token_estimate=0,
                containers_included=0,
                containers_truncated=0,
                was_summarized=False,
            )

        # Step 2 + 3: Format each container (with optional relationships)
        formatted_entries: List[Dict[str, Any]] = []
        for container in raw_containers:
            entry_text = self._format_container(container)

            if include_relationships:
                cid = container.get("id", "")
                neighbors = self.kg_service.get_neighbors(cid)
                if neighbors:
                    neighbor_lines = ["\n  Related:"]
                    for n in neighbors[:5]:
                        n_name = n.get("name", "?")
                        n_type = n.get("container_type", "?")
                        neighbor_lines.append(f"  - {n_name} ({n_type})")
                    entry_text += "\n".join(neighbor_lines)

            relevance = self._relevance_score(query, entry_text)
            # Phase H: boost relevance for semantically matched containers
            cid = container.get("id", "")
            if cid in semantic_ids:
                relevance = min(1.0, relevance + 0.3)
            formatted_entries.append({
                "text": entry_text,
                "relevance": relevance,
                "container": container,
            })

        # Step 4 + 5: Sort by relevance and apply token budget
        formatted_entries.sort(key=lambda e: e["relevance"], reverse=True)

        included_texts: List[str] = []
        included_buckets: List[ContextBucketInfo] = []
        running_tokens = 0
        containers_included = 0
        containers_truncated = 0

        for entry in formatted_entries:
            entry_tokens = self.estimate_tokens(entry["text"])
            if running_tokens + entry_tokens <= max_tokens:
                included_texts.append(entry["text"])
                running_tokens += entry_tokens
                containers_included += 1
                # Capture bucket metadata for Glass Box
                c = entry["container"]
                included_buckets.append(ContextBucketInfo(
                    id=c.get("id", ""),
                    name=c.get("name", c.get("container_type", "unknown")),
                    container_type=c.get("container_type", "unknown"),
                    summary=entry["text"][:120].replace("\n", " "),
                ))
            else:
                containers_truncated += 1

        assembled = "\n\n---\n\n".join(included_texts)

        # Step 6: Auto-inject relevant research (Task 4.3)
        try:
            research_containers = self.kg_service.find_containers(container_type="research")
            r_entries = []
            for c in research_containers:
                # ignore if already in included_buckets
                if any(b.id == c.get("id") for b in included_buckets):
                    continue
                entry_text = self._format_container(c)
                rel = self._relevance_score(query, entry_text)
                if rel >= 0.1:  # Simple overlap threshold
                    r_entries.append({"text": entry_text, "relevance": rel, "container": c})
            
            if r_entries:
                r_entries.sort(key=lambda e: e["relevance"], reverse=True)
                r_included = []
                for r in r_entries[:3]:
                    r_tokens = self.estimate_tokens(r["text"])
                    if running_tokens + r_tokens <= max_tokens:
                        r_included.append(r["text"])
                        running_tokens += r_tokens
                        c = r["container"]
                        included_buckets.append(ContextBucketInfo(
                            id=c.get("id", ""),
                            name=c.get("name", "research_note"),
                            container_type="research",
                            summary=r["text"][:120].replace("\n", " "),
                        ))
                
                if r_included:
                    assembled += "\n\n## Research Notes\n\n" + "\n\n---\n\n".join(r_included)
        except Exception as e:
            logger.warning("Failed to auto-inject research: %s", e)

        return ContextResult(
            text=assembled,
            token_estimate=self.estimate_tokens(assembled),
            containers_included=containers_included,
            containers_truncated=containers_truncated,
            was_summarized=False,
            buckets=included_buckets,
        )

    def summarize_if_needed(self, text: str, max_tokens: int = 2000) -> str:
        """If text exceeds max_tokens, use LiteLLM to produce a concise summary.

        Falls back to truncation if the LLM call fails.
        """
        current_tokens = self.estimate_tokens(text)
        if current_tokens <= max_tokens:
            return text

        try:
            from litellm import completion

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set; falling back to truncation.")
                return self._truncate(text, max_tokens)

            target_words = max_tokens  # rough 1:1 token-to-word for summaries
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise summarization assistant. "
                            "Summarize the following context while preserving all key details "
                            "about characters, settings, plot points, and relationships. "
                            f"Keep the summary under {target_words} words."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                api_key=api_key,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            logger.error("LLM summarization failed: %s", e)
            return self._truncate(text, max_tokens)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count: ~4 chars per token."""
        return len(text) // 4

    def get_tier1_memory(self, max_tokens: int = 2000, active_era_id: Optional[str] = None) -> str:
        """Fetch Tier 1 Memory (Global Lore/Facts) stored by the agent."""
        try:
            memory_containers = self.kg_service.find_containers(container_type="project_memory")
            
            if active_era_id:
                era_results = []
                for base in memory_containers:
                    if base.get("parent_version_id"):
                        continue
                    era_entity = self.kg_service.get_entity_at_era(base.get("id"), active_era_id)
                    if era_entity:
                        era_results.append(era_entity)
                memory_containers = era_results

            if not memory_containers:
                return ""

            lines = ["## Core Project Memory (Tier 1)"]
            running_tokens = self.estimate_tokens(lines[0])
            
            # Sort newest first assuming they have a created_at or just by list order
            for c in reversed(memory_containers):
                attrs = c.get("attributes", {})
                if isinstance(attrs, str):
                    try:
                        import json
                        attrs = json.loads(attrs)
                    except:
                        attrs = {}
                fact = attrs.get("fact", "")
                if fact:
                    line = f"- {fact}"
                    tokens = self.estimate_tokens(line)
                    if running_tokens + tokens <= max_tokens:
                        lines.append(line)
                        running_tokens += tokens
            
            if len(lines) > 1:
                return "\n".join(lines) + "\n\n"
            return ""
        except Exception as e:
            logger.error(f"Failed to fetch Tier 1 Memory: {e}")
            return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_containers(
        self,
        container_ids: Optional[List[str]] = None,
        container_types: Optional[List[str]] = None,
        active_era_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Resolve containers from the knowledge graph by IDs or types."""
        results: List[Dict[str, Any]] = []

        if container_ids:
            # Fetch each container by ID
            if active_era_id:
                for cid in container_ids:
                    era_entity = self.kg_service.get_entity_at_era(cid, active_era_id)
                    if era_entity:
                        results.append(era_entity)
            else:
                for cid in container_ids:
                    bases = self.kg_service.find_containers(filters={"id": cid})
                    if bases:
                        results.extend(bases)

        if container_types:
            for ctype in container_types:
                type_results = self.kg_service.find_containers(container_type=ctype)
                
                if active_era_id:
                    era_results = []
                    for base in type_results:
                        if base.get("parent_version_id"):
                            continue
                        era_entity = self.kg_service.get_entity_at_era(base.get("id"), active_era_id)
                        if era_entity:
                            era_results.append(era_entity)
                    type_results = era_results
                    
                # Deduplicate by id
                existing_ids = {c.get("id") for c in results}
                for c in type_results:
                    if c.get("id") not in existing_ids:
                        results.append(c)

        # If neither IDs nor types specified, fetch all containers
        if not container_ids and not container_types:
            results = self.kg_service.find_containers()
            if active_era_id:
                era_results = []
                for base in results:
                    if base.get("parent_version_id"):
                        continue
                    era_entity = self.kg_service.get_entity_at_era(base.get("id"), active_era_id)
                    if era_entity:
                        era_results.append(era_entity)
                results = era_results

        return results

    def _format_container(self, container: Dict[str, Any]) -> str:
        """Format a single container's data as structured text."""
        name = container.get("name", "Unknown")
        ctype = container.get("container_type", "unknown")

        # Parse attributes from JSON string if needed
        attrs = container.get("attributes", {})
        if isinstance(attrs, str):
            try:
                attrs = json.loads(attrs)
            except (json.JSONDecodeError, TypeError):
                attrs = {}
        elif "attributes_json" in container:
            raw = container["attributes_json"]
            if isinstance(raw, str):
                try:
                    attrs = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    attrs = {}
            else:
                attrs = raw if isinstance(raw, dict) else {}

        lines = [f"## {name} ({ctype})"]
        for key, value in attrs.items():
            if key.startswith("_") or key in ("id", "schema_version"):
                continue
            # Truncate long values to avoid a single container consuming the budget
            str_value = str(value)
            if len(str_value) > 500:
                str_value = str_value[:500] + "..."
            lines.append(f"- **{key}**: {str_value}")

        return "\n".join(lines)

    def _relevance_score(self, query: str, text: str) -> float:
        """Simple keyword-overlap relevance scoring.

        Computes the fraction of query words found in the text (case-insensitive).
        """
        if not query:
            return 0.5  # neutral relevance when no query provided

        query_words = set(query.lower().split())
        if not query_words:
            return 0.5

        text_lower = text.lower()
        matches = sum(1 for w in query_words if w in text_lower)
        return matches / len(query_words)

    def _truncate(self, text: str, max_tokens: int) -> str:
        """Hard truncation to stay within token budget."""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[...context truncated to fit token budget]"
