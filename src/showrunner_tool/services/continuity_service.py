import logging
import json
from typing import Optional, Dict, Any, List
import os
from dataclasses import dataclass

from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService
from showrunner_tool.services.context_engine import ContextEngine
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.services.agent_dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)

@dataclass
class ContinuityVerdict:
    status: str          # "APPROVED", "REJECTED", "REVISION"
    reasoning: str
    suggestions: str
    affected_entities: list[str]
    severity: str        # "high", "medium", "low"
    flagged_text: Optional[str] = None

class ContinuityService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        event_service: EventService,
        agent_dispatcher: AgentDispatcher,
    ):
        self.kg_service = kg_service
        self.context_engine = context_engine
        self.event_service = event_service
        self.agent_dispatcher = agent_dispatcher
        self._recent_issues: Dict[str, ContinuityVerdict] = {}

    async def check_continuity(
        self,
        container_id: str,
        proposed_changes: Optional[Dict[str, Any]] = None,
        branch_id: str = "main",
    ) -> ContinuityVerdict:
        """Run a continuity check against the knowledge graph and future events."""
        # 1. Fetch the container details
        container = self.kg_service.get_container(container_id)
        if not container:
            return ContinuityVerdict(
                status="FAILED",
                reasoning=f"Container {container_id} not found.",
                suggestions="",
                affected_entities=[],
                severity="high"
            )

        # 2. Extract involved entities
        related_ids = [r.target_id for r in container.relationships if hasattr(r, 'target_id')]
        
        # 3. Query future dependencies (events mentioning these entities)
        # Check only the linear event history of this branch
        all_events = self.event_service.get_event_chain(branch_id)
        future_deps = []
        for e in all_events:
            # Match if the event affects one of our related entities
            if e.get("container_id") in related_ids:
                future_deps.append(e)

        # 4. Build the payload
        # Proposed events if we have proposed changes, else we just validate current state
        # The prompt says: "proposed_events: Array of event objects describing the new changes"
        proposals = []
        if proposed_changes:
            proposals.append({
                "container_id": container_id,
                "changes": proposed_changes
            })
        else:
             proposals.append({
                 "container_id": container_id,
                 "state": container.to_dict() if hasattr(container, "to_dict") else vars(container) if hasattr(container, "__dict__") else container
             })
             
        # Assemble context for these entities
        ctx_result = self.context_engine.assemble_context(
            query=f"Continuity check for {container.name}",
            container_ids=list(set(related_ids))
        )
        
        graph_context_data = {"context": ctx_result.text}
        
        payload = {
            "proposed_events": proposals,
            "graph_context": graph_context_data,
            "future_dependencies": future_deps[-20:] # limit to avoid blown token budget
        }

        # 5. Call agent dispatcher
        skill = self.agent_dispatcher.skills.get("continuity_analyst")
        if not skill:
            logger.error("continuity_analyst skill not found in agent dispatcher")
            return ContinuityVerdict(
                status="APPROVED",
                reasoning="Continuity analyst skill unavailable.",
                suggestions="",
                affected_entities=[],
                severity="low"
            )

        intent = "Analyze continuity for these changes."
        result = await self.agent_dispatcher.execute(skill, intent, context=payload)
        
        # 6. Parse JSON verdict
        status = "APPROVED"
        reasoning = "No issues detected or parsing failed."
        suggestions = ""
        affected_entities = []
        severity = "low"
        
        try:
             # Try to find JSON in response if it's not direct
             content = result.response.strip()
             if content.startswith("```json"):
                 content = content[7:]
             if content.startswith("```"):
                 content = content[3:]
             if content.endswith("```"):
                 content = content[:-3]
                 
             data = json.loads(content.strip())
             status = data.get("status", status)
             reasoning = data.get("reasoning", reasoning)
             suggestions = data.get("suggestions", suggestions)
             affected_entities = data.get("affected_entities", affected_entities)
             severity = data.get("severity", severity)
             flagged_text = data.get("flagged_text", None)
        except Exception as e:
             logger.warning(f"Failed to parse continuity_analyst response: {e}")
             flagged_text = None
             if not result.success:
                 reasoning = f"Agent failed: {result.error}"
        
        verdict = ContinuityVerdict(
            status=status,
            reasoning=reasoning,
            suggestions=suggestions,
            affected_entities=affected_entities,
            severity=severity,
            flagged_text=flagged_text
        )
        
        self._recent_issues[container_id] = verdict
        return verdict

    async def check_scene_continuity(self, scene_id: str) -> List[ContinuityVerdict]:
        """Run continuity checks on all entities in a scene."""
        scene = self.kg_service.get_container(scene_id)
        if not scene:
            return []
            
        attr_chars = []
        if hasattr(scene, "attributes"):
             attr_chars = scene.attributes.get("characters_present", [])
        elif isinstance(scene, dict) and "attributes" in scene:
             attr_chars = scene["attributes"].get("characters_present", [])
             
        entities_to_check = set([scene_id])
        
        for char in attr_chars:
            c = self.kg_service.get_container(char)
            if c:
                entities_to_check.add(c.id)
            else:
                 found = self.kg_service.find_containers(container_type="character", name=char)
                 if found: 
                     entities_to_check.add(found[0].id)
                     
        if hasattr(scene, "relationships"):
             for rel in scene.relationships:
                  if rel.get("target_id"):
                       entities_to_check.add(rel["target_id"])

        verdicts = []
        for eid in entities_to_check:
             v = await self.check_continuity(eid)
             if v.status in ["REJECTED", "REVISION"]:
                 verdicts.append(v)
                 
        if not verdicts:
            # Return an approved verdict for the scene if all good
            return [ContinuityVerdict(
                status="APPROVED",
                reasoning="No continuity issues found in this scene.",
                suggestions="",
                affected_entities=[],
                severity="low"
            )]
            
        return verdicts

    async def get_recent_issues(
        self,
        scope: str = "all",
        scope_id: Optional[str] = None,
    ) -> List[ContinuityVerdict]:
        """List recently detected continuity issues."""
        if scope == "all":
            return list(self._recent_issues.values())
        if scope == "scene" and scope_id:
             # In a real impl, we'd filter by what's in the scene
             # For now, just return all
             return list(self._recent_issues.values())
        return list(self._recent_issues.values())

    async def suggest_resolutions(self, issue: dict, kg_context: dict) -> list:
        """Given a continuity issue, generate 3 resolution options via LLM."""
        try:
            from litellm import completion
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set for suggest_resolutions")
                return []
                
            prompt = f"""You found this continuity issue in a story:
Issue: {issue.get('description', issue.get('reasoning', ''))}
Status: {issue.get('status', 'unknown')}

Story context: {str(kg_context)[:3000]}

Generate exactly 3 resolution options as a JSON array of objects.
Each object must have these keys:
- "description": a short title for the fix
- "affected_scenes": list of scene IDs to change (strings)
- "original_text": the exact snippet of text from the scene that needs to be replaced (string)
- "edits": specific instructions on what to change, or the exact new replacement text
- "risk": "low" | "medium" | "high" 
- "trade_off": what the writer gives up or impacts

Return ONLY the JSON array, no other text.
"""
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
                
            # Basic validation
            data = json.loads(raw.strip())
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Failed to generate resolutions: {e}")
            return []
