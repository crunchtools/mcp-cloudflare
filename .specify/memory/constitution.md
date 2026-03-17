# mcp-cloudflare-crunchtools Constitution

> **Version:** 1.0.1
> **Ratified:** 2026-03-03
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.0.0
> **Profile:** MCP Server

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

### 4. Three Distribution Channels

Every release MUST be available through all three channels simultaneously:

| Channel | Command | Use Case |
|---------|---------|----------|
| uvx | `uvx mcp-cloudflare-crunchtools` | Zero-install, Claude Code |
| pip | `pip install mcp-cloudflare-crunchtools` | Virtual environments |
| Container | `podman run quay.io/crunchtools/mcp-cloudflare` | Isolated, systemd |

### 5. Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/) strictly. MAJOR/MINOR/PATCH. Version bump happens at release time, not per-commit.

### 6. AI Code Quality

All code MUST pass Gourmand checks before merge. Zero violations required.

---

## II. Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.10+ |
| MCP Framework | FastMCP | Latest |
| HTTP Client | httpx | Latest |
| Validation | Pydantic | v2 |
| Container Base | Hummingbird | Latest |
| Package Manager | uv | Latest |
| Build System | hatchling | Latest |
| Linter | ruff | Latest |
| Type Checker | mypy (strict) | Latest |
| Tests | pytest + pytest-asyncio | Latest |
| Slop Detector | gourmand | Latest |

---

## III. Testing Standards

### Mocked API Tests (MANDATORY)

Every tool MUST have a corresponding mocked test. Tests use `httpx.AsyncClient` mocking — no live API calls, no credentials required in CI.

**Singleton reset:** The `_reset_client_singleton` autouse fixture resets `_client` in client.py and `_config` in config.py between every test.

**Tool count assertion:** `test_tool_count` MUST be updated whenever tools are added or removed.

---

## IV. Gourmand (AI Slop Detection)

All code MUST pass `gourmand --full .` with **zero violations** before merge. Gourmand is a CI gate in GitHub Actions.

### Configuration

- `gourmand.toml` — Check settings, excluded paths
- `gourmand-exceptions.toml` — Documented exceptions with justifications
- `.gourmand-cache/` — Must be in `.gitignore`

### Exception Policy

Exceptions MUST have documented justifications in `gourmand-exceptions.toml`. Acceptable reasons:
- Standard API patterns (HTTP status codes, pagination params)
- Test-specific patterns (intentional invalid input)
- Framework requirements (CLAUDE.md for Claude Code)

Unacceptable reasons:
- "The code is special"
- "The threshold is too strict"
- Rewording to avoid detection

---

## V. Code Quality Gates

1. **Lint** — `uv run ruff check src tests`
2. **Type Check** — `uv run mypy src`
3. **Tests** — `CLOUDFLARE_API_TOKEN=test uv run pytest -v`
4. **Gourmand** — `gourmand --full .`
5. **Container Build** — `podman build -f Containerfile .`

---

## VI. Container Conventions

- Use **Containerfile** (not Dockerfile) as the build file name.
- Base image: **Hummingbird** (`quay.io/hummingbird/python:latest`) for minimal CVE surface.
- Always `dnf clean all` after package installs.
- Required LABELs: `maintainer`, `description`.
- Required OCI labels:
  ```
  org.opencontainers.image.source=https://github.com/crunchtools/mcp-cloudflare
  org.opencontainers.image.description=Secure MCP server for Cloudflare DNS, Transform Rules, and WAF management
  org.opencontainers.image.licenses=AGPL-3.0-or-later
  ```

### Dual-Push CI Architecture

Container CI workflows MUST use two separate jobs:

1. **`build-and-push-quay`** — Builds and pushes to Quay.io. Includes Trivy security scan.
2. **`build-and-push-ghcr`** — Builds and pushes to GHCR. Uses `needs: build-and-push-quay` dependency. Gated with `if: github.event_name != 'pull_request'`.

---

## VII. Naming Conventions

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-cloudflare` |
| PyPI package | `mcp-cloudflare-crunchtools` |
| CLI command | `mcp-cloudflare-crunchtools` |
| Python module | `mcp_cloudflare_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-cloudflare` |
| systemd service | `mcp-cloudflare.service` |
| HTTP port | 8004 |
| License | AGPL-3.0-or-later |

---

## VIII. Development Workflow

### Adding a New Tool

1. Add the async function to the appropriate `tools/*.py` file
2. Export it from `tools/__init__.py`
3. Import it in `server.py` and register with `@mcp.tool()`
4. Add a mocked test in `tests/test_tools.py`
5. Update the tool count in `test_tool_count`
6. Run all five quality gates
7. Update CLAUDE.md tool listing

### Adding a New Tool Group

1. Create `tools/new_group.py` with async functions
2. Add imports and `__all__` entries in `tools/__init__.py`
3. Add `@mcp.tool()` wrappers in `server.py`
4. Add a `TestNewGroupTools` class in `tests/test_tools.py`
5. Run all five quality gates

---

## IX. Governance

### Amendment Process

1. Create a PR with proposed changes to this constitution
2. Document rationale in PR description
3. Require maintainer approval
4. Update version number upon merge

### Ratification History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial constitution |
| 1.0.1 | 2026-03-16 | Add Section VI (Container Conventions); renumber VI-VIII → VII-IX |
