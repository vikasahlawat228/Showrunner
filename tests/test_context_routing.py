"""Tests for Phase G Track 3 - Automatic Context Routing."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from antigravity_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from antigravity_tool.repositories.event_sourcing_repo import EventService
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService
from antigravity_tool.services.writing_service import WritingService


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory with antigravity.yaml."""
    (tmp_path / "schemas").mkdir()
    (tmp_path / "antigravity.yaml").write_text(
        "name: Test Project\n"
        "version: 0.1.0\n"
        "default_model: gemini/gemini-2.0-flash\n"
    )
    return tmp_path

@pytest.fixture
def event_service() -> EventService:
    """In-memory event service."""
    return EventService(":memory:")

@pytest.fixture
def container_repo(tmp_project: Path) -> ContainerRepository:
    """Container repo pointing at a temp dir."""
    return ContainerRepository(tmp_project)

@pytest.fixture
def schema_repo(tmp_project: Path) -> SchemaRepository:
    """Schema repo pointing at schemas dir."""
    return SchemaRepository(tmp_project / "schemas")

@pytest.fixture
def kg_service(
    container_repo: ContainerRepository,
    schema_repo: SchemaRepository
) -> KnowledgeGraphService:
    indexer = SQLiteIndexer(":memory:")
    return KnowledgeGraphService(container_repo, schema_repo, indexer)

@pytest.fixture
def writing_service(
    container_repo: ContainerRepository,
    kg_service: KnowledgeGraphService,
    tmp_project: Path,
    event_service: EventService,
) -> WritingService:
    return WritingService(
        container_repo=container_repo,
        kg_service=kg_service,
        project_path=tmp_project,
        event_service=event_service,
    )


class TestAutomaticContextRouting:
    
    def test_save_fragment_with_entity_detection(self, writing_service: WritingService, kg_service: KnowledgeGraphService, event_service: EventService):
        # 1. Setup existing container in KG
        zara_container = GenericContainer(
            id="char_zara_123",
            container_type="character",
            name="Zara",
            attributes={"role": "protagonist"}
        )
        kg_service.container_repo.save_container(zara_container)
        
        # Ensure it's reachable in index
        results = kg_service.find_containers(filters={"id": "char_zara_123"})
        assert len(results) == 1
        
        # 2. Mock the LLM call to return "Zara" mention
        mock_detected = [
            {
                "mention": "Zara",
                "matched_name": "Zara",
                "confidence": 0.95
            }
        ]
        
        text = "Zara looked across the desolate wasteland."
        
        with patch.object(writing_service, '_llm_detect_entities', return_value=mock_detected):
            # 3. Call save_fragment
            fragment, detected = writing_service.save_fragment(
                text=text,
                title="Scene 1 Outline",
                branch_id="main"
            )
            
        # 4. Assertions on returned values
        assert len(detected) == 1
        assert detected[0].container_id == "char_zara_123"
        assert detected[0].mention == "Zara"
        
        assert "char_zara_123" in fragment.associated_containers
        
        # 5. Assertions on persisted container (relationships added)
        # Using KD indexer or just reading it from ContainerRepository
        saved_containers = kg_service.find_containers(container_type="fragment")
        assert len(saved_containers) == 1
        fs = saved_containers[0]
        
        attrs = json.loads(fs["attributes_json"]) if isinstance(fs["attributes_json"], str) else fs.get("attributes", {})
        assert "associated_containers" in attrs
        assert "char_zara_123" in attrs["associated_containers"]
        
        # Check relationships from KG index
        rels = kg_service.indexer.get_all_relationships()
        assert len(rels) >= 1
        mention_rels = [r for r in rels if r["rel_type"] == "mentions" and r["source_id"] == fs["id"]]
        assert len(mention_rels) == 1
        assert mention_rels[0]["target_id"] == "char_zara_123"
        
        # 6. Verify event sourcing includes the relationships
        events = event_service.get_all_events()
        # Find the CREATE event for the fragment
        frag_events = [e for e in events if e["container_id"] == fragment.id]
        assert len(frag_events) == 1
        
        payload = frag_events[0]["payload"]
        assert "associated_containers" in payload
        assert "char_zara_123" in payload["associated_containers"]
