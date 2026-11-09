"""The outbound HTTP contract (constitution v1.36.0, MCP Server profile Layer 3).

A real `httpx.AsyncClient` over a `MockTransport`: the agent string is a header
the client adds and the ceiling is enforced while the client reads, so the
`_patch_cf_client` recorder -- which replaces `send` -- cannot see either.
"""

import os
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from importlib.metadata import version
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from mcp_cloudflare_crunchtools import client as client_mod
from mcp_cloudflare_crunchtools.errors import CloudflareApiError

Handler = Callable[[httpx.Request], httpx.Response]


async def _chunks(chunk: bytes, times: int) -> AsyncIterator[bytes]:
    """A chunked body, which carries no content-length -- what a header check misses."""
    for _ in range(times):
        yield chunk


@contextmanager
def _serving(handler: Handler) -> Iterator[None]:
    """Let the client build itself, on a mock transport."""
    import mcp_cloudflare_crunchtools.config as config_mod

    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test_token_abc123"}, clear=True):
        config_mod._config = None
        client_mod._client = None
        with patch.object(httpx, "AsyncClient", factory):
            yield
        config_mod._config = None
        client_mod._client = None


class TestUserAgent:
    """A request says what it is -- to Cloudflare, of all places."""

    @pytest.mark.asyncio
    async def test_outgoing_request_names_the_product_and_version(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers["User-Agent"])
            return httpx.Response(200, json={"success": True, "result": {}})

        with _serving(handler):
            await client_mod.get_client().get("/zones")

        expected = (
            f"mcp-cloudflare-crunchtools/{version('mcp-cloudflare-crunchtools')} "
            "(+https://github.com/crunchtools/mcp-cloudflare)"
        )
        assert seen == [expected]
        # The agent this client used to send is the one Cloudflare's own bot
        # protection answers with a challenge page (RT #1596).
        assert "python-httpx" not in seen[0]


class TestResponseCeiling:
    """The cap is enforced while reading, not taken from a header."""

    @pytest.mark.asyncio
    async def test_chunked_body_over_the_cap_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 4096)

        def handler(_request: httpx.Request) -> httpx.Response:
            response = httpx.Response(
                200, headers={"content-type": "application/json"}, content=_chunks(b"x" * 1024, 16)
            )
            assert "content-length" not in response.headers
            return response

        with _serving(handler), pytest.raises(CloudflareApiError) as caught:
            await client_mod.get_client().graphql("query { viewer { zones { zoneTag } } }")

        message = str(caught.value)
        assert "over the 4096 byte limit" in message
        assert "/graphql" in message

    @pytest.mark.asyncio
    async def test_a_single_oversized_chunk_is_refused_before_it_is_copied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 1024)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_chunks(b"x" * 8192, 1)
            )

        with _serving(handler), pytest.raises(CloudflareApiError) as caught:
            await client_mod.get_client().get("/zones")

        assert "over the 1024 byte limit" in str(caught.value)

    @pytest.mark.asyncio
    async def test_a_declared_length_over_the_cap_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 64)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=b"x" * 128
            )

        with _serving(handler), pytest.raises(CloudflareApiError) as caught:
            await client_mod.get_client().get("/zones")

        assert "declared 128 bytes" in str(caught.value)


class TestErrorNamesTheSite:
    """RT #1596: the message has to say which site answered, and with what."""

    @pytest.mark.asyncio
    async def test_a_challenge_page_is_quoted_with_the_request(self) -> None:
        """The irony is the point: this is the client that talks to Cloudflare."""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                headers={"content-type": "text/html"},
                text="<!DOCTYPE html><title>Just a moment...</title>",
            )

        with _serving(handler), pytest.raises(CloudflareApiError) as caught:
            await client_mod.get_client().get("/zones")

        message = str(caught.value)
        assert "Just a moment" in message
        assert "text/html" in message
        assert "/zones" in message

    @pytest.mark.asyncio
    async def test_cloudflares_own_error_shape_is_still_used(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400, json={"success": False, "errors": [{"code": 1004, "message": "Bad zone"}]}
            )

        with _serving(handler), pytest.raises(CloudflareApiError) as caught:
            await client_mod.get_client().get("/zones")

        assert "Bad zone" in str(caught.value)
