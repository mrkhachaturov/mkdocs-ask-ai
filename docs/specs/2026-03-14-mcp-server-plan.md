# MCP Server Integration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an MCP server to mkdocs-ask-ai that exposes documentation as tools and resources, supporting stdio and streamable HTTP transports with full i18n support.

**Architecture:** The MCP server reads a `docs-index.json` file generated during `mkdocs build` plus the raw `.md` files from the site output directory. It uses FastMCP from the official Python MCP SDK. The server is optional — enabled via config and requires `pip install mkdocs-ask-ai[mcp]`.

**Tech Stack:** Python, `mcp` SDK (FastMCP), MkDocs plugin API

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/mkdocs_ask_ai/config.py` | Modify | Add MCP config options |
| `src/mkdocs_ask_ai/mcp_index.py` | Create | Build and read `docs-index.json` |
| `src/mkdocs_ask_ai/mcp_server.py` | Create | FastMCP server with 4 tools + resources |
| `src/mkdocs_ask_ai/cli.py` | Create | CLI entry point (`mkdocs-ask-ai mcp`) |
| `src/mkdocs_ask_ai/plugin.py` | Modify | Call index builder in `on_post_build` |
| `pyproject.toml` | Modify | Add optional `[mcp]` dependency, `console_scripts` |
| `tests/test_mcp_index.py` | Create | Tests for index builder |
| `tests/test_mcp_server.py` | Create | Tests for MCP server tools |

---

## Chunk 1: Documentation Index

### Task 1: Create `mcp_index.py` — index builder

**Files:**
- Create: `src/mkdocs_ask_ai/mcp_index.py`
- Test: `tests/test_mcp_index.py`

- [ ] **Step 1: Write test for `build_index()`**

```python
# tests/test_mcp_index.py
import json
from pathlib import Path
from mkdocs_ask_ai.mcp_index import build_index, load_index

def test_build_index_single_locale(tmp_path):
    """Index builder produces correct structure for single-locale site."""
    pages_data = {
        "Infrastructure": [
            {
                "src_uri": "infrastructure/proxmox/index.md",
                "title": "Proxmox — pve01",
                "description": "Proxmox docs",
                "markdown": "# Proxmox\n\nContent here.",
                "dest_path": "infrastructure/proxmox/index.html",
                "dest_uri": "infrastructure/proxmox/index.html",
            }
        ],
        "Services": [],
    }

    result = build_index(
        pages_data=pages_data,
        site_name="Test Wiki",
        site_url="https://test.example.com",
        default_locale="en",
        locale_prefix="",
    )

    assert result["site_name"] == "Test Wiki"
    assert result["site_url"] == "https://test.example.com"
    assert result["default_locale"] == "en"
    assert "en" in result["locales"]
    infra = result["locales"]["en"]["sections"]["Infrastructure"]
    assert len(infra) == 1
    assert infra[0]["title"] == "Proxmox — pve01"
    assert infra[0]["path"] == "infrastructure/proxmox/index.md"
    # Empty sections should be omitted
    assert "Services" not in result["locales"]["en"]["sections"]


def test_build_index_with_locale_prefix(tmp_path):
    """Index builder uses locale prefix for non-default locales."""
    pages_data = {
        "Infrastructure": [
            {
                "src_uri": "infrastructure/proxmox/index.md",
                "title": "Proxmox — pve01",
                "description": "",
                "markdown": "# Proxmox",
                "dest_path": "ru/infrastructure/proxmox/index.html",
                "dest_uri": "ru/infrastructure/proxmox/index.html",
            }
        ],
    }

    result = build_index(
        pages_data=pages_data,
        site_name="Test Wiki",
        site_url="https://test.example.com",
        default_locale="en",
        locale_prefix="ru",
    )

    assert "ru" in result["locales"]
    page = result["locales"]["ru"]["sections"]["Infrastructure"][0]
    assert page["path"] == "ru/infrastructure/proxmox/index.md"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugins/mkdocs-ask-ai && python -m pytest tests/test_mcp_index.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mkdocs_ask_ai.mcp_index'`

- [ ] **Step 3: Implement `build_index()` and `load_index()`**

```python
# src/mkdocs_ask_ai/mcp_index.py
"""Documentation index builder for MCP server.

Generates and reads docs-index.json — the bridge between the MkDocs build
and the MCP server.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def build_index(
    pages_data: Dict[str, List[Dict[str, Any]]],
    site_name: str,
    site_url: str,
    default_locale: str,
    locale_prefix: str,
) -> dict:
    """Build a structured index from collected page data.

    Args:
        pages_data: Section -> list of page dicts from the plugin.
        site_name: MkDocs site_name.
        site_url: MkDocs site_url.
        default_locale: Default locale code (e.g. "en").
        locale_prefix: Current locale prefix ("" for default, "ru" for Russian, etc).

    Returns:
        Index dict ready for JSON serialization.
    """
    locale = locale_prefix or default_locale
    sections = {}

    for section_name, pages in pages_data.items():
        section_pages = []
        for page in pages:
            if "title" not in page or "dest_path" not in page:
                continue
            dest_path = page["dest_path"]
            # Build the .md path from dest_path
            md_path = dest_path.replace(".html", ".md") if dest_path.endswith(".html") else dest_path
            section_pages.append({
                "title": page["title"],
                "path": md_path,
                "description": page.get("description", ""),
            })
        if section_pages:
            sections[section_name] = section_pages

    return {
        "site_name": site_name,
        "site_url": site_url.rstrip("/"),
        "default_locale": default_locale,
        "locales": {
            locale: {"sections": sections}
        },
    }


def save_index(index: dict, site_dir: Path) -> Path:
    """Save index to docs-index.json in site_dir. Merges with existing."""
    index_path = site_dir / "docs-index.json"

    # Merge with existing index (from previous locale builds)
    if index_path.exists():
        existing = json.loads(index_path.read_text(encoding="utf-8"))
        existing["locales"].update(index["locales"])
        index = existing

    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    return index_path


def load_index(site_dir: Path) -> dict:
    """Load docs-index.json from a built site directory.

    Raises FileNotFoundError if not found.
    """
    index_path = site_dir / "docs-index.json"
    if not index_path.exists():
        raise FileNotFoundError(
            f"docs-index.json not found in {site_dir}. "
            "Run 'mkdocs build' first with the ask-ai plugin enabled."
        )
    return json.loads(index_path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/mkdocs-ask-ai && python -m pytest tests/test_mcp_index.py -v`
Expected: PASS

- [ ] **Step 5: Add test for `save_index()` merging**

```python
# append to tests/test_mcp_index.py

def test_save_index_merges_locales(tmp_path):
    """save_index merges locale data when called multiple times."""
    from mkdocs_ask_ai.mcp_index import save_index, load_index

    index_en = {
        "site_name": "Wiki",
        "site_url": "https://example.com",
        "default_locale": "en",
        "locales": {
            "en": {"sections": {"Docs": [{"title": "Home", "path": "index.md", "description": ""}]}}
        },
    }
    index_ru = {
        "site_name": "Wiki",
        "site_url": "https://example.com",
        "default_locale": "en",
        "locales": {
            "ru": {"sections": {"Docs": [{"title": "Главная", "path": "ru/index.md", "description": ""}]}}
        },
    }

    save_index(index_en, tmp_path)
    save_index(index_ru, tmp_path)

    merged = load_index(tmp_path)
    assert "en" in merged["locales"]
    assert "ru" in merged["locales"]
    assert merged["locales"]["en"]["sections"]["Docs"][0]["title"] == "Home"
    assert merged["locales"]["ru"]["sections"]["Docs"][0]["title"] == "Главная"
```

- [ ] **Step 6: Run full test suite**

Run: `cd plugins/mkdocs-ask-ai && python -m pytest tests/test_mcp_index.py -v`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/mkdocs_ask_ai/mcp_index.py tests/test_mcp_index.py
git commit -m "feat: add docs-index.json builder for MCP server"
```

---

### Task 2: Wire index builder into plugin

**Files:**
- Modify: `src/mkdocs_ask_ai/plugin.py` (add call in `on_post_build`)
- Modify: `src/mkdocs_ask_ai/config.py` (add `enable_mcp` config option)

- [ ] **Step 1: Add MCP config options to `config.py`**

Add after the existing config options:

```python
    # MCP server options
    enable_mcp = config_options.Type(bool, default=False)
    """Whether to generate docs-index.json for MCP server."""

    mcp_transport = config_options.Type(str, default="stdio")
    """MCP transport: 'stdio' or 'streamable-http'."""

    mcp_path = config_options.Type(str, default="/mcp")
    """URL path for streamable HTTP transport."""

    mcp_port = config_options.Type(int, default=8808)
    """Port for standalone streamable HTTP server."""
```

- [ ] **Step 2: Add index generation to `on_post_build` in `plugin.py`**

Add at the top of plugin.py imports:

```python
from .mcp_index import build_index, save_index
```

Add at the end of `on_post_build()`, after the existing generation calls:

```python
        # Generate docs-index.json for MCP server
        if self.config.enable_mcp:
            locale_prefix = self._detect_locale_prefix()
            default_locale = "en"
            # Try to get default locale from i18n plugin config
            for plugin_name, plugin_inst in config.plugins.items():
                if "i18n" in plugin_name and hasattr(plugin_inst, "config"):
                    default_locale = getattr(plugin_inst.config, "default_language", "en")
                    break

            index = build_index(
                pages_data=self.pages_data,
                site_name=config.site_name,
                site_url=config.site_url or "",
                default_locale=default_locale,
                locale_prefix=locale_prefix,
            )
            save_index(index, site_dir)
```

- [ ] **Step 3: Verify build works**

Run: `cd /Volumes/storage/Projects/Git/Gitlab/homelab-am/wiki/wiki.homelab.am && .venv/bin/mkdocs build --strict 2>&1 | tail -5`
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add src/mkdocs_ask_ai/config.py src/mkdocs_ask_ai/plugin.py
git commit -m "feat: wire docs-index.json generation into plugin build"
```

---

## Chunk 2: MCP Server

### Task 3: Create `mcp_server.py` — FastMCP server with tools and resources

**Files:**
- Create: `src/mkdocs_ask_ai/mcp_server.py`
- Test: `tests/test_mcp_server.py`

- [ ] **Step 1: Write tests for MCP server tools**

```python
# tests/test_mcp_server.py
"""Tests for the MCP server tools."""

import json
from pathlib import Path

import pytest

# Skip all tests if mcp SDK is not installed
mcp = pytest.importorskip("mcp")

from mkdocs_ask_ai.mcp_server import create_server


@pytest.fixture
def site_dir(tmp_path):
    """Create a minimal built site with docs-index.json and .md files."""
    index = {
        "site_name": "Test Wiki",
        "site_url": "https://test.example.com",
        "default_locale": "en",
        "locales": {
            "en": {
                "sections": {
                    "Infrastructure": [
                        {"title": "Proxmox", "path": "infrastructure/proxmox/index.md", "description": "Proxmox VE docs"},
                        {"title": "Docker Host", "path": "infrastructure/docker/index.md", "description": "Docker docs"},
                    ],
                    "Services": [
                        {"title": "Traefik", "path": "services/traefik/index.md", "description": "Reverse proxy"},
                    ],
                }
            },
            "ru": {
                "sections": {
                    "Infrastructure": [
                        {"title": "Proxmox", "path": "ru/infrastructure/proxmox/index.md", "description": ""},
                    ],
                }
            },
        },
    }
    (tmp_path / "docs-index.json").write_text(json.dumps(index), encoding="utf-8")

    # Create .md files
    for path_str in [
        "infrastructure/proxmox/index.md",
        "infrastructure/docker/index.md",
        "services/traefik/index.md",
        "ru/infrastructure/proxmox/index.md",
    ]:
        p = tmp_path / path_str
        p.parent.mkdir(parents=True, exist_ok=True)

    (tmp_path / "infrastructure/proxmox/index.md").write_text(
        "# Proxmox VE\n\nProxmox Virtual Environment is an open-source server virtualization platform.\n\n## Installation\n\nDownload the ISO from proxmox.com.",
        encoding="utf-8",
    )
    (tmp_path / "infrastructure/docker/index.md").write_text(
        "# Docker Host\n\nLXC 115 running Docker with Portainer.",
        encoding="utf-8",
    )
    (tmp_path / "services/traefik/index.md").write_text(
        "# Traefik\n\nReverse proxy with automatic TLS via Let's Encrypt.",
        encoding="utf-8",
    )
    (tmp_path / "ru/infrastructure/proxmox/index.md").write_text(
        "# Proxmox VE\n\nПлатформа виртуализации серверов с открытым исходным кодом.",
        encoding="utf-8",
    )

    # Create llms.txt and llms-full.txt
    (tmp_path / "llms.txt").write_text("# Test Wiki\n\n## Infrastructure\n\n- [Proxmox](index.md)", encoding="utf-8")
    (tmp_path / "llms-full.txt").write_text("# Test Wiki\n\nFull docs content here.", encoding="utf-8")

    return tmp_path


@pytest.fixture
def server(site_dir):
    return create_server(site_dir)


class TestListPages:
    async def test_list_pages_default_locale(self, server, site_dir):
        """list_pages returns pages for default locale."""
        from mcp_server import _list_pages_impl
        # We'll test the implementation function directly
        pass


class TestGetPage:
    def test_placeholder(self):
        """Placeholder — actual tests use MCP client session."""
        pass
```

Note: Testing MCP tools properly requires calling them through the MCP protocol. We'll write simpler unit tests for the internal functions and integration tests using the MCP Inspector later. Let's focus on the implementation functions.

- [ ] **Step 2: Implement `mcp_server.py`**

```python
# src/mkdocs_ask_ai/mcp_server.py
"""MCP server for mkdocs-ask-ai.

Exposes documentation as MCP tools and resources so AI agents can
query the docs programmatically.

Requires: pip install mkdocs-ask-ai[mcp]
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "MCP SDK not installed. Install with: pip install mkdocs-ask-ai[mcp]"
    )

from .mcp_index import load_index


def create_server(site_dir: Path) -> FastMCP:
    """Create and configure the MCP server for a built site.

    Args:
        site_dir: Path to the built MkDocs site (contains docs-index.json).

    Returns:
        Configured FastMCP instance ready to run.
    """
    site_dir = Path(site_dir)
    index = load_index(site_dir)
    site_name = index["site_name"]
    default_locale = index["default_locale"]
    available_locales = list(index["locales"].keys())

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

        # If locale is non-default and path doesn't start with locale prefix,
        # prepend it
        if loc != default_locale and not path.startswith(f"{loc}/"):
            full_path = f"{loc}/{path}"
        else:
            full_path = path

        md_file = site_dir / full_path
        if not md_file.exists():
            # Try without locale prefix as fallback
            md_file = site_dir / path
        if not md_file.exists():
            # Suggest similar paths
            all_paths = _get_all_paths(index, loc)
            suggestions = [p for p in all_paths if _fuzzy_match(path, p)][:5]
            msg = f"Page not found: {path}"
            if suggestions:
                msg += f"\n\nDid you mean:\n" + "\n".join(f"  - {s}" for s in suggestions)
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
            return {"error": f"Locale '{loc}' not found.", "available_locales": available_locales}

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

                # Count term occurrences
                score = sum(content_lower.count(term) for term in query_terms)
                if score == 0:
                    continue

                # Extract snippet around first match
                snippet = _extract_snippet(content, query_terms)

                results.append({
                    "title": page["title"],
                    "path": page["path"],
                    "section": section_name,
                    "snippet": snippet,
                    "score": score,
                })

        # Sort by score descending
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

        # Try locale-specific llms-full.txt first
        if loc != default_locale:
            full_path = site_dir / loc / "llms-full.txt"
        else:
            full_path = site_dir / "llms-full.txt"

        if full_path.exists():
            return full_path.read_text(encoding="utf-8")

        # Fallback: build from index
        if loc not in index["locales"]:
            return f"Locale '{loc}' not found. Available: {', '.join(available_locales)}"

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
    for loc, locale_data in index["locales"].items():
        for section_name, pages in locale_data["sections"].items():
            for page in pages:
                _path = page["path"]
                _title = page["title"]

                @mcp.resource(f"docs://{site_name}/{_path}", name=f"{_title} ({loc})", mime_type="text/markdown")
                def _read_page(_bound_path=_path) -> str:
                    md_file = site_dir / _bound_path
                    if md_file.exists():
                        return md_file.read_text(encoding="utf-8")
                    return f"Page not found: {_bound_path}"

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
        return content[:context_chars * 2] + "..."

    start = max(0, earliest_pos - context_chars)
    end = min(len(content), earliest_pos + context_chars)
    snippet = content[start:end].strip()

    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    return snippet
```

- [ ] **Step 3: Write unit tests for helper functions**

```python
# tests/test_mcp_server.py
"""Tests for MCP server helper functions."""

import json
from pathlib import Path

import pytest


# Test helper functions that don't require the MCP SDK
class TestHelpers:
    def test_fuzzy_match(self):
        from mkdocs_ask_ai.mcp_server import _fuzzy_match
        assert _fuzzy_match("proxmox", "infrastructure/proxmox/index.md")
        assert _fuzzy_match("docker", "infrastructure/docker-host/index.md")
        assert not _fuzzy_match("zzzzz", "infrastructure/proxmox/index.md")

    def test_extract_snippet(self):
        from mkdocs_ask_ai.mcp_server import _extract_snippet
        content = "A" * 200 + "KEYWORD" + "B" * 200
        snippet = _extract_snippet(content, ["keyword"], context_chars=50)
        assert "KEYWORD" in snippet
        assert snippet.startswith("...")
        assert snippet.endswith("...")

    def test_get_all_paths(self):
        from mkdocs_ask_ai.mcp_server import _get_all_paths
        index = {
            "locales": {
                "en": {
                    "sections": {
                        "Docs": [
                            {"path": "a.md", "title": "A"},
                            {"path": "b.md", "title": "B"},
                        ]
                    }
                }
            }
        }
        paths = _get_all_paths(index, "en")
        assert paths == ["a.md", "b.md"]
        assert _get_all_paths(index, "fr") == []
```

- [ ] **Step 4: Run tests**

Run: `cd plugins/mkdocs-ask-ai && python -m pytest tests/ -v`
Expected: all PASS (MCP SDK tests skip gracefully if not installed)

- [ ] **Step 5: Commit**

```bash
git add src/mkdocs_ask_ai/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add MCP server with tools and resources"
```

---

### Task 4: Create CLI entry point

**Files:**
- Create: `src/mkdocs_ask_ai/cli.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Implement `cli.py`**

```python
# src/mkdocs_ask_ai/cli.py
"""CLI entry point for mkdocs-ask-ai MCP server."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="mkdocs-ask-ai",
        description="MkDocs Ask AI — LLM-friendly documentation tools",
    )
    subparsers = parser.add_subparsers(dest="command")

    # mcp subcommand
    mcp_parser = subparsers.add_parser("mcp", help="Start MCP server for documentation")
    mcp_parser.add_argument(
        "--site-dir",
        type=Path,
        default=Path("public"),
        help="Path to built MkDocs site directory (default: ./public)",
    )
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=8808,
        help="Port for HTTP transport (default: 8808)",
    )
    mcp_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transport (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    if args.command == "mcp":
        _run_mcp(args)
    else:
        parser.print_help()
        sys.exit(1)


def _run_mcp(args):
    try:
        from .mcp_server import create_server
    except ImportError:
        print("Error: MCP SDK not installed. Install with: pip install mkdocs-ask-ai[mcp]", file=sys.stderr)
        sys.exit(1)

    if not args.site_dir.exists():
        print(f"Error: Site directory not found: {args.site_dir}", file=sys.stderr)
        print("Run 'mkdocs build' first.", file=sys.stderr)
        sys.exit(1)

    server = create_server(args.site_dir)

    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add console_scripts and optional dependency to pyproject.toml**

Add to `[project]` section:

```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]

[project.scripts]
mkdocs-ask-ai = "mkdocs_ask_ai.cli:main"
```

- [ ] **Step 3: Reinstall package in editable mode to register CLI**

Run: `cd /Volumes/storage/Projects/Git/Gitlab/homelab-am/wiki/wiki.homelab.am && .venv/bin/pip install -e "plugins/mkdocs-ask-ai[mcp]"`
Expected: installs successfully, `mkdocs-ask-ai` CLI available

- [ ] **Step 4: Verify CLI**

Run: `cd /Volumes/storage/Projects/Git/Gitlab/homelab-am/wiki/wiki.homelab.am && .venv/bin/mkdocs-ask-ai --help`
Expected: shows help with `mcp` subcommand

- [ ] **Step 5: Commit**

```bash
git add src/mkdocs_ask_ai/cli.py pyproject.toml
git commit -m "feat: add CLI entry point for MCP server"
```

---

## Chunk 3: Integration and Release

### Task 5: End-to-end test

- [ ] **Step 1: Build the wiki with MCP enabled**

Add `enable_mcp: true` to mkdocs.yml ask-ai config, then:

Run: `.venv/bin/mkdocs build --strict`
Expected: build succeeds, `public/docs-index.json` exists

- [ ] **Step 2: Verify docs-index.json content**

Run: `cat public/docs-index.json | python3 -m json.tool | head -30`
Expected: valid JSON with both `en` and `ru` locales

- [ ] **Step 3: Test MCP server with Inspector**

Run: `npx @modelcontextprotocol/inspector .venv/bin/mkdocs-ask-ai mcp --site-dir ./public`

Verify:
- `list_pages` returns EN sections
- `list_pages(locale="ru")` returns RU sections
- `get_page("infrastructure/proxmox/index.md")` returns markdown
- `search_docs("proxmox")` returns results with snippets
- `get_full_docs()` returns full concatenated docs
- Resources tab shows all pages

- [ ] **Step 4: Commit final config**

```bash
git add mkdocs.yml
git commit -m "feat: enable MCP server in wiki config"
```

### Task 6: Bump version and publish

- [ ] **Step 1: Update version to 1.1.0**

In `pyproject.toml`: `version = "1.1.0"`
In `src/mkdocs_ask_ai/__init__.py`: `__version__ = "1.1.0"`

- [ ] **Step 2: Build and publish to PyPI**

```bash
cd plugins/mkdocs-ask-ai
rm -rf dist/
pyproject-build
twine upload dist/* -u __token__
```

- [ ] **Step 3: Update wiki requirements.txt**

Change to: `mkdocs-ask-ai[mcp]==1.1.0`

- [ ] **Step 4: Push plugin to GitHub, wiki to GitLab**

```bash
cd plugins/mkdocs-ask-ai && git push origin main
cd ../.. && git add -A && git commit -m "feat: enable MCP server, bump mkdocs-ask-ai to 1.1.0" && git push origin main
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/mkdocs_ask_ai/__init__.py
git commit -m "release: v1.1.0 — MCP server support"
```
