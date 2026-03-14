# mkdocs-ask-ai

[![PyPI version](https://img.shields.io/pypi/v/mkdocs-ask-ai?color=%2334D058&label=pypi)](https://pypi.org/project/mkdocs-ask-ai/)
[![Python versions](https://img.shields.io/pypi/pyversions/mkdocs-ask-ai)](https://pypi.org/project/mkdocs-ask-ai/)
[![Downloads](https://img.shields.io/pypi/dm/mkdocs-ask-ai?color=blue&label=downloads)](https://pypi.org/project/mkdocs-ask-ai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MkDocs](https://img.shields.io/badge/mkdocs-%E2%89%A51.4-blue?logo=markdown)](https://www.mkdocs.org)
[![Material](https://img.shields.io/badge/material-%E2%9C%93-blueviolet?logo=materialdesign)](https://squidfunk.github.io/mkdocs-material/)
[![MCP](https://img.shields.io/badge/MCP-compatible-orange?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0wIDE4Yy00LjQyIDAtOC0zLjU4LTgtOHMzLjU4LTggOC04IDggMy41OCA4IDgtMy41OCA4LTggOHoiLz48L3N2Zz4=)](https://modelcontextprotocol.io/)
[![llms.txt](https://img.shields.io/badge/llms.txt-supported-yellow)](https://llmstxt.org/)

Make your MkDocs documentation AI-ready. One plugin gives your site everything AI tools need to work with your docs — a "Use with AI" menu for visitors, `llms.txt` for crawlers, an MCP server for agents, and raw markdown URLs for everything else.

Works with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n) out of the box.

https://github.com/user-attachments/assets/b6a26956-c54c-4fcb-9d59-e58626a37786

---

## ✨ Features

### 🤖 "Use with AI" Dropdown

A floating button on every page with:

- **Copy page as Markdown** — one-click clipboard copy for any AI tool
- **View as Markdown** — opens the clean `.md` source in a new tab
- **Open in ChatGPT / Open in Claude**
  > Fetches the full page markdown and sends it directly into the chat — not a link. The AI gets the content immediately, no crawling required, works on private or uncrawlable sites. Pages over 7,500 characters are truncated with a link back to the full `.md` source so the AI can retrieve the rest.
- **llms.txt** — link to the full documentation index

Adapts to light and dark themes automatically. Inspired by [1Password's developer docs](https://developer.1password.com).

### 📄 llms.txt + llms-full.txt

Follows the [llms.txt standard](https://llmstxt.org/) to make your documentation discoverable by AI systems:

- **`llms.txt`** — structured index with sections, titles, and links to markdown sources
- **`llms-full.txt`** — complete documentation in a single file for full-context queries

### 🔗 Direct Markdown Serving

Every page is accessible as clean markdown at its `.md` URL. No HTML parsing needed — AI tools get exactly what they need.

```
https://your-site.com/getting-started/index.md
```

### ⚡ MCP Server

Expose your documentation as an [MCP](https://modelcontextprotocol.io/) server so AI agents can query it programmatically.

| Tool | Description |
|------|-------------|
| `list_pages(locale?)` | Discover available pages grouped by section |
| `get_page(path, locale?)` | Fetch a specific page as markdown |
| `search_docs(query, locale?)` | Full-text search with snippets |
| `get_full_docs(locale?)` | Get the entire documentation as one text |

| Transport | Use case |
|-----------|----------|
| `stdio` | Local tools — Claude Desktop, Cursor, Windsurf |
| `sse` / `http` | Public websites — `https://your-site.com/mcp` |

Every page is also registered as an MCP resource (`docs://site-name/path/to/page.md`).

### 🌍 i18n Support

Full support for multilingual sites via `mkdocs-static-i18n`. Each locale gets its own `llms.txt`, `llms-full.txt`, markdown URLs, and MCP tools with a `locale` parameter.

---

## 🚀 Installation & Quick Start

```bash
pip install mkdocs-ask-ai
```

With MCP server support:

```bash
pip install mkdocs-ask-ai[mcp]
```

Add to your `mkdocs.yml`:

```yaml
plugins:
  - ask-ai:
      sections:
        "Getting Started":
          - index.md: "Introduction"
          - quickstart.md: "Quick start guide"
        "API Reference":
          - api/*.md
```

Your site now has a **"Use with AI"** dropdown on every page, `llms.txt` and `llms-full.txt` at the root, and a `.md` URL for every page.

---

## ⚙️ Configuration

### Basic Options

```yaml
plugins:
  - ask-ai:
      sections: {}                      # Section names mapped to file patterns (glob supported)
      markdown_description: ""          # Description included in llms.txt header
      enable_ai_menu: true              # Show "Use with AI" dropdown
      ai_menu_button_text: "Use with AI"
      enable_chatgpt: true              # Show "Open in ChatGPT" item
      enable_claude: true               # Show "Open in Claude" item
      enable_markdown_urls: true        # Serve .md files alongside HTML
      enable_llms_txt: true             # Generate llms.txt
      enable_llms_full: true            # Generate llms-full.txt
```

### MCP Options

```yaml
plugins:
  - ask-ai:
      enable_mcp: true                  # Enable MCP server + docs-index.json
      mcp_path: "/mcp"                  # URL path for streamable HTTP
      mcp_port: 8808                    # Port for MCP HTTP server
```

### Section Patterns

Sections support explicit paths, descriptions, and glob patterns:

```yaml
sections:
  "Infrastructure":
    - infrastructure/index.md: "Infrastructure overview"
    - infrastructure/proxmox.md: "Proxmox hypervisor"
    - infrastructure/*.md              # glob — include all .md files
  "API":
    - api/*.md
```

---

## 🔌 MCP Server Setup

### With `mkdocs serve` (development)

When `enable_mcp: true` is set, the MCP server starts automatically alongside the dev server at `http://127.0.0.1:8808/mcp`. Add to your `.mcp.json` or Claude Desktop config:

```json
{
  "mcpServers": {
    "my-docs": {
      "type": "sse",
      "url": "http://127.0.0.1:8808/sse"
    }
  }
}
```

### With Claude Desktop / Cursor (stdio)

Build your site first, then point to the output directory:

```json
{
  "mcpServers": {
    "my-docs": {
      "command": "mkdocs-ask-ai",
      "args": ["mcp", "--site-dir", "./public"]
    }
  }
}
```

> If `mkdocs-ask-ai` is installed in a virtualenv, use the full path to the binary (e.g. `/path/to/.venv/bin/mkdocs-ask-ai`).

### Standalone HTTP Server

```bash
mkdocs-ask-ai mcp --transport http --port 8808 --site-dir ./public
```

### CLI Reference

```bash
mkdocs-ask-ai mcp [OPTIONS]

Options:
  --site-dir PATH              Built site directory (default: ./public)
  --transport {stdio,http,sse} Transport type (default: stdio)
  --port PORT                  HTTP/SSE port (default: 8808)
  --host HOST                  HTTP/SSE host (default: 127.0.0.1)
```

### Hosting

| Deployment | MCP support |
|------------|-------------|
| `mkdocs serve` | Automatic — starts alongside dev server |
| Self-hosted (Docker/VM) | Run `mkdocs-ask-ai mcp` as a sidecar service |
| Static hosting (GitHub Pages, GitLab Pages, Netlify) | Not supported — requires a running process |

> For static hosting, the "Use with AI" dropdown, `llms.txt`, and `.md` URLs all work out of the box. Only the MCP server requires a running process.

### With mkdocs-static-i18n

Place `ask-ai` **before** `i18n` in the plugins list:

```yaml
plugins:
  - ask-ai:
      sections:
        "Docs":
          - "*.md"
  - i18n:
      docs_structure: suffix
      languages:
        - locale: en
          default: true
          name: English
        - locale: ru
          name: Russian
```

Output per locale:

```
public/
  llms.txt              # English
  llms-full.txt
  docs-index.json       # merged index (all locales)
  ru/
    llms.txt            # Russian
    llms-full.txt
```

---

## License

MIT — see [LICENSE](LICENSE).

Originally inspired by [mkdocs-llmstxt-md](https://github.com/noklam/mkdocs-llmstxt-md) by Nok Lam Chan.
