"""ChromaDB vector store indexer for semantic search (RAG).

Wraps a ChromaDB PersistentClient collection to embed and retrieve
container attributes by cosine similarity.

Phase H upgrade: adds LiteLLM-based embeddings via ``upsert_embedding``
and ``semantic_search`` for API-quality vectors (``text-embedding-004``).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# Default embedding model used by the LiteLLM-powered methods.
DEFAULT_EMBEDDING_MODEL = "gemini/text-embedding-004"


# ------------------------------------------------------------------
# LiteLLM embedding helper
# ------------------------------------------------------------------

def _litellm_embed(texts: List[str], model: str = DEFAULT_EMBEDDING_MODEL) -> List[List[float]]:
    """Call ``litellm.embedding()`` and return a list of float vectors.

    Raises on failure so callers can decide on fallback behaviour.
    """
    from litellm import embedding as litellm_embedding

    response = litellm_embedding(model=model, input=texts)
    # response.data is a list of EmbeddingObject with an `embedding` field
    return [item["embedding"] for item in response.data]


class ChromaIndexer:
    """Manages a ChromaDB collection of container embeddings.

    Uses ChromaDB's built-in default embedding function
    (all-MiniLM-L6-v2 sentence-transformer) for the legacy ``upsert``/
    ``search`` methods, and LiteLLM-powered API embeddings for the new
    ``upsert_embedding``/``semantic_search`` methods.
    """

    COLLECTION_NAME = "containers"

    def __init__(
        self,
        persist_dir: str | Path,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        """Initialise ChromaDB with persistence in *persist_dir*."""
        import chromadb

        self.persist_dir = str(persist_dir)
        self.embedding_model = embedding_model
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaIndexer ready  dir=%s  docs=%d", self.persist_dir, self._collection.count())

    # ------------------------------------------------------------------
    # Legacy write operations (ChromaDB built-in embeddings)
    # ------------------------------------------------------------------

    def upsert(
        self,
        container_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add or update a container document in the vector store.

        *text* should be a human-readable representation of the container
        (typically ``name + " " + json.dumps(attributes)``).

        Uses ChromaDB's built-in embedding function.
        """
        self._collection.upsert(
            ids=[container_id],
            documents=[text],
            metadatas=[metadata] if metadata else None,
        )

    def delete(self, container_id: str) -> None:
        """Remove a container from the vector index."""
        try:
            self._collection.delete(ids=[container_id])
        except Exception:
            # Silently ignore if the ID doesn't exist
            pass

    # ------------------------------------------------------------------
    # Legacy read operations (ChromaDB built-in embeddings)
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Semantic search — returns the closest *n_results* documents.

        Each result dict contains ``id``, ``distance``, and ``metadata``.

        Uses ChromaDB's built-in embedding function.
        """
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
        )

        hits: List[Dict[str, Any]] = []
        if results and results["ids"]:
            for idx, doc_id in enumerate(results["ids"][0]):
                hit: Dict[str, Any] = {"id": doc_id}
                if results.get("distances"):
                    hit["distance"] = results["distances"][0][idx]
                if results.get("metadatas"):
                    hit["metadata"] = results["metadatas"][0][idx]
                if results.get("documents"):
                    hit["document"] = results["documents"][0][idx]
                hits.append(hit)
        return hits

    # ------------------------------------------------------------------
    # Phase H: LiteLLM-powered embedding methods
    # ------------------------------------------------------------------

    def upsert_embedding(
        self,
        container_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Embed *text* via LiteLLM and upsert the vector into ChromaDB.

        Falls back to ``upsert()`` (built-in embeddings) when the API
        call fails — ensuring writes never silently drop data.
        """
        try:
            vectors = _litellm_embed([text], model=self.embedding_model)
            self._collection.upsert(
                ids=[container_id],
                embeddings=vectors,
                documents=[text],
                metadatas=[metadata] if metadata else None,
            )
        except Exception as exc:
            logger.warning(
                "LiteLLM embedding failed for %s, falling back to built-in: %s",
                container_id, exc,
            )
            # Graceful fallback — use ChromaDB's default embedder
            self.upsert(container_id, text, metadata)

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """Embed *query* via LiteLLM and return the closest container IDs.

        Returns a list of ``container_id`` strings ordered by cosine
        similarity (closest first).  Falls back to the legacy
        ``search()`` pathway when the embedding API is unavailable.
        """
        try:
            query_vector = _litellm_embed([query], model=self.embedding_model)[0]
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
            )
        except Exception as exc:
            logger.warning(
                "LiteLLM query embedding failed, falling back to built-in search: %s",
                exc,
            )
            hits = self.search(query, n_results=limit)
            return [h["id"] for h in hits]

        if results and results["ids"]:
            return results["ids"][0]
        return []

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """Number of documents currently indexed."""
        return self._collection.count()
