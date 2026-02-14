"""Pydantic models for input validation.

All tool inputs are validated through these models to prevent injection attacks
and ensure data integrity before making API calls.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid DNS record types - intentionally restrictive
DNS_RECORD_TYPES = frozenset({"A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "CAA", "PTR"})

# Regex patterns for validation
ZONE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
RECORD_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
RULE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def validate_zone_id(zone_id: str) -> str:
    """Validate a zone ID is a 32-character hex string."""
    if not ZONE_ID_PATTERN.match(zone_id):
        raise ValueError("zone_id must be 32-character hex string")
    return zone_id


def validate_record_id(record_id: str) -> str:
    """Validate a record ID is a 32-character hex string."""
    if not RECORD_ID_PATTERN.match(record_id):
        raise ValueError("record_id must be 32-character hex string")
    return record_id


def validate_rule_id(rule_id: str) -> str:
    """Validate a rule ID is a 32-character hex string."""
    if not RULE_ID_PATTERN.match(rule_id):
        raise ValueError("rule_id must be 32-character hex string")
    return rule_id


class ZoneInput(BaseModel):
    """Validated zone identifier input.

    Either zone_id or zone_name should be provided, but not both required.
    """

    model_config = ConfigDict(extra="forbid")

    zone_id: str | None = Field(
        default=None, description="Zone ID (32-character hex string)"
    )
    zone_name: str | None = Field(
        default=None, description="Zone name (domain like example.com)"
    )

    @field_validator("zone_id")
    @classmethod
    def validate_zone_id_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return validate_zone_id(v)


class DnsRecordInput(BaseModel):
    """Validated DNS record input for creation."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="DNS record type (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)")
    name: str = Field(
        ..., min_length=1, max_length=255, description="DNS record name (e.g., www or @ for root)"
    )
    content: str = Field(
        ..., min_length=1, max_length=2048, description="DNS record content (e.g., IP address)"
    )
    ttl: int = Field(
        default=1, ge=1, le=86400, description="TTL in seconds (1 = auto)"
    )
    proxied: bool = Field(
        default=False, description="Whether to proxy through Cloudflare"
    )
    priority: int | None = Field(
        default=None, ge=0, le=65535, description="Priority (required for MX and SRV)"
    )
    comment: str | None = Field(
        default=None, max_length=500, description="Optional comment for the record"
    )

    @field_validator("type")
    @classmethod
    def validate_record_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in DNS_RECORD_TYPES:
            allowed = ", ".join(sorted(DNS_RECORD_TYPES))
            raise ValueError(f"Invalid record type. Allowed: {allowed}")
        return v_upper


class DnsRecordUpdateInput(BaseModel):
    """Validated DNS record input for updates."""

    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(
        default=None, description="DNS record type"
    )
    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="DNS record name"
    )
    content: str | None = Field(
        default=None, min_length=1, max_length=2048, description="DNS record content"
    )
    ttl: int | None = Field(
        default=None, ge=1, le=86400, description="TTL in seconds"
    )
    proxied: bool | None = Field(
        default=None, description="Whether to proxy through Cloudflare"
    )
    priority: int | None = Field(
        default=None, ge=0, le=65535, description="Priority"
    )
    comment: str | None = Field(
        default=None, max_length=500, description="Optional comment"
    )

    @field_validator("type")
    @classmethod
    def validate_record_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_upper = v.upper()
        if v_upper not in DNS_RECORD_TYPES:
            allowed = ", ".join(sorted(DNS_RECORD_TYPES))
            raise ValueError(f"Invalid record type. Allowed: {allowed}")
        return v_upper


class TransformRuleAction(BaseModel):
    """Transform rule action for header modifications."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["set", "add", "remove"] = Field(
        ..., description="Operation to perform"
    )
    header: str = Field(
        ..., min_length=1, max_length=256, description="Header name"
    )
    value: str | None = Field(
        default=None, max_length=2048, description="Header value (required for set/add)"
    )


class TransformRule(BaseModel):
    """Transform rule definition."""

    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        ..., min_length=1, max_length=4096, description="Rule expression (Cloudflare filter)"
    )
    description: str = Field(
        default="", max_length=500, description="Rule description"
    )
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    actions: list[TransformRuleAction] = Field(
        ..., min_length=1, max_length=10, description="Actions to perform"
    )


class UrlRewriteRule(BaseModel):
    """URL rewrite rule definition."""

    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        ..., min_length=1, max_length=4096, description="Rule expression"
    )
    description: str = Field(default="", max_length=500, description="Rule description")
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    # Path rewrite
    path_value: str | None = Field(
        default=None, max_length=2048, description="Static path value"
    )
    path_expression: str | None = Field(
        default=None, max_length=4096, description="Dynamic path expression"
    )
    # Query rewrite
    query_value: str | None = Field(
        default=None, max_length=2048, description="Static query value"
    )
    query_expression: str | None = Field(
        default=None, max_length=4096, description="Dynamic query expression"
    )


class PageRuleAction(BaseModel):
    """Page rule action."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, max_length=100, description="Action ID")
    value: str | int | bool | dict | None = Field(
        default=None, description="Action value"
    )


class PageRuleInput(BaseModel):
    """Page rule input for creation/update."""

    model_config = ConfigDict(extra="forbid")

    targets: list[dict] = Field(
        ..., min_length=1, max_length=10, description="URL pattern targets"
    )
    actions: list[PageRuleAction] = Field(
        ..., min_length=1, max_length=20, description="Actions to perform"
    )
    priority: int = Field(
        default=1, ge=1, le=1000, description="Rule priority"
    )
    status: Literal["active", "disabled"] = Field(
        default="active", description="Rule status"
    )


class CachePurgeInput(BaseModel):
    """Cache purge input."""

    model_config = ConfigDict(extra="forbid")

    purge_everything: bool = Field(
        default=False, description="Purge all cached content"
    )
    files: list[str] | None = Field(
        default=None, max_length=30, description="URLs to purge (max 30)"
    )
    tags: list[str] | None = Field(
        default=None, max_length=30, description="Cache tags to purge"
    )
    hosts: list[str] | None = Field(
        default=None, max_length=30, description="Hostnames to purge"
    )
    prefixes: list[str] | None = Field(
        default=None, max_length=30, description="URL prefixes to purge"
    )
