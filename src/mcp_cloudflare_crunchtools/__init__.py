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

from .server import mcp

__version__ = "0.1.0"
__all__ = ["main", "mcp"]


def main() -> None:
    """Main entry point for the MCP server."""
    mcp.run()
