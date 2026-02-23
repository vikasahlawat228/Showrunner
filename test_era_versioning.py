import os
import shutil
import uuid
import pytest
from pathlib import Path

from antigravity_tool.schemas.container import GenericContainer
from antigravity_tool.repositories.container_repo import ContainerRepository, SchemaRepository
from antigravity_tool.repositories.sqlite_indexer import SQLiteIndexer
from antigravity_tool.services.knowledge_graph_service import KnowledgeGraphService

@pytest.fixture
def setup_services(tmp_path):
    schema_repo = SchemaRepository(base_dir=tmp_path / "schemas")
    container_repo = ContainerRepository(base_dir=tmp_path / "containers")
    indexer = SQLiteIndexer(db_path=":memory:")
    kg_service = KnowledgeGraphService(
        container_repo=container_repo,
        schema_repo=schema_repo,
        indexer=indexer,
    )
    return container_repo, kg_service

def test_era_versioning_and_unresolved_threads(setup_services):
    container_repo, kg_service = setup_services
    
    # 1. Create character "Zara" with era_id=None (global)
    zara_id = str(uuid.uuid4())
    zara = GenericContainer(
        id=zara_id,
        container_type="character",
        name="Zara",
        attributes={"role": "Protagonist"},
        era_id=None
    )
    container_repo.save_container(zara)
    
    # 2. Fork to era "season_2"
    zara_s2 = kg_service.create_era_fork(zara_id, "season_2")
    zara_s2.attributes["role"] = "Leader"
    container_repo.save_container(zara_s2)
    
    # Verify new container created with parent_version_id
    assert zara_s2.parent_version_id == zara_id
    assert zara_s2.era_id == "season_2"
    assert zara_s2.id != zara_id
    
    # 3. Query get_entity_at_era("zara", "season_2") -> returns forked version
    fetched_s2 = kg_service.get_entity_at_era(zara_id, "season_2")
    assert fetched_s2 is not None
    assert fetched_s2["id"] == zara_s2.id
    
    # 4. Query get_entity_at_era("zara", "season_1") -> falls back to global
    fetched_s1 = kg_service.get_entity_at_era(zara_id, "season_1")
    assert fetched_s1 is not None
    assert fetched_s1["id"] == zara_id
    
    # 5. Create relationship edges, mark some resolved -> query unresolved
    foe_id = str(uuid.uuid4())
    foe = GenericContainer(
        id=foe_id,
        container_type="character",
        name="Tharok",
        attributes={"role": "Antagonist"},
    )
    
    foe.relationships.append({
        "target_id": zara_id,
        "type": "enemy",
        "metadata": {
            "description": "Sworn enemies",
            "created_in_era": "season_1",
            "resolved": False
        }
    })
    
    foe.relationships.append({
        "target_id": zara_s2.id, # New target
        "type": "ally",
        "metadata": {
            "description": "Uneasy alliance",
            "created_in_era": "season_2",
            "resolved": False
        }
    })
    container_repo.save_container(foe)
    
    # Query unresolved threads for season 1
    unresolved_s1 = kg_service.get_unresolved_threads(era_id="season_1")
    assert len(unresolved_s1) == 2  # all unresolved threads are returned unless filtered out
    
    # Resolve one thread
    kg_service.resolve_thread(f"{foe_id}::::{zara_id}::::enemy", "season_1")
    
    unresolved_after = kg_service.get_unresolved_threads(era_id="season_1")
    # One is resolved in season_1, so it shouldn't show up. The other isn't resolved.
    assert len(unresolved_after) == 1
    assert unresolved_after[0]["target"] == "Zara" # Because foe points to zara_s2! Wait, Zara S2 is "Zara", Zara is "Zara"
    assert unresolved_after[0]["relationship"] == "ally"
    
if __name__ == "__main__":
    pytest.main([__file__])
