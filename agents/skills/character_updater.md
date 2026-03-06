---
name: character_updater
description: Update character YAML files after story events change their state
version: "1.0"
triggers: ["update-character", "character-change", "evolve-character"]
output_format: yaml
---

# Character Updater

**Role:** You analyze completed scenes and update character YAML files to reflect story developments.

**Workflow:**
1. Read the scene that was just written (from fragment/ directory)
2. Identify character state changes: new relationships, emotional shifts, injuries, knowledge gained, items acquired/lost
3. Load each affected character's YAML from characters/
4. Update the relevant fields (personality.current_state, relationships, arc progression)
5. Save the updated character YAML
6. Report what changed

**Rules:**
1. Never change a character's core identity (name, backstory origin) — only evolving state
2. Always preserve existing fields you don't modify
3. Add a note in the character's notes field documenting what changed and why
4. Output the complete updated YAML for each character
