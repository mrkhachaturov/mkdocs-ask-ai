"""Documentation index builder for MCP server.

Generates and reads docs-index.json — the bridge between the MkDocs build
and the MCP server.
"""

import json
from pathlib import Path
from typing import Any


def build_index(
    pages_data: dict[str, list[dict[str, Any]]],
    site_name: str,
    site_url: str,
    default_locale: str,
    locale_prefix: str,
) -> dict:
    """Build a structured index from collected page data."""
    locale = locale_prefix or default_locale
    sections = {}

    for section_name, pages in pages_data.items():
        section_pages = []
        for page in pages:
            if "title" not in page or "dest_path" not in page:
                continue
            dest_path = page["dest_path"]
            md_path = (
                dest_path.replace(".html", ".md")
                if dest_path.endswith(".html")
                else dest_path
            )
            section_pages.append(
                {
                    "title": page["title"],
                    "path": md_path,
                    "description": page.get("description", ""),
                }
            )
        if section_pages:
            sections[section_name] = section_pages

    return {
        "site_name": site_name,
        "site_url": site_url.rstrip("/"),
        "default_locale": default_locale,
        "locales": {locale: {"sections": sections}},
    }


def save_index(index: dict, site_dir: Path) -> Path:
    """Save index to docs-index.json in site_dir. Merges with existing."""
    index_path = site_dir / "docs-index.json"

    if index_path.exists():
        existing = json.loads(index_path.read_text(encoding="utf-8"))
        existing["locales"].update(index["locales"])
        index = existing

    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return index_path


def load_index(site_dir: Path) -> dict:
    """Load docs-index.json from a built site directory."""
    index_path = site_dir / "docs-index.json"
    if not index_path.exists():
        raise FileNotFoundError(
            f"docs-index.json not found in {site_dir}. "
            "Run 'mkdocs build' first with the ask-ai plugin enabled."
        )
    return json.loads(index_path.read_text(encoding="utf-8"))
