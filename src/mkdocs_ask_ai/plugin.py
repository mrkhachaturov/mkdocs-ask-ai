"""Main plugin class for the Ask AI MkDocs plugin."""

import fnmatch
import mimetypes
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .config import AskAiConfig

# Pattern to match i18n locale suffixed files (e.g. page.ru.md, page.de.md)
_I18N_SUFFIX_RE = re.compile(r"\.[a-z]{2,3}\.md$")


class LlmsTxtPlugin(BasePlugin[AskAiConfig]):
    """MkDocs plugin for LLM-friendly documentation."""

    def __init__(self):
        super().__init__()
        self.mkdocs_config: MkDocsConfig = None
        self.pages_data: Dict[str, List[Dict[str, Any]]] = {}
        self.source_files: Dict[str, str] = {}

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """Store MkDocs configuration and validate settings."""
        if not config.site_url:
            raise ValueError(
                "site_url must be set in MkDocs config for ask-ai plugin"
            )

        # Configure MIME type for .md files so they display in browser instead of downloading
        if self.config.enable_markdown_urls:
            mimetypes.add_type("text/plain", ".md")

        self.mkdocs_config = config
        self.pages_data = {section: [] for section in self.config.sections.keys()}
        return config

    def _is_i18n_alternate(self, src_path: str, files: Files) -> bool:
        """Check if a file is an i18n alternate (e.g. page.ru.md).

        These files are handled by the i18n plugin and should not be included
        directly in glob results — they result in broken URLs.
        """
        return bool(_I18N_SUFFIX_RE.search(src_path))

    def on_files(self, files: Files, *, config: MkDocsConfig) -> Files:
        """Process files and expand glob patterns in sections."""
        all_src_paths = [f.src_uri for f in files]

        # Expand glob patterns in sections configuration
        for section_name, file_patterns in self.config.sections.items():
            if isinstance(file_patterns, list):
                for pattern in file_patterns:
                    if isinstance(pattern, dict):
                        file_path = list(pattern.keys())[0]
                        description = list(pattern.values())[0]
                    else:
                        file_path = pattern
                        description = ""

                    # Handle glob patterns
                    if "*" in file_path:
                        matches = fnmatch.filter(all_src_paths, file_path)
                        for match in matches:
                            if self._is_i18n_alternate(match, files):
                                continue
                            if match not in [
                                p["src_uri"] for p in self.pages_data[section_name]
                            ]:
                                self.pages_data[section_name].append(
                                    {"src_uri": match, "description": description}
                                )
                    else:
                        if file_path in all_src_paths:
                            if file_path not in [
                                p["src_uri"] for p in self.pages_data[section_name]
                            ]:
                                self.pages_data[section_name].append(
                                    {"src_uri": file_path, "description": description}
                                )

        return files

    def on_page_markdown(
        self, markdown: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str:
        """Store original markdown content for later use."""
        src_uri = page.file.src_uri

        # For i18n: also try matching without locale suffix (e.g. page.ru.md -> page.md)
        src_uri_base = _I18N_SUFFIX_RE.sub(".md", src_uri)

        # Check if this page is in any of our sections
        for _section_name, page_list in self.pages_data.items():
            for page_data in page_list:
                if page_data["src_uri"] in (src_uri, src_uri_base):
                    dest_uri = page.file.dest_uri
                    # Skip pages with no dest_uri
                    if not dest_uri:
                        continue
                    self.source_files[src_uri] = markdown
                    page_data.update(
                        {
                            "title": page.title or src_uri,
                            "markdown": markdown,
                            "dest_path": page.file.dest_path,
                            "dest_uri": dest_uri,
                        }
                    )
                    break

        return markdown

    def on_page_content(
        self, html: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str:
        """Inject the 'Use with AI' dropdown menu if enabled."""
        if not self.config.enable_ai_menu:
            return html

        src_uri = page.file.src_uri
        if src_uri in self.source_files:
            menu_html = self._get_ai_menu_html(config)
            html += menu_html

        return html

    def _detect_locale_prefix(self) -> str:
        """Detect locale prefix from collected page dest_paths.

        If pages have dest_paths like 'ru/infrastructure/index.html',
        returns 'ru'. Returns '' for default locale (no prefix).
        """
        for section_pages in self.pages_data.values():
            for page_data in section_pages:
                dest_path = page_data.get("dest_path", "")
                if dest_path:
                    # Check if dest_path starts with a locale-like prefix (2-3 letter dir)
                    parts = Path(dest_path).parts
                    if len(parts) >= 2 and len(parts[0]) <= 3 and parts[0].isalpha():
                        return parts[0]
                    return ""
        return ""

    def _get_output_dir(self, config: MkDocsConfig) -> Path:
        """Get the output directory, accounting for i18n locale subdirectories."""
        site_dir = Path(config.site_dir)
        locale_prefix = self._detect_locale_prefix()
        if locale_prefix:
            locale_dir = site_dir / locale_prefix
            locale_dir.mkdir(parents=True, exist_ok=True)
            return locale_dir
        return site_dir

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        """Generate llms.txt, llms-full.txt, and markdown files."""
        output_dir = self._get_output_dir(config)
        site_dir = Path(config.site_dir)

        # Generate individual markdown files if markdown URLs are enabled
        if self.config.enable_markdown_urls:
            self._generate_markdown_files(site_dir)

        # Generate llms.txt
        if self.config.enable_llms_txt:
            self._generate_llms_txt(output_dir, config)

        # Generate llms-full.txt
        if self.config.enable_llms_full:
            self._generate_llms_full_txt(output_dir, config)

    def _generate_markdown_files(self, site_dir: Path) -> None:
        """Generate individual .md files for each page."""
        for section_pages in self.pages_data.values():
            for page_data in section_pages:
                if "markdown" in page_data and "dest_path" in page_data:
                    # Create .md version alongside HTML
                    html_path = Path(page_data["dest_path"])
                    md_path = site_dir / html_path.with_suffix(".md")

                    # Ensure directory exists
                    md_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write markdown content
                    md_path.write_text(page_data["markdown"], encoding="utf-8")

    def _generate_llms_txt(self, site_dir: Path, config: MkDocsConfig) -> None:
        """Generate the llms.txt index file."""
        llms_txt_path = site_dir / "llms.txt"

        content = f"# {config.site_name}\n\n"

        if config.site_description:
            content += f"> {config.site_description}\n\n"

        if self.config.markdown_description:
            content += f"{self.config.markdown_description}\n\n"

        base_url = config.site_url.rstrip("/")

        for section_name, pages in self.pages_data.items():
            if pages:  # Only add section if it has pages
                content += f"## {section_name}\n\n"

                for page_data in pages:
                    dest_uri = page_data.get("dest_uri", "")
                    if not dest_uri:
                        continue
                    title = page_data.get("title", page_data["src_uri"])
                    description = page_data.get("description", "")

                    # Create markdown URL
                    md_url = urljoin(
                        base_url + "/",
                        dest_uri.replace(".html", ".md")
                        if dest_uri.endswith(".html")
                        else dest_uri + ".md",
                    )

                    desc_text = f": {description}" if description else ""
                    content += f"- [{title}]({md_url}){desc_text}\n"

                content += "\n"

        llms_txt_path.write_text(content.strip(), encoding="utf-8")

    def _generate_llms_full_txt(self, site_dir: Path, config: MkDocsConfig) -> None:
        """Generate the llms-full.txt complete documentation file."""
        llms_full_path = site_dir / "llms-full.txt"

        content = f"# {config.site_name}\n\n"

        if config.site_description:
            content += f"> {config.site_description}\n\n"

        if self.config.markdown_description:
            content += f"{self.config.markdown_description}\n\n"

        for section_name, pages in self.pages_data.items():
            if pages:  # Only add section if it has pages
                content += f"# {section_name}\n\n"

                for page_data in pages:
                    if "markdown" in page_data:
                        title = page_data.get("title", page_data["src_uri"])
                        content += f"## {title}\n\n"
                        content += f"{page_data['markdown']}\n\n"

        llms_full_path.write_text(content.strip(), encoding="utf-8")

    def _get_ai_menu_html(self, config: MkDocsConfig) -> str:
        """Generate the 'Use with AI' dropdown menu HTML, CSS, and JavaScript."""
        button_text = self.config.ai_menu_button_text

        # Build menu items
        chatgpt_item = ""
        if self.config.enable_chatgpt:
            chatgpt_item = """
            <button type="button" class="askai-item" role="menuitem" onclick="askAI.openInChatGPT()">
              <span class="askai-item-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071 0l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071 0l4.83 2.791a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08-4.778 2.758a.795.795 0 0 0-.393.681zm1.097-2.365 2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5Z"/></svg></span>
              <span class="askai-item-text"><span class="askai-item-title">Open in ChatGPT</span><span class="askai-item-desc">Chat about this page with ChatGPT</span></span>
            </button>"""

        claude_item = ""
        if self.config.enable_claude:
            claude_item = """
            <button type="button" class="askai-item" role="menuitem" onclick="askAI.openInClaude()">
              <span class="askai-item-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="m4.714 15.956 4.718-2.648.079-.23-.08-.128h-.23l-.79-.048-2.695-.073-2.337-.097-2.265-.122-.57-.121-.535-.704.055-.353.48-.321.685.06 1.518.104 2.277.157 1.651.098 2.447.255h.389l.054-.158-.133-.097-.103-.098-2.356-1.596-2.55-1.688-1.336-.972-.722-.491L2 6.223l-.158-1.008.655-.722.88.06.225.061.893.686 1.906 1.476 2.49 1.833.364.304.146-.104.018-.072-.164-.274-1.354-2.446-1.445-2.49-.644-1.032-.17-.619a2.972 2.972 0 0 1-.103-.729L6.287.133 6.7 0l.995.134.42.364.619 1.415L9.735 4.14l1.555 3.03.455.898.243.832.09.255h.159V9.01l.127-1.706.237-2.095.23-2.695.08-.76.376-.91.747-.492.583.28.48.685-.067.444-.286 1.851-.558 2.903-.365 1.942h.213l.243-.242.983-1.306 1.652-2.064.728-.82.85-.904.547-.431h1.032l.759 1.129-.34 1.166-1.063 1.347-.88 1.142-1.263 1.7-.79 1.36.074.11.188-.02 2.853-.606 1.542-.28 1.84-.315.832.388.09.395-.327.807-1.967.486-2.307.462-3.436.813-.043.03.049.061 1.548.146.662.036h1.62l3.018.225.79.522.473.638-.08.485-1.213.62-1.64-.389-3.825-.91-1.31-.329h-.183v.11l1.093 1.068 2.003 1.81 2.508 2.33.127.578-.321.455-.34-.049-2.204-1.657-.85-.747-1.925-1.62h-.127v.17l.443.649 2.343 3.521.122 1.08-.17.353-.607.213-.668-.122-1.372-1.924-1.415-2.168-1.141-1.943-.14.08-.674 7.254-.316.37-.728.28-.607-.461-.322-.747.322-1.476.388-1.924.316-1.53.285-1.9.17-.632-.012-.042-.14.018-1.432 1.967-2.18 2.945-1.724 1.845-.413.164-.716-.37.066-.662.401-.589 2.386-3.036 1.439-1.882.929-1.086-.006-.158h-.055L4.138 18.56l-1.13.146-.485-.456.06-.746.231-.243 1.907-1.312Z"/></svg></span>
              <span class="askai-item-text"><span class="askai-item-title">Open in Claude</span><span class="askai-item-desc">Chat about this page with Claude</span></span>
            </button>"""

        ai_divider = ""
        if chatgpt_item or claude_item:
            ai_divider = '<div class="askai-divider"></div>'

        return f"""
<style>
.askai-wrap {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: var(--md-text-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
}}
.askai-trigger {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--md-default-fg-color--lightest, rgba(0,0,0,.12));
  border-radius: 24px;
  background: var(--md-default-bg-color, #fff);
  color: var(--md-default-fg-color, #333);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,.12);
  transition: box-shadow .2s, border-color .2s;
}}
.askai-trigger:hover {{
  box-shadow: 0 4px 16px rgba(0,0,0,.18);
  border-color: var(--md-primary-fg-color, #4051b5);
}}
.askai-trigger svg {{
  flex-shrink: 0;
}}
.askai-trigger svg:first-child {{
  color: #f5a623;
}}
.askai-trigger .askai-chevron {{
  transition: transform .2s;
}}
.askai-wrap.open .askai-trigger .askai-chevron {{
  transform: rotate(180deg);
}}
.askai-menu {{
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  min-width: 320px;
  background: var(--md-default-bg-color, #fff);
  border: 1px solid var(--md-default-fg-color--lightest, rgba(0,0,0,.12));
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
  padding: 6px 0;
  overflow: hidden;
}}
.askai-wrap.open .askai-menu {{
  display: block;
  animation: askai-fade .15s ease;
}}
@keyframes askai-fade {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.askai-item {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  color: var(--md-default-fg-color, #333);
  text-align: left;
  cursor: pointer;
  text-decoration: none;
  font-family: inherit;
  font-size: 13px;
  transition: background .15s;
}}
a.askai-item {{
  color: var(--md-default-fg-color, #333);
}}
.askai-item:hover {{
  background: var(--md-default-fg-color--lightest, rgba(0,0,0,.04));
}}
.askai-item-icon {{
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  opacity: .7;
}}
.askai-item-text {{
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}}
.askai-item-title {{
  font-weight: 500;
  line-height: 1.4;
}}
.askai-item-desc {{
  font-size: 12px;
  color: var(--md-default-fg-color--light, #666);
  line-height: 1.4;
}}
.askai-divider {{
  height: 1px;
  margin: 4px 0;
  background: var(--md-default-fg-color--lightest, rgba(0,0,0,.08));
}}
.askai-toast {{
  position: fixed;
  bottom: 80px;
  right: 24px;
  padding: 10px 20px;
  background: var(--md-primary-fg-color, #4051b5);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0,0,0,.2);
  z-index: 10000;
  opacity: 0;
  transform: translateY(8px);
  transition: opacity .2s, transform .2s;
  pointer-events: none;
}}
.askai-toast.show {{
  opacity: 1;
  transform: translateY(0);
}}
</style>

<div class="askai-wrap" id="askai-wrap">
  <div class="askai-menu" id="askai-menu" role="menu">
    <button type="button" class="askai-item" role="menuitem" onclick="askAI.copyMarkdown()">
      <span class="askai-item-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></span>
      <span class="askai-item-text"><span class="askai-item-title">Copy page as Markdown</span><span class="askai-item-desc">Copy to clipboard for pasting into any AI tool</span></span>
    </button>
    <a class="askai-item" role="menuitem" id="askai-view-md" target="_blank" rel="noopener noreferrer">
      <span class="askai-item-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg></span>
      <span class="askai-item-text"><span class="askai-item-title">View as Markdown</span><span class="askai-item-desc">Open this page as clean Markdown in a new tab</span></span>
    </a>
    {ai_divider}
    {chatgpt_item}
    {claude_item}
    <div class="askai-divider"></div>
    <a class="askai-item" role="menuitem" href="/llms.txt" target="_blank" rel="noopener noreferrer">
      <span class="askai-item-icon"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/></svg></span>
      <span class="askai-item-text"><span class="askai-item-title">llms.txt</span><span class="askai-item-desc">Full documentation index for LLMs</span></span>
    </a>
  </div>
  <button class="askai-trigger" id="askai-trigger" type="button" aria-haspopup="true" aria-expanded="false">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9.5 2s1.1 4.4 2.6 5.9 5.9 2.6 5.9 2.6-4.4 1.1-5.9 2.6S9.5 19 9.5 19s-1.1-4.4-2.6-5.9S1 10.5 1 10.5s4.4-1.1 5.9-2.6S9.5 2 9.5 2ZM18.5 13s.5 2 1.5 3 3 1.5 3 1.5-2 .5-3 1.5-1.5 3-1.5 3-.5-2-1.5-3-3-1.5-3-1.5 2-.5 3-1.5 1.5-3 1.5-3Z"/></svg>
    {button_text}
    <svg class="askai-chevron" width="12" height="12" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.168l3.71-3.938a.75.75 0 1 1 1.08 1.04l-4.25 4.5a.75.75 0 0 1-1.08 0l-4.25-4.5a.75.75 0 0 1 .02-1.06z"/></svg>
  </button>
</div>
<div class="askai-toast" id="askai-toast"></div>

<script>
(function() {{
  const askAI = {{
    _getMdPath() {{
      const p = window.location.pathname;
      return p.endsWith('/') ? p + 'index.md' : p.replace(/\\.html$/, '.md');
    }},
    async _fetchMarkdown() {{
      const r = await fetch(this._getMdPath());
      if (!r.ok) throw new Error('Markdown not found');
      return await r.text();
    }},
    _toast(msg, ms) {{
      const t = document.getElementById('askai-toast');
      t.textContent = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), ms || 2500);
    }},
    _close() {{
      document.getElementById('askai-wrap').classList.remove('open');
      document.getElementById('askai-trigger').setAttribute('aria-expanded', 'false');
    }},
    toggle() {{
      const w = document.getElementById('askai-wrap');
      const open = w.classList.toggle('open');
      document.getElementById('askai-trigger').setAttribute('aria-expanded', open);
    }},
    async copyMarkdown() {{
      try {{
        const md = await this._fetchMarkdown();
        await navigator.clipboard.writeText(md);
        this._close();
        this._toast('Copied to clipboard');
      }} catch (e) {{
        this._toast('Failed to copy');
      }}
    }},
    _buildPrompt(md, siteName) {{
      const mdUrl = window.location.origin + this._getMdPath();
      const prefix = `Use the following ${{siteName}} documentation to help me:\n\n`;
      // URL max ~8000 chars to be safe across browsers
      const maxLen = 7500 - prefix.length;
      if (md.length > maxLen) {{
        const truncated = md.substring(0, maxLen);
        return prefix + truncated + `\n\n[Truncated — full page: ${{mdUrl}}]`;
      }}
      return prefix + md;
    }},
    async openInChatGPT() {{
      try {{
        const md = await this._fetchMarkdown();
        const prompt = this._buildPrompt(md, document.title);
        this._close();
        window.open('https://chatgpt.com/?q=' + encodeURIComponent(prompt), '_blank');
      }} catch (e) {{
        this._close();
        window.open('https://chatgpt.com/', '_blank');
      }}
    }},
    async openInClaude() {{
      try {{
        const md = await this._fetchMarkdown();
        const prompt = this._buildPrompt(md, document.title);
        this._close();
        window.open('https://claude.ai/new?q=' + encodeURIComponent(prompt), '_blank');
      }} catch (e) {{
        this._close();
        window.open('https://claude.ai/new', '_blank');
      }}
    }}
  }};

  // Expose globally
  window.askAI = askAI;

  // Set up "View as Markdown" link
  const viewMd = document.getElementById('askai-view-md');
  if (viewMd) viewMd.href = askAI._getMdPath();

  // Toggle on button click
  document.getElementById('askai-trigger').addEventListener('click', () => askAI.toggle());

  // Close on outside click
  document.addEventListener('click', (e) => {{
    const w = document.getElementById('askai-wrap');
    if (w.classList.contains('open') && !w.contains(e.target)) {{
      askAI._close();
    }}
  }});

  // Close on Escape
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') askAI._close();
  }});
}})();
</script>
"""
