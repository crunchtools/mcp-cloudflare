# MCP Cloudflare CrunchTools

A secure MCP (Model Context Protocol) server for Cloudflare DNS, Transform Rules, Page Rules, and cache management.

## Overview

This MCP server is designed to be:

- **Secure by default** - Comprehensive threat modeling, input validation, and token protection
- **No third-party services** - Runs locally via stdio, your API token never leaves your machine
- **Cross-platform** - Works on Linux, macOS, and Windows
- **Automatically updated** - GitHub Actions monitor for CVEs and update dependencies
- **Containerized** - Available at `quay.io/crunchtools/mcp-cloudflare` built on [Hummingbird Python](https://quay.io/repository/hummingbird/python) base image

## Naming Convention

| Component | Name |
|-----------|------|
| GitHub repo | [crunchtools/mcp-cloudflare](https://github.com/crunchtools/mcp-cloudflare) |
| Container | `quay.io/crunchtools/mcp-cloudflare` |
| Python package (PyPI) | `mcp-cloudflare-crunchtools` |
| CLI command | `mcp-cloudflare-crunchtools` |
| Module import | `mcp_cloudflare_crunchtools` |

## Why Hummingbird?

The container image is built on the [Hummingbird Python base image](https://quay.io/repository/hummingbird/python), which provides:

- **Minimal CVE exposure** - Hummingbird images are built with a minimal package set, dramatically reducing the attack surface compared to general-purpose images
- **Red Hat UBI foundation** - Built on Red Hat Universal Base Image, providing enterprise-grade security, compliance, and support
- **Regular updates** - Security patches are applied promptly, keeping CVE counts low
- **Optimized for Python** - Pre-configured Python environment with uv package manager for fast, reproducible builds
- **Production-ready** - Designed for production workloads with proper signal handling and non-root user defaults

This combination means your MCP server runs in a hardened environment with fewer vulnerabilities than typical Python container images

## Features

### Zone Management (2 tools)
- `list_zones` - List all zones accessible by your API token
- `get_zone` - Get zone details by ID or domain name

### DNS Records (5 tools)
- `list_dns_records` - List DNS records with filtering
- `get_dns_record` - Get a single DNS record
- `create_dns_record` - Create A, AAAA, CNAME, MX, TXT, NS, SRV, CAA records
- `update_dns_record` - Update existing records
- `delete_dns_record` - Delete records

### Transform Rules (6 tools)
- `list_request_header_rules` / `set_request_header_rules` - Modify request headers
- `list_response_header_rules` / `set_response_header_rules` - Modify response headers
- `list_url_rewrite_rules` / `set_url_rewrite_rules` - URL path/query rewrites

### Page Rules (4 tools)
- `list_page_rules` - List all page rules
- `create_page_rule` - Create redirects, cache settings, SSL modes
- `update_page_rule` - Modify existing rules
- `delete_page_rule` - Remove rules

### Cache Management (1 tool)
- `purge_cache` - Purge by URL, tag, host, prefix, or everything

## Installation

### With uvx (Recommended)

```bash
uvx mcp-cloudflare-crunchtools
```

### With pip

```bash
pip install mcp-cloudflare-crunchtools
```

### With Container

```bash
podman run -e CLOUDFLARE_API_TOKEN=your_token \
    quay.io/crunchtools/mcp-cloudflare
```

## Configuration

### Creating a Cloudflare API Token

1. **Navigate to API Tokens**
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"
   - Click "Get started" next to "Create Custom Token"

2. **Configure Token Name**
   - Enter: `mcp-cloudflare-crunchtools`

3. **Configure Permissions**

   The Permissions section has three dropdowns per row:
   - **First dropdown**: Resource type (`Account` or `Zone`)
   - **Second dropdown**: Specific permission category
   - **Third dropdown**: Access level (`Read` or `Edit`)

   Click "+ Add more" to add each permission row. For full management, add:

   | Resource | Permission | Access |
   |----------|------------|--------|
   | Zone | Zone | Read |
   | Zone | DNS | Edit |
   | Zone | Page Rules | Edit |
   | Zone | Transform Rules | Edit |
   | Zone | Cache Purge | Purge |

4. **Configure Zone Resources**
   - First dropdown: Select "Include"
   - Second dropdown: Select "All zones" or "Specific zone"

5. **Configure Client IP Address Filtering (Optional)**
   - Click "Use my IP" button to restrict token to your current IP

6. **Create and Copy Token**
   - Click "Continue to summary" → "Create Token"
   - **IMPORTANT: Copy the token immediately** - it's only shown once!

### Add to Claude Code

```bash
claude mcp add mcp-cloudflare-crunchtools \
    --env CLOUDFLARE_API_TOKEN=your_token_here \
    -- uvx mcp-cloudflare-crunchtools
```

Or for the container version:

```bash
claude mcp add mcp-cloudflare-crunchtools \
    --env CLOUDFLARE_API_TOKEN=your_token_here \
    -- podman run -i --rm -e CLOUDFLARE_API_TOKEN quay.io/crunchtools/mcp-cloudflare
```

### Permission Sets by Use Case

#### Read-Only (viewing only)
| Resource | Permission | Access |
|----------|------------|--------|
| Zone | Zone | Read |
| Zone | DNS | Read |

#### DNS Management Only
| Resource | Permission | Access |
|----------|------------|--------|
| Zone | Zone | Read |
| Zone | DNS | Edit |

#### Full Management (all features)
| Resource | Permission | Access |
|----------|------------|--------|
| Zone | Zone | Read |
| Zone | DNS | Edit |
| Zone | Page Rules | Edit |
| Zone | Transform Rules | Edit |
| Zone | Cache Purge | Purge |

## Usage Examples

### List Your Zones

```
User: List my Cloudflare zones
Assistant: [calls list_zones]
```

### Create a DNS Record

```
User: Create an A record for www.example.com pointing to 192.168.1.1
Assistant: [calls create_dns_record with type=A, name=www, content=192.168.1.1]
```

### Add Security Headers

```
User: Add X-Content-Type-Options: nosniff to all responses for zone abc123...
Assistant: [calls set_response_header_rules with appropriate rule]
```

### Purge Cache

```
User: Purge the cache for https://example.com/styles.css
Assistant: [calls purge_cache with files=["https://example.com/styles.css"]]
```

## Security

This server was designed with security as a primary concern. See [SECURITY.md](SECURITY.md) for:

- Threat model and attack vectors
- Defense in depth architecture
- Token handling best practices
- Input validation rules
- Audit logging

### Key Security Features

1. **Token Protection**
   - Stored as SecretStr (never accidentally logged)
   - Environment variable only (never in files or args)
   - Sanitized from all error messages

2. **Input Validation**
   - Pydantic models for all inputs
   - Allowlist for record types, actions
   - Strict format validation for IDs

3. **API Hardening**
   - Hardcoded API base URL (prevents SSRF)
   - TLS certificate validation
   - Request timeouts
   - Response size limits

4. **Automated CVE Scanning**
   - GitHub Actions scan dependencies weekly
   - Automatic PRs for security updates
   - Dependabot alerts enabled

## Development

### Setup

```bash
git clone https://github.com/crunchtools/mcp-cloudflare.git
cd mcp-cloudflare
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Lint and Type Check

```bash
uv run ruff check src tests
uv run mypy src
```

### Build Container

```bash
podman build -t mcp-cloudflare .
```

## License

Apache-2.0

## Contributing

Contributions welcome! Please read SECURITY.md before submitting security-related changes.

## Links

- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [crunchtools.com](https://crunchtools.com)
