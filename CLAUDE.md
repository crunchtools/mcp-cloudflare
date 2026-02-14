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

## Creating a Cloudflare API Token

### Step-by-Step Instructions

1. **Log in to Cloudflare Dashboard**
   - Go to https://dash.cloudflare.com
   - Sign in with your Cloudflare account

2. **Navigate to API Tokens**
   - Click your profile icon (top right)
   - Select "My Profile"
   - Click "API Tokens" in the left sidebar
   - Or go directly to: https://dash.cloudflare.com/profile/api-tokens

3. **Create a Custom Token**
   - Click "Create Token"
   - Click "Get started" next to "Create Custom Token"

4. **Configure Token Name**
   - Enter a descriptive name like "MCP Cloudflare CrunchTools"

5. **Set Permissions** (based on your needs)

   Choose ONE of these permission sets:

   #### Read-Only (Safest - for viewing only)
   | Permission | Access |
   |------------|--------|
   | Zone | Zone | Read |
   | Zone | DNS | Read |

   #### DNS Management (for managing DNS records)
   | Permission | Access |
   |------------|--------|
   | Zone | Zone | Read |
   | Zone | DNS | Edit |

   #### Full Management (all features)
   | Permission | Access |
   |------------|--------|
   | Zone | Zone | Read |
   | Zone | DNS | Edit |
   | Zone | Page Rules | Edit |
   | Zone | Transform Rules | Edit |
   | Zone | Cache Purge | Purge |

6. **Set Zone Resources**
   - "Include" → "Specific zone" → Select your domain(s)
   - Or "Include" → "All zones" (if managing multiple domains)

7. **Set IP Filtering (Optional but Recommended)**
   - Add your IP address for additional security
   - Or leave blank to allow from any IP

8. **Set TTL (Optional)**
   - Set an expiration date if desired
   - Or leave blank for no expiration

9. **Create and Copy Token**
   - Click "Continue to summary"
   - Review permissions
   - Click "Create Token"
   - **IMPORTANT: Copy the token immediately** - it won't be shown again

10. **Use the Token**
    ```bash
    claude mcp add mcp-cloudflare-crunchtools \
        --env CLOUDFLARE_API_TOKEN=your_copied_token \
        -- uvx mcp-cloudflare-crunchtools
    ```

### Security Best Practices

- **Principle of least privilege**: Only grant permissions you actually need
- **Use specific zones**: Don't grant access to all zones unless necessary
- **Set expiration**: Consider setting a TTL for tokens used in development
- **Rotate regularly**: Create new tokens periodically and revoke old ones
- **Never commit tokens**: Don't put tokens in code or config files in git

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
