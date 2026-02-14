"""Cloudflare MCP tools.

This package contains all the MCP tool implementations for Cloudflare operations.
"""

from .cache import purge_cache
from .dns import (
    create_dns_record,
    delete_dns_record,
    get_dns_record,
    list_dns_records,
    update_dns_record,
)
from .page_rules import (
    create_page_rule,
    delete_page_rule,
    list_page_rules,
    update_page_rule,
)
from .transform import (
    list_request_header_rules,
    list_response_header_rules,
    list_url_rewrite_rules,
    set_request_header_rules,
    set_response_header_rules,
    set_url_rewrite_rules,
)
from .zones import get_zone, list_zones

__all__ = [
    # Zones
    "list_zones",
    "get_zone",
    # DNS
    "list_dns_records",
    "get_dns_record",
    "create_dns_record",
    "update_dns_record",
    "delete_dns_record",
    # Transform Rules
    "list_request_header_rules",
    "set_request_header_rules",
    "list_response_header_rules",
    "set_response_header_rules",
    "list_url_rewrite_rules",
    "set_url_rewrite_rules",
    # Page Rules
    "list_page_rules",
    "create_page_rule",
    "update_page_rule",
    "delete_page_rule",
    # Cache
    "purge_cache",
]
