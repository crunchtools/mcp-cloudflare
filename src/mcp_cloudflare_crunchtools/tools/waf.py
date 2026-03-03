"""WAF custom rule tools.

Tools for managing Cloudflare WAF (Web Application Firewall) custom rules.
These rules use the Rulesets API with phase 'http_request_firewall_custom'.

Free plans support up to 5 custom rules.
"""

from typing import Any

from ..client import get_client
from ..models import validate_rule_id, validate_zone_id

WAF_PHASE = "http_request_firewall_custom"

# Valid actions for free/pro plans
VALID_ACTIONS = frozenset({
    "managed_challenge",
    "block",
    "js_challenge",
    "challenge",
    "skip",
    "log",
})


async def _get_waf_ruleset(
    zone_id: str,
) -> dict[str, Any] | None:
    """Find the custom WAF ruleset for a zone, if it exists."""
    client = get_client()
    response = await client.get(
        f"/zones/{zone_id}/rulesets",
        params={"phase": WAF_PHASE},
    )
    for ruleset in response.get("result", []):
        if ruleset.get("phase") == WAF_PHASE and ruleset.get("kind") == "zone":
            result: dict[str, Any] = ruleset
            return result
    return None


async def list_waf_rules(zone_id: str) -> dict[str, Any]:
    """List all WAF custom rules for a zone.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        List of WAF rules with their expressions, actions, and status
    """
    zone_id = validate_zone_id(zone_id)
    client = get_client()

    ruleset = await _get_waf_ruleset(zone_id)
    if not ruleset:
        return {"rules": [], "ruleset_id": None}

    # Fetch the full ruleset to get rule details
    response = await client.get(
        f"/zones/{zone_id}/rulesets/{ruleset['id']}"
    )
    result = response.get("result", {})

    rules = []
    for rule in result.get("rules", []):
        rules.append({
            "id": rule.get("id"),
            "description": rule.get("description", ""),
            "expression": rule.get("expression", ""),
            "action": rule.get("action", ""),
            "enabled": rule.get("enabled", True),
        })

    return {
        "rules": rules,
        "ruleset_id": result.get("id"),
        "rule_count": len(rules),
    }


async def create_waf_rule(
    zone_id: str,
    expression: str,
    action: str,
    description: str = "",
    enabled: bool = True,
) -> dict[str, Any]:
    """Create a new WAF custom rule.

    If no custom WAF ruleset exists for the zone, one will be created.
    Free plans support up to 5 custom rules.

    Args:
        zone_id: Zone ID (32-character hex string)
        expression: Cloudflare filter expression
            (e.g., '(http.request.uri.path contains "xmlrpc.php")')
        action: Action to take (managed_challenge, block, js_challenge,
            challenge, skip, log)
        description: Human-readable description of the rule
        enabled: Whether the rule is enabled (default: true)

    Returns:
        Created rule details
    """
    zone_id = validate_zone_id(zone_id)

    if action not in VALID_ACTIONS:
        return {"error": f"Invalid action. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"}

    client = get_client()
    ruleset = await _get_waf_ruleset(zone_id)

    rule_data = {
        "expression": expression,
        "action": action,
        "description": description,
        "enabled": enabled,
    }

    if ruleset:
        # Add rule to existing ruleset
        response = await client.post(
            f"/zones/{zone_id}/rulesets/{ruleset['id']}/rules",
            json_data=rule_data,
        )
    else:
        # Create new ruleset with this rule
        response = await client.post(
            f"/zones/{zone_id}/rulesets",
            json_data={
                "name": "Custom WAF Rules",
                "description": "WAF custom rules managed via MCP",
                "kind": "zone",
                "phase": WAF_PHASE,
                "rules": [rule_data],
            },
        )

    result = response.get("result", {})
    rules = result.get("rules", [])

    # Return the last rule (the one just created)
    created_rule = rules[-1] if rules else {}

    return {
        "rule": {
            "id": created_rule.get("id"),
            "description": created_rule.get("description", ""),
            "expression": created_rule.get("expression", ""),
            "action": created_rule.get("action", ""),
            "enabled": created_rule.get("enabled", True),
        },
        "ruleset_id": result.get("id"),
        "total_rules": len(rules),
    }


async def update_waf_rule(
    zone_id: str,
    rule_id: str,
    expression: str | None = None,
    action: str | None = None,
    description: str | None = None,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """Update an existing WAF custom rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        rule_id: Rule ID (32-character hex string)
        expression: New filter expression (optional)
        action: New action (optional)
        description: New description (optional)
        enabled: Enable or disable the rule (optional)

    Returns:
        Updated rule details
    """
    zone_id = validate_zone_id(zone_id)
    rule_id = validate_rule_id(rule_id)

    if action is not None and action not in VALID_ACTIONS:
        return {"error": f"Invalid action. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"}

    client = get_client()
    ruleset = await _get_waf_ruleset(zone_id)
    if not ruleset:
        return {"error": "No custom WAF ruleset found for this zone"}

    update_data: dict[str, Any] = {}
    if expression is not None:
        update_data["expression"] = expression
    if action is not None:
        update_data["action"] = action
    if description is not None:
        update_data["description"] = description
    if enabled is not None:
        update_data["enabled"] = enabled

    if not update_data:
        return {"error": "No fields to update"}

    response = await client.patch(
        f"/zones/{zone_id}/rulesets/{ruleset['id']}/rules/{rule_id}",
        json_data=update_data,
    )

    result = response.get("result", {})

    # Find the updated rule in the response
    updated_rule = {}
    for rule in result.get("rules", []):
        if rule.get("id") == rule_id:
            updated_rule = rule
            break

    return {
        "rule": {
            "id": updated_rule.get("id"),
            "description": updated_rule.get("description", ""),
            "expression": updated_rule.get("expression", ""),
            "action": updated_rule.get("action", ""),
            "enabled": updated_rule.get("enabled", True),
        },
    }


async def delete_waf_rule(
    zone_id: str,
    rule_id: str,
) -> dict[str, Any]:
    """Delete a WAF custom rule.

    Args:
        zone_id: Zone ID (32-character hex string)
        rule_id: Rule ID (32-character hex string)

    Returns:
        Deletion confirmation
    """
    zone_id = validate_zone_id(zone_id)
    rule_id = validate_rule_id(rule_id)
    client = get_client()

    ruleset = await _get_waf_ruleset(zone_id)
    if not ruleset:
        return {"error": "No custom WAF ruleset found for this zone"}

    await client.delete(
        f"/zones/{zone_id}/rulesets/{ruleset['id']}/rules/{rule_id}",
    )

    return {"deleted": True, "rule_id": rule_id}
