# Claude Code Instructions

This is a secure MCP server for Cloudflare DNS, Transform Rules, Page Rules, and cache management.

## Quick Start

### Option 1: Using uvx (Recommended)

```bash
claude mcp add mcp-cloudflare-crunchtools \
    --env CLOUDFLARE_API_TOKEN=your_token_here \
    -- uvx mcp-cloudflare-crunchtools
```

### Option 2: Using Container

```bash
claude mcp add mcp-cloudflare-crunchtools \
    --env CLOUDFLARE_API_TOKEN=your_token_here \
    -- podman run -i --rm -e CLOUDFLARE_API_TOKEN quay.io/crunchtools/mcp-cloudflare
```

### Option 3: Local Development

```bash
cd ~/Projects/crunchtools/mcp-cloudflare
claude mcp add mcp-cloudflare-crunchtools \
    --env CLOUDFLARE_API_TOKEN=your_token_here \
    -- uv run mcp-cloudflare-crunchtools
```

## Getting a Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Choose permissions based on your needs:

**Read-Only (Safest)**
- Zone:Read
- DNS:Read

**DNS Management**
- Zone:Read
- DNS:Edit

**Full Management**
- Zone:Read
- DNS:Edit
- Transform Rules:Edit
- Page Rules:Edit
- Cache Purge:Edit

## Available Tools

### Zone Management
- `list_zones` - List all zones accessible by your API token
- `get_zone` - Get zone details by ID or domain name

### DNS Records
- `list_dns_records` - List DNS records with filtering
- `get_dns_record` - Get a single DNS record
- `create_dns_record` - Create DNS records (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
- `update_dns_record` - Update existing records
- `delete_dns_record` - Delete records

### Transform Rules
- `list_request_header_rules` / `set_request_header_rules` - Modify request headers
- `list_response_header_rules` / `set_response_header_rules` - Modify response headers
- `list_url_rewrite_rules` / `set_url_rewrite_rules` - URL path/query rewrites

### Page Rules
- `list_page_rules` - List all page rules
- `create_page_rule` - Create redirects, cache settings, SSL modes
- `update_page_rule` - Modify existing rules
- `delete_page_rule` - Remove rules

### Cache Management
- `purge_cache` - Purge by URL, tag, host, prefix, or everything

## Example Usage

```
User: List my Cloudflare zones
User: Create an A record for www.example.com pointing to 192.168.1.1
User: Add X-Content-Type-Options: nosniff header to all responses
User: Purge the cache for https://example.com/styles.css
```

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```
