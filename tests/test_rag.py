"""Phase H Track 1 -- RAG Integration tests.

Tests cover:
  1. ChromaIndexer.upsert_embedding with mocked litellm.embedding
  2. ChromaIndexer.semantic_search with mocked litellm.embedding
  3. KnowledgeGraphService.hybrid_search
  4. ContextEngine semantic boost in assemble_context
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from antigravity_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.services.context_engine import ContextEngine
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

# Synthetic 3-dimensional embeddings for testing.
FAKE_VECTOR_A = [0.1, 0.2, 0.3]
FAKE_VECTOR_B = [0.4, 0.5, 0.6]
FAKE_VECTOR_C = [0.7, 0.8, 0.9]
FAKE_QUERY_VECTOR = [0.1, 0.2, 0.3]


def _make_embedding_response(vectors: list[list[float]]):
    """Build a fake litellm embedding response object."""
    data = [{"embedding": v, "index": i} for i, v in enumerate(vectors)]
    return MagicMock(data=data)


# Check chromadb availability for tests that need a real instance
try:
    import chromadb  # noqa: F401
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

skip_no_chromadb = pytest.mark.skipif(
    not HAS_CHROMADB,
    reason="chromadb not installed",
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def chroma(tmp_path: Path):
    """ChromaIndexer backed by a temp directory (requires chromadb)."""
    from antigravity_tool.repositories.chroma_indexer import ChromaIndexer
    return ChromaIndexer(tmp_path / ".chroma")


@pytest.fixture
def indexer() -> SQLiteIndexer:
    """In-memory SQLite indexer."""
    return SQLiteIndexer(":memory:")


@pytest.fixture
def container_repo(tmp_path: Path) -> ContainerRepository:
    return ContainerRepository(tmp_path)


@pytest.fixture
def schema_repo(tmp_path: Path) -> SchemaRepository:
    return SchemaRepository(tmp_path / "schemas")


# ═══════════════════════════════════════════════════════════════════
# Tests: ChromaIndexer LiteLLM embedding methods (need real chromadb)
# ═══════════════════════════════════════════════════════════════════


@skip_no_chromadb
class TestChromaIndexerEmbedding:
    """Verify upsert_embedding stores LiteLLM-powered vectors."""

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_upsert_embedding_stores_vector(self, mock_embed, chroma):
        """upsert_embedding should call litellm and store the result."""
        mock_embed.return_value = [FAKE_VECTOR_A]

        chroma.upsert_embedding("c1", "Zara is the protagonist", {"container_type": "character"})

        assert chroma.count == 1
        mock_embed.assert_called_once()
        args = mock_embed.call_args
        assert args[0][0] == ["Zara is the protagonist"]

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_upsert_embedding_fallback_on_failure(self, mock_embed, chroma):
        """upsert_embedding falls back to built-in embeddings on failure."""
        mock_embed.side_effect = RuntimeError("API key missing")

        # Should NOT raise — falls back to built-in upsert
        chroma.upsert_embedding("c1", "Zara is the protagonist")
        assert chroma.count == 1

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_upsert_embedding_multiple_containers(self, mock_embed, chroma):
        """Multiple containers can be upserted with distinct vectors."""
        mock_embed.side_effect = [
            [FAKE_VECTOR_A],
            [FAKE_VECTOR_B],
            [FAKE_VECTOR_C],
        ]

        chroma.upsert_embedding("c1", "character Zara", {"container_type": "character"})
        chroma.upsert_embedding("c2", "location Market", {"container_type": "location"})
        chroma.upsert_embedding("c3", "scene battle", {"container_type": "scene"})

        assert chroma.count == 3


@skip_no_chromadb
class TestChromaIndexerSemanticSearch:
    """Verify semantic_search returns correct container IDs."""

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_semantic_search_returns_ids(self, mock_embed, chroma):
        """semantic_search should return container IDs ordered by similarity."""
        mock_embed.side_effect = [
            [FAKE_VECTOR_A],
            [FAKE_VECTOR_B],
            [FAKE_VECTOR_C],
            [FAKE_QUERY_VECTOR],  # query — closest to FAKE_VECTOR_A
        ]

        chroma.upsert_embedding("c1", "character Zara")
        chroma.upsert_embedding("c2", "location Market")
        chroma.upsert_embedding("c3", "scene battle")

        results = chroma.semantic_search("protagonist Zara", limit=2)

        assert isinstance(results, list)
        assert len(results) <= 2
        # The query vector matches c1 exactly, so it should be first
        assert results[0] == "c1"

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_semantic_search_empty_collection(self, mock_embed, chroma):
        """semantic_search on an empty collection returns an empty list."""
        mock_embed.return_value = [FAKE_QUERY_VECTOR]
        results = chroma.semantic_search("anything")
        assert results == []

    @patch("antigravity_tool.repositories.chroma_indexer._litellm_embed")
    def test_semantic_search_fallback_on_failure(self, mock_embed, chroma):
        """semantic_search falls back to built-in search on API failure."""
        # First add a document with built-in embeddings
        chroma.upsert("c1", "Zara the warrior")

        # Now make the query embedding fail
        mock_embed.side_effect = RuntimeError("API down")

        results = chroma.semantic_search("warrior")
        # Should still return c1 via fallback
        assert "c1" in results


# ═══════════════════════════════════════════════════════════════════
# Tests: KnowledgeGraphService hybrid_search
# ═══════════════════════════════════════════════════════════════════


class TestKnowledgeGraphHybridSearch:
    """Verify hybrid_search combines vector + SQLite filtering."""

    def _setup_service(
        self,
        tmp_path: Path,
        indexer: SQLiteIndexer,
    ) -> KnowledgeGraphService:
        container_repo = ContainerRepository(tmp_path)
        schema_repo = SchemaRepository(tmp_path / "schemas")
        chroma = MagicMock()
        svc = KnowledgeGraphService(container_repo, schema_repo, indexer, chroma)
        return svc

    def test_hybrid_search_returns_filtered_results(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """hybrid_search filters by container_type when specified."""
        svc = self._setup_service(tmp_path, indexer)

        # Seed SQLite with two containers
        indexer.upsert_container("c1", "character", "Zara", "/z.yaml", {}, "2026-01-01", "2026-01-01")
        indexer.upsert_container("c2", "location", "Market", "/m.yaml", {}, "2026-01-01", "2026-01-01")

        # Mock semantic search returning both IDs
        svc.chroma_indexer.semantic_search.return_value = ["c1", "c2"]

        results = svc.hybrid_search("warrior", container_type="character", limit=5)
        assert len(results) == 1
        assert results[0]["name"] == "Zara"

    def test_hybrid_search_without_type_filter(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """hybrid_search returns all matching containers when no type filter."""
        svc = self._setup_service(tmp_path, indexer)

        indexer.upsert_container("c1", "character", "Zara", "/z.yaml", {}, "2026-01-01", "2026-01-01")
        indexer.upsert_container("c2", "location", "Market", "/m.yaml", {}, "2026-01-01", "2026-01-01")

        svc.chroma_indexer.semantic_search.return_value = ["c1", "c2"]

        results = svc.hybrid_search("world", limit=5)
        assert len(results) == 2

    def test_hybrid_search_no_chroma(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """hybrid_search falls back to relational query when no ChromaIndexer."""
        container_repo = ContainerRepository(tmp_path)
        schema_repo = SchemaRepository(tmp_path / "schemas")
        svc = KnowledgeGraphService(container_repo, schema_repo, indexer, chroma_indexer=None)

        indexer.upsert_container("c1", "character", "Zara", "/z.yaml", {}, "2026-01-01", "2026-01-01")

        results = svc.hybrid_search("warrior", limit=5)
        assert len(results) >= 1

    def test_semantic_search_uses_litellm_method(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """KG semantic_search calls chroma_indexer.semantic_search (LiteLLM)."""
        svc = self._setup_service(tmp_path, indexer)

        indexer.upsert_container("c1", "character", "Zara", "/z.yaml", {}, "2026-01-01", "2026-01-01")
        svc.chroma_indexer.semantic_search.return_value = ["c1"]

        results = svc.semantic_search("protagonist", limit=3)
        svc.chroma_indexer.semantic_search.assert_called_once_with("protagonist", limit=3)
        assert len(results) == 1
        assert results[0]["name"] == "Zara"
        assert results[0]["score"] == 0  # rank-based score


# ═══════════════════════════════════════════════════════════════════
# Tests: ContextEngine semantic boost
# ═══════════════════════════════════════════════════════════════════


class TestContextEngineSemanticBoost:
    """Verify that assemble_context merges semantic search results."""

    def _setup(self, tmp_path: Path, indexer: SQLiteIndexer):
        container_repo = ContainerRepository(tmp_path)
        schema_repo = SchemaRepository(tmp_path / "schemas")
        chroma = MagicMock()
        kg_svc = KnowledgeGraphService(container_repo, schema_repo, indexer, chroma)
        engine = ContextEngine(kg_svc, container_repo)
        return engine, kg_svc

    def test_semantic_hits_included_without_explicit_ids(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """assemble_context includes semantically relevant containers automatically."""
        engine, kg_svc = self._setup(tmp_path, indexer)

        # Seed two containers in SQLite
        indexer.upsert_container(
            "c1", "character", "Zara",
            "/z.yaml", {"role": "protagonist"},
            "2026-01-01", "2026-01-01",
        )
        indexer.upsert_container(
            "c2", "location", "Desert Fortress",
            "/d.yaml", {"type": "stronghold"},
            "2026-01-01", "2026-01-01",
        )

        # KG semantic_search returns c2 with full dict (it goes through KG method)
        kg_svc.chroma_indexer.semantic_search.return_value = ["c2"]

        result = engine.assemble_context(
            query="fortress battle",
            container_types=["character"],  # explicitly request characters
        )

        # c1 (character) is explicitly requested
        assert "Zara" in result.text
        # c2 (location) should be merged from semantic search
        assert "Desert Fortress" in result.text
        assert result.containers_included == 2

    def test_semantic_search_failure_doesnt_break_assembly(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """assemble_context works even if semantic search raises."""
        engine, kg_svc = self._setup(tmp_path, indexer)

        indexer.upsert_container(
            "c1", "character", "Kael",
            "/k.yaml", {"role": "antagonist"},
            "2026-01-01", "2026-01-01",
        )

        # Make semantic search raise
        kg_svc.chroma_indexer.semantic_search.side_effect = RuntimeError("boom")

        result = engine.assemble_context(
            query="dark villain",
            container_types=["character"],
        )

        # Should still include the explicitly requested container
        assert "Kael" in result.text
        assert result.containers_included == 1

    def test_semantic_deduplication(
        self, tmp_path: Path, indexer: SQLiteIndexer,
    ):
        """Containers found both explicitly and semantically aren't duplicated."""
        engine, kg_svc = self._setup(tmp_path, indexer)

        indexer.upsert_container(
            "c1", "character", "Zara",
            "/z.yaml", {"role": "protagonist"},
            "2026-01-01", "2026-01-01",
        )

        # c1 is found by both explicit type search AND semantic search
        kg_svc.chroma_indexer.semantic_search.return_value = ["c1"]

        result = engine.assemble_context(
            query="protagonist hero",
            container_types=["character"],
        )

        assert "Zara" in result.text
        assert result.containers_included == 1  # not duplicated
