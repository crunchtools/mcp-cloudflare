"""Zone management tools.

Tools for listing and retrieving Cloudflare zone information.
"""

from typing import Any

from ..client import get_client
from ..models import validate_zone_id


async def list_zones(
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """List all zones accessible by the API token.

    Args:
        name: Filter by zone name (domain)
        status: Filter by status (active, pending, initializing, moved, deleted)
        page: Page number for pagination
        per_page: Number of results per page (max 50)

    Returns:
        Dictionary containing zones list and pagination info
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 50),
    }

    if name:
        params["name"] = name
    if status:
        params["status"] = status

    response = await client.get("/zones", params=params)

    return {
        "zones": response.get("result", []),
        "result_info": response.get("result_info", {}),
    }


async def get_zone(
    zone_id: str | None = None,
    zone_name: str | None = None,
) -> dict[str, Any]:
    """Get zone details by ID or name.

    Args:
        zone_id: Zone ID (32-character hex string)
        zone_name: Zone name (domain like example.com)

    Returns:
        Zone details dictionary

    Note:
        Provide either zone_id or zone_name, not both.
        If zone_name is provided, a lookup will be performed first.
    """
    client = get_client()

    # If zone_name provided, look up the zone_id first
    if zone_name and not zone_id:
        zones_response = await client.get("/zones", params={"name": zone_name})
        zones = zones_response.get("result", [])
        if not zones:
            return {"error": f"Zone not found: {zone_name}"}
        zone_id = zones[0]["id"]

    if not zone_id:
        return {"error": "Either zone_id or zone_name must be provided"}

    # Validate zone_id format
    zone_id = validate_zone_id(zone_id)

    response = await client.get(f"/zones/{zone_id}")

    return {"zone": response.get("result", {})}
