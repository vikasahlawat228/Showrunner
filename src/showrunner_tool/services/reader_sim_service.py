from typing import Any
from dataclasses import dataclass
from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.server.api_schemas import ReadingSimResult, PanelReadingMetrics


class ReaderSimService:
    def __init__(self, container_repo: ContainerRepository):
        self.container_repo = container_repo

    def simulate_reading(self, scene_id: str) -> ReadingSimResult:
        """Simulate the webtoon reading experience for a scene to assess pacing."""
        
        # Get panels for scene
        scene_container = self.container_repo.get_container(scene_id)
        if not scene_container or scene_container.container_type != "scene":
            raise ValueError(f"Scene not found: {scene_id}")

        all_panels = self.container_repo.list_containers(container_type="panel")
        scene_panels = [
            p for p in all_panels 
            if p.attributes.get("scene_id") == scene_id
        ]
        
        # Sort by panel_number
        scene_panels.sort(key=lambda p: p.attributes.get("panel_number", 0))

        metrics_list = []
        total_seconds = 0.0
        
        pacing_dead_zones = []
        info_overload_warnings = []
        
        consecutive_slow = 0
        slow_start_panel = None
        
        for panel in scene_panels:
            attrs = panel.attributes
            panel_num = attrs.get("panel_number", 0)
            panel_type = attrs.get("camera_angle", "medium")
            desc = set(attrs.get("description", "").split())
            dialogue_text = " ".join([d.get("text", "") for d in attrs.get("dialogues", [])])
            dial_words = len(dialogue_text.split())
            desc_words = len(attrs.get("description", "").split())
            
            # Base logic
            base_duration = attrs.get("duration_seconds", 3.0)
            
            # Additional heuristic adjustments
            desc_time = (desc_words / 10.0) * 0.3 # 0.3s per 10 words
            dial_time = (dial_words / 10.0) * 0.5 # 0.5s per 10 words
            
            # Type factor
            type_bonus = 0.0
            type_lower = panel_type.lower()
            if "splash" in type_lower or "full" in type_lower:
                type_bonus = 2.0
            elif "establishing" in type_lower or "wide" in type_lower:
                type_bonus = 1.5
            elif "close" in type_lower or "insert" in type_lower:
                type_bonus = 0.5
                
            est_reading_seconds = base_duration + desc_time + dial_time + type_bonus
            
            # Normalization
            total_words = desc_words + dial_words
            max_expected = 50.0  # arbitrary baseline for dense panels
            text_density = min(total_words / max_expected, 1.0)
            
            is_info_dense = text_density > 0.7
            
            if is_info_dense:
                info_overload_warnings.append({
                    "panel_id": panel.id,
                    "panel_number": panel_num,
                    "reason": "Text density exceeds 70% threshold"
                })
                
            pacing_type = "medium"
            if est_reading_seconds > 5.0:
                pacing_type = "slow"
                consecutive_slow += 1
                if consecutive_slow == 1:
                    slow_start_panel = panel_num
            elif est_reading_seconds < 2.5:
                pacing_type = "fast"
                consecutive_slow = 0
            else:
                consecutive_slow = 0
                
            if consecutive_slow >= 3:
                pacing_dead_zones.append({
                    "start_panel": slow_start_panel,
                    "end_panel": panel_num,
                    "reason": f"{consecutive_slow} consecutive slow panels"
                })
            
            metrics = PanelReadingMetrics(
                panel_id=panel.id,
                panel_number=panel_num,
                panel_type=panel_type,
                estimated_reading_seconds=round(est_reading_seconds, 1),
                text_density=round(text_density, 2),
                is_info_dense=is_info_dense,
                pacing_type=pacing_type
            )
            metrics_list.append(metrics)
            total_seconds += est_reading_seconds
            
        # Engagement score based on pacing variety
        fast_count = sum(1 for p in metrics_list if p.pacing_type == "fast")
        slow_count = sum(1 for p in metrics_list if p.pacing_type == "slow")
        total_p = len(metrics_list)
        
        engagement = 0.8  # Default baseline
        if total_p > 0:
            if fast_count == 0 or slow_count == 0:
                engagement -= 0.2  # Monotonous
            if len(pacing_dead_zones) > 0:
                engagement -= (0.1 * len(pacing_dead_zones))
            if len(info_overload_warnings) > 0:
                engagement -= 0.05 * len(info_overload_warnings)
                
            # Bonus for healthy mix
            if 0.2 <= fast_count / total_p <= 0.4 and 0.1 <= slow_count / total_p <= 0.3:
                engagement += 0.15
                
        engagement_score = min(max(engagement, 0.0), 1.0)
        
        recommendations = []
        if len(pacing_dead_zones) > 0:
            recommendations.append("Break up consecutive slow panels to prevent reader drop-off.")
        if len(info_overload_warnings) > 0:
            recommendations.append("Reduce text density in highlighted panels. Consider showing rather than telling.")
        if fast_count == 0 and total_p > 5:
            recommendations.append("Add quick reaction shots or transitions to increase pacing variety.")
        if engagement_score > 0.8:
            recommendations.append("Good pacing variety!")
            
        return ReadingSimResult(
            scene_id=scene_id,
            scene_name=scene_container.attributes.get("title", scene_id),
            total_reading_seconds=round(total_seconds, 1),
            panels=metrics_list,
            pacing_dead_zones=pacing_dead_zones,
            info_overload_warnings=info_overload_warnings,
            engagement_score=round(engagement_score, 2),
            recommendations=recommendations
        )

    def simulate_chapter_reading(self, chapter: int) -> list[ReadingSimResult]:
        all_scenes = self.container_repo.list_containers(container_type="scene")
        chapter_scenes = [
            s for s in all_scenes 
            if s.attributes.get("chapter") == chapter
        ]
        chapter_scenes.sort(key=lambda s: s.attributes.get("scene_number", 0))
        
        results = []
        for s in chapter_scenes:
            try:
                res = self.simulate_reading(s.id)
                results.append(res)
            except Exception:
                continue
                
        return results
