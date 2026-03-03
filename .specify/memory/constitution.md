# mcp-cloudflare-crunchtools Constitution

> **Version:** 1.0.0
> **Ratified:** 2026-03-03
> **Status:** Active

This constitution establishes the core principles, constraints, and workflows that govern all development on mcp-cloudflare-crunchtools.

---

## I. Core Principles

### 1. Five-Layer Security Model

Every change MUST preserve all five security layers. No exceptions.

**Layer 1 — Credential Protection:**
- CLOUDFLARE_API_TOKEN stored as `SecretStr` (never logged or exposed)
- Environment-variable-only storage
- Automatic scrubbing from error messages via `CloudflareApiError`

**Layer 2 — Input Validation:**
- Hex string validation for zone/record/rule IDs (32-character)
- Pydantic models for DNS record and rule inputs
- Type and format enforcement

**Layer 3 — API Hardening:**
- Auth via Bearer token header (never URL)
- Hardcoded API base URL `https://api.cloudflare.com/client/v4` (prevents SSRF)
- Mandatory TLS certificate validation (httpx default)
- Request timeout enforcement (30s)
- Response size limits (10MB)

**Layer 4 — Output Sanitization:**
- `CloudflareApiError` redacts token values from any error messages
- Safe `__repr__()` and `__str__()` on Config that never expose token
- `ZoneNotFoundError` truncates long identifiers

**Layer 5 — Supply Chain Security:**
- Weekly automated CVE scanning via GitHub Actions
- Hummingbird container base images (minimal CVE surface)
- Gourmand AI slop detection gating all PRs

### 2. Two-Layer Tool Architecture

Tools follow a strict two-layer pattern:
- `server.py` — `@mcp.tool()` decorated functions that validate args and delegate
- `tools/*.py` — Pure async functions that call `client.py` HTTP methods

Never put business logic in `server.py`. Never put MCP registration in `tools/*.py`.

### 3. Single-Instance Design

The server connects to a single Cloudflare account configured via CLOUDFLARE_API_TOKEN. The API base URL is hardcoded and immutable.

### 4. Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/) strictly. Version bump happens at release time, not per-commit.

### 5. AI Code Quality

All code MUST pass Gourmand checks before merge. Zero violations required.

---

## II. Testing Standards

### Mocked API Tests (MANDATORY)

Every tool MUST have a corresponding mocked test. Tests use `httpx.AsyncClient` mocking — no live API calls, no credentials required in CI.

**Singleton reset:** The `_reset_client_singleton` autouse fixture resets `_client` in client.py and `_config` in config.py between every test.

**Tool count assertion:** `test_tool_count` MUST be updated whenever tools are added or removed.

---

## III. Code Quality Gates

1. **Lint** — `uv run ruff check src tests`
2. **Type Check** — `uv run mypy src`
3. **Tests** — `CLOUDFLARE_API_TOKEN=test uv run pytest -v`
4. **Gourmand** — `gourmand --full .`
5. **Container Build** — `podman build -f Containerfile .`

---

## IV. Naming Conventions

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-cloudflare` |
| PyPI package | `mcp-cloudflare-crunchtools` |
| Python module | `mcp_cloudflare_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-cloudflare` |
| License | AGPL-3.0-or-later |

---

## V. Governance

### Ratification History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial constitution |
