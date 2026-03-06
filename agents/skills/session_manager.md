---
name: session_manager
description: Manage writing sessions — start with briefing, end with summary and next steps
version: "1.0"
triggers: ["session", "start-session", "end-session", "brief"]
output_format: markdown
---

# Session Manager

**Role:** You manage the start and end of writing sessions for the Showrunner creative studio.

**Starting a Session:**
1. Read CLAUDE.md for project context
2. Run `showrunner brief show` to get the current project state
3. Load the last session log from .showrunner/sessions/
4. Summarize: where we left off, what's next, any open decisions
5. Present a brief to the writer with suggested next actions

**Ending a Session:**
1. Summarize what was accomplished (files created/modified, words written, scenes completed)
2. List any open decisions or unresolved plot threads
3. Suggest next steps for the following session
4. Run `showrunner session end "<summary>" --next "<next steps>"`
5. Run `showrunner git stage-story && showrunner git commit-message`
