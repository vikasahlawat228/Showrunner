"""Storyboard service — panel CRUD, reordering, and AI-powered panel generation."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from showrunner_tool.repositories.container_repo import ContainerRepository
from showrunner_tool.repositories.event_sourcing_repo import EventService
from showrunner_tool.schemas.container import GenericContainer
from showrunner_tool.schemas.storyboard import (
    Panel,
    PanelType,
    CameraAngle,
)

logger = logging.getLogger(__name__)


class StoryboardService:
    """Manages storyboard panels — CRUD, ordering, and LLM generation.

    Persists panels via ContainerRepository as GenericContainer with
    container_type="panel" and emits events to EventService on mutations.
    """

    def __init__(
        self,
        container_repo: ContainerRepository,
        event_service: EventService,
    ):
        self.container_repo = container_repo
        self.event_service = event_service

    # ------------------------------------------------------------------
    # Panel <-> GenericContainer conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _panel_to_container(panel: Panel) -> GenericContainer:
        """Convert a Panel domain object to a GenericContainer for storage."""
        return GenericContainer(
            id=panel.id,
            container_type="panel",
            name=f"Panel {panel.panel_number} ({panel.scene_id[:8]})",
            attributes={
                "scene_id": panel.scene_id,
                "panel_number": panel.panel_number,
                "panel_type": panel.panel_type.value,
                "camera_angle": panel.camera_angle.value,
                "description": panel.description,
                "dialogue": panel.dialogue,
                "action_notes": panel.action_notes,
                "sound_effects": panel.sound_effects,
                "duration_seconds": panel.duration_seconds,
                "image_ref": panel.image_ref,
                "image_prompt": panel.image_prompt,
                "characters": panel.characters,
            },
            relationships=[],
            created_at=panel.created_at,
            updated_at=panel.updated_at,
        )

    @staticmethod
    def _container_to_panel(container: GenericContainer) -> Panel:
        """Reconstruct a Panel domain object from a GenericContainer."""
        attrs = container.attributes
        return Panel(
            id=container.id,
            scene_id=attrs.get("scene_id", ""),
            panel_number=attrs.get("panel_number", 0),
            panel_type=PanelType(attrs.get("panel_type", "action")),
            camera_angle=CameraAngle(attrs.get("camera_angle", "medium")),
            description=attrs.get("description", ""),
            dialogue=attrs.get("dialogue", ""),
            action_notes=attrs.get("action_notes", ""),
            sound_effects=attrs.get("sound_effects", ""),
            duration_seconds=attrs.get("duration_seconds", 3.0),
            image_ref=attrs.get("image_ref", ""),
            image_prompt=attrs.get("image_prompt", ""),
            characters=attrs.get("characters", []),
            created_at=container.created_at,
            updated_at=container.updated_at,
        )

    def _load_all_panels(self) -> List[Panel]:
        """Load all panels from the container repository."""
        containers = self.container_repo.list_by_type("panel")
        panels = []
        for c in containers:
            try:
                panels.append(self._container_to_panel(c))
            except Exception as e:
                logger.warning("Failed to load panel from container %s: %s", c.id, e)
        return panels

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_panels_for_scene(self, scene_id: str) -> List[Panel]:
        """Get all panels for a scene, ordered by panel_number."""
        all_panels = self._load_all_panels()
        panels = [p for p in all_panels if p.scene_id == scene_id]
        panels.sort(key=lambda p: p.panel_number)
        return panels

    def get_panel(self, panel_id: str) -> Optional[Panel]:
        """Get a single panel by ID."""
        all_panels = self._load_all_panels()
        for p in all_panels:
            if p.id == panel_id:
                return p
        return None

    def save_panel(self, panel: Panel) -> Panel:
        """Save or update a panel."""
        # Check if this is an update (panel already exists)
        existing = self.get_panel(panel.id)
        event_type = "UPDATE" if existing else "CREATE"

        container = self._panel_to_container(panel)
        self.container_repo.save_container(container)

        # Emit event to EventService
        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type=event_type,
                container_id=panel.id,
                payload=container.attributes,
            )
        except Exception as e:
            logger.warning("Failed to emit %s event for panel %s: %s", event_type, panel.id, e)

        return panel

    def delete_panel(self, panel_id: str) -> bool:
        """Delete a panel. Returns True if found."""
        panel = self.get_panel(panel_id)
        if not panel:
            return False

        # Delete the YAML file from the panel subdirectory
        container_name = f"Panel {panel.panel_number} ({panel.scene_id[:8]})"
        file_stem = container_name.lower().replace(" ", "_")
        panel_dir = self.container_repo.base_dir / "panel"
        if panel_dir.exists():
            # Try to find and delete the file
            original_base = self.container_repo.base_dir
            self.container_repo.base_dir = panel_dir
            try:
                self.container_repo.delete(file_stem)
            finally:
                self.container_repo.base_dir = original_base

        # Emit DELETE event
        try:
            self.event_service.append_event(
                parent_event_id=None,
                branch_id="main",
                event_type="DELETE",
                container_id=panel_id,
                payload={"deleted": True},
            )
        except Exception as e:
            logger.warning("Failed to emit DELETE event for panel %s: %s", panel_id, e)

        return True

    def reorder_panels(self, scene_id: str, panel_ids: List[str]) -> List[Panel]:
        """Reorder panels within a scene by updating panel_number."""
        all_panels = {p.id: p for p in self._load_all_panels()}
        for idx, pid in enumerate(panel_ids):
            panel = all_panels.get(pid)
            if panel and panel.scene_id == scene_id:
                panel.panel_number = idx
                self.save_panel(panel)
        return self.get_panels_for_scene(scene_id)

    # ------------------------------------------------------------------
    # AI Panel Generation
    # ------------------------------------------------------------------

    async def generate_panels_for_scene(
        self,
        scene_id: str,
        scene_text: str,
        scene_name: str,
        panel_count: int = 6,
        style: str = "manga",
    ) -> List[Panel]:
        """Use LLM to break a scene into storyboard panels.

        Generates panel descriptions, dialogue, camera angles, and action notes.
        """
        prompt = f"""You are a professional storyboard artist breaking down a scene into {panel_count} individual panels.

Scene Name: {scene_name}
Scene Text:
{scene_text}

Visual Style: {style}

For each panel, provide:
1. panel_type: one of "dialogue", "action", "establishing", "closeup", "transition", "montage"
2. camera_angle: one of "wide", "medium", "close", "extreme_close", "over_shoulder", "birds_eye", "low_angle", "dutch", "pov"
3. description: detailed visual description of what we see (2-3 sentences)
4. dialogue: character dialogue (empty string if none)
5. action_notes: stage directions and movement (1 sentence)
6. duration_seconds: estimated shot duration (2.0-8.0)

Return ONLY a JSON array of {panel_count} objects with these fields. No markdown, no explanation."""

        try:
            from litellm import completion

            api_key = os.getenv("GEMINI_API_KEY")
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                temperature=0.7,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]

            panel_data = json.loads(raw)

        except Exception as e:
            logger.error("AI panel generation failed: %s", e)
            # Fallback: auto-generate basic panels
            panel_data = self._generate_fallback_panels(panel_count)

        # Convert to Panel objects
        panels: List[Panel] = []
        for idx, pd in enumerate(panel_data[:panel_count]):
            panel = Panel(
                scene_id=scene_id,
                panel_number=idx,
                panel_type=self._safe_panel_type(pd.get("panel_type", "action")),
                camera_angle=self._safe_camera_angle(pd.get("camera_angle", "medium")),
                description=pd.get("description", f"Panel {idx + 1}"),
                dialogue=pd.get("dialogue", ""),
                action_notes=pd.get("action_notes", ""),
                duration_seconds=min(max(float(pd.get("duration_seconds", 3.0)), 1.0), 15.0),
            )
            self.save_panel(panel)
            panels.append(panel)

        return panels

    # ------------------------------------------------------------------
    # Image Prompt Generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_image_prompt(panel: Panel, style: str = "manga") -> str:
        """Compose an image generation prompt from panel metadata."""
        parts = [
            f"{style} style illustration.",
            f"Camera: {panel.camera_angle.value} shot.",
            f"Scene: {panel.description}",
        ]
        if panel.action_notes:
            parts.append(f"Action: {panel.action_notes}")
        if panel.dialogue:
            parts.append(f"(Character speaking: \"{panel.dialogue[:80]}\")")

        return " ".join(parts)

    async def suggest_layout(self, scene_id: str, scene_text: str, scene_name: str) -> dict:
        """
        Analyze the narrative beat type of a scene and suggest panel layout.
        """
        prompt = f"""You are an expert manga/comic storyboard director analyzing a scene to determine its optimal panel layout.

Scene Name: {scene_name}
Scene Text:
{scene_text}

First, determine the primary narrative beat type from these options:
- action: diagonal panel cuts, motion lines, dynamic camera angles (low_angle, dutch), more panels (6-8)
- dialogue: small panels, close-ups, over_shoulder shots, medium count (4-6)
- dramatic_reveal: splash panel (full-width) for the key moment, few supporting panels (3-4)
- transition: horizontal widescreen panels, establishing shots, few panels (2-3)
- montage: grid of equal-sized panels, varied subjects, many panels (6-9)
- emotional: close-ups, extreme close-ups, medium panels with white space (3-5)

Then, suggest a layout for the whole page/spread.

Return ONLY a JSON object with this exact structure:
{{
    "beat_type": "string (one of the beat types above)",
    "suggested_panel_count": int,
    "layout": [
        {{
            "panel_number": int (0-indexed),
            "panel_type": "string (action, dialogue, establishing, closeup, transition, montage)",
            "camera_angle": "string (wide, medium, close, extreme_close, over_shoulder, birds_eye, low_angle, dutch, pov)",
            "size_hint": "string (large, medium, small, splash)",
            "description_hint": "string (brief visual suggestion)",
            "composition_notes": "string (e.g., Rule of thirds)"
        }}
    ],
    "reasoning": "string (explanation of why this layout fits the scene)",
    "pacing_notes": "string (notes on reading speed, gutters, page flow)"
}}
No markdown formatting, just the raw JSON object."""

        from litellm import completion
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                temperature=0.7,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]

            layout_data = json.loads(raw)
            return layout_data

        except Exception as e:
            logger.error("AI layout suggestion failed: %s", e)
            return {
                "beat_type": "action",
                "suggested_panel_count": 4,
                "layout": [
                    {"panel_number": 0, "panel_type": "establishing", "camera_angle": "wide", "size_hint": "large", "description_hint": "Establishing shot", "composition_notes": ""},
                    {"panel_number": 1, "panel_type": "action", "camera_angle": "medium", "size_hint": "medium", "description_hint": "Action beat 1", "composition_notes": ""},
                    {"panel_number": 2, "panel_type": "action", "camera_angle": "close", "size_hint": "medium", "description_hint": "Action beat 2", "composition_notes": ""},
                    {"panel_number": 3, "panel_type": "action", "camera_angle": "low_angle", "size_hint": "large", "description_hint": "Action climax", "composition_notes": ""},
                ],
                "reasoning": "Fallback layout applied due to generation error.",
                "pacing_notes": "Standard pacing."
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def generate_live_sketch(self, recent_prose: str, scene_id: Optional[str] = None) -> Panel:
        """Quickly generate a single ephemeral live sketch panel based on recent prose."""
        prompt = f"""You are a live storyboard artist visualizing a writer's latest prose in real time.
Read the recent prose and describe one single powerful comic panel that illustrates the current beat.

Recent Prose:
{recent_prose}

Return ONLY a JSON object with this exact structure for ONE panel:
{{
    "panel_type": "string (action, dialogue, establishing, closeup, transition, montage)",
    "camera_angle": "string (wide, medium, close, extreme_close, over_shoulder, birds_eye, low_angle, dutch, pov)",
    "description": "string (detailed visual description of the shot, 1-2 sentences)",
    "action_notes": "string (brief action/stage note)"
}}
No markdown formatting, just the raw JSON object."""

        try:
            from litellm import completion
            api_key = os.getenv("GEMINI_API_KEY")
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key,
                temperature=0.7,
                max_tokens=250,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]

            pd = json.loads(raw)
            
            # Create a non-persistent Panel object (ephemeral)
            return Panel(
                scene_id=scene_id or "live",
                panel_number=-1, # Indicates it's an ephemeral live sketch
                panel_type=self._safe_panel_type(pd.get("panel_type", "action")),
                camera_angle=self._safe_camera_angle(pd.get("camera_angle", "medium")),
                description=pd.get("description", "A live storyboard sketch of the action."),
                dialogue="",
                action_notes=pd.get("action_notes", ""),
                duration_seconds=3.0,
            )

        except Exception as e:
            logger.error("Live sketch generation failed: %s", e)
            return Panel(
                scene_id=scene_id or "live",
                panel_number=-1,
                panel_type=PanelType.ACTION,
                camera_angle=CameraAngle.MEDIUM,
                description="Live sketch failed. Fallback action shot.",
            )

    @staticmethod
    def _safe_panel_type(value: str) -> PanelType:
        try:
            return PanelType(value.lower())
        except ValueError:
            return PanelType.ACTION

    @staticmethod
    def _safe_camera_angle(value: str) -> CameraAngle:
        try:
            return CameraAngle(value.lower())
        except ValueError:
            return CameraAngle.MEDIUM

    @staticmethod
    def _generate_fallback_panels(count: int) -> List[Dict[str, Any]]:
        """Generate basic fallback panels when LLM fails."""
        templates = [
            {"panel_type": "establishing", "camera_angle": "wide", "description": "Establishing shot of the scene location.", "dialogue": "", "action_notes": "Camera pans across the environment.", "duration_seconds": 4.0},
            {"panel_type": "dialogue", "camera_angle": "medium", "description": "Characters face each other.", "dialogue": "[Dialogue placeholder]", "action_notes": "Characters in conversation.", "duration_seconds": 3.0},
            {"panel_type": "action", "camera_angle": "close", "description": "Close-up of character reaction.", "dialogue": "", "action_notes": "Character reacts to the situation.", "duration_seconds": 2.0},
            {"panel_type": "action", "camera_angle": "medium", "description": "Key action beat.", "dialogue": "", "action_notes": "Main action occurs.", "duration_seconds": 3.0},
            {"panel_type": "closeup", "camera_angle": "extreme_close", "description": "Dramatic close-up on important detail.", "dialogue": "", "action_notes": "Focus on critical moment.", "duration_seconds": 2.0},
            {"panel_type": "transition", "camera_angle": "wide", "description": "Scene transition.", "dialogue": "", "action_notes": "Camera pulls back as scene ends.", "duration_seconds": 3.0},
        ]
        result = []
        for i in range(count):
            template = templates[i % len(templates)].copy()
            result.append(template)
        return result
