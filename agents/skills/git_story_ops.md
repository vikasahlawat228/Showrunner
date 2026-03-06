---
name: git_story_ops
description: Version control workflow for story files — staging, committing, branching
version: "1.0"
triggers: ["git", "commit", "save-story", "version", "branch"]
output_format: markdown
---

# Git Story Ops

**Role:** You manage Git version control specifically for story content in Showrunner projects.

**Available Commands:**
- `showrunner git stage-story` — stage only story-related files (characters, world, fragments, containers)
- `showrunner git commit-message` — generate an AI-powered commit message from the staged diff
- `showrunner git history` — show commit history for story files
- `showrunner git diff` — show current changes to story files

**Common Workflows:**

Save Progress:
1. `showrunner git stage-story`
2. `showrunner git commit-message`
3. Review and confirm the commit

Create Story Branch:
1. `git checkout -b arc/<arc-name>` for new story arcs
2. `git checkout -b alt/<scenario>` for "what if" explorations
3. `git checkout -b draft/v<N>` for revision drafts

**Rules:**
1. Always use `showrunner git stage-story` instead of `git add` to ensure only story files are staged
2. Never commit system databases (.db files) or .chroma/ directories
3. Use descriptive branch names that reflect story content
4. Commit after completing each scene or significant character update
