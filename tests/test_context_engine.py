"""Tests for ContextEngine — unified context assembly with token budgeting."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from showrunner_tool.services.context_engine import ContextEngine, ContextResult


@pytest.fixture
def mock_kg_service():
    kg = MagicMock()
    return kg


@pytest.fixture
def mock_container_repo():
    repo = MagicMock()
    return repo


@pytest.fixture
def engine(mock_kg_service, mock_container_repo):
    return ContextEngine(kg_service=mock_kg_service, container_repo=mock_container_repo)


def test_get_tier1_memory_empty(engine, mock_kg_service):
    """Test getting tier 1 memory when no project_memory containers exist."""
    mock_kg_service.find_containers.return_value = []
    
    result = engine.get_tier1_memory()
    assert result == ""
    mock_kg_service.find_containers.assert_called_with(container_type="project_memory")


def test_get_tier1_memory_with_facts(engine, mock_kg_service):
    """Test getting tier 1 memory when facts exist."""
    # Mock some project_memory containers
    container1 = {
        "id": "1",
        "container_type": "project_memory",
        "attributes": {"fact": "The sky is green."}
    }
    container2 = {
        "id": "2",
        "container_type": "project_memory",
        # Test stringified JSON attributes
        "attributes": json.dumps({"fact": "Magic requires a silver coin."})
    }
    
    mock_kg_service.find_containers.return_value = [container1, container2]
    
    result = engine.get_tier1_memory(max_tokens=1000)
    
    assert "## Core Project Memory (Tier 1)" in result
    assert "- The sky is green." in result
    assert "- Magic requires a silver coin." in result


def test_get_tier1_memory_budget_limit(engine, mock_kg_service):
    """Test getting tier 1 memory respects the token budget."""
    container1 = {
        "id": "1",
        "container_type": "project_memory",
        "attributes": {"fact": "A short fact."}
    }
    container2 = {
        "id": "2",
        "container_type": "project_memory",
        "attributes": {"fact": "A very long fact that will exceed the budget " * 10}
    }
    
    # Return them. Reversed order is used in the engine, so container2 comes first, then container1.
    # Actually `reversed(memory_containers)` means if [c1, c2], c2 is processed first.
    mock_kg_service.find_containers.return_value = [container1, container2]
    
    # Give a very small budget that only fits the short fact
    # length of "A short fact." is 13 chars (~3 tokens)
    result = engine.get_tier1_memory(max_tokens=15)
    
    assert "## Core Project Memory (Tier 1)" in result
    assert "- A short fact." in result
    assert "A very long fact" not in result


def test_assemble_context_empty(engine, mock_kg_service):
    """Assemble context when no containers match."""
    mock_kg_service.find_containers.return_value = []
    mock_kg_service.semantic_search.return_value = []
    
    result = engine.assemble_context(query="test", container_ids=["unknown"])
    
    assert isinstance(result, ContextResult)
    assert result.text == ""
    assert result.containers_included == 0


def test_assemble_context_with_containers(engine, mock_kg_service):
    """Assemble context successfully formats containers."""
    c1 = {
        "id": "char1",
        "name": "Zara",
        "container_type": "character",
        "attributes": {"age": 25, "role": "Hero"}
    }
    
    mock_kg_service.find_containers.return_value = [c1]
    mock_kg_service.semantic_search.return_value = []
    mock_kg_service.get_neighbors.return_value = []
    
    result = engine.assemble_context(query="Zara", container_ids=["char1"])
    
    assert isinstance(result, ContextResult)
    assert "## Zara (character)" in result.text
    assert "- **age**: 25" in result.text
    assert "- **role**: Hero" in result.text
    assert result.containers_included == 1
    assert len(result.buckets) == 1
    assert result.buckets[0].name == "Zara"
