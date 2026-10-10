"""Cloudflare Access (Zero Trust) tools.

Tools for putting a hostname behind an Access login: self-hosted applications
and the policies that say who gets in. Access belongs to the account, not the
zone, so each tool takes a zone ID like every other tool here and looks up the
account that owns it.
"""

from collections.abc import Awaitable
from typing import Any

from ..client import get_client
from ..errors import PermissionDeniedError, ZoneNotFoundError
from ..models import AccessAppInput, AccessPolicyInput, validate_hex_id, validate_uuid

APPS_SCOPE = "Account > Access: Apps and Policies (Edit)"
ORGANIZATION_SCOPE = "Account > Access: Organizations, Identity Providers, and Groups (Read)"

# Applications come back a page at a time. An account with more than this many
# pages is told so instead of being handed a short list.
MAX_APP_PAGES = 20
APPS_PER_PAGE = 50


async def _with_scope(call: Awaitable[dict[str, Any]], scope: str) -> dict[str, Any]:
    """Await an API call, naming the Access scope if the token is refused."""
    try:
        return await call
    except PermissionDeniedError as error:
        raise PermissionDeniedError(f"{scope}, on a valid API token") from error


async def _access_path(zone_id: str) -> str:
    """The Access API root of the account that owns a zone."""
    zone_id = validate_hex_id(zone_id, "zone_id")
    zone = await get_client().get(f"/zones/{zone_id}")
    account_id = validate_hex_id(
        str(zone.get("result", {}).get("account", {}).get("id", "")), "account_id"
    )
    return f"/accounts/{account_id}/access"


async def get_access_organization(zone_id: str) -> dict[str, Any]:
    """Get the Zero Trust organization behind a zone's Access applications.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        The organization, whose auth_domain is the team login domain. When Zero
        Trust has never been enabled, enabled is False and organization is None.
    """
    access = await _access_path(zone_id)

    try:
        response = await _with_scope(
            get_client().get(f"{access}/organizations"), ORGANIZATION_SCOPE
        )
    except ZoneNotFoundError as error:
        return {"enabled": False, "organization": None, "detail": str(error)}

    return {"enabled": True, "organization": response.get("result", {})}


async def list_access_apps(zone_id: str) -> dict[str, Any]:
    """List the Access applications on a zone.

    Args:
        zone_id: Zone ID (32-character hex string)

    Returns:
        Dictionary containing every application in the zone's account. complete
        is False if the account has more than the tool will page through.
    """
    access = await _access_path(zone_id)
    client = get_client()

    apps: list[dict[str, Any]] = []
    for page in range(1, MAX_APP_PAGES + 1):
        response = await _with_scope(
            client.get(f"{access}/apps", params={"page": page, "per_page": APPS_PER_PAGE}),
            APPS_SCOPE,
        )
        apps.extend(response.get("result", []))
        if page >= response.get("result_info", {}).get("total_pages", 1):
            return {"apps": apps, "complete": True}

    return {"apps": apps, "complete": False}


async def get_access_app(zone_id: str, app_id: str) -> dict[str, Any]:
    """Get one Access application.

    Args:
        zone_id: Zone ID (32-character hex string)
        app_id: Application ID (UUID)

    Returns:
        The application, including aud, the audience tag its login tokens carry
    """
    app_id = validate_uuid(app_id, "app_id")
    access = await _access_path(zone_id)
    client = get_client()

    response = await _with_scope(client.get(f"{access}/apps/{app_id}"), APPS_SCOPE)

    return {"app": response.get("result", {})}


async def create_access_app(
    zone_id: str,
    name: str,
    domain: str,
    session_duration: str = "24h",
) -> dict[str, Any]:
    """Put a hostname behind an Access login.

    A new application has no policy and so admits no one. Add one with
    create_access_policy.

    Args:
        zone_id: Zone ID (32-character hex string)
        name: Display name
        domain: Hostname to protect, optionally with a path. No scheme.
        session_duration: How long a login lasts, such as 24h or 720h

    Returns:
        Created application details
    """
    app = AccessAppInput(name=name, domain=domain, session_duration=session_duration)
    access = await _access_path(zone_id)
    client = get_client()

    body = {
        "type": "self_hosted",
        "name": app.name,
        "domain": app.domain,
        "session_duration": app.session_duration,
        "app_launcher_visible": False,
    }

    response = await _with_scope(client.post(f"{access}/apps", json_data=body), APPS_SCOPE)

    return {"app": response.get("result", {})}


async def delete_access_app(zone_id: str, app_id: str) -> dict[str, Any]:
    """Delete an Access application, leaving its hostname with no Access login.

    Args:
        zone_id: Zone ID (32-character hex string)
        app_id: Application ID (UUID)

    Returns:
        Deletion confirmation
    """
    app_id = validate_uuid(app_id, "app_id")
    access = await _access_path(zone_id)
    client = get_client()

    response = await _with_scope(client.delete(f"{access}/apps/{app_id}"), APPS_SCOPE)

    return {
        "deleted": True,
        "id": response.get("result", {}).get("id", app_id),
    }


async def list_access_policies(zone_id: str, app_id: str) -> dict[str, Any]:
    """List the policies on an Access application.

    Args:
        zone_id: Zone ID (32-character hex string)
        app_id: Application ID (UUID)

    Returns:
        Dictionary containing the policies, in the order Access evaluates them
    """
    app_id = validate_uuid(app_id, "app_id")
    access = await _access_path(zone_id)
    client = get_client()

    response = await _with_scope(client.get(f"{access}/apps/{app_id}/policies"), APPS_SCOPE)

    return {"policies": response.get("result", [])}


async def create_access_policy(
    zone_id: str,
    app_id: str,
    name: str,
    decision: str,
    include: list[dict[str, Any]],
    exclude: list[dict[str, Any]] | None = None,
    require: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Add a policy to an Access application.

    Each rule is an object with exactly one key:
    {"email": "user@example.com"}, {"email_domain": "example.com"},
    {"ip": "203.0.113.0/24"} or {"everyone": true}.

    Args:
        zone_id: Zone ID (32-character hex string)
        app_id: Application ID (UUID)
        name: Policy name
        decision: allow, deny, bypass (no login at all) or non_identity
        include: Rules of which a visitor must match at least one
        exclude: Rules of which a visitor must match none (optional)
        require: Rules of which a visitor must match all (optional)

    Returns:
        Created policy details
    """
    app_id = validate_uuid(app_id, "app_id")
    policy = AccessPolicyInput.model_validate(
        {
            "name": name,
            "decision": decision,
            "include": include,
            "exclude": exclude or [],
            "require": require or [],
        }
    )
    access = await _access_path(zone_id)
    client = get_client()

    body = {
        "name": policy.name,
        "decision": policy.decision,
        "include": [rule.to_api() for rule in policy.include],
        "exclude": [rule.to_api() for rule in policy.exclude],
        "require": [rule.to_api() for rule in policy.require],
    }

    response = await _with_scope(
        client.post(f"{access}/apps/{app_id}/policies", json_data=body),
        APPS_SCOPE,
    )

    return {"policy": response.get("result", {})}


async def delete_access_policy(zone_id: str, app_id: str, policy_id: str) -> dict[str, Any]:
    """Delete a policy from an Access application.

    Args:
        zone_id: Zone ID (32-character hex string)
        app_id: Application ID (UUID)
        policy_id: Policy ID (UUID)

    Returns:
        Deletion confirmation
    """
    app_id = validate_uuid(app_id, "app_id")
    policy_id = validate_uuid(policy_id, "policy_id")
    access = await _access_path(zone_id)
    client = get_client()

    response = await _with_scope(
        client.delete(f"{access}/apps/{app_id}/policies/{policy_id}"),
        APPS_SCOPE,
    )

    return {
        "deleted": True,
        "id": response.get("result", {}).get("id", policy_id),
    }
