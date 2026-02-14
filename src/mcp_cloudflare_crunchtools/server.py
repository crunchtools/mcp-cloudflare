"""FastMCP server setup for Cloudflare MCP.

This module creates and configures the MCP server with all tools.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from .tools import (
    # Cache
    purge_cache,
    # DNS
    create_dns_record,
    delete_dns_record,
    get_dns_record,
    list_dns_records,
    update_dns_record,
    # Page Rules
    create_page_rule,
    delete_page_rule,
    list_page_rules,
    update_page_rule,
    # Transform Rules
    list_request_header_rules,
    list_response_header_rules,
    list_url_rewrite_rules,
    set_request_header_rules,
    set_response_header_rules,
    set_url_rewrite_rules,
    # Zones
    get_zone,
    list_zones,
)

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    name="mcp-cloudflare-crunchtools",
    version="0.1.0",
    description="Secure MCP server for Cloudflare DNS, Transform Rules, Page Rules, and Cache",
)


# Register Zone tools


@mcp.tool()
async def list_zones_tool(
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """List all Cloudflare zones accessible by the API token.

    Args:
        name: Filter by zone name (domain)
        status: Filter by status (active, pending, initializing, moved, deleted)
        page: Page number for pagination (default: 1)
        per_page: Results per page, max 50 (default: 50)

    Returns:
        List of zones with pagination info
    """
    return await list_zones(name=name, status=status, page=page, per_page=per_page)


@mcp.tool()
async def get_zone_tool(
    zone_id: str | None = None,
    zone_name: str | None = None,
) -> dict[str, Any]:
    """Get Cloudflare zone details by ID or name.

    Provide either zone_id or zone_name, not both.

    Args:
        zone_id: Zone ID (32-character hex string)
        zone_name: Zone name (domain like example.com)

    Returns:
        Zone details
    """
    return await get_zone(zone_id=zone_id, zone_name=zone_name)


# Register DNS tools


@mcp.tool()
async def list_dns_records_tool(
    zone_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> dict[str, Any]:
    """List DNS records for a Cloudflare zone.

    Args:
        zone_id: Zone ID (32-character hex string)
        type: Filter by record type (A, AAAA, CNAME, MX, TXT, etc.)
        name: Filter by record name
        content: Filter by record content
        page: Page number (default: 1)
        per_page: Results per page, max 100 (default: 100)

    Returns:
        List of DNS records with pagination info
    """
    return await list_dns_records(
        zone_id=zone_id, type=type, name=name, content=content, page=page, per_page=per_page
    )


@mcp.tool()
async def get_dns_record_tool(
    zone_id: str,
    record_id: str,
) -> dict[str, Any]:
    """Get a single DNS record by ID.

    Args:
        zone_id: Zone ID (32-character hex string)
        record_id: DNS record ID (32-character hex string)

    Returns:
        DNS record details
    """
    return await get_dns_record(zone_id=zone_id, record_id=record_id)


@mcp.tool()
async def create_dns_record_tool(
    zone_id: str,
    type: str,
    name: str,
    content: str,
    ttl: int = 1,
    proxied: bool = False,
    priority: int | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Create a new DNS record.

    Args:
        zone_id: Zone ID (32-character hex string)
        type: Record type (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
        name: Record name (e.g., www, @, subdomain.example.com)
        content: Record content (IP address, target domain, etc.)
        ttl: TTL in seconds, 1 = auto (default: 1)
        proxied: Proxy through Cloudflare (default: false)
        priority: Priority for MX/SRV records
        comment: Optional comment

    Returns:
        Created DNS record details
    """
    return await create_dns_record(
        zone_id=zone_id,
        type=type,
        name=name,
        content=content,
        ttl=ttl,
        proxied=proxied,
        priority=priority,
        comment=comment,
    )


@mcp.tool()
async def update_dns_record_tool(
    zone_id: str,
    record_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    ttl: int | None = None,
    proxied: bool | None = None,
    priority: int | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Update an existing DNS record.

    Args:
        zone_id: Zone ID (32-character hex string)
        record_id: DNS record ID (32-character hex string)
        type: Record type (optional)
        name: Record name (optional)
        content: Record content (optional)
        ttl: TTL in seconds (optional)
        proxied: Proxy through Cloudflare (optional)
        priority: Priority (optional)
        comment: Comment (optional)

    Returns:
        Updated DNS record details
    """
    return await update_dns_record(
        zone_id=zone_id,
        record_id=record_id,
        type=type,
        name=name,
        content=content,
        ttl=ttl,
        proxied=proxied,
        priority=priority,
        comment=comment,
    )


@mcp.tool()
async def delete_dns_record_tool(
    zone_id: str,
    record_id: str,
) -> dict[str, Any]:
    """Delete a DNS record.

    Args:
        zone_id: Zone ID (32-character hex string)
        record_id: DNS record ID (32-character hex string)

    Returns:
        Deletion confirmation
    """
    return await delete_dns_record(zone_id=zone_id, record_id=record_id)


# Register Transform Rules tools


@mcp.tool()
async def list_request_header_rules_tool(zone_id: str) -> dict[str, Any]:
    """List request header modification rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Ruleset with request header modification rules
    """
    return await list_request_header_rules(zone_id=zone_id)


@mcp.tool()
async def set_request_header_rules_tool(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set request header modification rules (replaces all existing rules).

    Each rule should have:
    - expression: Filter expression (e.g., "true" for all requests)
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"headers": {"Header-Name": {"operation": "set|add|remove", "value": "..."}}}

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset
    """
    return await set_request_header_rules(zone_id=zone_id, rules=rules)


@mcp.tool()
async def list_response_header_rules_tool(zone_id: str) -> dict[str, Any]:
    """List response header modification rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Ruleset with response header modification rules
    """
    return await list_response_header_rules(zone_id=zone_id)


@mcp.tool()
async def set_response_header_rules_tool(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set response header modification rules (replaces all existing rules).

    Each rule should have:
    - expression: Filter expression (e.g., "true" for all responses)
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"headers": {"Header-Name": {"operation": "set|add|remove", "value": "..."}}}

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset
    """
    return await set_response_header_rules(zone_id=zone_id, rules=rules)


@mcp.tool()
async def list_url_rewrite_rules_tool(zone_id: str) -> dict[str, Any]:
    """List URL rewrite rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Ruleset with URL rewrite rules
    """
    return await list_url_rewrite_rules(zone_id=zone_id)


@mcp.tool()
async def set_url_rewrite_rules_tool(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set URL rewrite rules (replaces all existing rules).

    Each rule should have:
    - expression: Filter expression
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"uri": {"path": {"value": "..."}, "query": {"value": "..."}}}

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset
    """
    return await set_url_rewrite_rules(zone_id=zone_id, rules=rules)


# Register Page Rules tools


@mcp.tool()
async def list_page_rules_tool(
    zone_id: str,
    status: str | None = None,
    order: str = "priority",
) -> dict[str, Any]:
    """List all page rules for a zone.

    Args:
        zone_id: Zone ID (32-character hex string)
        status: Filter by status (active, disabled)
        order: Sort order (status, priority)

    Returns:
        List of page rules
    """
    return await list_page_rules(zone_id=zone_id, status=status, order=order)


@mcp.tool()
async def create_page_rule_tool(
    zone_id: str,
    targets: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    priority: int = 1,
    status: str = "active",
) -> dict[str, Any]:
    """Create a new page rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        targets: URL patterns, e.g., [{"target": "url", "constraint": {"operator": "matches", "value": "*example.com/*"}}]
        actions: Actions, e.g., [{"id": "forwarding_url", "value": {"url": "https://...", "status_code": 301}}]
        priority: Rule priority 1-1000 (default: 1)
        status: active or disabled (default: active)

    Returns:
        Created page rule details
    """
    return await create_page_rule(
        zone_id=zone_id, targets=targets, actions=actions, priority=priority, status=status
    )


@mcp.tool()
async def update_page_rule_tool(
    zone_id: str,
    rule_id: str,
    targets: list[dict[str, Any]] | None = None,
    actions: list[dict[str, Any]] | None = None,
    priority: int | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Update an existing page rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        rule_id: Page rule ID (32-character hex string)
        targets: URL patterns (optional)
        actions: Actions (optional)
        priority: Priority (optional)
        status: Status (optional)

    Returns:
        Updated page rule details
    """
    return await update_page_rule(
        zone_id=zone_id,
        rule_id=rule_id,
        targets=targets,
        actions=actions,
        priority=priority,
        status=status,
    )


@mcp.tool()
async def delete_page_rule_tool(
    zone_id: str,
    rule_id: str,
) -> dict[str, Any]:
    """Delete a page rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        rule_id: Page rule ID (32-character hex string)

    Returns:
        Deletion confirmation
    """
    return await delete_page_rule(zone_id=zone_id, rule_id=rule_id)


# Register Cache tools


@mcp.tool()
async def purge_cache_tool(
    zone_id: str,
    purge_everything: bool = False,
    files: list[str] | None = None,
    tags: list[str] | None = None,
    hosts: list[str] | None = None,
    prefixes: list[str] | None = None,
) -> dict[str, Any]:
    """Purge cached content from Cloudflare's edge.

    Use one of: purge_everything, files, tags, hosts, or prefixes.
    tags, hosts, and prefixes require Enterprise plan.

    Args:
        zone_id: Zone ID (32-character hex string)
        purge_everything: Purge all cached content
        files: URLs to purge (max 30)
        tags: Cache tags to purge (Enterprise)
        hosts: Hostnames to purge (Enterprise)
        prefixes: URL prefixes to purge (Enterprise)

    Returns:
        Purge operation result
    """
    return await purge_cache(
        zone_id=zone_id,
        purge_everything=purge_everything,
        files=files,
        tags=tags,
        hosts=hosts,
        prefixes=prefixes,
    )
