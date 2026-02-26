# Prompt: Track 2 — The Context Engine

**Goal**: Build a centralized `ContextEngine` service that manages context assembly, token budgeting, and intelligent summarization for all LLM calls.

**Context**:
Right now, LLM prompts inside `storyboard_service.py` and `pipeline_service.py` (and the future Zen Mode expansions) blindly inject gathered text without bounds checking. With the 2025 best standard of "Tiered Context" and token limits, we need a service dedicated to preparing context before hitting LiteLLM.

**Required Actions (Backend Only)**:

1. **Create `services/context_engine.py`**:
   - Design a `ContextEngine` class.
   - Implement `assemble_context(query: str, container_ids: list[str], max_tokens: int = 4000) -> str`.
   - It should retrieve raw text from the `KnowledgeGraphService` via the container IDs.
   - Implement a basic truncation/summarization strategy if the gathered text exceeds `max_tokens`.
   - *Stretch Goal:* Implement hierarchical summarization if an entity exceeds 2000 tokens.

2. **Integration**:
   - Update `pipeline_service.py` (specifically the `GATHER_BUCKETS` step handler) to use the new `ContextEngine` instead of raw string concatenation.
   - Update `director_service.py` to utilize `ContextEngine` when looking up state.

**Output Specification**:
Provide the Python code for:
1. `src/showrunner_tool/services/context_engine.py`
2. The modified methods in `src/showrunner_tool/services/pipeline_service.py` and `director_service.py` integrating the new engine.

*Note: You can estimate tokens using roughly 4 chars per token. Use LiteLLM (which is already installed) if you need to call a summarization model during the engine's compilation process.*
