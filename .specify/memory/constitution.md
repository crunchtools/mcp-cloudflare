# mcp-cloudflare-crunchtools Constitution

> **Version:** 1.1.0
> **Ratified:** 2026-03-03
> **Amended:** 2026-10-02
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.18.0
> **Profile:** MCP Server

This file holds what is specific to mcp-cloudflare. The fleet rules and the
MCP Server profile (five-layer security model, two-layer tools, distribution
channels, quality gates, Gourmand) apply at the inherited version and are
checked against this repo's files by `constitution.yml`. They are not
restated here.

## Security Model Specifics

- **Credentials:** `CLOUDFLARE_API_TOKEN`, held as `SecretStr`, read from the
  environment only and redacted from error messages by `CloudflareApiError`.
  `Config.__repr__()`/`__str__()` never expose it.
- **Input limits:** zone, record and rule IDs are validated as 32-character
  hex strings; DNS record and rule inputs go through Pydantic models.
  `ZoneNotFoundError` truncates long identifiers.
- **API:** Bearer token header, never the URL; requests time out after 30s;
  responses are capped at 10MB.

## Single Account

The server talks to one Cloudflare account, chosen by the token. The API base
URL `https://api.cloudflare.com/client/v4` is hardcoded and immutable, which
rules out SSRF through configuration.

## Tool Groups

`tools/` holds zones, DNS, transform rules, page rules, WAF, cache and
analytics. `test_tool_count` is updated whenever a tool is added or removed.

## Instance

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-cloudflare` |
| PyPI package | `mcp-cloudflare-crunchtools` |
| Container image | `quay.io/crunchtools/mcp-cloudflare` |
| systemd service | `mcp-cloudflare.service` |
| HTTP port | 8004 |

## History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial constitution |
| 1.0.1 | 2026-03-16 | Add Section VI (Container Conventions); renumber VI-VIII to VII-IX |
| 1.0.2 | 2026-09-25 | Inherit constitution v1.17.0 (Gatehouse gates) |
| 1.1.0 | 2026-10-02 | Manifest under constitution v1.18.0: profile restatement removed, mcp-cloudflare specifics kept |
