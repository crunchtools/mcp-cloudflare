"""Shared test fixtures for mcp-cloudflare tests."""

import json
import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import call, patch

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


class _Recorder:
    """What the caller asked for, and what it gets back.

    The client streams now -- `build_request` then `send(..., stream=True)` --
    so there is no single mocked method carrying both the request arguments and
    the reply. This keeps that one place: `build_request` records its kwargs
    here and `send` answers from the same record, so a test reads
    `call_args_list[i].kwargs` and sets `side_effect` exactly as it did when
    `request` was one call.

    What a patch at this level cannot see is the client's own behaviour -- the
    User-Agent it adds, and the bounded read it performs. Those are tested in
    `test_http_contract.py` over a `MockTransport` (constitution v1.36.0,
    Layer 3).
    """

    def __init__(self, default: httpx.Response) -> None:
        self.default = default
        self.call_args_list: list[Any] = []
        self.side_effect: Any = None
        self._queue: Any = None

    @property
    def call_count(self) -> int:
        return len(self.call_args_list)

    @property
    def call_args(self) -> Any:
        return self.call_args_list[-1] if self.call_args_list else None

    def assert_not_awaited(self) -> None:
        """Kept from the Mock interface: nothing reached the API at all."""
        assert not self.call_args_list, f"expected no request, got {self.call_args_list}"

    def answer(self) -> httpx.Response:
        """The reply for the call just recorded.

        `side_effect` keeps both meanings it has on a Mock: a callable is asked
        for a reply from the request arguments, and anything else iterable is a
        queue of replies consumed in order.
        """
        if self.side_effect is None:
            return self.default
        if callable(self.side_effect):
            return self.side_effect(**self.call_args_list[-1].kwargs)
        if self._queue is None:
            self._queue = iter(self.side_effect)
        return next(self._queue)


@asynccontextmanager
async def _patch_cf_client(
    response: httpx.Response | None = None,
) -> AsyncIterator[_Recorder]:
    """Patch the client to answer with a mock Cloudflare response."""
    env = {
        "CLOUDFLARE_API_TOKEN": "test_token_abc123",
    }
    recorder = _Recorder(response if response is not None else _mock_cf_response())
    real_build = httpx.AsyncClient.build_request

    def build(self: httpx.AsyncClient, *args: Any, **kwargs: Any) -> httpx.Request:
        recorder.call_args_list.append(call(**kwargs))
        return real_build(self, *args, **kwargs)

    async def send(_self: httpx.AsyncClient, _request: httpx.Request, **_: Any) -> httpx.Response:
        # The reply comes from what `build_request` recorded a moment earlier,
        # so neither the client nor the built request is needed here.
        return recorder.answer()

    with (
        patch.dict(os.environ, env, clear=True),
        patch("httpx.AsyncClient.build_request", build),
        patch("httpx.AsyncClient.send", send),
    ):
        yield recorder
