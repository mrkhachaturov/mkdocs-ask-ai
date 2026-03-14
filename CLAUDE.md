# mkdocs-ask-ai — Claude Context

## What This Is

MkDocs plugin for AI-ready documentation. Published on PyPI as `mkdocs-ask-ai`.

## Repo Structure

```
src/mkdocs_ask_ai/
├── __init__.py       ← version string
├── config.py         ← MkDocs plugin config options
├── plugin.py         ← main MkDocs plugin (hooks, AI menu, llms.txt generation)
├── mcp_index.py      ← docs-index.json builder
├── mcp_server.py     ← FastMCP server (tools + resources)
└── cli.py            ← CLI entry point (mkdocs-ask-ai mcp)
tests/                ← pytest tests
```

## Development

```bash
make install-dev      # editable install with dev + mcp extras
make check            # lint + format check + tests
make lint             # ruff check --fix
make format           # ruff format
make test             # pytest
```

## Release

Use the `/release` skill — it bumps version, tags, and pushes to trigger
automated PyPI publishing via GitHub Actions trusted publishing.

## Key Rules

- Version must be updated in BOTH `pyproject.toml` and `src/mkdocs_ask_ai/__init__.py`
- MCP SDK is an optional dependency — guard imports with `_HAS_MCP` flag
- Plugin supports Python 3.9+, MCP features require 3.10+
- Pre-commit hooks run ruff lint + format on every commit
