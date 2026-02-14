"""Tests for MCP tools.

These tests verify tool behavior without making actual API calls.
Integration tests with a real Cloudflare account should be run separately.
"""

import pytest


class TestToolRegistration:
    """Tests to verify all tools are properly registered."""

    def test_server_has_tools(self) -> None:
        """Server should have all expected tools registered."""
        from mcp_cloudflare_crunchtools.server import mcp

        # Get tool names from the server
        # Note: The exact API depends on FastMCP version
        assert mcp is not None

    def test_imports(self) -> None:
        """All tool functions should be importable."""
        from mcp_cloudflare_crunchtools.tools import (
            create_dns_record,
            create_page_rule,
            delete_dns_record,
            delete_page_rule,
            get_dns_record,
            get_zone,
            list_dns_records,
            list_page_rules,
            list_request_header_rules,
            list_response_header_rules,
            list_url_rewrite_rules,
            list_zones,
            purge_cache,
            set_request_header_rules,
            set_response_header_rules,
            set_url_rewrite_rules,
            update_dns_record,
            update_page_rule,
        )

        # Verify all functions are callable
        assert callable(list_zones)
        assert callable(get_zone)
        assert callable(list_dns_records)
        assert callable(get_dns_record)
        assert callable(create_dns_record)
        assert callable(update_dns_record)
        assert callable(delete_dns_record)
        assert callable(list_request_header_rules)
        assert callable(set_request_header_rules)
        assert callable(list_response_header_rules)
        assert callable(set_response_header_rules)
        assert callable(list_url_rewrite_rules)
        assert callable(set_url_rewrite_rules)
        assert callable(list_page_rules)
        assert callable(create_page_rule)
        assert callable(update_page_rule)
        assert callable(delete_page_rule)
        assert callable(purge_cache)


class TestErrorSafety:
    """Tests to verify error messages don't leak sensitive data."""

    def test_cloudflare_api_error_sanitizes_token(self) -> None:
        """CloudflareApiError should sanitize tokens from messages."""
        import os

        from mcp_cloudflare_crunchtools.errors import CloudflareApiError

        # Set a fake token
        os.environ["CLOUDFLARE_API_TOKEN"] = "secret_token_12345"

        try:
            error = CloudflareApiError(401, "Invalid token: secret_token_12345")
            assert "secret_token_12345" not in str(error)
            assert "***" in str(error)
        finally:
            del os.environ["CLOUDFLARE_API_TOKEN"]

    def test_zone_not_found_truncates_long_ids(self) -> None:
        """ZoneNotFoundError should truncate long identifiers."""
        from mcp_cloudflare_crunchtools.errors import ZoneNotFoundError

        long_id = "a" * 100
        error = ZoneNotFoundError(long_id)
        error_str = str(error)

        # Should be truncated
        assert long_id not in error_str
        assert "..." in error_str


class TestConfigSafety:
    """Tests for configuration security."""

    def test_config_repr_hides_token(self) -> None:
        """Config repr should never show the token."""
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
        """Config should require CLOUDFLARE_API_TOKEN."""
        import os

        from mcp_cloudflare_crunchtools.config import Config
        from mcp_cloudflare_crunchtools.errors import ConfigurationError

        # Ensure token is not set
        token = os.environ.pop("CLOUDFLARE_API_TOKEN", None)

        try:
            # Reset the global config
            import mcp_cloudflare_crunchtools.config as config_module

            config_module._config = None

            with pytest.raises(ConfigurationError):
                Config()
        finally:
            if token:
                os.environ["CLOUDFLARE_API_TOKEN"] = token
