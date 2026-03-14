---
paths:
  - src/mkdocs_ask_ai/mcp_server.py
  - src/mkdocs_ask_ai/mcp_index.py
---

- All MCP SDK imports must stay inside the `_HAS_MCP` guard or inside `create_server()`. Never import from `mcp.*` at module top-level.
- `FastMCP` comes from `mcp.server.fastmcp` — do not switch to other MCP server classes without verifying the mcp>=1.0.0 API.
- `get_page()` builds file paths from user input (`path` argument). Before any HTTP-exposed deployment, add a containment check: `assert resolved.is_relative_to(site_dir)`.
- MCP files may use Python 3.10+ syntax (they require the `[mcp]` extra which implies 3.10+).
