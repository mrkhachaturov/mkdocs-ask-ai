# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-14

### Added
- Initial public release of mkdocs-ask-ai
- "Use with AI" dropdown menu on every page:
  - Copy page as Markdown
  - View as Markdown (raw `.md` in new tab)
  - Open in ChatGPT (sends content via `?q=` parameter)
  - Open in Claude (sends content via `?q=` parameter)
  - Link to `llms.txt` index
- Generate `llms.txt` index file with markdown URLs
- Generate `llms-full.txt` with complete documentation
- Serve original markdown at `.md` URLs alongside HTML
- Full `mkdocs-static-i18n` support (suffix structure):
  - Per-locale `llms.txt` and `llms-full.txt` output
  - Automatic locale detection from page dest paths
  - Locale-suffixed file matching (e.g. `page.ru.md`)
- Material for MkDocs theme integration (dark/light mode)
- Configurable sections with glob patterns and descriptions
- Long content truncation with link to full `.md` source

[0.3.0]: https://github.com/mrkhachaturov/mkdocs-ask-ai/releases/tag/v0.3.0
