"""Knowledge base query interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.utils.io import read_yaml

KB_ROOT = Path(__file__).parent

CATEGORIES = ["structures", "panels", "writing", "image_prompts"]


class KnowledgeBase:
    """Search, filter, and load knowledge base articles."""

    def __init__(self, kb_path: Path | None = None):
        self.kb_path = kb_path or KB_ROOT
        self._indexes: dict[str, list[dict]] = {}
        self._load_indexes()

    def _load_indexes(self) -> None:
        for category in CATEGORIES:
            index_path = self.kb_path / category / "index.yaml"
            if index_path.exists():
                data = read_yaml(index_path)
                articles = data.get("articles", []) if isinstance(data, dict) else []
                for article in articles:
                    article["category"] = category
                self._indexes[category] = articles

    def search(
        self,
        query: str,
        category: str | None = None,
        step: str | None = None,
    ) -> list[dict]:
        """Search articles by keyword match against title, tags, and summary."""
        query_lower = query.lower()
        results = []

        for cat, articles in self._indexes.items():
            if category and cat != category:
                continue
            for article in articles:
                if step and step not in article.get("use_in_steps", []):
                    continue
                searchable = " ".join([
                    article.get("title", ""),
                    " ".join(article.get("tags", [])),
                    article.get("summary", ""),
                ]).lower()
                if query_lower in searchable:
                    results.append(article)

        return results

    def get_for_step(self, step: str) -> list[dict]:
        """Get all articles relevant to a workflow step."""
        results = []
        for articles in self._indexes.values():
            for article in articles:
                if step in article.get("use_in_steps", []):
                    results.append(article)
        return results

    def load_article(self, category: str, filename: str) -> str | None:
        """Load the full markdown content of an article."""
        path = self.kb_path / category / filename
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_all(self, category: str | None = None) -> list[dict]:
        """List all articles, optionally filtered by category."""
        results = []
        for cat, articles in self._indexes.items():
            if category and cat != category:
                continue
            results.extend(articles)
        return results

    def get_evaluation_criteria(self, eval_type: str) -> str:
        """Load evaluation criteria content from the knowledge base."""
        mapping = {
            "pacing": ("writing", "pacing.md"),
            "dialogue": ("writing", "dialogue.md"),
            "composition": ("panels", "composition_rules.md"),
            "shot_types": ("panels", "shot_types.md"),
            "character_arcs": ("writing", "character_arcs.md"),
        }
        if eval_type in mapping:
            cat, filename = mapping[eval_type]
            return self.load_article(cat, filename) or ""
        return ""
