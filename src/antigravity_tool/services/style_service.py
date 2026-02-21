import logging
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService
from antigravity_tool.services.context_engine import ContextEngine
from antigravity_tool.services.agent_dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)

@dataclass
class StyleIssue:
    category: str
    severity: str
    location: str
    description: str
    suggestion: str

@dataclass
class StyleEvaluation:
    status: str
    overall_score: float
    issues: List[StyleIssue]
    strengths: List[str]
    summary: str

class StyleService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        agent_dispatcher: AgentDispatcher,
    ):
        self.kg_service = kg_service
        self.context_engine = context_engine
        self.agent_dispatcher = agent_dispatcher

    async def evaluate_style(
        self,
        text: str,
        scene_id: Optional[str] = None,
    ) -> StyleEvaluation:
        """Evaluate prose against the project's narrative style guide."""
        
        # 1. Load NarrativeStyleGuide
        style_guides = self.kg_service.find_containers(container_type="style_guide")
        
        if style_guides:
            sg = style_guides[0]
            style_guide_context = sg.attributes if hasattr(sg, "attributes") else (sg.get("attributes", {}) if isinstance(sg, dict) else {})
            if isinstance(style_guide_context, str):
                 try:
                     style_guide_context = json.loads(style_guide_context)
                 except:
                     pass
        else:
            style_guide_context = {
                "general_notes": "Third-person past tense, accessible literary vocabulary, medium pacing."
            }

        # 2. If scene_id provided, load scene context
        scene_context = {}
        if scene_id:
            scene = self.kg_service.get_container(scene_id)
            if scene:
                 scene_attr = scene.attributes if hasattr(scene, "attributes") else (scene.get("attributes", {}) if isinstance(scene, dict) else {})
                 scene_context = {
                     "tone": scene_attr.get("mood", "neutral"),
                     "pov_character_id": scene_attr.get("pov_character_id", "")
                 }
                 
                 # Assemble extra context if helpful
                 ctx_result = self.context_engine.assemble_context(
                     query=f"Scene style requirements",
                     container_ids=[scene_id]
                 )
                 scene_context["extra_notes"] = ctx_result.text

        # 3. Build payload for style_enforcer
        payload = {
            "text": text,
            "style_guide": style_guide_context,
            "scene_context": scene_context
        }

        # 4. Execute agent
        skill = self.agent_dispatcher.skills.get("style_enforcer")
        if not skill:
            logger.error("style_enforcer skill not found.")
            return StyleEvaluation(
                status="ERROR",
                overall_score=0.0,
                issues=[StyleIssue(category="system", severity="high", location="system", description="style_enforcer agent missing", suggestion="")],
                strengths=[],
                summary="System configuration error: style agent is missing."
            )

        intent = "Evaluate this text against our style guide requirements."
        result = await self.agent_dispatcher.execute(skill, intent, context=payload)

        # 5. Parse response
        status = "APPROVED"
        overall_score = 1.0
        issues = []
        strengths = []
        summary = "No stylistic issues flagged."

        try:
             content = result.response.strip()
             if content.startswith("```json"):
                 content = content[7:]
             if content.startswith("```"):
                 content = content[3:]
             if content.endswith("```"):
                 content = content[:-3]

             data = json.loads(content.strip())
             status = data.get("status", status)
             overall_score = float(data.get("overall_score", overall_score))
             strengths = data.get("strengths", strengths)
             summary = data.get("summary", summary)

             raw_issues = data.get("issues", [])
             for i in raw_issues:
                 issues.append(StyleIssue(
                     category=i.get("category", "other"),
                     severity=i.get("severity", "low"),
                     location=i.get("location", "unknown"),
                     description=i.get("description", ""),
                     suggestion=i.get("suggestion", "")
                 ))
        except Exception as e:
             logger.warning(f"Failed to parse style_enforcer output: {e}\nRaw output: {result.response}")
             if not result.success:
                 summary = f"Agent execution failed: {result.error}"
                 status = "ERROR"

        return StyleEvaluation(
            status=status,
            overall_score=overall_score,
            issues=issues,
            strengths=strengths,
            summary=summary
        )
