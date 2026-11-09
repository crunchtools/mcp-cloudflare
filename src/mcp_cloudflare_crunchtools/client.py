"""Cloudflare API client with security hardening.

This module provides a secure async HTTP client for the Cloudflare API.
All requests go through this client to ensure consistent security practices.
"""

import json
import logging
from importlib.metadata import version
from typing import Any

import httpx

from .config import get_config
from .errors import (
    CloudflareApiError,
    PermissionDeniedError,
    RateLimitError,
    ZoneNotFoundError,
)

logger = logging.getLogger(__name__)

# Response size limit to prevent memory exhaustion (10MB)
MAX_RESPONSE_SIZE = 10 * 1024 * 1024

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

BODY_SNIPPET_CHARS = 200
ELLIPSIS = "..."

# Identify this client by name. httpx otherwise sends `python-httpx/<version>`,
# which Cloudflare's OWN bot protection answers with an HTML challenge page --
# that is the failure that cost an afternoon on mcp-wordpress (RT #1596), and
# this is the client that talks to Cloudflare. The version comes from installed
# package metadata so it cannot drift from pyproject.toml.
USER_AGENT = (
    f"mcp-cloudflare-crunchtools/{version('mcp-cloudflare-crunchtools')} "
    "(+https://github.com/crunchtools/mcp-cloudflare)"
)


def _body_snippet(body: bytes) -> str:
    """A short, single-line excerpt of a response body, for an error message."""
    prefix = body[: BODY_SNIPPET_CHARS * 4]
    collapsed = " ".join(prefix.decode("utf-8", errors="replace").split())
    if not collapsed:
        return "<empty body>"
    if len(collapsed) > BODY_SNIPPET_CHARS or len(body) > len(prefix):
        return collapsed[: BODY_SNIPPET_CHARS - len(ELLIPSIS)] + ELLIPSIS
    return collapsed


def _where(response: httpx.Response) -> str:
    """Which request a response answered, for an error message."""
    return (
        f"{response.request.method} {response.request.url} "
        f"(HTTP {response.status_code}, {response.headers.get('content-type', 'no content-type')})"
    )


async def _read_capped(response: httpx.Response) -> bytes:
    """Read the body, aborting as soon as it would pass MAX_RESPONSE_SIZE.

    One buffer, measured before the copy: `aiter_bytes()` promises nothing about
    chunk size -- one chunk can be the whole body -- so appending first would
    copy in exactly the response being refused. The `content-length` check this
    replaces was the only limit, and a GraphQL analytics reply is the kind of
    body that arrives chunked.
    """
    declared = response.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_RESPONSE_SIZE:
        raise CloudflareApiError(
            response.status_code,
            f"{_where(response)} declared {declared} bytes, over the "
            f"{MAX_RESPONSE_SIZE} byte limit",
        )
    body = bytearray()
    async for chunk in response.aiter_bytes():
        if len(body) + len(chunk) > MAX_RESPONSE_SIZE:
            raise CloudflareApiError(
                response.status_code,
                f"{_where(response)} sent over the {MAX_RESPONSE_SIZE} byte limit",
            )
        body += chunk
    return bytes(body)


# The error code Cloudflare gives a token that is valid but not allowed to do this.
TOKEN_REFUSED_CODE = 10000


class CloudflareClient:
    """Async HTTP client for Cloudflare API.

    Security features:
    - Hardcoded base URL (prevents SSRF)
    - Token passed via auth header (not URL)
    - TLS certificate validation (httpx default)
    - Request timeout enforcement
    - Response size limits
    """

    def __init__(self) -> None:
        """Initialize the Cloudflare client."""
        self._config = get_config()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._config.api_base_url,
                headers={
                    "Authorization": f"Bearer {self._config.token}",
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                },
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                # Enable TLS certificate verification (default, but explicit)
                verify=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., /zones)
            params: Query parameters
            json_data: JSON body data

        Returns:
            API response data

        Raises:
            CloudflareApiError: On API errors
            RateLimitError: On rate limiting
            PermissionDeniedError: On authorization failures
        """
        client = await self._get_client()

        # Log request (without sensitive data)
        logger.debug("API request: %s %s", method, path)

        try:
            request = client.build_request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )
            response = await client.send(request, stream=True)
            try:
                body = await _read_capped(response)
            finally:
                await response.aclose()
        except httpx.TimeoutException as e:
            raise CloudflareApiError(0, f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise CloudflareApiError(0, f"Request failed: {e}") from e

        try:
            payload: dict[str, Any] = json.loads(body)
        except ValueError as e:
            raise CloudflareApiError(
                response.status_code,
                f"{_where(response)} is not JSON ({e}): {_body_snippet(body)}",
            ) from e

        if not response.is_success:
            self._handle_error_response(response.status_code, payload)

        return payload

    def _handle_error_response(self, status_code: int, payload: dict[str, Any]) -> None:
        """Handle error responses from the API.

        Args:
            status_code: HTTP status code
            payload: Parsed response body

        Raises:
            Various UserError subclasses based on error type
        """
        # Extract error details
        errors = payload.get("errors", [])
        error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
        error_code = errors[0].get("code", 0) if errors else 0

        # Handle specific status codes
        if status_code == 401:
            raise PermissionDeniedError("Valid API token")
        # Cloudflare refuses a token that lacks a scope with code 10000. Any other
        # 403 says something specific, such as Access not being enabled on the
        # account, and falls through to carry Cloudflare's own message.
        if status_code == 403 and error_code == TOKEN_REFUSED_CODE:
            raise PermissionDeniedError("Required permission scope")
        if status_code == 404:
            raise ZoneNotFoundError(error_msg)
        if status_code == 429:
            retry_after = payload.get("retry_after")
            raise RateLimitError(retry_after)

        raise CloudflareApiError(error_code, error_msg)

    # Convenience methods for HTTP verbs

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", path, params=params, json_data=json_data)

    async def put(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", path, json_data=json_data)

    async def patch(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", path, json_data=json_data)

    async def delete(self, path: str) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", path)

    async def graphql(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GraphQL query to the Cloudflare Analytics API.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            The 'data' portion of the GraphQL response

        Raises:
            CloudflareApiError: On GraphQL errors (which may arrive with HTTP 200)
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self.post("/graphql", json_data=payload)

        # GraphQL errors come back inside the response body, not as HTTP errors
        if response.get("errors"):
            messages = [e.get("message", "Unknown error") for e in response["errors"]]
            raise CloudflareApiError(0, "; ".join(messages))

        result: dict[str, Any] = response.get("data", {})
        return result


# Global client instance
_client: CloudflareClient | None = None


def get_client() -> CloudflareClient:
    """Get the global Cloudflare client instance."""
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client
