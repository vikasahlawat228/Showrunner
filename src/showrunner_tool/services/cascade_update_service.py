"""Cascade Update Service — auto-sync related entities when a file changes.

When a scene/fragment changes, this service detects which characters, locations,
and other entities were affected and updates their YAML files accordingly.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from showrunner_tool.schemas.container import GenericContainer

logger = logging.getLogger(__name__)


class CascadeUpdateService:
    """Analyze scene changes and update related entity YAML files.

    When a scene is written/updated, detect:
    - Which characters appear in the scene
    - How their emotional state/location might have changed
    - Which locations are mentioned
    - Which relationships were affected

    Then update the relevant character/location YAML files.
    """

    def __init__(
        self,
        kg_service,
        container_repo,
        agent_dispatcher,
    ):
        """Initialize with required services.

        Args:
            kg_service: KnowledgeGraphService for querying entities
            container_repo: ContainerRepository for reading/writing YAML
            agent_dispatcher: AgentDispatcher for LLM analysis
        """
        self.kg_service = kg_service
        self.container_repo = container_repo
        self.agent_dispatcher = agent_dispatcher

    async def analyze_and_update(
        self,
        changed_file_path: Path,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Analyze a changed file and cascade updates to related entities.

        Args:
            changed_file_path: Path to the changed YAML file (e.g., fragment/ch4-sc3.yaml)
            dry_run: If True, don't write changes, just report what would change

        Returns:
            Dict with:
                status: "success" or "error"
                changed_files: List of files that were updated
                updates: Dict mapping entity_id → list of changed attributes
                errors: Any errors encountered
        """
        result = {
            "status": "success",
            "changed_files": [],
            "updates": {},
            "errors": [],
        }

        try:
            # 1. Read the changed file
            logger.info(f"Analyzing changes in {changed_file_path}")

            file_relative = changed_file_path.relative_to(self.container_repo.base_dir)
            
            # Using private _load_file_optional or find by ID
            # If the path is relative to base_dir, we can load it directly
            try:
                # We can't access read(), but base class has _load_file_optional
                container = self.container_repo._load_file_optional(self.container_repo.base_dir / file_relative)
            except AttributeError:
                # Fallback implementation
                import yaml
                from showrunner_tool.schemas.container import GenericContainer
                with open(self.container_repo.base_dir / file_relative, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    container = GenericContainer(**data)

            if not container:
                result["status"] = "error"
                result["errors"].append(f"Could not read {changed_file_path}")
                return result

            # 2. Only process fragments and scenes
            if container.container_type not in ("fragment", "scene"):
                logger.info(f"Skipping {container.container_type} (not a fragment/scene)")
                return result

            # 3. Extract entities from the scene
            entities_and_changes = await self._extract_entity_changes(container)
            if not entities_and_changes:
                logger.info("No entity changes detected in scene")
                return result

            # 4. Update each entity
            for entity_id, changes in entities_and_changes.items():
                try:
                    file_path = await self._update_entity(entity_id, changes, dry_run)
                    if file_path:
                        result["changed_files"].append(str(file_path))
                        result["updates"][entity_id] = changes
                except Exception as e:
                    logger.error(f"Error updating entity {entity_id}: {e}")
                    result["errors"].append(str(e))

            if result["changed_files"]:
                logger.info(f"Cascade updates complete: {len(result['changed_files'])} files changed")
            else:
                logger.info("No files needed updating")

            return result

        except Exception as e:
            logger.error(f"Cascade update failed: {e}", exc_info=True)
            result["status"] = "error"
            result["errors"].append(str(e))
            return result

    async def _extract_entity_changes(
        self,
        scene_container: GenericContainer,
    ) -> Dict[str, Dict[str, Any]]:
        """Use LLM to extract entity changes from a scene.

        Returns:
            Dict mapping entity_id → {old_value: new_value} changes
        """
        attrs = scene_container.attributes or {}
        prose = attrs.get("prose", "")
        characters_present = attrs.get("characters_present", [])
        plot_events = attrs.get("plot_events", [])
        location = attrs.get("location", "")

        if not prose:
            return {}

        # Build context for the agent
        scene_context = f"""
Scene: {scene_container.name}
Location: {location}
Characters: {", ".join(characters_present)}
Plot Events: {plot_events}

Prose:
{prose[:1000]}  # First 1000 chars to avoid context explosion
"""

        try:
            # Use agent_dispatcher to analyze scene impacts
            analysis_prompt = f"""You are an analysis agent. Read this scene and identify:

1. For each character present, did their:
   - emotional_state change? (e.g., "Determined" → "Conflicted")
   - location change? (where are they now?)
   - relationships change? (did they learn something about someone?)

2. For each location mentioned, did its:
   - description change? (anything new discovered?)
   - significance change? (is it more important now?)

Return ONLY valid JSON with NO markdown formatting:
{{
  "characters": {{
    "character_name_1": {{
      "old_emotional_state": "...",
      "new_emotional_state": "...",
      "old_location": "...",
      "new_location": "...",
      "relationship_changes": {{"other_name": "old_type → new_type"}}
    }}
  }},
  "locations": {{
    "location_name": {{
      "discoveries": ["what was found"],
      "significance_change": "..."
    }}
  }}
}}

SCENE:
{scene_context}
"""

            result_text = await self.agent_dispatcher.execute(
                analysis_prompt,
                skill_hint="continuity_analyst"
            )

            # Parse JSON from result
            try:
                # Try to extract JSON from result
                if isinstance(result_text, dict):
                    analysis = result_text
                else:
                    # Try to find JSON in the text
                    import re
                    json_match = re.search(r'\{.*\}', str(result_text), re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group(0))
                    else:
                        logger.warning("Could not parse JSON from analysis")
                        return {}
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from analysis: {result_text[:200]}")
                return {}

            # Convert character/location names to IDs
            entity_changes = {}

            # Process character changes
            for char_name, changes in analysis.get("characters", {}).items():
                # Find character by name in KG
                char_containers = self.kg_service.find_containers(
                    container_type="character",
                    filters={"name": char_name}
                )
                if char_containers:
                    char_id = char_containers[0]["id"]
                    entity_changes[char_id] = changes
                else:
                    logger.warning(f"Character '{char_name}' not found in KG")

            # Process location changes
            for loc_name, changes in analysis.get("locations", {}).items():
                loc_containers = self.kg_service.find_containers(
                    container_type="location",
                    filters={"name": loc_name}
                )
                if loc_containers:
                    loc_id = loc_containers[0]["id"]
                    entity_changes[loc_id] = changes
                else:
                    logger.warning(f"Location '{loc_name}' not found in KG")

            return entity_changes

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}", exc_info=True)
            return {}

    async def _update_entity(
        self,
        entity_id: str,
        changes: Dict[str, Any],
        dry_run: bool = False,
    ) -> Optional[Path]:
        """Update a single entity (character/location) with detected changes.

        Args:
            entity_id: The entity's ID
            changes: Dict of {attribute: {"old_value": ..., "new_value": ...}}
            dry_run: Don't write if True

        Returns:
            Path to updated file, or None if no update needed
        """
        try:
            # Find the entity in KG
            entity_containers = self.kg_service.find_containers(
                filters={"id": entity_id}
            )
            if not entity_containers:
                logger.warning(f"Entity {entity_id} not found in KG")
                return None

            entity_data = entity_containers[0]
            container_type = entity_data.get("container_type")

            # Reconstruct the container to apply updates
            container = GenericContainer(
                id=entity_id,
                name=entity_data.get("name"),
                container_type=container_type,
                attributes=entity_data.get("attributes", {}),
            )

            # Apply changes to attributes
            old_attributes = dict(container.attributes or {})
            new_attributes = dict(old_attributes)

            # Handle character updates
            if container_type == "character":
                for key, value in changes.items():
                    if key == "new_emotional_state" and value:
                        new_attributes["emotional_state"] = value
                    elif key == "new_location" and value:
                        new_attributes["location"] = value
                    elif key == "relationship_changes" and value:
                        # Merge relationship changes
                        rels = new_attributes.get("relationships", {})
                        for other_name, rel_change in value.items():
                            if "→" in rel_change:
                                new_rel = rel_change.split("→")[-1].strip()
                                rels[other_name] = new_rel
                        new_attributes["relationships"] = rels

            # Handle location updates
            elif container_type == "location":
                if "discoveries" in changes and changes["discoveries"]:
                    new_attributes["recent_discoveries"] = changes["discoveries"]
                if "significance_change" in changes:
                    new_attributes["significance"] = changes["significance_change"]

            # Check if anything actually changed
            if old_attributes == new_attributes:
                logger.info(f"No actual changes for {entity_id}")
                return None

            # Update container and write
            container.attributes = new_attributes
            container.updated_at = datetime.utcnow()

            if not dry_run:
                # Write back to repo
                self.container_repo.write(container)
                # Update KG
                self.kg_service.index_container(container)
                logger.info(f"Updated {container.name} ({container_type})")

                # Log the changes
                for key in old_attributes:
                    if old_attributes[key] != new_attributes[key]:
                        logger.info(
                            f"  - {key}: {old_attributes[key]} → {new_attributes[key]}"
                        )

            # Return the path to the updated file
            file_path = self.container_repo.get_path_for_id(entity_id)
            return file_path if file_path else None

        except Exception as e:
            logger.error(f"Error updating entity {entity_id}: {e}", exc_info=True)
            raise
