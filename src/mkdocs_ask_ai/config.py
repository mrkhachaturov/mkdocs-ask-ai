"""Configuration for the Ask AI plugin."""

from mkdocs.config import config_options
from mkdocs.config.base import Config


class AskAiConfig(Config):
    """Configuration options for the Ask AI plugin."""

    sections = config_options.Type(dict, default={})
    """Dictionary mapping section names to lists of file patterns."""

    enable_markdown_urls = config_options.Type(bool, default=True)
    """Whether to serve original markdown at .md URLs."""

    enable_llms_txt = config_options.Type(bool, default=True)
    """Whether to generate llms.txt file."""

    enable_llms_full = config_options.Type(bool, default=True)
    """Whether to generate llms-full.txt file."""

    enable_ai_menu = config_options.Type(bool, default=True)
    """Whether to add the 'Use with AI' dropdown menu on pages."""

    ai_menu_button_text = config_options.Type(str, default="Use with AI")
    """Text for the dropdown trigger button."""

    enable_chatgpt = config_options.Type(bool, default=True)
    """Whether to show 'Open in ChatGPT' menu item."""

    enable_claude = config_options.Type(bool, default=True)
    """Whether to show 'Open in Claude' menu item."""

    markdown_description = config_options.Optional(config_options.Type(str))
    """Optional description to include in llms.txt."""

    # Deprecated options — kept for backward compatibility
    enable_copy_button = config_options.Type(bool, default=False)
    copy_button_text = config_options.Type(str, default="Copy Markdown")
    copy_button_position = config_options.Type(
        dict, default={"top": "80px", "right": "20px", "z_index": "1100"}
    )
    copy_button_style = config_options.Type(dict, default={})
