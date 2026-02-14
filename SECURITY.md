# Security Design Document

This document describes the security architecture of mcp-cloudflare-crunchtools.

## 1. Threat Model

### 1.1 Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| Cloudflare API Token | Critical | Full account access, DNS hijacking, service disruption |
| Zone Configuration | High | Traffic redirection, downtime |
| DNS Records | High | Domain hijacking, phishing enablement |
| Transform Rules | Medium | Request/response manipulation |

### 1.2 Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| Malicious AI Agent | Can craft tool inputs | Data exfiltration, privilege escalation |
| Local Attacker | Access to filesystem | Token theft, configuration tampering |
| Network Attacker | Man-in-the-middle | Token interception (mitigated by TLS) |

### 1.3 Attack Vectors

| Vector | Description | Mitigation |
|--------|-------------|------------|
| **Token Leakage** | Token exposed in logs, errors, or outputs | Never log tokens, scrub from errors |
| **Input Injection** | Malicious zone_id or record content | Strict input validation with Pydantic |
| **Path Traversal** | Manipulated file paths | No filesystem operations |
| **SSRF** | Redirect API calls to internal services | Hardcoded API base URL |
| **Denial of Service** | Exhaust Cloudflare rate limits | Rate limiting awareness |
| **Privilege Escalation** | Access zones beyond token scope | Server validates token scope |
| **Supply Chain** | Compromised dependencies | Automated CVE scanning |

## 2. Security Architecture

### 2.1 Defense in Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation                                    │
│ - Pydantic models for all tool inputs                       │
│ - Allowlist for zone IDs, record types, rule actions        │
│ - Reject unexpected fields                                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Token Handling                                      │
│ - Environment variable only (never file, never arg)         │
│ - Never log, never include in errors                        │
│ - Use httpx with auth parameter (not in URL)                │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: API Client Hardening                               │
│ - Hardcoded base URL (https://api.cloudflare.com/client/v4) │
│ - TLS certificate validation (default in httpx)             │
│ - Request timeout enforcement                               │
│ - Response size limits                                      │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Output Sanitization                                │
│ - Redact tokens from any error messages                     │
│ - Limit response sizes to prevent memory exhaustion         │
│ - Structured errors without internal details                │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Runtime Protection                                 │
│ - No filesystem access                                      │
│ - No shell execution (subprocess)                           │
│ - No dynamic code evaluation (eval/exec)                    │
│ - Type-safe with Pydantic                                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 6: Supply Chain Security                              │
│ - Automated CVE scanning via GitHub Actions                 │
│ - Dependabot alerts enabled                                 │
│ - Weekly dependency audits                                  │
│ - Container built on Hummingbird (UBI) for minimal CVEs     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Token Security

The API token is handled with multiple protections:

```python
from pydantic import SecretStr

class Config:
    def __init__(self):
        token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not token:
            raise ConfigurationError("CLOUDFLARE_API_TOKEN required")

        # Store as SecretStr to prevent accidental logging
        self._token = SecretStr(token)

    @property
    def token(self) -> str:
        """Get token value - use sparingly."""
        return self._token.get_secret_value()

    def __repr__(self) -> str:
        return "Config(token=***)"
```

### 2.3 Input Validation Rules

All inputs are validated using Pydantic models:

- **Zone IDs**: Must be 32-character lowercase hex strings
- **Record IDs**: Must be 32-character lowercase hex strings
- **DNS Record Types**: Allowlist of A, AAAA, CNAME, MX, TXT, NS, SRV, CAA, PTR
- **TTL Values**: Range 1-86400
- **Priority Values**: Range 0-65535
- **Extra Fields**: Rejected (Pydantic extra="forbid")

### 2.4 Error Handling

Errors are sanitized before being returned:

```python
class CloudflareApiError(UserError):
    def __init__(self, code: int, message: str):
        # Sanitize message to remove any token references
        token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
        safe_message = message.replace(token, "***") if token else message
        super().__init__(f"Cloudflare API error {code}: {safe_message}")
```

## 3. Minimum Permission Scopes

### 3.1 Read-Only Token (Safest)

```
Zone:Read
DNS:Read
```

**Capabilities:** List zones, list DNS records, view rules
**Risk:** Information disclosure only

### 3.2 DNS Management Token

```
Zone:Read
DNS:Edit
```

**Capabilities:** Full DNS CRUD
**Risk:** DNS hijacking if token compromised

### 3.3 Full Management Token

```
Zone:Read
DNS:Edit
Transform Rules:Edit
Page Rules:Edit
Cache Purge:Edit
```

**Capabilities:** All server features
**Risk:** Full zone control

## 4. Supply Chain Security

### 4.1 Automated CVE Scanning

This project uses GitHub Actions to automatically scan for and address CVEs in dependencies:

1. **Weekly Scheduled Scans**: Every Monday at 9 AM UTC, `pip-audit` scans all dependencies
2. **PR Checks**: Every pull request is scanned before merge
3. **Automatic Updates**: When CVEs are found, an issue is created and a PR with updates is generated
4. **Dependabot**: Enabled for automatic security updates

### 4.2 Container Security

The container image is built on **[Hummingbird Python](https://quay.io/repository/hummingbird/python)**, a minimal Python base image built on Red Hat UBI:

**Why Hummingbird?**

| Advantage | Description |
|-----------|-------------|
| **Minimal CVE Count** | Built with only essential packages, dramatically reducing attack surface compared to general-purpose Python images |
| **Red Hat UBI Foundation** | Enterprise-grade security, compliance (FedRAMP, HIPAA, PCI-DSS), and commercial support available |
| **Rapid Security Updates** | Security patches applied promptly with automated rebuilds |
| **Python Optimized** | Pre-configured with uv package manager for fast, reproducible builds |
| **Non-Root Default** | Runs as non-root user by default for defense in depth |
| **Production Ready** | Proper signal handling, minimal footprint, suitable for production workloads |

**CVE Comparison** (typical counts):

| Base Image | Typical CVE Count |
|------------|-------------------|
| python:3.12 (Debian) | 100-200+ |
| python:3.12-slim | 50-100 |
| python:3.12-alpine | 10-30 |
| Hummingbird Python | <10 |

The minimal package set in Hummingbird images means fewer dependencies to track, patch, and audit

### 4.3 Events Logged

| Event | Level | Fields |
|-------|-------|--------|
| Server startup | INFO | version, capabilities detected |
| Tool invocation | INFO | tool_name, zone_id (not full params) |
| Cloudflare API call | DEBUG | method, path (no auth headers) |
| Permission denied | WARN | tool_name, required_scope |
| Rate limited | WARN | retry_after |
| Error | ERROR | error_type (no internals) |

### 4.4 Never Logged

- API tokens (any form)
- Full request/response bodies
- Record content (may contain secrets)
- Rule expressions (may contain business logic)

## 5. Security Checklist

Before each release:

- [ ] All inputs validated through Pydantic models
- [ ] No token exposure in logs or errors
- [ ] No filesystem operations
- [ ] No shell execution
- [ ] No eval/exec
- [ ] Rate limiting considered
- [ ] Error messages don't leak internals
- [ ] Dependencies scanned for CVEs
- [ ] Container rebuilt with latest UBI

## 6. Reporting Security Issues

Please report security issues to security@crunchtools.com or open a private security advisory on GitHub.

Do NOT open public issues for security vulnerabilities.
