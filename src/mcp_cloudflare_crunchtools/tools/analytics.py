"""Analytics tools using the Cloudflare GraphQL API.

Tools for retrieving traffic analytics, top pages, country breakdowns,
and security events for Cloudflare zones.

Note: httpRequestsAdaptiveGroups has plan-based time range limits:
  Free: 24h, Pro: 72h, Business: 7d, Enterprise: 30d+
The adaptive queries default to 24h to work on all plans.
httpRequests1dGroups (used for zone summary) supports 30d+ on all plans.
firewallEventsAdaptiveGroups requires Business+ plan.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from ..client import get_client
from ..errors import CloudflareApiError
from ..models import validate_zone_id


def _default_date_range(
    since: str | None, until: str | None
) -> tuple[str, str]:
    """Return ISO date strings defaulting to the last 30 days."""
    now = datetime.now(timezone.utc)
    if until is None:
        until = now.strftime("%Y-%m-%d")
    if since is None:
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    return since, until


def _default_datetime_range(
    since: str | None, until: str | None
) -> tuple[str, str]:
    """Return ISO datetime strings defaulting to the last 24 hours.

    Used for adaptive datasets which have tighter time range limits.
    """
    now = datetime.now(timezone.utc)
    if until is None:
        until = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if since is None:
        since = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return since, until


async def get_zone_analytics(
    zone_id: str,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """Get zone traffic analytics summary.

    Returns total requests, unique visitors, bandwidth, cache ratio,
    and status code breakdown for the given date range.

    Args:
        zone_id: Zone ID (32-character hex string)
        since: Start date ISO format (default: 30 days ago)
        until: End date ISO format (default: today)

    Returns:
        Analytics summary dictionary
    """
    zone_id = validate_zone_id(zone_id)
    since, until = _default_date_range(since, until)
    client = get_client()

    query = """
    query ZoneAnalytics($zoneTag: string!, $since: Date!, $until: Date!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          totals: httpRequests1dGroups(
            filter: {date_geq: $since, date_leq: $until}
            limit: 1
          ) {
            sum {
              requests
              bytes
              cachedRequests
              cachedBytes
              encryptedRequests
              pageViews
            }
            uniq {
              uniques
            }
          }
          statusCodes: httpRequests1dGroups(
            filter: {date_geq: $since, date_leq: $until}
            limit: 500
          ) {
            sum {
              responseStatusMap {
                edgeResponseStatus
                requests
              }
            }
          }
        }
      }
    }
    """

    data = await client.graphql(query, {
        "zoneTag": zone_id,
        "since": since,
        "until": until,
    })

    zones = data.get("viewer", {}).get("zones", [])
    if not zones:
        return {"error": "No analytics data found for this zone"}

    zone_data = zones[0]
    totals = zone_data.get("totals", [{}])
    total = totals[0] if totals else {}
    sums = total.get("sum", {})
    uniq = total.get("uniq", {})

    # Build status code summary from responseStatusMap across all days
    status_breakdown: dict[str, int] = {}
    for day in zone_data.get("statusCodes", []):
        for entry in day.get("sum", {}).get("responseStatusMap", []):
            status = str(entry.get("edgeResponseStatus", "unknown"))
            status_breakdown[status] = (
                status_breakdown.get(status, 0) + entry.get("requests", 0)
            )

    total_requests = sums.get("requests", 0)
    cached_requests = sums.get("cachedRequests", 0)
    total_bytes = sums.get("bytes", 0)
    cached_bytes = sums.get("cachedBytes", 0)

    return {
        "period": {"since": since, "until": until},
        "requests": {
            "total": total_requests,
            "cached": cached_requests,
            "uncached": total_requests - cached_requests,
            "cache_ratio": (
                round(cached_requests / total_requests * 100, 1) if total_requests else 0
            ),
            "encrypted": sums.get("encryptedRequests", 0),
        },
        "bandwidth": {
            "total_bytes": total_bytes,
            "cached_bytes": cached_bytes,
            "uncached_bytes": total_bytes - cached_bytes,
            "cache_ratio": round(cached_bytes / total_bytes * 100, 1) if total_bytes else 0,
        },
        "visitors": {"unique": uniq.get("uniques", 0)},
        "page_views": sums.get("pageViews", 0),
        "status_codes": status_breakdown,
    }


async def get_top_pages(
    zone_id: str,
    since: str | None = None,
    until: str | None = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Get top pages by request count.

    Uses adaptive dataset — defaults to last 24 hours.
    Free plans support up to 24h, Pro 72h, Business 7d.

    Args:
        zone_id: Zone ID (32-character hex string)
        since: Start datetime ISO format (default: 24 hours ago)
        until: End datetime ISO format (default: now)
        limit: Number of results (default: 15)

    Returns:
        Top pages with request counts and bandwidth
    """
    zone_id = validate_zone_id(zone_id)
    since, until = _default_datetime_range(since, until)
    client = get_client()

    query = """
    query TopPages(
      $zoneTag: string!, $since: DateTime!, $until: DateTime!, $limit: Int!
    ) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequestsAdaptiveGroups(
            filter: {datetime_geq: $since, datetime_leq: $until}
            limit: $limit
            orderBy: [count_DESC]
          ) {
            count
            dimensions {
              clientRequestPath
            }
            sum {
              edgeResponseBytes
            }
          }
        }
      }
    }
    """

    data = await client.graphql(query, {
        "zoneTag": zone_id,
        "since": since,
        "until": until,
        "limit": limit,
    })

    zones = data.get("viewer", {}).get("zones", [])
    if not zones:
        return {"error": "No analytics data found for this zone"}

    pages = []
    for group in zones[0].get("httpRequestsAdaptiveGroups", []):
        path = group.get("dimensions", {}).get("clientRequestPath", "unknown")
        pages.append({
            "path": path,
            "requests": group.get("count", 0),
            "bytes": group.get("sum", {}).get("edgeResponseBytes", 0),
        })

    return {
        "period": {"since": since, "until": until},
        "pages": pages,
    }


async def get_traffic_by_country(
    zone_id: str,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get traffic breakdown by country.

    Uses adaptive dataset — defaults to last 24 hours.
    Free plans support up to 24h, Pro 72h, Business 7d.

    Args:
        zone_id: Zone ID (32-character hex string)
        since: Start datetime ISO format (default: 24 hours ago)
        until: End datetime ISO format (default: now)
        limit: Number of countries (default: 20)

    Returns:
        Country breakdown with request counts
    """
    zone_id = validate_zone_id(zone_id)
    since, until = _default_datetime_range(since, until)
    client = get_client()

    query = """
    query TrafficByCountry(
      $zoneTag: string!, $since: DateTime!, $until: DateTime!, $limit: Int!
    ) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequestsAdaptiveGroups(
            filter: {datetime_geq: $since, datetime_leq: $until}
            limit: $limit
            orderBy: [count_DESC]
          ) {
            count
            dimensions {
              clientCountryName
            }
            sum {
              edgeResponseBytes
            }
          }
        }
      }
    }
    """

    data = await client.graphql(query, {
        "zoneTag": zone_id,
        "since": since,
        "until": until,
        "limit": limit,
    })

    zones = data.get("viewer", {}).get("zones", [])
    if not zones:
        return {"error": "No analytics data found for this zone"}

    countries = []
    for group in zones[0].get("httpRequestsAdaptiveGroups", []):
        country = group.get("dimensions", {}).get("clientCountryName", "Unknown")
        countries.append({
            "country": country,
            "requests": group.get("count", 0),
            "bytes": group.get("sum", {}).get("edgeResponseBytes", 0),
        })

    return {
        "period": {"since": since, "until": until},
        "countries": countries,
    }


async def get_security_events(
    zone_id: str,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get security/firewall events grouped by action and source.

    Requires Cloudflare Business or Enterprise plan.
    Defaults to last 24 hours.

    Args:
        zone_id: Zone ID (32-character hex string)
        since: Start datetime ISO format (default: 24 hours ago)
        until: End datetime ISO format (default: now)
        limit: Number of results (default: 20)

    Returns:
        Security events grouped by action with source details
    """
    zone_id = validate_zone_id(zone_id)
    since, until = _default_datetime_range(since, until)
    client = get_client()

    query = """
    query SecurityEvents(
      $zoneTag: string!, $since: DateTime!, $until: DateTime!, $limit: Int!
    ) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          firewallEventsAdaptiveGroups(
            filter: {datetime_geq: $since, datetime_leq: $until}
            limit: $limit
            orderBy: [count_DESC]
          ) {
            count
            dimensions {
              action
              clientCountryName
              source
            }
          }
        }
      }
    }
    """

    try:
        data = await client.graphql(query, {
            "zoneTag": zone_id,
            "since": since,
            "until": until,
            "limit": limit,
        })
    except CloudflareApiError as e:
        if "does not have access" in str(e):
            return {
                "error": "Firewall analytics requires Cloudflare Business or Enterprise plan",
            }
        raise

    zones = data.get("viewer", {}).get("zones", [])
    if not zones:
        return {"error": "No security data found for this zone"}

    events = []
    for group in zones[0].get("firewallEventsAdaptiveGroups", []):
        dims = group.get("dimensions", {})
        events.append({
            "action": dims.get("action", "unknown"),
            "country": dims.get("clientCountryName", "Unknown"),
            "source": dims.get("source", "unknown"),
            "count": group.get("count", 0),
        })

    return {
        "period": {"since": since, "until": until},
        "events": events,
    }
