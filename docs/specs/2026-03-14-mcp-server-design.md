# MCP Server Integration for mkdocs-ask-ai

**Date:** 2026-03-14
**Status:** Approved

## Problem

AI tools (Claude Desktop, Cursor, Windsurf, etc.) need programmatic access to
documentation sites. Currently, mkdocs-ask-ai generates static files (llms.txt,
llms-full.txt, .md URLs) that work for browser-based interaction. There is no
way for an AI agent to connect to the documentation via MCP and query it
directly.

## Solution

Add an MCP server to the mkdocs-ask-ai plugin that exposes documentation as
MCP tools and resources. It supports two transports depending on the deployment:

| Use case | Transport | How it runs |
|---|---|---|
| Private / local docs | stdio | `mkdocs-ask-ai mcp --site-dir ./public` |
| Public website | Streamable HTTP | Alongside `mkdocs serve` or standalone at a configurable path |

## Configuration

```yaml
# mkdocs.yml
plugins:
  - ask-ai:
      enable_mcp: false          # disabled by default
      mcp_transport: "stdio"     # "stdio" or "streamable-http"
      mcp_path: "/mcp"           # URL path for streamable HTTP
      mcp_port: 8808             # port for standalone streamable HTTP
```

## MCP Tools

All tools accept an optional `locale` parameter (e.g. `"en"`, `"ru"`).
When omitted, defaults to the site's default locale.

### `list_pages(locale?)`

Returns the llms.txt index for the given locale — a structured list of all
documentation sections and pages with titles, paths, and descriptions.

**Use case:** Agent discovers what documentation is available before diving in.

**Returns:**
```json
{
  "site_name": "Homelab Wiki",
  "locale": "en",
  "sections": [
    {
      "name": "Infrastructure",
      "pages": [
        {"title": "Proxmox — pve01", "path": "infrastructure/proxmox/index.md", "description": "..."}
      ]
    }
  ],
  "available_locales": ["en", "ru"]
}
```

### `get_page(path, locale?)`

Fetches a single documentation page as clean markdown.

**Parameters:**
- `path` (required): Page path relative to docs root, e.g. `"infrastructure/proxmox/index.md"`
- `locale` (optional): Locale code

**Returns:** The full markdown content of the page.

**Error:** Returns actionable error if page not found, suggesting similar paths.

### `search_docs(query, locale?)`

Full-text search across all documentation pages within a locale.

**Parameters:**
- `query` (required): Search string
- `locale` (optional): Locale code to search within

**Returns:**
```json
{
  "query": "proxmox",
  "locale": "en",
  "results": [
    {
      "title": "Proxmox — pve01",
      "path": "infrastructure/proxmox/index.md",
      "snippet": "...matching text with context...",
      "score": 0.95
    }
  ],
  "total": 3
}
```

### `get_full_docs(locale?)`

Returns the complete documentation content (llms-full.txt equivalent) for a
locale. Useful when the agent needs comprehensive context.

**Parameters:**
- `locale` (optional): Locale code

**Returns:** Full concatenated markdown of all pages, structured by sections.

## MCP Resources

Each documentation page is exposed as an MCP resource:

- **URI pattern:** `docs://{site_name}/{locale}/{path}`
- **Examples:**
  - `docs://homelab-wiki/en/infrastructure/proxmox/index.md`
  - `docs://homelab-wiki/ru/services/index.md`
- **MIME type:** `text/markdown`

The resource list is dynamically built from the plugin's `sections` config and
the pages discovered during the MkDocs build.

## i18n Support

The MCP server is fully locale-aware:

1. **Locale detection:** Reads available locales from the built site structure
   (presence of locale subdirectories like `ru/`, `de/`).
2. **Default locale:** Derived from MkDocs i18n config or falls back to `"en"`.
3. **Per-tool filtering:** Each tool filters pages by the requested locale.
4. **Locale discovery:** `list_pages` includes `available_locales` so agents
   know which locales exist.

## Architecture

### File structure

```
src/mkdocs_ask_ai/
├── __init__.py
├── config.py          # add MCP config options
├── plugin.py          # existing plugin, adds MCP lifecycle hooks
├── mcp_server.py      # MCP server implementation
└── mcp_index.py       # documentation index (shared between plugin and MCP)
```

### Data flow

```
mkdocs build
    │
    ▼
plugin.on_post_build()
    │
    ├── generates llms.txt, llms-full.txt, .md files (existing)
    └── writes docs-index.json to site_dir (new)
            │
            ▼
MCP server reads docs-index.json + .md files from site_dir
    │
    ├── stdio: reads from built site directory
    └── streamable-http: serves at configured path
```

### docs-index.json

A JSON file generated during build that the MCP server reads. Contains the
structured index of all pages, sections, and locales:

```json
{
  "site_name": "Homelab Wiki",
  "site_url": "https://wiki.homelab.am",
  "default_locale": "en",
  "locales": {
    "en": {
      "sections": {
        "Infrastructure": [
          {
            "title": "Proxmox — pve01",
            "path": "infrastructure/proxmox/index.md",
            "description": "Proxmox hypervisor documentation"
          }
        ]
      }
    },
    "ru": {
      "sections": {
        "Infrastructure": [
          {
            "title": "Proxmox — pve01",
            "path": "ru/infrastructure/proxmox/index.md",
            "description": ""
          }
        ]
      }
    }
  }
}
```

### Search implementation

Simple substring/keyword search over the markdown files on disk. No external
search engine dependency. For each match, extract a snippet with surrounding
context. Rank results by number of query term occurrences.

This is intentionally simple — the documentation corpus is small enough that
in-memory search is fast and sufficient. Can be upgraded to full-text indexing
later if needed.

## CLI Entry Points

Add a CLI command via the `console_scripts` entry point in pyproject.toml:

```bash
# stdio mode — for Claude Desktop, Cursor, etc.
mkdocs-ask-ai mcp --site-dir ./public

# streamable HTTP — standalone server
mkdocs-ask-ai mcp --transport http --port 8808 --site-dir ./public
```

**Claude Desktop config example:**
```json
{
  "mcpServers": {
    "homelab-wiki": {
      "command": "mkdocs-ask-ai",
      "args": ["mcp", "--site-dir", "/path/to/public"]
    }
  }
}
```

**Remote MCP (streamable HTTP) — any MCP client:**
```
https://wiki.homelab.am/mcp
```

## Dependencies

MCP SDK added as an optional dependency:

```toml
[project.optional-dependencies]
mcp = ["mcp>=1.0.0"]
```

Install: `pip install mkdocs-ask-ai[mcp]`

The base plugin (llms.txt generation, AI menu) has no new dependencies.
MCP features are only available when the optional dependency is installed.

## Implementation Order

1. `mcp_index.py` — docs index builder, generates `docs-index.json`
2. Update `plugin.py` — call index builder in `on_post_build`
3. `mcp_server.py` — MCP server with all 4 tools + resources
4. Update `config.py` — add MCP config options
5. CLI entry point in `pyproject.toml`
6. Tests
7. README update

## Out of Scope

- Authentication / authorization (can be added later)
- Write operations (creating/editing docs via MCP)
- Real-time file watching (the MCP server reads the last build)
- WebSocket transport (streamable HTTP covers remote use cases)
