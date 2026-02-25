"""MCP Cloudflare CrunchTools - Secure MCP server for Cloudflare.

A security-focused MCP server for Cloudflare DNS, Transform Rules,
Page Rules, and cache management.

Usage:
    # Run directly
    mcp-cloudflare-crunchtools

    # Or with Python module
    python -m mcp_cloudflare_crunchtools

    # With uvx
    uvx mcp-cloudflare-crunchtools

Environment Variables:
    CLOUDFLARE_API_TOKEN: Required. Cloudflare API token with appropriate permissions.

Example with Claude Code:
    claude mcp add mcp-cloudflare-crunchtools \\
        --env CLOUDFLARE_API_TOKEN=your_token_here \\
        -- uvx mcp-cloudflare-crunchtools
"""

import argparse

from .server import mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP server for Cloudflare")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP transports (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
