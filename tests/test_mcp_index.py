import json
from pathlib import Path
from mkdocs_ask_ai.mcp_index import build_index, load_index, save_index


def test_build_index_single_locale(tmp_path):
    """Index builder produces correct structure for single-locale site."""
    pages_data = {
        "Infrastructure": [
            {
                "src_uri": "infrastructure/proxmox/index.md",
                "title": "Proxmox — pve01",
                "description": "Proxmox docs",
                "markdown": "# Proxmox\n\nContent here.",
                "dest_path": "infrastructure/proxmox/index.html",
                "dest_uri": "infrastructure/proxmox/index.html",
            }
        ],
        "Services": [],
    }

    result = build_index(
        pages_data=pages_data,
        site_name="Test Wiki",
        site_url="https://test.example.com",
        default_locale="en",
        locale_prefix="",
    )

    assert result["site_name"] == "Test Wiki"
    assert result["site_url"] == "https://test.example.com"
    assert result["default_locale"] == "en"
    assert "en" in result["locales"]
    infra = result["locales"]["en"]["sections"]["Infrastructure"]
    assert len(infra) == 1
    assert infra[0]["title"] == "Proxmox — pve01"
    assert infra[0]["path"] == "infrastructure/proxmox/index.md"
    assert "Services" not in result["locales"]["en"]["sections"]


def test_build_index_with_locale_prefix(tmp_path):
    """Index builder uses locale prefix for non-default locales."""
    pages_data = {
        "Infrastructure": [
            {
                "src_uri": "infrastructure/proxmox/index.md",
                "title": "Proxmox — pve01",
                "description": "",
                "markdown": "# Proxmox",
                "dest_path": "ru/infrastructure/proxmox/index.html",
                "dest_uri": "ru/infrastructure/proxmox/index.html",
            }
        ],
    }

    result = build_index(
        pages_data=pages_data,
        site_name="Test Wiki",
        site_url="https://test.example.com",
        default_locale="en",
        locale_prefix="ru",
    )

    assert "ru" in result["locales"]
    page = result["locales"]["ru"]["sections"]["Infrastructure"][0]
    assert page["path"] == "ru/infrastructure/proxmox/index.md"


def test_save_index_merges_locales(tmp_path):
    """save_index merges locale data when called multiple times."""
    index_en = {
        "site_name": "Wiki",
        "site_url": "https://example.com",
        "default_locale": "en",
        "locales": {
            "en": {"sections": {"Docs": [{"title": "Home", "path": "index.md", "description": ""}]}}
        },
    }
    index_ru = {
        "site_name": "Wiki",
        "site_url": "https://example.com",
        "default_locale": "en",
        "locales": {
            "ru": {"sections": {"Docs": [{"title": "Главная", "path": "ru/index.md", "description": ""}]}}
        },
    }

    save_index(index_en, tmp_path)
    save_index(index_ru, tmp_path)

    merged = load_index(tmp_path)
    assert "en" in merged["locales"]
    assert "ru" in merged["locales"]
    assert merged["locales"]["en"]["sections"]["Docs"][0]["title"] == "Home"
    assert merged["locales"]["ru"]["sections"]["Docs"][0]["title"] == "Главная"
