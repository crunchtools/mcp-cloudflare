"""Pydantic models for input validation.

All tool inputs are validated through these models to prevent injection attacks
and ensure data integrity before making API calls.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid DNS record types - intentionally restrictive
DNS_RECORD_TYPES = frozenset({"A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "CAA", "PTR"})

# Cloudflare identifies zones, DNS records and rules with the same 32-hex form.
HEX_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")

# Cloudflare API field limits.
MAX_RECORD_NAME = 255
MAX_RECORD_CONTENT = 2048
MAX_TTL_SECONDS = 86400
MAX_PRIORITY = 65535
MAX_COMMENT = 500
MAX_HEADER_NAME = 256
MAX_EXPRESSION = 4096
MAX_ACTION_ID = 100
MAX_RULE_ACTIONS = 10
MAX_PAGE_RULE_ACTIONS = 20
MAX_PAGE_RULE_TARGETS = 10
MAX_PAGE_RULE_PRIORITY = 1000
MAX_PURGE_ITEMS = 30


def validate_hex_id(value: str, field_name: str) -> str:
    """Validate an identifier is a 32-character hex string."""
    if not HEX_ID_PATTERN.match(value):
        raise ValueError(f"{field_name} must be 32-character hex string")
    return value


def validate_record_type(record_type: str) -> str:
    """Normalise a DNS record type to upper case and check it is supported."""
    upper = record_type.upper()
    if upper not in DNS_RECORD_TYPES:
        allowed = ", ".join(sorted(DNS_RECORD_TYPES))
        raise ValueError(f"Invalid record type. Allowed: {allowed}")
    return upper


class ZoneInput(BaseModel):
    """Validated zone identifier input.

    Either zone_id or zone_name should be provided, but not both required.
    """

    model_config = ConfigDict(extra="forbid")

    zone_id: str | None = Field(default=None, description="Zone ID (32-character hex string)")
    zone_name: str | None = Field(default=None, description="Zone name (domain like example.com)")

    @field_validator("zone_id")
    @classmethod
    def validate_zone_id_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validate_hex_id(v, "zone_id")


class DnsRecordInput(BaseModel):
    """Validated DNS record input for creation."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="DNS record type (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)")
    name: str = Field(
        ...,
        min_length=1,
        max_length=MAX_RECORD_NAME,
        description="DNS record name (e.g., www or @ for root)",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=MAX_RECORD_CONTENT,
        description="DNS record content (e.g., IP address)",
    )
    ttl: int = Field(default=1, ge=1, le=MAX_TTL_SECONDS, description="TTL in seconds (1 = auto)")
    proxied: bool = Field(default=False, description="Whether to proxy through Cloudflare")
    priority: int | None = Field(
        default=None, ge=0, le=MAX_PRIORITY, description="Priority (required for MX and SRV)"
    )
    comment: str | None = Field(
        default=None, max_length=MAX_COMMENT, description="Optional comment for the record"
    )

    @field_validator("type")
    @classmethod
    def check_record_type(cls, v: str) -> str:
        return validate_record_type(v)


class DnsRecordUpdateInput(BaseModel):
    """Validated DNS record input for updates."""

    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(default=None, description="DNS record type")
    name: str | None = Field(
        default=None, min_length=1, max_length=MAX_RECORD_NAME, description="DNS record name"
    )
    content: str | None = Field(
        default=None, min_length=1, max_length=MAX_RECORD_CONTENT, description="DNS record content"
    )
    ttl: int | None = Field(default=None, ge=1, le=MAX_TTL_SECONDS, description="TTL in seconds")
    proxied: bool | None = Field(default=None, description="Whether to proxy through Cloudflare")
    priority: int | None = Field(default=None, ge=0, le=MAX_PRIORITY, description="Priority")
    comment: str | None = Field(
        default=None, max_length=MAX_COMMENT, description="Optional comment"
    )

    @field_validator("type")
    @classmethod
    def check_record_type(cls, v: str | None) -> str | None:
        return None if v is None else validate_record_type(v)


class TransformRuleAction(BaseModel):
    """Transform rule action for header modifications."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["set", "add", "remove"] = Field(..., description="Operation to perform")
    header: str = Field(..., min_length=1, max_length=MAX_HEADER_NAME, description="Header name")
    value: str | None = Field(
        default=None,
        max_length=MAX_RECORD_CONTENT,
        description="Header value (required for set/add)",
    )


class TransformRule(BaseModel):
    """Transform rule definition."""

    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        ...,
        min_length=1,
        max_length=MAX_EXPRESSION,
        description="Rule expression (Cloudflare filter)",
    )
    description: str = Field(default="", max_length=MAX_COMMENT, description="Rule description")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    actions: list[TransformRuleAction] = Field(
        ..., min_length=1, max_length=MAX_RULE_ACTIONS, description="Actions to perform"
    )


class UrlRewriteRule(BaseModel):
    """URL rewrite rule definition."""

    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        ..., min_length=1, max_length=MAX_EXPRESSION, description="Rule expression"
    )
    description: str = Field(default="", max_length=MAX_COMMENT, description="Rule description")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    # Path rewrite
    path_value: str | None = Field(
        default=None, max_length=MAX_RECORD_CONTENT, description="Static path value"
    )
    path_expression: str | None = Field(
        default=None, max_length=MAX_EXPRESSION, description="Dynamic path expression"
    )
    # Query rewrite
    query_value: str | None = Field(
        default=None, max_length=MAX_RECORD_CONTENT, description="Static query value"
    )
    query_expression: str | None = Field(
        default=None, max_length=MAX_EXPRESSION, description="Dynamic query expression"
    )


class PageRuleAction(BaseModel):
    """Page rule action."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=MAX_ACTION_ID, description="Action ID")
    value: str | int | bool | dict[str, Any] | None = Field(
        default=None, description="Action value"
    )


class PageRuleInput(BaseModel):
    """Page rule input for creation/update."""

    model_config = ConfigDict(extra="forbid")

    targets: list[dict[str, Any]] = Field(
        ..., min_length=1, max_length=MAX_PAGE_RULE_TARGETS, description="URL pattern targets"
    )
    actions: list[PageRuleAction] = Field(
        ..., min_length=1, max_length=MAX_PAGE_RULE_ACTIONS, description="Actions to perform"
    )
    priority: int = Field(default=1, ge=1, le=MAX_PAGE_RULE_PRIORITY, description="Rule priority")
    status: Literal["active", "disabled"] = Field(default="active", description="Rule status")


class CachePurgeInput(BaseModel):
    """Cache purge input."""

    model_config = ConfigDict(extra="forbid")

    purge_everything: bool = Field(default=False, description="Purge all cached content")
    files: list[str] | None = Field(
        default=None, max_length=MAX_PURGE_ITEMS, description="URLs to purge (max 30)"
    )
    tags: list[str] | None = Field(
        default=None, max_length=MAX_PURGE_ITEMS, description="Cache tags to purge"
    )
    hosts: list[str] | None = Field(
        default=None, max_length=MAX_PURGE_ITEMS, description="Hostnames to purge"
    )
    prefixes: list[str] | None = Field(
        default=None, max_length=MAX_PURGE_ITEMS, description="URL prefixes to purge"
    )
