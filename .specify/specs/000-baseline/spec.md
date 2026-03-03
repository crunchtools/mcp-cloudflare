# Specification: Baseline

> **Spec ID:** 000-baseline
> **Status:** Implemented
> **Version:** 0.5.0
> **Author:** crunchtools.com
> **Date:** 2026-03-03

## Overview

Baseline specification for mcp-cloudflare-crunchtools v0.5.0, documenting all 26 tools across 7 categories that provide secure access to the Cloudflare API.

---

## Tools (26)

### Zone Tools (2)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `list_zones` | `GET /zones` | List zones in account |
| `get_zone` | `GET /zones/{id}` | Get zone details |

### DNS Tools (5)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `list_dns_records` | `GET /zones/{id}/dns_records` | List DNS records |
| `get_dns_record` | `GET /zones/{id}/dns_records/{id}` | Get DNS record details |
| `create_dns_record` | `POST /zones/{id}/dns_records` | Create DNS record |
| `update_dns_record` | `PATCH /zones/{id}/dns_records/{id}` | Update DNS record |
| `delete_dns_record` | `DELETE /zones/{id}/dns_records/{id}` | Delete DNS record |

### Transform Rules Tools (6)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `list_request_header_rules` | `GET /zones/{id}/rulesets` | List request header rules |
| `set_request_header_rules` | `PUT /zones/{id}/rulesets` | Set request header rules |
| `list_response_header_rules` | `GET /zones/{id}/rulesets` | List response header rules |
| `set_response_header_rules` | `PUT /zones/{id}/rulesets` | Set response header rules |
| `list_url_rewrite_rules` | `GET /zones/{id}/rulesets` | List URL rewrite rules |
| `set_url_rewrite_rules` | `PUT /zones/{id}/rulesets` | Set URL rewrite rules |

### Page Rules Tools (4)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `list_page_rules` | `GET /zones/{id}/pagerules` | List page rules |
| `create_page_rule` | `POST /zones/{id}/pagerules` | Create page rule |
| `update_page_rule` | `PATCH /zones/{id}/pagerules/{id}` | Update page rule |
| `delete_page_rule` | `DELETE /zones/{id}/pagerules/{id}` | Delete page rule |

### Cache Tools (1)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `purge_cache` | `POST /zones/{id}/purge_cache` | Purge cache |

### Analytics Tools (4)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `get_zone_analytics` | `GET /zones/{id}/analytics` | Get zone analytics |
| `get_top_pages` | `GET /zones/{id}/analytics` | Get top pages |
| `get_traffic_by_country` | `GET /zones/{id}/analytics` | Get traffic by country |
| `get_security_events` | `GET /zones/{id}/analytics` | Get security events |

### WAF Tools (4) — Note: not in MCP server instructions (18 tools), but present in code (25 tools)

| Tool | Cloudflare API Endpoint | Description |
|------|-------------------------|-------------|
| `list_waf_rules` | `GET /zones/{id}/rulesets` | List WAF rules |
| `create_waf_rule` | `POST /zones/{id}/rulesets` | Create WAF rule |
| `update_waf_rule` | `PATCH /zones/{id}/rulesets/{id}` | Update WAF rule |
| `delete_waf_rule` | `DELETE /zones/{id}/rulesets/{id}` | Delete WAF rule |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLOUDFLARE_API_TOKEN` | Yes | — | Cloudflare API token with zone permissions |

---

## Error Hierarchy

```
UserError
├── ConfigurationError
├── ValidationError
├── InvalidZoneIdError
├── InvalidRecordIdError
├── InvalidRuleIdError
├── ZoneNotFoundError
├── PermissionDeniedError
├── RateLimitError
└── CloudflareApiError
```

---

## Module Structure

```
src/mcp_cloudflare_crunchtools/
├── __init__.py          # Entry point, version, CLI args
├── __main__.py          # python -m support
├── server.py            # FastMCP server, @mcp.tool() wrappers
├── client.py            # httpx async client, Cloudflare API
├── config.py            # SecretStr credentials, hardcoded API URL
├── errors.py            # UserError hierarchy with token scrubbing
├── models.py            # Pydantic models for input validation
└── tools/
    ├── __init__.py      # Re-exports all 25 tool functions
    ├── zones.py         # list_zones, get_zone
    ├── dns.py           # 5 DNS record tools
    ├── transform.py     # 6 transform rules tools
    ├── page_rules.py    # 4 page rules tools
    ├── cache.py         # purge_cache
    ├── analytics.py     # 4 analytics tools
    └── waf.py           # 4 WAF tools
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.5.0 | 2026-03-03 | V2 architecture: governance, mocked tests, version sync |
| 0.1.0 | 2026-02-15 | Initial release |
