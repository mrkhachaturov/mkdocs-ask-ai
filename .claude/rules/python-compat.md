---
paths:
  - src/**/*.py
  - tests/**/*.py
---

- Target Python 3.9+. Do NOT use:
  - `match` / `case` statements (3.10+)
  - `X | Y` union type syntax in annotations — use `Union[X, Y]` or `Optional[X]`
  - `dict | None` parameter defaults
  - `tomllib` (stdlib only in 3.11+ — use `tomli` or avoid)
  - `str.removeprefix` / `str.removesuffix` without a fallback
- Exception: `mcp_server.py` and `cli.py` may use 3.10+ syntax since they are gated behind the `[mcp]` extra.
- Always check the CI matrix (`python-version` in `.github/workflows/`) before using any stdlib feature added after 3.9.
