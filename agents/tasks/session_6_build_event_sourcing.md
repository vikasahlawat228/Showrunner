# Coding Task: CQRS Event Sourcing & Branching (Phase 5 Execution)

**Context:** We are building "Showrunner", an AI co-writer. Because AI generation can violently alter the story state across multiple character and faction objects, we cannot use standard CRUD (overwriting YAML files). We are implementing a Git-style "Undo Tree" using a Directed Acyclic Graph (DAG) event log in SQLite.

**Your Objective: Write the Python Backend Code**
You need to implement the Event Sourcing layer in `src/showrunner_tool/repositories/event_sourcing_repo.py`.

**Requirements:**
1. **The SQLite Schema (in a `setup()` method):**
   - Table `events`: `id` (string UIID), `parent_event_id` (string UUID, nullable), `branch_id` (string), `timestamp`, `event_type` (e.g., `CREATE`, `UPDATE`, `DELETE`), `container_id` (string), `payload_json` (the exact diff/data).
   - Table `branches`: `id` (string, e.g., "main", "alt_timeline"), `head_event_id` (string UUID).
2. **The EventService Class:**
   - `append_event(parent_event_id, branch_id, event_type, container_id, payload) -> event_id`: Safely inserts a new event into the log and updates the branch's `head_event_id`.
   - `branch(source_branch_id: str, new_branch_name: str, checkout_event_id: str) -> None`: Creates a new row in the `branches` table, pointing its head at the designated historical event (allowing the user to branch off the past).
   - `project_state(branch_id: str) -> Dict[str, dict]`: The most complex method. It must find the `head_event_id` of the branch, walk backwards to the root using `parent_event_id` to build the linear chain of events, and then apply those JSON payloads sequentially to construct the current "Projected State" of all containers on that branch. Returns a dictionary mapping `container_id` to its fully resolved payload.

**Output:** Provide the exact, production-ready Python code for `event_sourcing_repo.py`, ensuring it uses proper `sqlite3` context managers and robust error handling.
