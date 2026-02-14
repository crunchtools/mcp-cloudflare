"""Transform Rules management tools.

Tools for managing Cloudflare Transform Rules including request headers,
response headers, and URL rewrites.
"""

from typing import Any

from ..client import get_client
from ..models import validate_zone_id

# Cloudflare ruleset phases for transform rules
PHASE_REQUEST_HEADERS = "http_request_late_transform"
PHASE_RESPONSE_HEADERS = "http_response_headers_transform"
PHASE_URL_REWRITE = "http_request_transform"


async def _get_ruleset(zone_id: str, phase: str) -> dict[str, Any]:
    """Get or create a ruleset for a specific phase."""
    client = get_client()

    # List rulesets to find the one for this phase
    response = await client.get(f"/zones/{zone_id}/rulesets")
    rulesets = response.get("result", [])

    for ruleset in rulesets:
        if ruleset.get("phase") == phase:
            # Get full ruleset with rules
            ruleset_id = ruleset["id"]
            ruleset_response = await client.get(f"/zones/{zone_id}/rulesets/{ruleset_id}")
            result: dict[str, Any] = ruleset_response.get("result", {})
            return result

    # No ruleset found for this phase
    return {}


async def _update_ruleset(
    zone_id: str,
    phase: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Update or create a ruleset for a specific phase."""
    client = get_client()

    # Check if ruleset exists
    response = await client.get(f"/zones/{zone_id}/rulesets")
    rulesets = response.get("result", [])

    existing_ruleset_id = None
    for ruleset in rulesets:
        if ruleset.get("phase") == phase:
            existing_ruleset_id = ruleset["id"]
            break

    body: dict[str, Any] = {
        "rules": rules,
    }

    if existing_ruleset_id:
        # Update existing ruleset
        response = await client.put(
            f"/zones/{zone_id}/rulesets/{existing_ruleset_id}",
            json_data=body,
        )
    else:
        # Create new ruleset
        body["name"] = f"MCP Managed {phase}"
        body["kind"] = "zone"
        body["phase"] = phase
        response = await client.post(
            f"/zones/{zone_id}/rulesets",
            json_data=body,
        )

    result: dict[str, Any] = response.get("result", {})
    return result


# Request Header Rules


async def list_request_header_rules(zone_id: str) -> dict[str, Any]:
    """List request header modification rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Dictionary containing the ruleset and its rules
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _get_ruleset(zone_id, PHASE_REQUEST_HEADERS)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_REQUEST_HEADERS,
        "rules": ruleset.get("rules", []),
    }


async def set_request_header_rules(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set request header modification rules.

    This replaces all existing rules in the phase. Each rule should have:
    - expression: Filter expression (e.g., "true" for all requests)
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"headers": {...}}

    Example rule:
    {
        "expression": "true",
        "description": "Add custom header",
        "action": "rewrite",
        "action_parameters": {
            "headers": {
                "X-Custom-Header": {
                    "operation": "set",
                    "value": "custom-value"
                }
            }
        }
    }

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset details
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _update_ruleset(zone_id, PHASE_REQUEST_HEADERS, rules)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_REQUEST_HEADERS,
        "rules": ruleset.get("rules", []),
    }


# Response Header Rules


async def list_response_header_rules(zone_id: str) -> dict[str, Any]:
    """List response header modification rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Dictionary containing the ruleset and its rules
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _get_ruleset(zone_id, PHASE_RESPONSE_HEADERS)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_RESPONSE_HEADERS,
        "rules": ruleset.get("rules", []),
    }


async def set_response_header_rules(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set response header modification rules.

    This replaces all existing rules in the phase. Each rule should have:
    - expression: Filter expression (e.g., "true" for all responses)
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"headers": {...}}

    Example rule:
    {
        "expression": "true",
        "description": "Add security headers",
        "action": "rewrite",
        "action_parameters": {
            "headers": {
                "X-Content-Type-Options": {
                    "operation": "set",
                    "value": "nosniff"
                }
            }
        }
    }

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset details
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _update_ruleset(zone_id, PHASE_RESPONSE_HEADERS, rules)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_RESPONSE_HEADERS,
        "rules": ruleset.get("rules", []),
    }


# URL Rewrite Rules


async def list_url_rewrite_rules(zone_id: str) -> dict[str, Any]:
    """List URL rewrite rules.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Dictionary containing the ruleset and its rules
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _get_ruleset(zone_id, PHASE_URL_REWRITE)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_URL_REWRITE,
        "rules": ruleset.get("rules", []),
    }


async def set_url_rewrite_rules(
    zone_id: str,
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Set URL rewrite rules.

    This replaces all existing rules in the phase. Each rule should have:
    - expression: Filter expression
    - description: Human-readable description
    - action: "rewrite"
    - action_parameters: {"uri": {"path": {...}, "query": {...}}}

    Example rule:
    {
        "expression": "http.request.uri.path eq \"/old-path\"",
        "description": "Rewrite old path to new path",
        "action": "rewrite",
        "action_parameters": {
            "uri": {
                "path": {
                    "value": "/new-path"
                }
            }
        }
    }

    Args:
        zone_id: Zone ID (32-character hex string)
        rules: List of rule definitions

    Returns:
        Updated ruleset details
    """
    zone_id = validate_zone_id(zone_id)
    ruleset = await _update_ruleset(zone_id, PHASE_URL_REWRITE, rules)

    return {
        "ruleset_id": ruleset.get("id"),
        "phase": PHASE_URL_REWRITE,
        "rules": ruleset.get("rules", []),
    }
