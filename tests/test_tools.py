"""Mocked tool tests for all 25 Cloudflare tools."""

import pytest

from mcp_cloudflare_crunchtools.errors import (
    CloudflareApiError,
    ConfigurationError,
    InvalidRecordIdError,
    InvalidRuleIdError,
    InvalidZoneIdError,
    PermissionDeniedError,
    RateLimitError,
    UserError,
    ValidationError,
    ZoneNotFoundError,
)
from mcp_cloudflare_crunchtools.tools import __all__ as tools_all
from mcp_cloudflare_crunchtools.tools import (
    create_dns_record,
    create_page_rule,
    create_waf_rule,
    delete_dns_record,
    delete_page_rule,
    delete_waf_rule,
    get_dns_record,
    get_security_events,
    get_top_pages,
    get_traffic_by_country,
    get_zone,
    get_zone_analytics,
    list_dns_records,
    list_page_rules,
    list_request_header_rules,
    list_response_header_rules,
    list_url_rewrite_rules,
    list_waf_rules,
    list_zones,
    purge_cache,
    set_request_header_rules,
    set_response_header_rules,
    set_url_rewrite_rules,
    update_dns_record,
    update_page_rule,
    update_waf_rule,
)
from tests.conftest import _mock_cf_response, _patch_cf_client

TOOL_FUNCTIONS = [
    list_zones, get_zone,
    list_dns_records, get_dns_record, create_dns_record, update_dns_record, delete_dns_record,
    list_request_header_rules, set_request_header_rules,
    list_response_header_rules, set_response_header_rules,
    list_url_rewrite_rules, set_url_rewrite_rules,
    list_page_rules, create_page_rule, update_page_rule, delete_page_rule,
    purge_cache,
    get_zone_analytics, get_top_pages, get_traffic_by_country, get_security_events,
    list_waf_rules, create_waf_rule, update_waf_rule, delete_waf_rule,
]

EXPECTED_TOOL_COUNT = 26
EXPECTED_ALL_COUNT = 26

ZONE_ID = "a" * 32
RECORD_ID = "b" * 32


def test_tool_count() -> None:
    """Verify expected number of exports in tools.__all__."""
    assert len(tools_all) == EXPECTED_ALL_COUNT


def test_imports() -> None:
    """Verify all tool functions are importable and callable."""
    assert len(TOOL_FUNCTIONS) == EXPECTED_TOOL_COUNT, f"Expected {EXPECTED_TOOL_COUNT}, got {len(TOOL_FUNCTIONS)}"
    for func in TOOL_FUNCTIONS:
        assert callable(func)


# =============================================================================
# Error Hierarchy Tests
# =============================================================================


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_user_error_is_exception(self) -> None:
        assert issubclass(UserError, Exception)

    def test_all_errors_are_user_errors(self) -> None:
        error_classes = [
            ConfigurationError, InvalidZoneIdError, InvalidRecordIdError,
            InvalidRuleIdError, ZoneNotFoundError, PermissionDeniedError,
            RateLimitError, CloudflareApiError, ValidationError,
        ]
        for error_class in error_classes:
            assert issubclass(error_class, UserError)


class TestErrorMessages:
    """Tests for error message formatting."""

    def test_invalid_zone_id_error(self) -> None:
        error = InvalidZoneIdError()
        assert "zone_id" in str(error)
        assert "hex" in str(error)

    def test_invalid_record_id_error(self) -> None:
        error = InvalidRecordIdError()
        assert "record_id" in str(error)

    def test_invalid_rule_id_error(self) -> None:
        error = InvalidRuleIdError()
        assert "rule_id" in str(error)

    def test_zone_not_found_truncates(self) -> None:
        long_id = "x" * 100
        error = ZoneNotFoundError(long_id)
        assert long_id not in str(error)
        assert "..." in str(error)

    def test_permission_denied_error(self) -> None:
        error = PermissionDeniedError("dns:write")
        assert "dns:write" in str(error)

    def test_rate_limit_error_without_retry(self) -> None:
        error = RateLimitError()
        assert "rate limit" in str(error).lower()

    def test_rate_limit_error_with_retry(self) -> None:
        error = RateLimitError(retry_after=60)
        assert "60" in str(error)

    def test_cloudflare_api_error_sanitizes_token(self) -> None:
        import os
        os.environ["CLOUDFLARE_API_TOKEN"] = "secret_token_12345"
        error = CloudflareApiError(401, "Invalid token: secret_token_12345")
        assert "secret_token_12345" not in str(error)
        assert "***" in str(error)
        del os.environ["CLOUDFLARE_API_TOKEN"]


class TestConfigSafety:
    """Tests for configuration security."""

    def test_config_repr_hides_token(self) -> None:
        import os
        os.environ["CLOUDFLARE_API_TOKEN"] = "secret_test_token"
        try:
            from mcp_cloudflare_crunchtools.config import Config
            config = Config()
            assert "secret_test_token" not in repr(config)
            assert "secret_test_token" not in str(config)
            assert "***" in repr(config)
        finally:
            del os.environ["CLOUDFLARE_API_TOKEN"]

    def test_config_requires_token(self) -> None:
        import os
        from mcp_cloudflare_crunchtools.config import Config
        token = os.environ.pop("CLOUDFLARE_API_TOKEN", None)
        try:
            import mcp_cloudflare_crunchtools.config as config_module
            config_module._config = None
            with pytest.raises(ConfigurationError):
                Config()
        finally:
            if token:
                os.environ["CLOUDFLARE_API_TOKEN"] = token


# =============================================================================
# Mocked API Tests — Zone Tools
# =============================================================================


class TestZoneTools:
    """Tests for zone tools."""

    @pytest.mark.asyncio
    async def test_list_zones(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": [{"id": ZONE_ID, "name": "example.com", "status": "active"}],
            "result_info": {"page": 1, "total_count": 1},
        })
        async with _patch_cf_client(response=resp):
            result = await list_zones()
            assert "zones" in result
            assert len(result["zones"]) == 1
            assert result["zones"][0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_zone(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": {"id": ZONE_ID, "name": "example.com", "status": "active"},
        })
        async with _patch_cf_client(response=resp):
            result = await get_zone(zone_id=ZONE_ID)
            assert "zone" in result
            assert result["zone"]["name"] == "example.com"


# =============================================================================
# Mocked API Tests — DNS Tools
# =============================================================================


class TestDnsTools:
    """Tests for DNS record tools."""

    @pytest.mark.asyncio
    async def test_list_dns_records(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": [{"id": RECORD_ID, "type": "A", "name": "example.com", "content": "1.2.3.4"}],
            "result_info": {"page": 1, "total_count": 1},
        })
        async with _patch_cf_client(response=resp):
            result = await list_dns_records(zone_id=ZONE_ID)
            assert "records" in result
            assert len(result["records"]) == 1
            assert result["records"][0]["type"] == "A"

    @pytest.mark.asyncio
    async def test_get_dns_record(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": {"id": RECORD_ID, "type": "A", "name": "example.com", "content": "1.2.3.4"},
        })
        async with _patch_cf_client(response=resp):
            result = await get_dns_record(zone_id=ZONE_ID, record_id=RECORD_ID)
            assert "record" in result
            assert result["record"]["content"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_create_dns_record(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": {"id": RECORD_ID, "type": "A", "name": "test.example.com", "content": "5.6.7.8"},
        })
        async with _patch_cf_client(response=resp):
            result = await create_dns_record(
                zone_id=ZONE_ID, type="A", name="test.example.com", content="5.6.7.8"
            )
            assert "record" in result

    @pytest.mark.asyncio
    async def test_update_dns_record(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": {"id": RECORD_ID, "type": "A", "name": "example.com", "content": "9.8.7.6"},
        })
        async with _patch_cf_client(response=resp):
            result = await update_dns_record(
                zone_id=ZONE_ID, record_id=RECORD_ID, content="9.8.7.6"
            )
            assert "record" in result

    @pytest.mark.asyncio
    async def test_delete_dns_record(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True, "result": {"id": RECORD_ID},
        })
        async with _patch_cf_client(response=resp):
            result = await delete_dns_record(zone_id=ZONE_ID, record_id=RECORD_ID)
            assert result.get("deleted") is True


# =============================================================================
# Mocked API Tests — Cache Tools
# =============================================================================


class TestCacheTools:
    """Tests for cache tools."""

    @pytest.mark.asyncio
    async def test_purge_cache(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True, "result": {"id": "purge123"},
        })
        async with _patch_cf_client(response=resp):
            result = await purge_cache(zone_id=ZONE_ID, purge_everything=True)
            assert result["success"] is True


# =============================================================================
# Mocked API Tests — Page Rules Tools
# =============================================================================


class TestPageRulesTools:
    """Tests for page rules tools."""

    @pytest.mark.asyncio
    async def test_list_page_rules(self) -> None:
        resp = _mock_cf_response(json_data={
            "success": True,
            "result": [{"id": "rule1", "targets": [], "actions": [], "status": "active"}],
        })
        async with _patch_cf_client(response=resp):
            result = await list_page_rules(zone_id=ZONE_ID)
            assert "page_rules" in result


# =============================================================================
# Mocked API Tests — Analytics Tools
# =============================================================================


class TestAnalyticsTools:
    """Tests for analytics tools."""

    @pytest.mark.asyncio
    async def test_get_zone_analytics(self) -> None:
        # Analytics uses GraphQL — client.graphql() extracts data from response["data"]
        resp = _mock_cf_response(json_data={
            "data": {"viewer": {"zones": [{"totals": [{"sum": {"requests": 1000, "bytes": 5000,
             "cachedRequests": 500, "cachedBytes": 2500}, "uniq": {"uniques": 100}}],
             "statusCodes": []}]}},
        })
        async with _patch_cf_client(response=resp):
            result = await get_zone_analytics(zone_id=ZONE_ID)
            assert "requests" in result
