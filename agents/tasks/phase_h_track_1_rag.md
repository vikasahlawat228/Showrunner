# Phase H, Track 1: Full RAG Integration

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 1 of Phase H**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Integrate Embeddings into ChromaIndexer**
   - Open `src/showrunner_tool/repositories/chroma_indexer.py`.
   - Update `upsert_embedding` to use `litellm.embedding()` (defaulting to `text-embedding-3-small` or `text-embedding-004`) to convert the container's JSON contents into a vector.
   - Implement `semantic_search(query: str, limit: int = 5) -> List[str]`, which embeds the query and returns matching `container_id`s from ChromaDB.

2. **Expose Hybrid Search in KnowledgeGraphService**
   - Open `src/showrunner_tool/services/knowledge_graph_service.py`.
   - Add a `semantic_search` method that proxies to `ChromaIndexer.semantic_search`.
   - Consider a fallback or unified method that combines exact SQLite filtering with semantic similarity.

3. **Enhance Context Engine**
   - Open `src/showrunner_tool/services/context_engine.py`.
   - Update `assemble_context` to leverage `KnowledgeGraphService.semantic_search(query)` when building the prompt. Include semantically relevant lore/character buckets automatically if they fit in the token budget.

4. **Backend Tests**
   - Create `tests/test_rag.py`.
   - Write tests mocking the `litellm.embedding` response to ensure `ChromaIndexer` correctly stores vectors and that `semantic_search` successfully returns the expected container IDs.

Please execute these changes and ensure existing tests remain green.
