"""DNS record management tools.

Tools for CRUD operations on Cloudflare DNS records.
"""

from typing import Any

from ..client import get_client
from ..models import (
    DnsRecordInput,
    DnsRecordUpdateInput,
    validate_record_id,
    validate_zone_id,
)


async def list_dns_records(
    zone_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> dict[str, Any]:
    """List DNS records for a zone.

    Args:
        zone_id: Zone ID (32-character hex string)
        type: Filter by record type (A, AAAA, CNAME, MX, TXT, etc.)
        name: Filter by record name
        content: Filter by record content
        page: Page number for pagination
        per_page: Number of results per page (max 100)

    Returns:
        Dictionary containing DNS records list and pagination info
    """
    zone_id = validate_zone_id(zone_id)
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
    }

    if type:
        params["type"] = type.upper()
    if name:
        params["name"] = name
    if content:
        params["content"] = content

    response = await client.get(f"/zones/{zone_id}/dns_records", params=params)

    return {
        "records": response.get("result", []),
        "result_info": response.get("result_info", {}),
    }


async def get_dns_record(
    zone_id: str,
    record_id: str,
) -> dict[str, Any]:
    """Get a single DNS record.

    Args:
        zone_id: Zone ID (32-character hex string)
        record_id: DNS record ID (32-character hex string)

    Returns:
        DNS record details
    """
    zone_id = validate_zone_id(zone_id)
    record_id = validate_record_id(record_id)
    client = get_client()

    response = await client.get(f"/zones/{zone_id}/dns_records/{record_id}")

    return {"record": response.get("result", {})}


async def create_dns_record(
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
        type: DNS record type (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
        name: DNS record name (e.g., www, @, or subdomain.example.com)
        content: DNS record content (e.g., IP address, target domain)
        ttl: TTL in seconds (1 = auto, default)
        proxied: Whether to proxy through Cloudflare (default: false)
        priority: Priority (required for MX and SRV records)
        comment: Optional comment for the record

    Returns:
        Created DNS record details
    """
    zone_id = validate_zone_id(zone_id)

    # Validate input using Pydantic model
    record_input = DnsRecordInput(
        type=type,
        name=name,
        content=content,
        ttl=ttl,
        proxied=proxied,
        priority=priority,
        comment=comment,
    )

    client = get_client()

    # Build request body
    body: dict[str, Any] = {
        "type": record_input.type,
        "name": record_input.name,
        "content": record_input.content,
        "ttl": record_input.ttl,
        "proxied": record_input.proxied,
    }

    if record_input.priority is not None:
        body["priority"] = record_input.priority
    if record_input.comment:
        body["comment"] = record_input.comment

    response = await client.post(f"/zones/{zone_id}/dns_records", json_data=body)

    return {"record": response.get("result", {})}


async def update_dns_record(
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
        type: DNS record type (optional)
        name: DNS record name (optional)
        content: DNS record content (optional)
        ttl: TTL in seconds (optional)
        proxied: Whether to proxy through Cloudflare (optional)
        priority: Priority (optional)
        comment: Optional comment (optional)

    Returns:
        Updated DNS record details
    """
    zone_id = validate_zone_id(zone_id)
    record_id = validate_record_id(record_id)

    # Validate input using Pydantic model
    update_input = DnsRecordUpdateInput(
        type=type,
        name=name,
        content=content,
        ttl=ttl,
        proxied=proxied,
        priority=priority,
        comment=comment,
    )

    client = get_client()

    # Build request body with only provided fields
    body: dict[str, Any] = {}

    if update_input.type is not None:
        body["type"] = update_input.type
    if update_input.name is not None:
        body["name"] = update_input.name
    if update_input.content is not None:
        body["content"] = update_input.content
    if update_input.ttl is not None:
        body["ttl"] = update_input.ttl
    if update_input.proxied is not None:
        body["proxied"] = update_input.proxied
    if update_input.priority is not None:
        body["priority"] = update_input.priority
    if update_input.comment is not None:
        body["comment"] = update_input.comment

    if not body:
        return {"error": "No fields provided for update"}

    response = await client.patch(f"/zones/{zone_id}/dns_records/{record_id}", json_data=body)

    return {"record": response.get("result", {})}


async def delete_dns_record(
    zone_id: str,
    record_id: str,
) -> dict[str, Any]:
    """Delete a DNS record.

    Args:
        zone_id: Zone ID (32-character hex string)
        record_id: DNS record ID (32-character hex string)

    Returns:
        Deletion confirmation with record ID
    """
    zone_id = validate_zone_id(zone_id)
    record_id = validate_record_id(record_id)
    client = get_client()

    response = await client.delete(f"/zones/{zone_id}/dns_records/{record_id}")

    return {
        "deleted": True,
        "id": response.get("result", {}).get("id", record_id),
    }
