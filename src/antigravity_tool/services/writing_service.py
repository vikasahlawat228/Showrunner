"""Writing Service — business logic for the Zen Mode writing surface."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from antigravity_tool.schemas.fragment import (
    ContainerContextResponse,
    EntityDetection,
    WritingFragment,
)
from antigravity_tool.repositories.container_repo import ContainerRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)


class WritingService:
    """Handles saving writing fragments, entity detection, and context retrieval."""

    def __init__(
        self,
        container_repo: ContainerRepository,
        kg_service: KnowledgeGraphService,
        project_path: Path,
        event_service: EventService,
    ):
        self.container_repo = container_repo
        self.kg_service = kg_service
        self.project_path = project_path
        self.event_service = event_service

    # ------------------------------------------------------------------
    # Fragment persistence
    # ------------------------------------------------------------------

    def save_fragment(
        self,
        text: str,
        title: Optional[str] = None,
        scene_id: Optional[str] = None,
        chapter: Optional[int] = None,
        branch_id: str = "main",
        associated_containers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[WritingFragment, List[EntityDetection]]:
        """Persist a writing fragment as a YAML-backed container."""
        
        # Compute word count
        word_count = len(text.split()) if text.strip() else 0
        meta = metadata or {}
        meta["word_count"] = word_count

        # Auto-detect entities
        detected = self.detect_entities(text)
        relationships = []
        assoc = list(set(associated_containers or []))
        for d in detected:
            relationships.append({
                "target_id": d.container_id,
                "type": "mentions",
                "metadata": {
                    "mention": d.mention,
                    "confidence": d.confidence
                }
            })
            if d.container_id not in assoc:
                assoc.append(d.container_id)

        fragment = WritingFragment(
            text=text,
            title=title,
            scene_id=scene_id,
            chapter=chapter,
            branch_id=branch_id,
            associated_containers=assoc,
            metadata=meta,
        )

        # Build the GenericContainer wrapper for storage
        from antigravity_tool.schemas.container import GenericContainer

        container = GenericContainer(
            id=fragment.id,
            container_type="fragment",
            name=title or f"Fragment {fragment.id[:8]}",
            attributes={
                "text": text,
                "scene_id": scene_id,
                "chapter": chapter,
                "branch_id": branch_id,
                "associated_containers": assoc,
                **meta,
            },
            relationships=relationships,
            created_at=fragment.created_at,
            updated_at=fragment.updated_at,
        )

        # Save via the container repo (triggers knowledge graph sync).
        # ContainerRepository auto-creates the fragment/ subdirectory.
        self.container_repo.save_container(container)

        # Emit event to EventService for event sourcing (mandatory in Phase F)
        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id=branch_id,
                event_type="CREATE",
                container_id=fragment.id,
                payload=container.attributes,
            )
        except Exception as e:
            logger.warning("Failed to emit CREATE event for fragment %s: %s", fragment.id, e)

        return fragment, detected

    # ------------------------------------------------------------------
    # Entity detection (LLM-based via Gemini)
    # ------------------------------------------------------------------

    def detect_entities(self, text: str) -> List[EntityDetection]:
        """Use Gemini to identify entity mentions in the text, then match to containers."""
        # Step 1: Get all known container names from the knowledge graph
        all_containers = self.kg_service.find_containers()
        if not all_containers:
            return []

        # Build a lookup of names → container info
        container_lookup: Dict[str, Dict[str, Any]] = {}
        for c in all_containers:
            container_lookup[c["name"].lower()] = c

        # Step 2: Call Gemini to extract entity mentions
        container_names = [c["name"] for c in all_containers]
        entities_from_llm = self._llm_detect_entities(text, container_names)

        # Step 3: Match LLM results to actual containers
        detections: List[EntityDetection] = []
        for mention_info in entities_from_llm:
            mention = mention_info.get("mention", "")
            matched_name = mention_info.get("matched_name", "").lower()
            confidence = mention_info.get("confidence", 0.5)

            container = container_lookup.get(matched_name)
            if container:
                detections.append(
                    EntityDetection(
                        mention=mention,
                        container_id=container["id"],
                        container_type=container["container_type"],
                        container_name=container["name"],
                        confidence=confidence,
                    )
                )

        return detections

    def _llm_detect_entities(
        self, text: str, known_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Call Gemini to identify which known entities are mentioned in the text."""
        try:
            from litellm import completion

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set; falling back to fuzzy match.")
                return self._fuzzy_fallback(text, known_names)

            system_prompt = (
                "You are an entity detection assistant for a creative writing tool. "
                "Given a piece of text and a list of known entity names, identify which "
                "entities are mentioned or referenced in the text. Return a JSON array of objects, "
                "each with: {\"mention\": \"<exact text span>\", \"matched_name\": \"<name from the known list>\", "
                "\"confidence\": <0.0-1.0>}. Only include entities you are confident about. "
                "Return ONLY the JSON array, no other text."
            )

            user_prompt = (
                f"Known entities: {json.dumps(known_names)}\n\n"
                f"Text to analyze:\n{text}"
            )

            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                api_key=api_key,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

            return json.loads(raw)

        except Exception as e:
            logger.error("LLM entity detection failed: %s", e)
            return self._fuzzy_fallback(text, known_names)

    def _fuzzy_fallback(
        self, text: str, known_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Simple substring matching fallback when LLM is unavailable."""
        text_lower = text.lower()
        results = []
        for name in known_names:
            if name.lower() in text_lower:
                results.append(
                    {
                        "mention": name,
                        "matched_name": name,
                        "confidence": 0.8,
                    }
                )
        return results

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    def get_context_summary(self, container_id: str) -> Optional[ContainerContextResponse]:
        """Build a formatted context summary for a container."""
        # Look up the container from the knowledge graph
        containers = self.kg_service.find_containers(filters={"id": container_id})

        # Fallback: query by direct ID match on the index
        if not containers:
            all_c = self.kg_service.find_containers()
            containers = [c for c in all_c if c.get("id") == container_id]

        if not containers:
            return None

        container = containers[0]
        attrs = container.get("attributes", {})
        if isinstance(attrs, str):
            import json as _json
            attrs = _json.loads(attrs)
        elif "attributes_json" in container:
            raw = container["attributes_json"]
            attrs = json.loads(raw) if isinstance(raw, str) else raw

        # Get related containers
        related = self.kg_service.get_neighbors(container_id)

        # Build a prose context string
        name = container.get("name", "Unknown")
        ctype = container.get("container_type", "unknown")
        lines = [f"**{name}** ({ctype})"]
        for key, value in attrs.items():
            if key.startswith("_") or key in ("id", "schema_version"):
                continue
            lines.append(f"- {key}: {value}")

        if related:
            lines.append(f"\n**Related entities:** {len(related)}")
            for r in related[:5]:
                lines.append(f"- {r.get('name', '?')} ({r.get('container_type', '?')})")

        return ContainerContextResponse(
            container_id=container_id,
            container_type=ctype,
            name=name,
            context_text="\n".join(lines),
            attributes=attrs,
            related_count=len(related),
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_containers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fuzzy search containers by name."""
        all_containers = self.kg_service.find_containers()
        query_lower = query.lower()

        scored = []
        for c in all_containers:
            name = c.get("name", "")
            name_lower = name.lower()

            # Exact match → highest score
            if name_lower == query_lower:
                scored.append((1.0, c))
            elif name_lower.startswith(query_lower):
                scored.append((0.8, c))
            elif query_lower in name_lower:
                scored.append((0.5, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, c in scored[:limit]:
            # Parse attributes_json if present
            attrs = c.get("attributes", {})
            if "attributes_json" in c:
                raw = c["attributes_json"]
                attrs = json.loads(raw) if isinstance(raw, str) else raw

            results.append({
                "id": c["id"],
                "name": c["name"],
                "container_type": c["container_type"],
                "attributes": attrs,
                "score": score,
            })

        return results
