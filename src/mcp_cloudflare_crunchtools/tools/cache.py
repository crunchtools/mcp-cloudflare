"""Cache management tools.

Tools for purging Cloudflare cache.
"""

from typing import Any

from ..client import get_client
from ..models import validate_hex_id


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
    - Cache tags (tags)
    - Hostnames (hosts)
    - URL prefixes (prefixes)

    Every method is available on every plan, Free included. Prefer the
    narrowest one that does the job over purge_everything.

    Args:
        zone_id: Zone ID (32-character hex string)
        purge_everything: Purge all cached content (use with caution)
        files: List of URLs to purge (max 30)
        tags: List of cache tags to purge
        hosts: List of hostnames to purge
        prefixes: List of URL prefixes to purge

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

        # Purge by cache tag
        purge_cache(zone_id="...", tags=["static-assets", "images"])

        # Purge one hostname, leaving the rest of the zone cached
        purge_cache(zone_id="...", hosts=["dev.example.com"])
    """
    zone_id = validate_hex_id(zone_id, "zone_id")
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
        return {"error": "Must specify purge_everything, files, tags, hosts, or prefixes"}

    response = await client.post(f"/zones/{zone_id}/purge_cache", json_data=body)

    result = response.get("result", {})

    return {
        "success": response.get("success", False),
        "id": result.get("id"),
    }
