"""Schema migration script for Showrunner.

This script parses a legacy Showrunner project and converts the
hardcoded YAML files (Characters, Scenes, etc.) into the new
Generic Container format, saving them to a new output directory.
"""

import argparse
from pathlib import Path

from showrunner_tool.core.project import Project
from showrunner_tool.schemas.container import GenericContainer


def migrate_characters(project: Project, output_dir: Path) -> None:
    """Migrate characters to the new format."""
    print("Migrating Characters...")
    for char in project.load_all_characters(filter_secrets=False):
        # Convert the legacy character to a GenericContainer
        container = GenericContainer(
            container_type="character",
            name=char.name,
            attributes={
                "role": char.personality.tags[0] if char.personality.tags else "Unknown",
                "traits": char.personality.traits,
                "bio": "\n".join(char.arc.notes) if char.arc.notes else "No bio provided.",
                "dna": char.dna.model_dump()
            }
        )
        
        # Preserve original creation times if possible
        container.created_at = char.created_at
        container.updated_at = char.updated_at
        
        # Save to the new directory structure
        char_dir = output_dir / "character"
        char_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{char.name.lower().replace(' ', '_')}.yaml"
        
        from showrunner_tool.utils.io import write_yaml
        write_yaml(char_dir / file_name, container.model_dump(mode="json"))
        print(f"  Migrated: {char.name}")


def migrate_world(project: Project, output_dir: Path) -> None:
    """Migrate world settings. For simplicity we create one generic world container."""
    print("Migrating World...")
    settings = project.load_world_settings()
    if not settings:
        return
        
    container = GenericContainer(
        container_type="location",
        name=settings.name,
        attributes={
            "description": settings.description,
            "region": "World Map",
            "points_of_interest": settings.key_locations
        }
    )
    
    loc_dir = output_dir / "location"
    loc_dir.mkdir(parents=True, exist_ok=True)
    
    from showrunner_tool.utils.io import write_yaml
    write_yaml(loc_dir / f"{settings.name.lower().replace(' ', '_')}.yaml", container.model_dump(mode="json"))
    print(f"  Migrated: {settings.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy Showrunner project to Showrunner Containers.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Path to project directory.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "containers", help="Path to output directory.")
    args = parser.parse_args()

    project = Project(args.project_dir)
    print(f"Found project: {project.name}")
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    migrate_characters(project, args.output_dir)
    migrate_world(project, args.output_dir)
    # Note: Scenes are stored in chapters, skipping for this demo as they require 
    # more complex nested directory parsing, but the logic is identical.
    
    print(f"Migration complete! Files saved to {args.output_dir}")

if __name__ == "__main__":
    main()
