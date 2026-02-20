"""antigravity knowledge - knowledge base query commands."""

from __future__ import annotations

from typing import Optional

import typer

from antigravity_tool.knowledge.loader import KnowledgeBase
from antigravity_tool.utils.display import console, print_info, print_markdown, create_table

app = typer.Typer(help="Query the built-in knowledge base.")


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    step: Optional[str] = typer.Option(None, "--step", "-s", help="Filter by workflow step"),
) -> None:
    """Search knowledge base articles."""
    kb = KnowledgeBase()
    results = kb.search(query, category=category, step=step)

    if not results:
        print_info(f"No results for '{query}'.")
        return

    table = create_table("Knowledge Base Results", [
        ("Category", "cyan"),
        ("Title", "green"),
        ("Tags", "yellow"),
    ])
    for article in results:
        table.add_row(
            article["category"],
            article["title"],
            ", ".join(article.get("tags", [])[:5]),
        )
    console.print(table)


@app.command("show")
def show(
    category: str = typer.Argument(..., help="Category: structures, panels, writing, image_prompts"),
    article: str = typer.Argument(..., help="Article filename (e.g., shot_types.md)"),
) -> None:
    """Display a knowledge base article."""
    kb = KnowledgeBase()
    content = kb.load_article(category, article)
    if content is None:
        print_info(f"Article not found: {category}/{article}")
        return
    print_markdown(content)


@app.command("list")
def list_articles(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
) -> None:
    """List all available knowledge base articles."""
    kb = KnowledgeBase()
    articles = kb.list_all(category=category)

    if not articles:
        print_info("No articles found.")
        return

    table = create_table("Knowledge Base", [
        ("Category", "cyan"),
        ("File", "green"),
        ("Title", ""),
        ("Steps", "yellow"),
    ])
    for article in articles:
        table.add_row(
            article["category"],
            article["file"],
            article["title"],
            ", ".join(article.get("use_in_steps", [])[:3]),
        )
    console.print(table)
