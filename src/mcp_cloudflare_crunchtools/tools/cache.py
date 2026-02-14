"""Cache management tools.

Tools for purging Cloudflare cache.
"""

from typing import Any

from ..client import get_client
from ..models import validate_zone_id


async def purge_cache(
    zone_id: str,
    purge_everything: bool = False,
    files: list[str] | None = None,
    tags: list[str] | None = None,
    hosts: list[str] | None = None,
    prefixes: list[str] | None = None,
) -> dict[str, Any]:
    """Purge cached content from Cloudflare's edge.

    You can purge by:
    - Everything (purge_everything=True)
    - Specific URLs (files)
    - Cache tags (tags) - requires Enterprise
    - Hostnames (hosts) - requires Enterprise
    - URL prefixes (prefixes) - requires Enterprise

    Args:
        zone_id: Zone ID (32-character hex string)
        purge_everything: Purge all cached content (use with caution)
        files: List of URLs to purge (max 30)
        tags: List of cache tags to purge (Enterprise only)
        hosts: List of hostnames to purge (Enterprise only)
        prefixes: List of URL prefixes to purge (Enterprise only)

    Returns:
        Purge operation result

    Examples:
        # Purge everything
        purge_cache(zone_id="...", purge_everything=True)

        # Purge specific URLs
        purge_cache(zone_id="...", files=[
            "https://example.com/styles.css",
            "https://example.com/script.js"
        ])

        # Purge by cache tag (Enterprise)
        purge_cache(zone_id="...", tags=["static-assets", "images"])
    """
    zone_id = validate_zone_id(zone_id)
    client = get_client()

    body: dict[str, Any] = {}

    if purge_everything:
        body["purge_everything"] = True
    elif files:
        # Limit to 30 files per request
        body["files"] = files[:30]
    elif tags:
        body["tags"] = tags[:30]
    elif hosts:
        body["hosts"] = hosts[:30]
    elif prefixes:
        body["prefixes"] = prefixes[:30]
    else:
        return {
            "error": "Must specify purge_everything, files, tags, hosts, or prefixes"
        }

    response = await client.post(f"/zones/{zone_id}/purge_cache", json_data=body)

    result = response.get("result", {})

    return {
        "success": response.get("success", False),
        "id": result.get("id"),
    }
