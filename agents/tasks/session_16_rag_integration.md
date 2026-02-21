# Prompt: Track 4 — Embedded RAG & Semantic Retrieval

**Goal**: Upgrade the `KnowledgeGraphService` to include a simple vector store for Retrieval-Augmented Generation (RAG).

**Context**:
Currently, the `KnowledgeGraphService` indexes containers into SQLite using JSON1 for relational queries. However, our new features (Zen Mode Slash Commands, Pipeline Searches, Storyboard Panel Generation) lack semantic context. To achieve 2025 best practices for context engineering, we need to embed the container `attributes` into a vector store.

**Required Actions (Backend Only)**:

1. **Enhance `SQLiteIndexer` (or create `chroma_indexer.py`)**:
   - For a zero-dependency setup, leverage SQLite `vss` or simply use a lightweight, in-memory library like `ChromaDB` (or the local SQLite equivalent).
   - In the `sync_all()` method of `KnowledgeGraphService`, every time a container is parsed via the `ContainerRepository`, calculate a dense embedding of its JSON `attributes` and save it to the vector store index.
   - Use `litellm`'s embedding endpoint (via Gemini or an equivalent cheap embedding model) to generate the vector.

2. **Add Semantic Search API**:
   - Add a `semantic_search(query: str, limit: int = 5) -> List[GenericContainer]` method to `KnowledgeGraphService`.
   - The method computes the embedding of the user `query` and performs a cosine-similarity search against the container index.

3. **Update Router**:
   - Expose the method on `routers/graph.py` as `GET /api/v1/graph/search?q={query}`.

**Output Specification**:
Provide the Python code for:
1. `src/antigravity_tool/services/knowledge_graph_service.py` (with the new RAG embedding sync and search methods)
2. `src/antigravity_tool/server/routers/graph.py` (with the new search endpoint)

*Note: Assume the user has `litellm` installed and `GEMINI_API_KEY` set in their environment for generating embeddings. Use `ChromaDB` if it keeps the implementation cleanest.*
