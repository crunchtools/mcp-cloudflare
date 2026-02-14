"""Page Rules management tools.

Tools for managing Cloudflare Page Rules.
"""

from typing import Any

from ..client import get_client
from ..models import validate_rule_id, validate_zone_id


async def list_page_rules(
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
        Dictionary containing page rules list
    """
    zone_id = validate_zone_id(zone_id)
    client = get_client()

    params: dict[str, Any] = {
        "order": order,
    }

    if status:
        params["status"] = status

    response = await client.get(f"/zones/{zone_id}/pagerules", params=params)

    return {
        "page_rules": response.get("result", []),
    }


async def create_page_rule(
    zone_id: str,
    targets: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    priority: int = 1,
    status: str = "active",
) -> dict[str, Any]:
    """Create a new page rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        targets: URL pattern targets. Example:
            [{"target": "url", "constraint": {"operator": "matches", "value": "..."}}]
        actions: Actions to perform. Example:
            [{"id": "forwarding_url", "value": {"url": "...", "status_code": 301}}]
        priority: Rule priority (1-1000, lower = higher priority)
        status: Rule status (active, disabled)

    Returns:
        Created page rule details

    Common actions:
    - forwarding_url: Redirect to another URL
    - always_https: Force HTTPS
    - cache_level: Set cache level (bypass, basic, simplified, aggressive, cache_everything)
    - browser_cache_ttl: Set browser cache TTL
    - edge_cache_ttl: Set edge cache TTL
    - disable_security: Disable security features
    - ssl: Set SSL mode (off, flexible, full, strict)
    """
    zone_id = validate_zone_id(zone_id)
    client = get_client()

    body = {
        "targets": targets,
        "actions": actions,
        "priority": priority,
        "status": status,
    }

    response = await client.post(f"/zones/{zone_id}/pagerules", json_data=body)

    return {"page_rule": response.get("result", {})}


async def update_page_rule(
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
        targets: URL pattern targets (optional)
        actions: Actions to perform (optional)
        priority: Rule priority (optional)
        status: Rule status (optional)

    Returns:
        Updated page rule details
    """
    zone_id = validate_zone_id(zone_id)
    rule_id = validate_rule_id(rule_id)
    client = get_client()

    body: dict[str, Any] = {}

    if targets is not None:
        body["targets"] = targets
    if actions is not None:
        body["actions"] = actions
    if priority is not None:
        body["priority"] = priority
    if status is not None:
        body["status"] = status

    if not body:
        return {"error": "No fields provided for update"}

    response = await client.patch(f"/zones/{zone_id}/pagerules/{rule_id}", json_data=body)

    return {"page_rule": response.get("result", {})}


async def delete_page_rule(
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
    zone_id = validate_zone_id(zone_id)
    rule_id = validate_rule_id(rule_id)
    client = get_client()

    response = await client.delete(f"/zones/{zone_id}/pagerules/{rule_id}")

    return {
        "deleted": True,
        "id": response.get("result", {}).get("id", rule_id),
    }
