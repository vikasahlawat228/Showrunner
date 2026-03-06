---
description: Start a daily writing session, write, and close cleanly
---

1. Start the session: use the session_manager skill to get the briefing
2. Review the brief and confirm the plan for today
3. Write 1-3 scenes using the write-scene workflow
4. After each scene, run continuity check: `showrunner cascade update <file>`
5. End the session: use the session_manager skill to summarize and set next steps
6. Final commit: `showrunner git stage-story && showrunner git commit-message`
