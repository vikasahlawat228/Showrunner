"""Tests for SchemaInferenceService — heuristic schema analysis."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from showrunner_tool.schemas.container import GenericContainer, ContainerSchema
from showrunner_tool.services.schema_inference_service import SchemaInferenceService, _infer_field_type


# ── Helpers ─────────────────────────────────────────────────────

def _make_container(ctype: str, name: str, attrs: dict) -> GenericContainer:
    return GenericContainer(container_type=ctype, name=name, attributes=attrs)


class FakeContainerRepo:
    """Mimic ContainerRepository.list_all()."""

    def __init__(self, containers):
        self._containers = containers

    def list_all(self):
        return self._containers


class FakeSchemaRepo:
    """Mimic SchemaRepository._list_files()."""

    def __init__(self, schemas=None):
        self._schemas = schemas or []

    def _list_files(self):
        return self._schemas

    def _load_file(self, f):
        return f


# ── Tests ───────────────────────────────────────────────────────

class TestInferFieldType:
    def test_all_strings(self):
        assert _infer_field_type(["hello", "world"]) == "string"

    def test_all_ints(self):
        assert _infer_field_type([1, 2, 3]) == "integer"

    def test_mixed_int_float(self):
        assert _infer_field_type([1, 2.5]) == "float"

    def test_booleans(self):
        assert _infer_field_type([True, False]) == "boolean"

    def test_lists(self):
        assert _infer_field_type([["a"], ["b"]]) == "list[string]"

    def test_mixed_types_fallback(self):
        assert _infer_field_type(["hello", 42, True]) == "string"


class TestAnalyzeUnstructuredContainers:
    def test_no_suggestions_when_single_container(self):
        containers = [_make_container("lore", "Magic System", {"power_source": "emotion"})]
        repo = FakeContainerRepo(containers)
        schema_repo = FakeSchemaRepo()
        service = SchemaInferenceService(repo, schema_repo)
        suggestions = service.analyze_unstructured_containers()
        assert suggestions == []

    def test_suggestions_when_multiple_similar_containers(self):
        containers = [
            _make_container("lore", "Fire Magic", {"power_source": "heat", "element": "fire", "weakness": "water"}),
            _make_container("lore", "Ice Magic", {"power_source": "cold", "element": "ice", "weakness": "fire"}),
            _make_container("lore", "Storm Magic", {"power_source": "wind", "element": "air", "weakness": "earth"}),
        ]
        repo = FakeContainerRepo(containers)
        schema_repo = FakeSchemaRepo()
        service = SchemaInferenceService(repo, schema_repo)
        suggestions = service.analyze_unstructured_containers()

        assert len(suggestions) == 1
        s = suggestions[0]
        assert s["container_type"] == "lore"
        assert s["instance_count"] == 3
        assert "power_source" in s["common_keys"]
        assert "element" in s["common_keys"]
        assert "weakness" in s["common_keys"]

    def test_skips_containers_with_existing_schema(self):
        schema = ContainerSchema(name="lore", display_name="Lore", fields=[])
        containers = [
            _make_container("lore", "Fire Magic", {"power_source": "heat"}),
            _make_container("lore", "Ice Magic", {"power_source": "cold"}),
        ]
        repo = FakeContainerRepo(containers)
        schema_repo = FakeSchemaRepo([schema])
        service = SchemaInferenceService(repo, schema_repo)
        suggestions = service.analyze_unstructured_containers()
        assert suggestions == []

    def test_internal_keys_skipped(self):
        containers = [
            _make_container("concept", "A", {"_source_text": "foo", "visible_key": "bar"}),
            _make_container("concept", "B", {"_source_text": "baz", "visible_key": "qux"}),
        ]
        repo = FakeContainerRepo(containers)
        schema_repo = FakeSchemaRepo()
        service = SchemaInferenceService(repo, schema_repo)
        suggestions = service.analyze_unstructured_containers()

        assert len(suggestions) == 1
        field_names = [f["name"] for f in suggestions[0]["inferred_fields"]]
        assert "visible_key" in field_names
        assert "_source_text" not in field_names


@pytest.mark.asyncio
class TestExtractContainerFromText:
    @patch("showrunner_tool.services.schema_inference_service.litellm")
    async def test_extracts_from_text(self, mock_litellm):
        import json
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "name": "The Aether Crystal",
            "container_type": "item",
            "attributes": {"power_source": "emotional resonance", "color": "iridescent blue"},
            "tags": ["#magic-system"],
        })
        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        repo = FakeContainerRepo([])
        schema_repo = FakeSchemaRepo()
        service = SchemaInferenceService(repo, schema_repo)

        container = await service.extract_container_from_text(
            "The Aether Crystal glows with iridescent blue light, powered by emotional resonance."
        )

        assert container.name == "The Aether Crystal"
        assert container.container_type == "item"
        assert container.attributes["power_source"] == "emotional resonance"

    @patch("showrunner_tool.services.schema_inference_service.litellm")
    async def test_fallback_on_llm_failure(self, mock_litellm):
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("API down"))

        repo = FakeContainerRepo([])
        schema_repo = FakeSchemaRepo()
        service = SchemaInferenceService(repo, schema_repo)

        container = await service.extract_container_from_text("Some lore text about magic")
        assert container.container_type == "lore"
        assert "raw_text" in container.attributes
