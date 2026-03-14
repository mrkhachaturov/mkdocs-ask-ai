# mkdocs-ask-ai — Claude Context

## What This Is

MkDocs plugin for AI-ready documentation. Published on PyPI as `mkdocs-ask-ai`.

## Repo Structure

```
src/mkdocs_ask_ai/
├── __init__.py       ← version string (must stay in sync with pyproject.toml)
├── config.py         ← MkDocs plugin config options (includes deprecated copy_button_* — do NOT remove)
├── plugin.py         ← main MkDocs plugin (hooks, AI menu, llms.txt generation)
├── mcp_index.py      ← docs-index.json builder
├── mcp_server.py     ← FastMCP server (tools + resources)
└── cli.py            ← CLI entry point: `mkdocs-ask-ai mcp` starts the MCP server
tests/                ← pytest unit tests (mcp_index + mcp_server helpers)
test-site/            ← fixture MkDocs site used by CI smoke tests (not real user docs)
docs/                 ← internal design artifacts (specs, plans) — tracked in git
.artifacts/           ← local AI planning output — gitignored, never commit
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

- Version must be updated in BOTH `pyproject.toml` AND `src/mkdocs_ask_ai/__init__.py`
- MCP SDK is an optional dependency — all `mcp.*` imports must stay inside the `_HAS_MCP` guard or inside `create_server()`
- Plugin supports Python 3.9+; MCP features require 3.10+ (guarded by `[mcp]` extra)
- `config.py` has deprecated options (`enable_copy_button`, `copy_button_text`, `copy_button_position`, `copy_button_style`) — keep them for backwards compatibility, do not remove
- `test-site/` is a CI fixture, not user-facing documentation — do not edit it as real content
- Pre-commit hooks run ruff lint + format on every commit

## Superpowers Overrides

Plans: .artifacts/plans/YYYY-MM-DD-<feature-name>.md
Specs: .artifacts/specs/YYYY-MM-DD-<topic>-design.md
