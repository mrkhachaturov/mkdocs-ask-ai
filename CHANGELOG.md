# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Demo video switched to GitHub-hosted URL (removed `assets/demo.mp4` binary from repo)

## [1.1.3] - 2026-03-14

Minor docs update — not a functional change.

### Changed
- README: added demo GIF and comparison table

## [1.1.2] - 2026-03-14

Minor internal tooling — no functional changes to the plugin.

### Changed
- Added `CLAUDE.md` and release skill for AI-assisted development

## [1.1.1] - 2026-03-14

### Fixed
- Lazy MCP SDK import for Python 3.9 compatibility
- CI: install `[mcp]` extra only on Python ≥ 3.10

## [1.1.0] - 2026-03-14

### Added
- MCP server (`mkdocs-ask-ai mcp`) — FastMCP server exposing docs as tools and resources
- CLI entry point for starting the MCP server
- `docs-index.json` builder for MCP server document indexing
- SSE transport support

## [0.3.0] - 2026-03-14

### Added
- Initial public release
- "Use with AI" dropdown menu (Copy Markdown, View Markdown, Open in ChatGPT/Claude, link to `llms.txt`)
- `llms.txt` and `llms-full.txt` generation
- Serve original markdown at `.md` URLs
- `mkdocs-static-i18n` support with per-locale output
- Material for MkDocs theme integration
- Configurable sections with glob patterns

[Unreleased]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.3...HEAD
[1.1.3]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/mrkhachaturov/mkdocs-ask-ai/releases/tag/v1.1.0
[0.3.0]: https://github.com/mrkhachaturov/mkdocs-ask-ai/releases/tag/v0.3.0
