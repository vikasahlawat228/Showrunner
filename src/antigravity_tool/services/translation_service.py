import json
import logging
from dataclasses import dataclass, field
from uuid import uuid4

from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService
from antigravity_tool.services.context_engine import ContextEngine
from antigravity_tool.services.agent_dispatcher import AgentDispatcher
from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.repositories.container_repo import ContainerRepository

logger = logging.getLogger(__name__)

@dataclass
class AdaptationNote:
    original: str
    adapted: str
    reason: str

@dataclass
class CulturalFlag:
    location: str
    flag: str
    action_taken: str

@dataclass
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    adaptation_notes: list[AdaptationNote]
    cultural_flags: list[CulturalFlag]
    glossary_applied: dict[str, str]
    confidence: float

class TranslationService:
    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        context_engine: ContextEngine,
        agent_dispatcher: AgentDispatcher,
        container_repo: ContainerRepository,
    ):
        self.kg_service = kg_service
        self.context_engine = context_engine
        self.agent_dispatcher = agent_dispatcher
        self.container_repo = container_repo

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        character_ids: list[str] | None = None,
        scene_id: str | None = None,
    ) -> TranslationResult:
        """Translate prose using the translator agent with cultural adaptation."""
        # 1. Load character profiles
        character_profiles = []
        if character_ids:
            for cid in character_ids:
                matches = self.kg_service.find_containers(filters={"id": cid})
                if matches:
                    c = matches[0]
                    name = c.get("name", "Unknown")
                    attrs = c.get("attributes", {})
                    speech = attrs.get("speech_style", "")
                    personality = attrs.get("personality", "")
                    character_profiles.append(
                        f"Character Name: {name}\nSpeech Style: {speech}\nPersonality: {personality}"
                    )

        # 2. Load project glossary
        glossary_entries = self.kg_service.find_containers(container_type="glossary_entry")
        glossary = {}
        for entry in glossary_entries:
            term = entry.get("name", "")
            attrs = entry.get("attributes", {})
            translations = attrs.get("translations", {})
            target_trans = translations.get(target_language)
            if term and target_trans:
                glossary[term] = target_trans

        # 3. Load scene context
        scene_context = ""
        if scene_id:
            matches = self.kg_service.find_containers(filters={"id": scene_id})
            if matches:
                scene = matches[0]
                attrs = scene.get("attributes", {})
                mood = attrs.get("mood", "")
                setting = attrs.get("setting", "")
                tone = attrs.get("tone", "")
                scene_context = f"Scene Context:\\nMood: {mood}\\nSetting: {setting}\\nTone: {tone}"

        # 4. Build input for translator_agent
        context = {
            "source_text": text,
            "source_language": source_language,
            "target_language": target_language,
        }
        if character_profiles:
            context["character_profiles"] = character_profiles
        if glossary:
            context["glossary"] = glossary
        if scene_context:
            context["scene_context"] = scene_context

        # 5. Execute agent
        skill = self.agent_dispatcher.skills.get("translator_agent")
        if not skill:
            raise ValueError("Translation skill 'translator_agent' not found.")

        intent = (
            "Translate the provided `source_text` from the `source_language` to "
            "the `target_language`. Apply the `glossary` if available, and adapt the text "
            "for cultural nuances, character speech styles, and scene context. Output the result "
            "exactly in the required JSON format."
        )

        result = await self.agent_dispatcher.execute(skill, intent=intent, context=context)
        if not result.success:
            logger.error(f"Translation failed: {result.error}")
            raise RuntimeError(f"Translation agent execution failed: {result.error}")

        # 6. Parse JSON response
        try:
            # Sometime LLMs wrap in markdown block
            resp_text = result.response.strip()
            if resp_text.startswith("```json"):
                resp_text = resp_text[7:]
            if resp_text.startswith("```"):
                resp_text = resp_text[3:]
            if resp_text.endswith("```"):
                resp_text = resp_text[:-3]

            parsed = json.loads(resp_text)
            
            adaptation_notes = [
                AdaptationNote(**n) for n in parsed.get("adaptation_notes", [])
            ]
            cultural_flags = [
                CulturalFlag(**f) for f in parsed.get("cultural_flags", [])
            ]
            
            return TranslationResult(
                translated_text=parsed.get("translated_text", ""),
                source_language=parsed.get("source_language", source_language),
                target_language=parsed.get("target_language", target_language),
                adaptation_notes=adaptation_notes,
                cultural_flags=cultural_flags,
                glossary_applied=parsed.get("glossary_applied", {}),
                confidence=parsed.get("confidence", 1.0),
            )
        except Exception as e:
            logger.error(f"Failed to parse translation result: {e} - Response: {result.response}")
            raise ValueError("Failed to parse the JSON response from the translator agent.")


    def get_glossary(self) -> list[dict]:
        """List all glossary entries for the project."""
        entries = self.kg_service.find_containers(container_type="glossary_entry")
        # Ensure 'id' is extracted along with name and attributes
        return [{"id": e.get("id"), "term": e.get("name"), **e.get("attributes", {})} for e in entries]

    def save_glossary_entry(
        self,
        term: str,
        translations: dict[str, str],
        notes: str = "",
    ) -> dict:
        """Create or update a glossary entry."""
        # Find if term exists
        existing = self.kg_service.find_containers(container_type="glossary_entry", filters={"name": term})
        
        if existing:
            container_id = existing[0].get("id")
            container = self.container_repo.get(container_id)
            if not container:
                 # fallback to create new if somehow missing in repo
                 container = GenericContainer(
                    id=str(uuid4()),
                    name=term,
                    container_type="glossary_entry",
                    attributes={"translations": translations, "notes": notes},
                    project_path=self.container_repo.project_path,
                )
            else:
                container.attributes["translations"] = translations
                container.attributes["notes"] = notes
        else:
            container = GenericContainer(
                id=str(uuid4()),
                name=term,
                container_type="glossary_entry",
                attributes={"translations": translations, "notes": notes},
                project_path=self.container_repo.project_path,
            )
            
        self.container_repo.save(container)
        self.kg_service.update_container(container)
        
        return {
            "id": container.id,
            "term": container.name,
            **container.attributes
        }
