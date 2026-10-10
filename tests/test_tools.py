"""Mocked tool tests for the Cloudflare tools."""

import os
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError as PydanticValidationError

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
from mcp_cloudflare_crunchtools.server import mcp
from mcp_cloudflare_crunchtools.tools import __all__ as tools_all
from mcp_cloudflare_crunchtools.tools import (
    create_access_app,
    create_access_policy,
    create_dns_record,
    create_page_rule,
    create_waf_rule,
    delete_access_app,
    delete_access_policy,
    delete_dns_record,
    delete_page_rule,
    delete_waf_rule,
    get_access_app,
    get_access_organization,
    get_dns_record,
    get_security_events,
    get_top_pages,
    get_traffic_by_country,
    get_zone,
    get_zone_analytics,
    list_access_apps,
    list_access_policies,
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
    list_zones,
    get_zone,
    list_dns_records,
    get_dns_record,
    create_dns_record,
    update_dns_record,
    delete_dns_record,
    list_request_header_rules,
    set_request_header_rules,
    list_response_header_rules,
    set_response_header_rules,
    list_url_rewrite_rules,
    set_url_rewrite_rules,
    list_page_rules,
    create_page_rule,
    update_page_rule,
    delete_page_rule,
    purge_cache,
    get_zone_analytics,
    get_top_pages,
    get_traffic_by_country,
    get_security_events,
    list_waf_rules,
    create_waf_rule,
    update_waf_rule,
    delete_waf_rule,
    get_access_organization,
    list_access_apps,
    get_access_app,
    create_access_app,
    delete_access_app,
    list_access_policies,
    create_access_policy,
    delete_access_policy,
]

EXPECTED_TOOL_COUNT = 34
EXPECTED_ALL_COUNT = 34

ZONE_ID = "a" * 32
RECORD_ID = "b" * 32
APP_ID = "11111111-2222-3333-4444-555555555555"
POLICY_ID = "66666666-7777-8888-9999-aaaaaaaaaaaa"
ACCOUNT_ID = "d" * 32
ACCESS = f"/accounts/{ACCOUNT_ID}/access"


def test_tool_count() -> None:
    """Verify expected number of exports in tools.__all__."""
    assert len(tools_all) == EXPECTED_ALL_COUNT


def test_imports() -> None:
    """Verify all tool functions are importable and callable."""
    assert len(TOOL_FUNCTIONS) == EXPECTED_TOOL_COUNT, (
        f"Expected {EXPECTED_TOOL_COUNT}, got {len(TOOL_FUNCTIONS)}"
    )
    for func in TOOL_FUNCTIONS:
        assert callable(func)


# Read-only classification

READ_ONLY = frozenset(
    {
        "list_zones_tool",
        "get_zone_tool",
        "list_dns_records_tool",
        "get_dns_record_tool",
        "list_request_header_rules_tool",
        "list_response_header_rules_tool",
        "list_url_rewrite_rules_tool",
        "list_page_rules_tool",
        "list_waf_rules_tool",
        "get_zone_analytics_tool",
        "get_top_pages_tool",
        "get_traffic_by_country_tool",
        "get_security_events_tool",
        "get_access_organization_tool",
        "list_access_apps_tool",
        "get_access_app_tool",
        "list_access_policies_tool",
    }
)
WRITES = frozenset(
    {
        "create_dns_record_tool",
        "update_dns_record_tool",
        "delete_dns_record_tool",
        "set_request_header_rules_tool",
        "set_response_header_rules_tool",
        "set_url_rewrite_rules_tool",
        "create_page_rule_tool",
        "update_page_rule_tool",
        "delete_page_rule_tool",
        "purge_cache_tool",
        "create_waf_rule_tool",
        "update_waf_rule_tool",
        "delete_waf_rule_tool",
        "create_access_app_tool",
        "delete_access_app_tool",
        "create_access_policy_tool",
        "delete_access_policy_tool",
    }
)

# Read-only tools allowed to POST. Cloudflare serves analytics only through its
# GraphQL endpoint, which takes the query in a POST body. Each of these sends one
# fixed `query` document (never a `mutation`) with the caller's values as variables.
GRAPHQL_READS = frozenset(
    {
        "get_zone_analytics_tool",  # query ZoneAnalytics
        "get_top_pages_tool",  # query TopPages
        "get_traffic_by_country_tool",  # query TrafficByCountry
        "get_security_events_tool",  # query SecurityEvents
    }
)

RULESET_ID = "c" * 32

# Arguments that satisfy each read-only tool. Tools that accept zone_name get it
# rather than zone_id, so the name lookup is exercised too.
READ_ONLY_CALLS: dict[str, dict[str, Any]] = {
    "list_zones_tool": {"name": "example.com"},
    "get_zone_tool": {"zone_name": "example.com"},
    "list_dns_records_tool": {"zone_id": ZONE_ID, "type": "A"},
    "get_dns_record_tool": {"zone_id": ZONE_ID, "record_id": RECORD_ID},
    "list_request_header_rules_tool": {"zone_id": ZONE_ID},
    "list_response_header_rules_tool": {"zone_id": ZONE_ID},
    "list_url_rewrite_rules_tool": {"zone_id": ZONE_ID},
    "list_page_rules_tool": {"zone_id": ZONE_ID},
    "list_waf_rules_tool": {"zone_name": "example.com"},
    "get_zone_analytics_tool": {"zone_name": "example.com"},
    "get_top_pages_tool": {"zone_name": "example.com"},
    "get_traffic_by_country_tool": {"zone_name": "example.com"},
    "get_security_events_tool": {"zone_name": "example.com"},
    "get_access_organization_tool": {"zone_id": ZONE_ID},
    "list_access_apps_tool": {"zone_id": ZONE_ID},
    "get_access_app_tool": {"zone_id": ZONE_ID, "app_id": APP_ID},
    "list_access_policies_tool": {"zone_id": ZONE_ID, "app_id": APP_ID},
}

# One ruleset per phase the read tools look for, so each follows through to the
# second request that fetches the ruleset itself.
_RULESETS = [
    {"id": RULESET_ID, "phase": phase, "kind": "zone"}
    for phase in (
        "http_request_late_transform",
        "http_response_headers_transform",
        "http_request_transform",
        "http_request_firewall_custom",
    )
]
_COLLECTIONS: dict[str, list[dict[str, Any]]] = {
    "/zones": [{"id": ZONE_ID, "name": "example.com"}],
    "/rulesets": _RULESETS,
    "/dns_records": [{"id": RECORD_ID}],
    "/pagerules": [{"id": RECORD_ID}],
    "/access/apps": [{"id": APP_ID}],
    "/policies": [{"id": POLICY_ID}],
}


def _cloudflare_reply(*, url: str, **_: Any) -> httpx.Response:
    """Answer a request the way Cloudflare shapes it: a list for a collection, else an object."""
    if url == "/graphql":
        return _mock_cf_response(json_data={"data": {"viewer": {"zones": [{}]}}})
    for suffix, items in _COLLECTIONS.items():
        if url.endswith(suffix):
            return _mock_cf_response(json_data={"success": True, "result": items})
    return _mock_cf_response(
        json_data={
            "success": True,
            "result": {"id": RULESET_ID, "rules": [], "account": {"id": ACCOUNT_ID}},
        }
    )


class TestReadOnlyAnnotation:
    """Every registered tool is classified, and the reads really only read."""

    @pytest.mark.asyncio
    async def test_every_tool_is_classified(self) -> None:
        tools = await mcp.list_tools()
        assert READ_ONLY.isdisjoint(WRITES)
        assert {tool.name for tool in tools} == READ_ONLY | WRITES
        annotated = {
            tool.name
            for tool in tools
            if tool.annotations is not None
            and tool.annotations.model_dump(by_alias=True).get("readOnlyHint") is True
        }
        assert annotated == READ_ONLY

    def test_call_table_covers_every_read(self) -> None:
        assert set(READ_ONLY_CALLS) == READ_ONLY
        assert GRAPHQL_READS <= READ_ONLY

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", sorted(READ_ONLY))
    async def test_read_only_tool_sends_only_reads(self, name: str) -> None:
        """A read sends GET; an analytics read may also POST a GraphQL query."""
        async with _patch_cf_client() as request:
            assert isinstance(request, AsyncMock)
            request.side_effect = _cloudflare_reply
            await mcp.call_tool(name, READ_ONLY_CALLS[name])
        assert request.await_count >= 1
        posts = 0
        for call in request.await_args_list:
            method, url = call.kwargs["method"], call.kwargs["url"]
            if method == "GET":
                continue
            assert name in GRAPHQL_READS, f"{name} sent {method} {url}"
            assert (method, url) == ("POST", "/graphql")
            assert call.kwargs["json"]["query"].lstrip().startswith("query ")
            posts += 1
        assert posts == (1 if name in GRAPHQL_READS else 0)


# Error Hierarchy Tests


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_user_error_is_exception(self) -> None:
        assert issubclass(UserError, Exception)

    def test_all_errors_are_user_errors(self) -> None:
        error_classes = [
            ConfigurationError,
            InvalidZoneIdError,
            InvalidRecordIdError,
            InvalidRuleIdError,
            ZoneNotFoundError,
            PermissionDeniedError,
            RateLimitError,
            CloudflareApiError,
            ValidationError,
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
        os.environ["CLOUDFLARE_API_TOKEN"] = "secret_token_12345"
        error = CloudflareApiError(401, "Invalid token: secret_token_12345")
        assert "secret_token_12345" not in str(error)
        assert "***" in str(error)
        del os.environ["CLOUDFLARE_API_TOKEN"]


class TestConfigSafety:
    """Tests for configuration security."""

    def test_config_repr_hides_token(self) -> None:
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


# Mocked API Tests — Zone Tools


class TestZoneTools:
    """Tests for zone tools."""

    @pytest.mark.asyncio
    async def test_list_zones(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": [{"id": ZONE_ID, "name": "example.com", "status": "active"}],
                "result_info": {"page": 1, "total_count": 1},
            }
        )
        async with _patch_cf_client(response=resp):
            result = await list_zones()
            assert "zones" in result
            assert len(result["zones"]) == 1
            assert result["zones"][0]["name"] == "example.com"

    @pytest.mark.asyncio
    async def test_get_zone(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {"id": ZONE_ID, "name": "example.com", "status": "active"},
            }
        )
        async with _patch_cf_client(response=resp):
            result = await get_zone(zone_id=ZONE_ID)
            assert "zone" in result
            assert result["zone"]["name"] == "example.com"


# Mocked API Tests — DNS Tools


class TestDnsTools:
    """Tests for DNS record tools."""

    @pytest.mark.asyncio
    async def test_list_dns_records(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": [
                    {"id": RECORD_ID, "type": "A", "name": "example.com", "content": "1.2.3.4"}
                ],
                "result_info": {"page": 1, "total_count": 1},
            }
        )
        async with _patch_cf_client(response=resp):
            result = await list_dns_records(zone_id=ZONE_ID)
            assert "records" in result
            assert len(result["records"]) == 1
            assert result["records"][0]["type"] == "A"

    @pytest.mark.asyncio
    async def test_get_dns_record(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {
                    "id": RECORD_ID,
                    "type": "A",
                    "name": "example.com",
                    "content": "1.2.3.4",
                },
            }
        )
        async with _patch_cf_client(response=resp):
            result = await get_dns_record(zone_id=ZONE_ID, record_id=RECORD_ID)
            assert "record" in result
            assert result["record"]["content"] == "1.2.3.4"

    @pytest.mark.asyncio
    async def test_create_dns_record(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {
                    "id": RECORD_ID,
                    "type": "A",
                    "name": "test.example.com",
                    "content": "5.6.7.8",
                },
            }
        )
        async with _patch_cf_client(response=resp):
            result = await create_dns_record(
                zone_id=ZONE_ID, type="A", name="test.example.com", content="5.6.7.8"
            )
            assert "record" in result

    @pytest.mark.asyncio
    async def test_update_dns_record(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {
                    "id": RECORD_ID,
                    "type": "A",
                    "name": "example.com",
                    "content": "9.8.7.6",
                },
            }
        )
        async with _patch_cf_client(response=resp):
            result = await update_dns_record(
                zone_id=ZONE_ID, record_id=RECORD_ID, content="9.8.7.6"
            )
            assert "record" in result

    @pytest.mark.asyncio
    async def test_delete_dns_record(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {"id": RECORD_ID},
            }
        )
        async with _patch_cf_client(response=resp):
            result = await delete_dns_record(zone_id=ZONE_ID, record_id=RECORD_ID)
            assert result.get("deleted") is True


# Mocked API Tests — Cache Tools


class TestCacheTools:
    """Tests for cache tools."""

    @pytest.mark.asyncio
    async def test_purge_cache(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": {"id": "purge123"},
            }
        )
        async with _patch_cf_client(response=resp):
            result = await purge_cache(zone_id=ZONE_ID, purge_everything=True)
            assert result["success"] is True


# Mocked API Tests — Page Rules Tools


class TestPageRulesTools:
    """Tests for page rules tools."""

    @pytest.mark.asyncio
    async def test_list_page_rules(self) -> None:
        resp = _mock_cf_response(
            json_data={
                "success": True,
                "result": [{"id": "rule1", "targets": [], "actions": [], "status": "active"}],
            }
        )
        async with _patch_cf_client(response=resp):
            result = await list_page_rules(zone_id=ZONE_ID)
            assert "page_rules" in result


# Mocked API Tests — Access Tools


def _access_reply(result: Any = None, status_code: int = 200, **extra: Any) -> Any:
    """Answer the zone lookup with its account, and every Access call with `result`."""

    def reply(*, url: str, **_: Any) -> httpx.Response:
        if url == f"/zones/{ZONE_ID}":
            return _mock_cf_response(
                json_data={"success": True, "result": {"account": {"id": ACCOUNT_ID}}}
            )
        return _mock_cf_response(
            status_code=status_code,
            json_data={"success": status_code == 200, "result": result, **extra},
        )

    return reply


FORBIDDEN = {"status_code": 403, "errors": [{"code": 10000, "message": "Authentication"}]}


class TestAccessTools:
    """Tests for Access application and policy tools."""

    @pytest.mark.asyncio
    async def test_get_access_organization(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({"auth_domain": "team.cloudflareaccess.com"})
            result = await get_access_organization(zone_id=ZONE_ID)
        assert result["enabled"] is True
        assert result["organization"]["auth_domain"] == "team.cloudflareaccess.com"
        assert request.await_args.kwargs["url"] == f"{ACCESS}/organizations"

    @pytest.mark.asyncio
    async def test_organization_absent_means_zero_trust_is_off(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply(
                status_code=404, errors=[{"code": 12130, "message": "not_found"}]
            )
            result = await get_access_organization(zone_id=ZONE_ID)
        assert result["enabled"] is False
        assert result["organization"] is None

    @pytest.mark.asyncio
    async def test_get_access_app(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({"id": APP_ID, "aud": "tag"})
            result = await get_access_app(zone_id=ZONE_ID, app_id=APP_ID)
        assert result["app"]["aud"] == "tag"
        assert request.await_args.kwargs["url"] == f"{ACCESS}/apps/{APP_ID}"

    @pytest.mark.asyncio
    async def test_list_access_apps_follows_pages(self) -> None:
        def page(number: int, name: str) -> httpx.Response:
            return _mock_cf_response(
                json_data={
                    "success": True,
                    "result": [{"id": name}],
                    "result_info": {"page": number, "total_pages": 2},
                }
            )

        async with _patch_cf_client() as request:
            request.side_effect = [
                _access_reply()(url=f"/zones/{ZONE_ID}"),
                page(1, "one"),
                page(2, "two"),
            ]
            result = await list_access_apps(zone_id=ZONE_ID)
        assert [call.kwargs["params"]["page"] for call in request.await_args_list[1:]] == [1, 2]
        assert result == {"apps": [{"id": "one"}, {"id": "two"}], "complete": True}

    @pytest.mark.asyncio
    async def test_list_access_apps_says_when_it_stopped_short(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply([{"id": APP_ID}], result_info={"total_pages": 99})
            result = await list_access_apps(zone_id=ZONE_ID)
        assert result["complete"] is False
        assert len(result["apps"]) == 20

    @pytest.mark.asyncio
    async def test_create_access_app_is_self_hosted(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({"id": APP_ID, "aud": "x"})
            result = await create_access_app(
                zone_id=ZONE_ID, name="Dev", domain="dev.example.com", session_duration="720h"
            )
        assert result["app"]["id"] == APP_ID
        sent = request.await_args.kwargs
        assert (sent["method"], sent["url"]) == ("POST", f"{ACCESS}/apps")
        assert sent["json"] == {
            "type": "self_hosted",
            "name": "Dev",
            "domain": "dev.example.com",
            "session_duration": "720h",
            "app_launcher_visible": False,
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "fields",
        [
            {"domain": "https://dev.example.com"},
            {"domain": "dev.example.com/a b"},
            {"session_duration": "a month"},
            {"name": ""},
        ],
    )
    async def test_create_access_app_rejects_bad_input_before_any_request(
        self, fields: dict[str, str]
    ) -> None:
        good = {"name": "Dev", "domain": "dev.example.com", "session_duration": "24h"}
        async with _patch_cf_client() as request:
            with pytest.raises(PydanticValidationError):
                await create_access_app(zone_id=ZONE_ID, **{**good, **fields})
        request.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_access_policy_sends_cloudflares_rule_shape(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({"id": POLICY_ID})
            result = await create_access_policy(
                zone_id=ZONE_ID,
                app_id=APP_ID,
                name="Owner",
                decision="allow",
                include=[{"email": "owner@example.com"}, {"email_domain": "example.com"}],
                exclude=[{"ip": "203.0.113.0/24"}],
            )
        assert result["policy"]["id"] == POLICY_ID
        sent = request.await_args.kwargs
        assert sent["url"] == f"{ACCESS}/apps/{APP_ID}/policies"
        assert sent["json"] == {
            "name": "Owner",
            "decision": "allow",
            "include": [
                {"email": {"email": "owner@example.com"}},
                {"email_domain": {"domain": "example.com"}},
            ],
            "exclude": [{"ip": {"ip": "203.0.113.0/24"}}],
            "require": [],
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("decision", "include"),
        [
            ("permit", [{"email": "owner@example.com"}]),
            ("allow", []),
            ("allow", [{"email": "not-an-address"}]),
            ("allow", [{"email_domain": "https://example.com"}]),
            ("allow", [{"email_domain": "localhost"}]),
            ("allow", [{"email": "a@example.com", "everyone": True}]),
            ("allow", [{"everyone": False}]),
            ("allow", [{"group": "admins"}]),
            ("allow", [{"ip": "not-an-ip"}]),
        ],
    )
    async def test_create_access_policy_rejects_bad_input_before_any_request(
        self, decision: str, include: list[dict[str, Any]]
    ) -> None:
        async with _patch_cf_client() as request:
            with pytest.raises(PydanticValidationError):
                await create_access_policy(
                    zone_id=ZONE_ID, app_id=APP_ID, name="P", decision=decision, include=include
                )
        request.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_everyone_rule(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({"id": POLICY_ID})
            await create_access_policy(
                zone_id=ZONE_ID,
                app_id=APP_ID,
                name="Public",
                decision="bypass",
                include=[{"everyone": True}],
            )
        assert request.await_args.kwargs["json"]["include"] == [{"everyone": {}}]

    @pytest.mark.asyncio
    async def test_list_access_policies(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply([{"id": POLICY_ID}])
            result = await list_access_policies(zone_id=ZONE_ID, app_id=APP_ID)
        assert result == {"policies": [{"id": POLICY_ID}]}

    @pytest.mark.asyncio
    async def test_delete_access_app_and_policy(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply({})
            app = await delete_access_app(zone_id=ZONE_ID, app_id=APP_ID)
            policy = await delete_access_policy(zone_id=ZONE_ID, app_id=APP_ID, policy_id=POLICY_ID)
        assert app == {"deleted": True, "id": APP_ID}
        assert policy == {"deleted": True, "id": POLICY_ID}
        sent = [(call.kwargs["method"], call.kwargs["url"]) for call in request.await_args_list]
        assert ("DELETE", f"{ACCESS}/apps/{APP_ID}") in sent
        assert ("DELETE", f"{ACCESS}/apps/{APP_ID}/policies/{POLICY_ID}") in sent

    @pytest.mark.asyncio
    async def test_non_uuid_ids_never_reach_the_api(self) -> None:
        async with _patch_cf_client() as request:
            with pytest.raises(ValueError, match="app_id must be a UUID"):
                await get_access_app(zone_id=ZONE_ID, app_id="../../zones")
            with pytest.raises(ValueError, match="policy_id must be a UUID"):
                await delete_access_policy(zone_id=ZONE_ID, app_id=APP_ID, policy_id=ZONE_ID)
        request.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_refused_token_names_the_access_scope(self) -> None:
        async with _patch_cf_client() as request:
            request.side_effect = _access_reply(**FORBIDDEN)
            with pytest.raises(PermissionDeniedError, match="Access: Apps and Policies"):
                await list_access_apps(zone_id=ZONE_ID)
            with pytest.raises(PermissionDeniedError, match="Access: Organizations"):
                await get_access_organization(zone_id=ZONE_ID)


# Mocked API Tests — Analytics Tools


class TestAnalyticsTools:
    """Tests for analytics tools."""

    @pytest.mark.asyncio
    async def test_get_zone_analytics(self) -> None:
        # Analytics uses GraphQL — client.graphql() extracts data from response["data"]
        resp = _mock_cf_response(
            json_data={
                "data": {
                    "viewer": {
                        "zones": [
                            {
                                "totals": [
                                    {
                                        "sum": {
                                            "requests": 1000,
                                            "bytes": 5000,
                                            "cachedRequests": 500,
                                            "cachedBytes": 2500,
                                        },
                                        "uniq": {"uniques": 100},
                                    }
                                ],
                                "statusCodes": [],
                            }
                        ]
                    }
                },
            }
        )
        async with _patch_cf_client(response=resp):
            result = await get_zone_analytics(zone_id=ZONE_ID)
            assert "requests" in result
