"""Shared test fixtures for mcp-cloudflare tests."""

import json
import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> Generator[None, None, None]:
    """Reset the Cloudflare client and config singletons between tests."""
    import mcp_cloudflare_crunchtools.client as client_mod
    import mcp_cloudflare_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None
    yield
    client_mod._client = None
    config_mod._config = None


def _mock_cf_response(
    status_code: int = 200,
    json_data: dict[str, Any] | list[Any] | None = None,
) -> httpx.Response:
    """Build a mock Cloudflare API JSON response."""
    if json_data is None:
        json_data = {"success": True, "result": {}, "errors": [], "messages": []}
    return httpx.Response(
        status_code,
        content=json.dumps(json_data).encode(),
        headers={"content-type": "application/json"},
        request=httpx.Request("GET", "https://api.cloudflare.com/client/v4"),
    )


@asynccontextmanager
async def _patch_cf_client(
    response: httpx.Response | None = None,
) -> AsyncIterator[AsyncMock]:
    """Patch httpx.AsyncClient to return mock Cloudflare responses."""
    env = {
        "CLOUDFLARE_API_TOKEN": "test_token_abc123",
    }
    mock_method = AsyncMock()
    if response is not None:
        mock_method.return_value = response
    else:
        mock_method.return_value = _mock_cf_response()

    with patch.dict(os.environ, env, clear=True), patch(
        "httpx.AsyncClient.request", mock_method
    ):
        yield mock_method
