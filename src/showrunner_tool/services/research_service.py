"""Research service — agent-powered research with Knowledge Graph persistence."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.schemas.container import GenericContainer
from showrunner_tool.services.agent_dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)


class ResearchService:
    """Executes research queries via the research agent skill and persists
    results as GenericContainer objects with container_type="research_topic".
    """

    def __init__(
        self,
        container_repo: ContainerRepository,
        event_service: EventService,
        agent_dispatcher: AgentDispatcher,
    ):
        self.container_repo = container_repo
        self.event_service = event_service
        self.agent_dispatcher = agent_dispatcher

    # ------------------------------------------------------------------
    # Container conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _research_to_container(
        query: str,
        summary: str,
        confidence_score: float,
        sources: List[str],
        key_facts: Dict[str, Any],
    ) -> GenericContainer:
        """Create a GenericContainer for a research result."""
        return GenericContainer(
            container_type="research_topic",
            name=f"Research: {query[:50]}",
            attributes={
                "original_query": query,
                "summary": summary,
                "confidence_score": confidence_score,
                "sources": sources,
                "key_facts": key_facts,
            },
            relationships=[],
        )

    @staticmethod
    def _container_to_research_dict(container: GenericContainer) -> Dict[str, Any]:
        """Extract research data from a GenericContainer."""
        attrs = container.attributes
        return {
            "id": container.id,
            "original_query": attrs.get("original_query", ""),
            "summary": attrs.get("summary", ""),
            "confidence_score": attrs.get("confidence_score", 0.0),
            "sources": attrs.get("sources", []),
            "key_facts": attrs.get("key_facts", {}),
            "created_at": container.created_at.isoformat()
            if hasattr(container.created_at, "isoformat")
            else str(container.created_at),
            "updated_at": container.updated_at.isoformat()
            if hasattr(container.updated_at, "isoformat")
            else str(container.updated_at),
        }

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save_research(
        self,
        query: str,
        summary: str,
        confidence_score: float,
        sources: List[str],
        key_facts: Dict[str, Any],
    ) -> GenericContainer:
        """Create and persist a research_topic container."""
        container = self._research_to_container(
            query=query,
            summary=summary,
            confidence_score=confidence_score,
            sources=sources,
            key_facts=key_facts,
        )
        self.container_repo.save_container(container)

        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type="CREATE",
                container_id=container.id,
                payload=container.attributes,
            )
        except Exception as e:
            logger.warning(
                "Failed to emit CREATE event for research %s: %s", container.id, e
            )

        return container

    def list_research(self) -> List[Dict[str, Any]]:
        """Return all research_topic containers as dicts."""
        containers = self.container_repo.list_by_type("research_topic")
        results = []
        for c in containers:
            try:
                results.append(self._container_to_research_dict(c))
            except Exception as e:
                logger.warning("Failed to load research container %s: %s", c.id, e)
        return results

    def get_research(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Get a single research result by ID, or None if not found."""
        for item in self.list_research():
            if item["id"] == research_id:
                return item
        return None

    # ------------------------------------------------------------------
    # Agent execution
    # ------------------------------------------------------------------

    async def execute_research(self, query: str) -> Optional[Dict[str, Any]]:
        """Dispatch a research query to the research_agent skill and persist results.

        Returns the research dict on success, or None on failure.
        """
        skill = self.agent_dispatcher.skills.get("research_agent")
        if skill is None:
            logger.error("research_agent skill not loaded")
            return None

        result = await self.agent_dispatcher.execute(skill, query)

        if not result.success:
            logger.error("Research agent failed: %s", result.error)
            return None

        # Try to extract structured data from the agent response
        research_data = self._parse_agent_response(result)
        if research_data is None:
            logger.error("Failed to parse research agent response")
            return None

        container = self.save_research(
            query=query,
            summary=research_data.get("summary", ""),
            confidence_score=float(research_data.get("confidence_score", 0.0)),
            sources=research_data.get("sources", []),
            key_facts=research_data.get("key_facts", {}),
        )

        return self._container_to_research_dict(container)

    @staticmethod
    def _parse_agent_response(result) -> Optional[Dict[str, Any]]:
        """Extract structured JSON from an AgentResult.

        Tries result.actions first (pre-extracted by AgentDispatcher),
        then falls back to parsing result.response as raw JSON.
        """
        # AgentDispatcher._extract_actions() already parses JSON from code fences
        if result.actions:
            return result.actions[0]

        # Fallback: try parsing the raw response
        raw = result.response.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None
