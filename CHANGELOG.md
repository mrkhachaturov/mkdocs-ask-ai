# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2026-03-14

### Added
- SSE transport support for MCP server — compatible with Claude Code, browser-based clients, and any SSE-capable MCP client
- MCP server now starts automatically alongside `mkdocs serve` when `enable_mcp: true`

## [1.1.1] - 2026-03-14

### Fixed
- MCP SDK import moved inside `create_server()` so the plugin remains importable without the `[mcp]` extra — fixes Python 3.9 compatibility
- CI: `[mcp]` extra now only installed on Python ≥ 3.10

## [1.0.0] - 2026-03-14

### Added
- MCP server exposing documentation as tools and resources for AI agents
- Four MCP tools: `list_pages`, `get_page`, `search_docs`, `get_full_docs`
- Every page registered as an MCP resource (`docs://site-name/path/to/page.md`)
- CLI entry point: `mkdocs-ask-ai mcp` with stdio and streamable HTTP transports
- `docs-index.json` generated at build time for MCP server indexing
- Full i18n support: `locale` parameter on all MCP tools

[Unreleased]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.2...HEAD
[1.1.2]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/mrkhachaturov/mkdocs-ask-ai/compare/v1.0.0...v1.1.1
[1.0.0]: https://github.com/mrkhachaturov/mkdocs-ask-ai/releases/tag/v1.0.0
