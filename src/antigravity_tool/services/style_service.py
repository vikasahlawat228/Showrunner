import logging
import json
from typing import Optional, List, Dict, Any
import os
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

    async def extract_dialogue_by_speaker(self, text: str, speaker_name: str) -> list:
        """Use LLM to identify lines of dialogue attributed to a specific character.
        Returns list of {"line_number": int, "original_text": str, "speaker": str}"""
        try:
            from litellm import completion
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not set for extract_dialogue")
                return []
                
            # Split text into lines for reference
            lines = text.split('\n')
            lines_with_numbers = "\n".join([f"[{i}] {line}" for i, line in enumerate(lines)])
            
            prompt = f"""You are a dialogue extraction assistant.
Given this text with line numbers, find all spoken dialogue attributed to the character: {speaker_name}

Return a JSON array of objects with these keys for each spoken line:
- "line_number": the integer line number (from the brackets)
- "original_text": the exact string of dialogue spoken
- "speaker": "{speaker_name}"

Text:
{lines_with_numbers}

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
                
            data = json.loads(raw.strip())
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Failed to extract dialogue: {e}")
            return []

    async def enforce_style_on_dialogue(self, text: str, speaker_name: str, voice_profile: dict) -> str:
        """Restyle only the specified character's dialogue while preserving surrounding prose."""
        try:
            dialogue_lines = await self.extract_dialogue_by_speaker(text, speaker_name)
            if not dialogue_lines:
                return text
                
            from litellm import completion
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return text
                
            lines = text.split('\n')
            
            # For each line, rewrite it according to the voice profile
            for item in dialogue_lines:
                line_idx = item.get("line_number")
                original = item.get("original_text", "")
                
                if line_idx is None or line_idx >= len(lines) or not original:
                    continue
                    
                full_context_line = lines[line_idx]
                
                prompt = f"""Rewrite the following dialogue for {speaker_name} to match their voice profile.
Voice Profile:
- Tone/Style: {voice_profile.get('tone', 'neutral')}
- Vocabulary: {voice_profile.get('vocabulary_level', 'average')}
- Speech Patterns: {voice_profile.get('speech_patterns', 'normal')}
- Forbidden Words: {voice_profile.get('forbidden_words', [])}

Original line in context:
"{full_context_line}"

Specifically rewrite ONLY the spoken portion: "{original}"

Return ONLY the completely revised full line (including surrounding action tags), nothing else.
"""
                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=[{"role": "user", "content": prompt}],
                    api_key=api_key
                )
                
                revised_line = response.choices[0].message.content.strip()
                # Remove quotes if the LLM added them unnecessarily around the whole line
                if revised_line.startswith('"') and revised_line.endswith('"') and not full_context_line.startswith('"'):
                     revised_line = revised_line[1:-1]
                     
                lines[line_idx] = revised_line
                
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Failed to enforce dialogue style: {e}")
            return text
