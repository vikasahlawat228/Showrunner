import json
from dataclasses import dataclass
from typing import Any

from litellm import completion

from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.services.context_engine import ContextEngine
from showrunner_tool.services.knowledge_graph_service import KnowledgeGraphService


@dataclass
class EmotionalScore:
    """Per-scene emotional analysis result."""
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    hope: float          # 0.0-1.0
    conflict: float      # 0.0-1.0
    tension: float       # 0.0-1.0
    sadness: float       # 0.0-1.0
    joy: float           # 0.0-1.0
    dominant_emotion: str # "tension", "hope", etc.
    summary: str         # 1-line explanation


@dataclass
class EmotionalArcResult:
    """Full emotional arc analysis across scenes."""
    scores: list[EmotionalScore]
    flat_zones: list[dict[str, Any]]    # { start_scene, end_scene, reason }
    peak_moments: list[dict[str, Any]]  # { scene_id, emotion, intensity }
    pacing_grade: str                   # "A", "B", "C", "D", "F"
    recommendations: list[str]


@dataclass
class CharacterRibbon:
    """Per-scene character presence data for ribbon visualization."""
    scene_id: str
    scene_name: str
    chapter: int
    scene_number: int
    characters: list[dict[str, Any]]  # { character_id, character_name, prominence: 0.0-1.0 }

@dataclass
class VoiceProfile:
    character_id: str
    character_name: str
    avg_sentence_length: float
    vocabulary_diversity: float   # unique words / total words (0.0-1.0)
    formality_score: float        # 0.0 (casual) - 1.0 (formal)
    top_phrases: list[str]        # Most distinctive phrases (3-5)
    dialogue_sample_count: int


@dataclass
class VoiceScorecardResult:
    profiles: list[VoiceProfile]
    similarity_matrix: list[dict]  # [{ char_a, char_b, similarity: 0.0-1.0 }]
    warnings: list[str]

class AnalysisService:
    """Analyzes story content for emotional arcs, character voices, and ribbons."""

    def __init__(
        self,
        kg_service: KnowledgeGraphService,
        container_repo: ContainerRepository,
        context_engine: ContextEngine,
    ):
        self.kg_service = kg_service
        self.container_repo = container_repo
        self.context_engine = context_engine

    async def analyze_emotional_arc(self, chapter: int | None = None) -> EmotionalArcResult:
        """
        Score each scene for emotional valence using LLM analysis.
        If chapter is None, analyze all chapters.
        Returns scores + flat zones + recommendations.
        """
        scenes = self.kg_service.find_containers(container_type="scene")
        
        # Sort scenes based on their chapter and scene_number (if available in attributes)
        def get_sort_key(s):
            ch = s.attributes.get("chapter", 999)
            sc = s.attributes.get("scene_number", 999)
            return (ch, sc)
            
        scenes.sort(key=get_sort_key)
        
        if chapter is not None:
            scenes = [s for s in scenes if s.attributes.get("chapter") == chapter]
            
        scores = []
        for s in scenes:
            ch_num = s.attributes.get("chapter", 0)
            sc_num = s.attributes.get("scene_number", 0)
            
            # Assemble context using ContextEngine
            ctx_result = self.context_engine.assemble_context(
                query=f"Scene emotional context for '{s.name}'",
                container_ids=[s.id]
            )
            
            system_prompt = (
                "You are an expert story analyst. Analyze the following scene context "
                "and score its emotional valence. Output your result strictly as JSON without markdown blocks formatting.\n"
                "Format: {\"hope\": 0.0-1.0, \"conflict\": 0.0-1.0, \"tension\": 0.0-1.0, \"sadness\": 0.0-1.0, \"joy\": 0.0-1.0, \"dominant_emotion\": \"tension\", \"summary\": \"1-line summary\"}"
            )
            
            user_prompt = f"Scene ID: {s.id}\nScene Name: {s.name}\nContext:\n{ctx_result.text}"
            
            try:
                # We use a default fast model for analysis
                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=256,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response")
                
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to strip markdown code blocks
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    result = json.loads(content.strip())
                
                hope = float(result.get("hope", 0.0))
                conflict = float(result.get("conflict", 0.0))
                tension = float(result.get("tension", 0.0))
                sadness = float(result.get("sadness", 0.0))
                joy = float(result.get("joy", 0.0))
                dominant = result.get("dominant_emotion", "neutral")
                summary = result.get("summary", "")
                
            except Exception as e:
                # Fallback on parsing failure
                hope, conflict, tension, sadness, joy = 0.5, 0.5, 0.5, 0.0, 0.5
                dominant, summary = "unknown", f"Failed analysis: {str(e)}"
                
            scores.append(EmotionalScore(
                scene_id=s.id,
                scene_name=s.name,
                chapter=ch_num,
                scene_number=sc_num,
                hope=hope,
                conflict=conflict,
                tension=tension,
                sadness=sadness,
                joy=joy,
                dominant_emotion=dominant,
                summary=summary
            ))

        # Detect flat zones (3+ consecutive scenes with tension < 0.3)
        flat_zones = []
        current_flat_start = None
        for i, score in enumerate(scores):
            if score.tension < 0.3:
                if current_flat_start is None:
                    current_flat_start = i
            else:
                if current_flat_start is not None and i - current_flat_start >= 3:
                    flat_zones.append({
                        "start_scene": scores[current_flat_start].scene_name,
                        "end_scene": scores[i-1].scene_name,
                        "reason": f"Low tension for {i - current_flat_start} consecutive scenes"
                    })
                current_flat_start = None
                
        if current_flat_start is not None and len(scores) - current_flat_start >= 3:
            flat_zones.append({
                "start_scene": scores[current_flat_start].scene_name,
                "end_scene": scores[-1].scene_name,
                "reason": f"Low tension for {len(scores) - current_flat_start} consecutive scenes"
            })

        # Detect peak moments (any emotion > 0.8)
        peak_moments = []
        for score in scores:
            for emotion in ["hope", "conflict", "tension", "sadness", "joy"]:
                val = getattr(score, emotion)
                if val > 0.8:
                    peak_moments.append({
                        "scene_id": score.scene_id,
                        "emotion": emotion,
                        "intensity": val
                    })

        # Compute pacing grade (heuristic based on variance)
        tensions = [s.tension for s in scores]
        grade = "C"
        variance = 0
        if tensions:
            mean_tension = sum(tensions) / len(tensions)
            variance = sum((t - mean_tension) ** 2 for t in tensions) / len(tensions)
            if variance > 0.1 and len(peak_moments) > 0 and len(flat_zones) == 0:
                grade = "A"
            elif variance > 0.05 and len(flat_zones) <= 1:
                grade = "B"
            elif len(flat_zones) > 2:
                grade = "D"
            if len(flat_zones) > 3 or (len(peak_moments) == 0 and len(scores) > 3):
                grade = "F"
        
        recs = []
        if grade in ["D", "F"]:
            recs.append("Add a peak conflict moment to break up long flat zones.")
            recs.append("Increase tension variation to improve pacing.")
        elif grade in ["C"]:
            recs.append("Consider condensing some scenes to increase tension variance.")
        else:
            recs.append("Pacing looks dynamic and varied. Keep it up.")

        return EmotionalArcResult(
            scores=scores,
            flat_zones=flat_zones,
            peak_moments=peak_moments,
            pacing_grade=grade,
            recommendations=recs
        )

    def compute_character_ribbons(self, chapter: int | None = None) -> list[CharacterRibbon]:
        """
        Derive character presence + prominence per scene from KG relationships.
        No LLM call — pure KG query + heuristic scoring.
        Returns ribbon data for SVG visualization.
        """
        scenes = self.kg_service.find_containers(container_type="scene")
        
        # Sort scenes
        def get_sort_key(s):
            ch = s.attributes.get("chapter", 999)
            sc = s.attributes.get("scene_number", 999)
            return (ch, sc)
            
        scenes.sort(key=get_sort_key)
        
        if chapter is not None:
            scenes = [s for s in scenes if s.attributes.get("chapter") == chapter]
            
        ribbons = []
        for s in scenes:
            ch_num = s.attributes.get("chapter", 0)
            sc_num = s.attributes.get("scene_number", 0)
            
            # Use relationships (or characters_present attribute if available)
            chars_present = []
            
            pov_char_id = s.attributes.get("pov_character_id")
            attr_chars = s.attributes.get("characters_present", [])
            
            seen_char_ids = set()
            
            # POV = 1.0, otherwise 0.7 if in characters_present list, 0.3 if mentioned in relationships
            if pov_char_id:
                char_c = self.kg_service.get_container(pov_char_id)
                if char_c:
                    chars_present.append({
                        "character_id": char_c.id,
                        "character_name": char_c.name,
                        "prominence": 1.0
                    })
                    seen_char_ids.add(char_c.id)
            
            for attr_char in attr_chars:
                # attr_char could be a name or ID, try ID
                char_c = self.kg_service.get_container(attr_char)
                # If not found, try to find by name
                if not char_c:
                    found = self.kg_service.find_containers(container_type="character", name=attr_char)
                    if found:
                        char_c = found[0]
                
                if char_c and char_c.id not in seen_char_ids:
                    chars_present.append({
                        "character_id": char_c.id,
                        "character_name": char_c.name,
                        "prominence": 0.7
                    })
                    seen_char_ids.add(char_c.id)
            
            # Check relationships for any "mentions" or "features"
            for rel in s.relationships:
                tid = rel.get("target_id")
                if tid and tid not in seen_char_ids:
                    # check if target is a character
                    target_c = self.kg_service.get_container(tid)
                    if target_c and target_c.container_type == "character":
                        chars_present.append({
                            "character_id": target_c.id,
                            "character_name": target_c.name,
                            "prominence": 0.3
                        })
                        seen_char_ids.add(target_c.id)
                        
            ribbons.append(CharacterRibbon(
                scene_id=s.id,
                scene_name=s.name,
                chapter=ch_num,
                scene_number=sc_num,
                characters=chars_present
            ))
            
        return ribbons

    async def analyze_character_voices(self, character_ids: list[str] | None = None) -> VoiceScorecardResult:
        import math
        import re
        
        chars = self.kg_service.find_containers(container_type="character")
        if character_ids:
            char_set = set(character_ids)
            chars = [c for c in chars if c.id in char_set]
            
        profiles = []
        # Get all fragments to match against scenes
        all_fragments = self.kg_service.find_containers(container_type="fragment")
        all_scenes = self.kg_service.find_containers(container_type="scene")
        
        for char in chars:
            # Gather scenes character is present in
            char_scene_ids = set()
            for s in all_scenes:
                attr_chars = s.attributes.get("characters_present", [])
                if char.id in attr_chars or char.name in attr_chars:
                    char_scene_ids.add(s.id)
                for rel in s.relationships:
                    if rel.get("target_id") == char.id:
                        char_scene_ids.add(s.id)
            for rel in char.relationships:
                 if rel.get("type") == "present_in" and rel.get("target_id"):
                     char_scene_ids.add(rel["target_id"])

            text_blocks = []
            for f in all_fragments:
                # Find scene_id reference in fragment
                f_scene_id = f.attributes.get("scene_id")
                if f_scene_id in char_scene_ids:
                    if "text" in f.attributes:
                        text_blocks.append(f.attributes["text"])
            
            combined_text = "\n".join(text_blocks)
            if not combined_text.strip():
                # Fallback: general query
                ctx_result = self.context_engine.assemble_context(
                    query=f"Dialogue spoken by {char.name}",
                    container_ids=[char.id]
                )
                combined_text = ctx_result.text
                
            if not combined_text.strip():
                continue

            # Limit text context to avoid token overflow
            combined_text = combined_text[:12000]

            dialogue_system = f"Extract all dialogue lines spoken by {char.name} from this text. Return only the dialogue spoken by {char.name}, one quote per line. Do not include tags or descriptions."
            
            try:
                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=[
                        {"role": "system", "content": dialogue_system},
                        {"role": "user", "content": combined_text}
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                dialogue_text = response.choices[0].message.content or ""
            except Exception:
                dialogue_text = ""
                
            if not dialogue_text.strip():
                continue
                
            # Sentence splitting and length
            sentences = [s.strip() for s in re.split(r'[.!?]+', dialogue_text) if s.strip()]
            if not sentences:
                continue
            words_per_sentence = [len(s.split()) for s in sentences]
            avg_sentence_length = sum(words_per_sentence) / len(sentences)
            
            # Vocab diversity
            words = re.findall(r'\b\w+\b', dialogue_text.lower())
            if not words:
                continue
            unique_words = set(words)
            vocab_diversity = len(unique_words) / len(words)
            
            # Formality & Top phrases via LLM
            eval_system = (
                "Analyze the following dialogue snippet for a character. Provide a JSON response with:\n"
                "1. 'formality_score' (number from 0.0 for very casual/slang to 1.0 for extremely formal/pedantic)\n"
                "2. 'top_phrases': an array of 3 to 5 distinctive phrases, verbal tics, or repeated words used by this character.\n"
                "Return only JSON."
            )
            formality_score = 0.5
            top_phrases = []
            try:
                eval_resp = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=[
                        {"role": "system", "content": eval_system},
                        {"role": "user", "content": dialogue_text[:4000]}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                content = eval_resp.choices[0].message.content or "{}"
                content = content.strip()
                if content.startswith("```json"):
                     content = content[7:-3]
                elif content.startswith("```"):
                     content = content[3:-3]
                eval_data = json.loads(content)
                formality_score = float(eval_data.get("formality_score", 0.5))
                top_phrases = eval_data.get("top_phrases", [])
            except Exception:
                pass
                
            profiles.append(VoiceProfile(
                character_id=char.id,
                character_name=char.name,
                avg_sentence_length=avg_sentence_length,
                vocabulary_diversity=vocab_diversity,
                formality_score=formality_score,
                top_phrases=top_phrases,
                dialogue_sample_count=len(sentences)
            ))
            
        warnings = []
        sim_matrix = []
        
        for i in range(len(profiles)):
            for j in range(i + 1, len(profiles)):
                p1 = profiles[i]
                p2 = profiles[j]
                
                v1 = [min(p1.avg_sentence_length / 30.0, 1.0), p1.vocabulary_diversity, p1.formality_score]
                v2 = [min(p2.avg_sentence_length / 30.0, 1.0), p2.vocabulary_diversity, p2.formality_score]
                
                dot = sum(a*b for a, b in zip(v1, v2))
                mag1 = math.sqrt(sum(a*a for a in v1))
                mag2 = math.sqrt(sum(a*a for a in v2))
                
                sim = 0.0
                if mag1 > 0 and mag2 > 0:
                    sim = dot / (mag1 * mag2)
                    
                sim_matrix.append({
                    "char_a": p1.character_id,
                    "char_b": p2.character_id,
                    "similarity": sim
                })
                
                if sim > 0.7:
                     warnings.append(
                         f"⚠️ {p1.character_name} and {p2.character_name} sound {int(sim*100)}% similar."
                     )
                     
        return VoiceScorecardResult(
            profiles=profiles,
            similarity_matrix=sim_matrix,
            warnings=warnings
        )
