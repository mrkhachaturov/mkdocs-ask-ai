# mkdocs-ask-ai

MkDocs plugin that makes your documentation AI-friendly:

- **"Use with AI" dropdown** — Copy markdown, open in ChatGPT/Claude, view raw `.md`
- **llms.txt / llms-full.txt** — LLM-optimized documentation indexes
- **Direct markdown serving** — Access source markdown at `.md` URLs
- **i18n support** — Per-locale output with `mkdocs-static-i18n`

## Installation

```bash
pip install mkdocs-ask-ai
```

## Quick Start

Add to your `mkdocs.yml`:

```yaml
plugins:
  - ask-ai:
      sections:
        "Getting Started":
          - index.md: "Introduction"
          - quickstart.md
        "API Reference":
          - api/*.md
```

Every page gets a "Use with AI" button with:

- **Copy page as Markdown** — clipboard copy for any AI tool
- **View as Markdown** — opens `.md` source in a new tab
- **Open in ChatGPT** — sends page content directly to ChatGPT
- **Open in Claude** — sends page content directly to Claude
- **llms.txt** — link to the full documentation index

## With mkdocs-static-i18n

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
          name: Русский
```

Generates separate outputs per locale:
- `site/llms.txt` + `site/llms-full.txt` (default locale)
- `site/ru/llms.txt` + `site/ru/llms-full.txt` (additional locales)

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `sections` | `{}` | Section names mapped to file patterns |
| `enable_ai_menu` | `true` | Show "Use with AI" dropdown on pages |
| `ai_menu_button_text` | `"Use with AI"` | Dropdown trigger text |
| `enable_chatgpt` | `true` | Show "Open in ChatGPT" item |
| `enable_claude` | `true` | Show "Open in Claude" item |
| `enable_markdown_urls` | `true` | Serve `.md` files alongside HTML |
| `enable_llms_txt` | `true` | Generate `llms.txt` |
| `enable_llms_full` | `true` | Generate `llms-full.txt` |
| `markdown_description` | — | Description included in `llms.txt` |

## License

MIT — see [LICENSE](LICENSE).
