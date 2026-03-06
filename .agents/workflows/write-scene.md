---
description: Write a complete scene from outline to committed YAML
---
// turbo-all

1. Load the scene outline: check containers/ for the scene's structural bucket
2. Load character sheets: read all characters/*.yaml for characters in the scene
3. Load world context: read world/settings.yaml
4. Load previous scenes: read the last 2-3 fragments from fragment/
5. Use the writing_agent skill to draft the scene prose
6. Save the output to fragment/<scene-slug>.yaml
7. Run cascade update: `showrunner cascade update fragment/<scene-slug>.yaml`
8. Stage and commit: `showrunner git stage-story && showrunner git commit-message`
