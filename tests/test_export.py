"""Tests for the ExportService."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from showrunner_tool.schemas.container import GenericContainer, ContainerSchema, FieldDefinition
from showrunner_tool.services.export_service import ExportService


@pytest.fixture
def mock_kg_service():
    kg = MagicMock()
    # Mock structure tree: Season 1 -> Chapter 1 -> Scene 1
    kg.get_structure_tree.return_value = [
        {
            "id": "season_1",
            "name": "Season 1",
            "container_type": "season",
            "sort_order": 0,
            "children": [
                {
                    "id": "ch_1",
                    "name": "Chapter 1",
                    "container_type": "chapter",
                    "sort_order": 0,
                    "children": [
                        {
                            "id": "sc_1",
                            "name": "Scene 1",
                            "container_type": "scene",
                            "sort_order": 0,
                            "children": [],
                        }
                    ],
                }
            ],
        }
    ]

    # Mock full container list for JSON bundle
    kg.find_containers.return_value = [
        {"id": "season_1", "name": "Season 1", "container_type": "season"},
        {"id": "ch_1", "name": "Chapter 1", "container_type": "chapter"},
        {"id": "sc_1", "name": "Scene 1", "container_type": "scene"},
        {"id": "frag_1", "name": "Fragment 1", "container_type": "fragment", "attributes_json": '{"text": "It was a dark and stormy night."}'},
        {"id": "frag_2", "name": "Fragment 2", "container_type": "fragment", "attributes_json": '{"scene_heading": "EXT. DESERT - DAY", "action": "The sun beats down.", "character": "ZARA", "dialogue": "I hate sand."}'},
    ]

    kg.get_all_relationships.return_value = []

    def mock_get_children(parent_id):
        if parent_id == "sc_1":
            return [
                {
                    "id": "frag_1",
                    "container_type": "fragment",
                    "sort_order": 0,
                    "attributes_json": '{"text": "It was a dark and stormy night."}',
                },
                {
                    "id": "frag_2",
                    "container_type": "fragment",
                    "sort_order": 1,
                    # attributes for screenplay test
                    "attributes_json": '{"scene_heading": "EXT. DESERT - DAY", "action": "The sun beats down.", "character": "ZARA", "dialogue": "I hate sand."}',
                }
            ]
        return []
    
    kg.get_children.side_effect = mock_get_children

    return kg


@pytest.fixture
def mock_schema_repo():
    repo = MagicMock()
    # Return a dummy schema for bundle testing
    schema = ContainerSchema(
        name="fragment",
        display_name="Fragment",
        description="A piece of prose",
        fields=[FieldDefinition(name="text", type="text", required=True)]
    )
    repo.list_all.return_value = [schema]
    return repo


@pytest.fixture
def mock_event_service():
    es = MagicMock()
    es.get_all_events.return_value = [{"id": "evt_1", "event_type": "CREATE"}]
    return es


@pytest.fixture
def export_service(mock_kg_service, mock_schema_repo, mock_event_service):
    # Pass None for container_repo as it's not used directly by the current methods
    return ExportService(mock_kg_service, None, mock_schema_repo, mock_event_service)


def test_export_markdown_headings_and_text(export_service):
    md = export_service.export_markdown()
    
    # Check headings
    assert "# Season 1" in md
    assert "## Chapter 1" in md
    assert "### Scene 1" in md
    
    # Check fragment text
    assert "It was a dark and stormy night." in md
    
    # Check order
    season_idx = md.find("# Season 1")
    ch_idx = md.find("## Chapter 1")
    sc_idx = md.find("### Scene 1")
    text_idx = md.find("It was a dark and stormy night.")
    
    assert season_idx < ch_idx < sc_idx < text_idx


def test_export_json_bundle_keys(export_service):
    bundle = export_service.export_json_bundle()
    
    assert "containers" in bundle
    assert "schemas" in bundle
    assert "relationships" in bundle
    assert "events" in bundle
    
    assert len(bundle["containers"]) == 5
    assert len(bundle["schemas"]) == 1
    assert bundle["schemas"][0]["name"] == "fragment"
    assert len(bundle["events"]) == 1
    assert bundle["events"][0]["id"] == "evt_1"


def test_export_fountain_format(export_service):
    fountain = export_service.export_fountain()
    
    # Check Fountain screenplay formatting from frag_2
    assert "EXT. DESERT - DAY" in fountain
    assert "The sun beats down." in fountain
    assert "ZARA" in fountain
    assert "I hate sand." in fountain
    
    # The plain text fragment (frag_1) should act as a fallback and be included as action/prose
    assert "It was a dark and stormy night." in fountain
