---
name: project_initializer
description: Bootstrap a new Showrunner story project from concept to first scene
version: "1.0"
triggers: ["init", "new-project", "bootstrap", "setup"]
output_format: yaml
---

# Project Initializer

**Role:** You bootstrap a complete Showrunner story project from a concept pitch.

**Workflow:**
1. Ask for: story concept, genre, target medium (manga/novel/webtoon)
2. Run `showrunner init "<project_name>" --genre <genre>`
3. Build the world: create world/settings.yaml with locations, rules, factions
4. Create characters: create characters/<name>.yaml for 3-5 main characters
5. Outline the story: create the story structure (season/arc/act/chapter/scene hierarchy)
6. Write the first scene as a fragment
7. Initialize git: `git init && showrunner git stage-story && git commit -m "feat: initial story setup"`
8. Generate a briefing: `showrunner brief update`
