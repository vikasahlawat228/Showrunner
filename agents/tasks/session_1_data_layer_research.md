# Task: Data Layer & Meta-Agent Skill Definition

**Context:** We are building "Showrunner", a node-based, transparent AI co-writer (like n8n for storytelling). Instead of rigid tables for "Characters" and "Scenes," we are shifting to a "Generic Container" EAV (Entity-Attribute-Value) model. Users can define Custom Schemas (e.g., "Spell" or "Faction"). The backend uses Local YAML as the source of truth, but we need an in-memory SQLite (or DuckDB) layer to index these YAMLs into a relational Knowledge Graph for fast UI querying.

**Your Objective (Outsourced Research & Skill Prompt Definition):**
1. **Research & Architectural Analysis:** Analyze the best way to implement a Generic Container EAV model backed by YAML but indexed in SQLite using Python (FastAPI/Pydantic/SQLAlchemy). Specifically, how do we handle dynamic schemas (`pydantic.create_model`) so the API can validate user-defined container types at runtime?
2. **Meta-Agent Skill Prompt Creation:** Based on your research, write a comprehensive System Prompt (Skill) for a "Schema Architect Meta-Agent". This agent’s job is to read user requests ("I want to track magical artifacts") and output valid Pydantic schemas/JSON representations of new Container Types.
3. **Output:** Provide your architectural recommendation and the exact Markdown text for the `schema_architect.md` skill file.
