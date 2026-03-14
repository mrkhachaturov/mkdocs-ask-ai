"""CLI entry point for mkdocs-ask-ai MCP server."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="mkdocs-ask-ai",
        description="MkDocs Ask AI — LLM-friendly documentation tools",
    )
    subparsers = parser.add_subparsers(dest="command")

    mcp_parser = subparsers.add_parser("mcp", help="Start MCP server for documentation")
    mcp_parser.add_argument(
        "--site-dir",
        type=Path,
        default=Path("public"),
        help="Path to built MkDocs site directory (default: ./public)",
    )
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=8808,
        help="Port for HTTP transport (default: 8808)",
    )
    mcp_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transport (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    if args.command == "mcp":
        _run_mcp(args)
    else:
        parser.print_help()
        sys.exit(1)


def _run_mcp(args):
    try:
        from .mcp_server import create_server
    except ImportError:
        print(
            "Error: MCP SDK not installed. Install with: pip install mkdocs-ask-ai[mcp]",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.site_dir.exists():
        print(f"Error: Site directory not found: {args.site_dir}", file=sys.stderr)
        print("Run 'mkdocs build' first.", file=sys.stderr)
        sys.exit(1)

    server = create_server(args.site_dir)

    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
