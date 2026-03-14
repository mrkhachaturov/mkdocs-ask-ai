"""MCP server for mkdocs-ask-ai.

Exposes documentation as MCP tools and resources so AI agents can
query the docs programmatically.

Requires: pip install mkdocs-ask-ai[mcp]
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP

    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False

from .mcp_index import load_index


def create_server(site_dir: Path) -> FastMCP:
    if not _HAS_MCP:
        raise ImportError(
            "MCP SDK not installed. Install with: pip install mkdocs-ask-ai[mcp]"
        )
    """Create and configure the MCP server for a built site."""
    site_dir = Path(site_dir)
    index = load_index(site_dir)
    site_name = index["site_name"]
    default_locale = index["default_locale"]
    available_locales = list(index["locales"].keys())

    # Slugify site name for use in URIs
    site_slug = re.sub(r"[^a-zA-Z0-9-]", "-", site_name).strip("-").lower()

    mcp = FastMCP(
        name=f"{site_name} Docs",
        instructions=(
            f"MCP server for {site_name} documentation. "
            f"Available locales: {', '.join(available_locales)}. "
            f"Default locale: {default_locale}. "
            "Use list_pages to discover available documentation, "
            "get_page to read a specific page, "
            "search_docs to find relevant pages, "
            "get_full_docs for the complete documentation."
        ),
    )

    @mcp.tool()
    def list_pages(locale: str = "") -> dict:
        """List all documentation pages grouped by section.

        Use this to discover what documentation is available before reading
        specific pages. Returns section names, page titles, paths, and
        descriptions.

        Args:
            locale: Locale code (e.g. 'en', 'ru'). Defaults to site default.
        """
        loc = locale or default_locale
        if loc not in index["locales"]:
            return {
                "error": f"Locale '{loc}' not found.",
                "available_locales": available_locales,
            }
        return {
            "site_name": site_name,
            "locale": loc,
            "sections": index["locales"][loc]["sections"],
            "available_locales": available_locales,
        }

    @mcp.tool()
    def get_page(path: str, locale: str = "") -> str:
        """Get a documentation page as clean markdown.

        Args:
            path: Page path, e.g. 'infrastructure/proxmox/index.md'.
            locale: Locale code. Defaults to site default.
        """
        loc = locale or default_locale

        if loc != default_locale and not path.startswith(f"{loc}/"):
            full_path = f"{loc}/{path}"
        else:
            full_path = path

        md_file = site_dir / full_path
        if not md_file.exists():
            md_file = site_dir / path
        if not md_file.exists():
            all_paths = _get_all_paths(index, loc)
            suggestions = [p for p in all_paths if _fuzzy_match(path, p)][:5]
            msg = f"Page not found: {path}"
            if suggestions:
                msg += "\n\nDid you mean:\n" + "\n".join(
                    f"  - {s}" for s in suggestions
                )
            return msg

        return md_file.read_text(encoding="utf-8")

    @mcp.tool()
    def search_docs(query: str, locale: str = "") -> dict:
        """Search across all documentation pages.

        Performs keyword search and returns matching pages with snippets.

        Args:
            query: Search terms.
            locale: Locale to search within. Defaults to site default.
        """
        loc = locale or default_locale
        if loc not in index["locales"]:
            return {
                "error": f"Locale '{loc}' not found.",
                "available_locales": available_locales,
            }

        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for section_name, pages in index["locales"][loc]["sections"].items():
            for page in pages:
                md_file = site_dir / page["path"]
                if not md_file.exists():
                    continue
                content = md_file.read_text(encoding="utf-8")
                content_lower = content.lower()

                score = sum(content_lower.count(term) for term in query_terms)
                if score == 0:
                    continue

                snippet = _extract_snippet(content, query_terms)

                results.append(
                    {
                        "title": page["title"],
                        "path": page["path"],
                        "section": section_name,
                        "snippet": snippet,
                        "score": score,
                    }
                )

        results.sort(key=lambda r: r["score"], reverse=True)

        return {
            "query": query,
            "locale": loc,
            "results": results[:20],
            "total": len(results),
        }

    @mcp.tool()
    def get_full_docs(locale: str = "") -> str:
        """Get the complete documentation as a single text.

        Returns all pages concatenated with section headings. Useful when
        you need comprehensive context about the entire site.

        Args:
            locale: Locale code. Defaults to site default.
        """
        loc = locale or default_locale

        if loc != default_locale:
            full_path = site_dir / loc / "llms-full.txt"
        else:
            full_path = site_dir / "llms-full.txt"

        if full_path.exists():
            return full_path.read_text(encoding="utf-8")

        if loc not in index["locales"]:
            return (
                f"Locale '{loc}' not found. Available: {', '.join(available_locales)}"
            )

        parts = [f"# {site_name}\n"]
        for section_name, pages in index["locales"][loc]["sections"].items():
            parts.append(f"\n## {section_name}\n")
            for page in pages:
                md_file = site_dir / page["path"]
                if md_file.exists():
                    parts.append(f"\n### {page['title']}\n")
                    parts.append(md_file.read_text(encoding="utf-8"))

        return "\n".join(parts)

    # Register each page as an MCP resource
    def _make_reader(path: str):
        """Create a closure that reads a specific page."""

        def reader() -> str:
            md_file = site_dir / path
            if md_file.exists():
                return md_file.read_text(encoding="utf-8")
            return f"Page not found: {path}"

        return reader

    for loc, locale_data in index["locales"].items():
        for _section_name, pages in locale_data["sections"].items():
            for page in pages:
                mcp.resource(
                    f"docs://{site_slug}/{page['path']}",
                    name=f"{page['title']} ({loc})",
                    mime_type="text/markdown",
                )(_make_reader(page["path"]))

    return mcp


def _get_all_paths(index: dict, locale: str) -> list[str]:
    """Get all page paths for a locale."""
    paths = []
    if locale in index["locales"]:
        for pages in index["locales"][locale]["sections"].values():
            paths.extend(p["path"] for p in pages)
    return paths


def _fuzzy_match(query: str, path: str) -> bool:
    """Simple fuzzy matching — checks if any query segment appears in path."""
    query_parts = re.split(r"[/._-]", query.lower())
    path_lower = path.lower()
    return any(part in path_lower for part in query_parts if len(part) > 2)


def _extract_snippet(content: str, terms: list[str], context_chars: int = 150) -> str:
    """Extract a text snippet around the first term match."""
    content_lower = content.lower()
    earliest_pos = len(content)
    for term in terms:
        pos = content_lower.find(term)
        if pos != -1 and pos < earliest_pos:
            earliest_pos = pos

    if earliest_pos == len(content):
        return content[: context_chars * 2] + "..."

    start = max(0, earliest_pos - context_chars)
    end = min(len(content), earliest_pos + context_chars)
    snippet = content[start:end].strip()

    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet
