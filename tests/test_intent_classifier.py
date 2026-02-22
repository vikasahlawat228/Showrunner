"""Tests for IntentClassifier — keyword-based intent classification."""

from __future__ import annotations

import pytest

from antigravity_tool.schemas.chat import ToolIntent
from antigravity_tool.services.intent_classifier import IntentClassifier


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def classifier():
    return IntentClassifier()


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════


class TestChatDefault:
    """Generic messages should classify as CHAT."""

    def test_greeting(self, classifier):
        result = classifier.classify("Hello, how are you?")
        assert result.tool == "CHAT"

    def test_question(self, classifier):
        result = classifier.classify("Can you help me with my story?")
        assert result.tool == "CHAT"

    def test_returns_tool_intent(self, classifier):
        result = classifier.classify("hi")
        assert isinstance(result, ToolIntent)
        assert result.confidence > 0


class TestSearchIntent:
    def test_find_keyword(self, classifier):
        result = classifier.classify("Find all characters in chapter 3")
        assert result.tool == "SEARCH"

    def test_search_keyword(self, classifier):
        result = classifier.classify("Search for scenes in the forest")
        assert result.tool == "SEARCH"

    def test_show_me(self, classifier):
        result = classifier.classify("Show me all the world settings")
        assert result.tool == "SEARCH"

    def test_list_all(self, classifier):
        result = classifier.classify("List all characters")
        assert result.tool == "SEARCH"


class TestCreateIntent:
    def test_create_character(self, classifier):
        result = classifier.classify("Create a new character named Zara")
        assert result.tool == "CREATE"

    def test_add_scene(self, classifier):
        result = classifier.classify("Add a new scene in the throne room")
        assert result.tool == "CREATE"

    def test_generate_outline(self, classifier):
        result = classifier.classify("Generate an outline for chapter 2")
        assert result.tool == "CREATE"

    def test_write_a_scene(self, classifier):
        result = classifier.classify("Write a scene where Zara meets Kael")
        assert result.tool == "CREATE"

    def test_draft(self, classifier):
        result = classifier.classify("Draft a dialogue between the two characters")
        assert result.tool == "CREATE"

    def test_extracts_entity_type(self, classifier):
        result = classifier.classify("Create a new character named Zara")
        assert result.params.get("entity_type") == "character"


class TestUpdateIntent:
    def test_update(self, classifier):
        result = classifier.classify("Update Zara's backstory")
        assert result.tool == "UPDATE"

    def test_edit(self, classifier):
        result = classifier.classify("Edit the world settings")
        assert result.tool == "UPDATE"

    def test_change(self, classifier):
        result = classifier.classify("Change the scene location")
        assert result.tool == "UPDATE"

    def test_revise(self, classifier):
        result = classifier.classify("Revise the dialogue in scene 3")
        assert result.tool == "UPDATE"

    def test_requires_approval(self, classifier):
        result = classifier.classify("Update Zara's backstory")
        assert result.requires_approval is True


class TestDeleteIntent:
    def test_delete(self, classifier):
        result = classifier.classify("Delete the old character file")
        assert result.tool == "DELETE"

    def test_remove(self, classifier):
        result = classifier.classify("Remove scene 5 from the outline")
        assert result.tool == "DELETE"

    def test_requires_approval(self, classifier):
        result = classifier.classify("Delete character Zara")
        assert result.requires_approval is True


class TestPipelineIntent:
    def test_run_pipeline(self, classifier):
        result = classifier.classify("Run pipeline for chapter 1")
        assert result.tool == "PIPELINE"

    def test_start_pipeline(self, classifier):
        result = classifier.classify("Start pipeline from world building")
        assert result.tool == "PIPELINE"

    def test_requires_approval(self, classifier):
        result = classifier.classify("Run pipeline")
        assert result.requires_approval is True


class TestNavigateIntent:
    def test_open(self, classifier):
        result = classifier.classify("Open the timeline view")
        assert result.tool == "NAVIGATE"

    def test_go_to(self, classifier):
        result = classifier.classify("Go to the storyboard")
        assert result.tool == "NAVIGATE"

    def test_extracts_target(self, classifier):
        result = classifier.classify("Go to the storyboard")
        assert result.params.get("target") == "storyboard"


class TestEvaluateIntent:
    def test_evaluate(self, classifier):
        result = classifier.classify("Evaluate scene 3 for quality")
        assert result.tool == "EVALUATE"

    def test_review(self, classifier):
        result = classifier.classify("Review the dialogue in chapter 1")
        assert result.tool == "EVALUATE"


class TestResearchIntent:
    def test_research(self, classifier):
        result = classifier.classify("Research medieval castle architecture")
        assert result.tool == "RESEARCH"

    def test_investigate(self, classifier):
        result = classifier.classify("Investigate the history of samurai")
        assert result.tool == "RESEARCH"


class TestPlanIntent:
    def test_plan(self, classifier):
        result = classifier.classify("Plan the next chapter")
        assert result.tool == "PLAN"

    def test_outline(self, classifier):
        result = classifier.classify("Outline the story arc for season 2")
        assert result.tool == "PLAN"


class TestDecideIntent:
    def test_decision(self, classifier):
        result = classifier.classify("I've made a decision about the tone")
        assert result.tool == "DECIDE"

    def test_always_use(self, classifier):
        result = classifier.classify("Always use dark colors in night scenes")
        assert result.tool == "DECIDE"

    def test_remember_that(self, classifier):
        result = classifier.classify("Remember that Zara is left-handed")
        assert result.tool == "DECIDE"


class TestClassifyBatch:
    def test_batch(self, classifier):
        messages = ["Hello", "Create a new character", "Delete scene 5"]
        results = classifier.classify_batch(messages)
        assert len(results) == 3
        assert results[0].tool == "CHAT"
        assert results[1].tool == "CREATE"
        assert results[2].tool == "DELETE"


class TestConfidence:
    """Confidence should increase with more keyword matches."""

    def test_single_keyword_lower_confidence(self, classifier):
        result = classifier.classify("Find x")
        assert result.confidence < 0.8

    def test_multiple_keywords_higher_confidence(self, classifier):
        result = classifier.classify("Search and find all characters, show me the list")
        assert result.confidence >= 0.5
