"""Tests for MCP server helper functions."""

import json
from pathlib import Path

import pytest


class TestHelpers:
    def test_fuzzy_match(self):
        from mkdocs_ask_ai.mcp_server import _fuzzy_match
        assert _fuzzy_match("proxmox", "infrastructure/proxmox/index.md")
        assert _fuzzy_match("docker", "infrastructure/docker-host/index.md")
        assert not _fuzzy_match("zzzzz", "infrastructure/proxmox/index.md")

    def test_extract_snippet(self):
        from mkdocs_ask_ai.mcp_server import _extract_snippet
        content = "A" * 200 + "KEYWORD" + "B" * 200
        snippet = _extract_snippet(content, ["keyword"], context_chars=50)
        assert "KEYWORD" in snippet
        assert snippet.startswith("...")
        assert snippet.endswith("...")

    def test_get_all_paths(self):
        from mkdocs_ask_ai.mcp_server import _get_all_paths
        index = {
            "locales": {
                "en": {
                    "sections": {
                        "Docs": [
                            {"path": "a.md", "title": "A"},
                            {"path": "b.md", "title": "B"},
                        ]
                    }
                }
            }
        }
        paths = _get_all_paths(index, "en")
        assert paths == ["a.md", "b.md"]
        assert _get_all_paths(index, "fr") == []
