"""Cloudflare API client with security hardening.

This module provides a secure async HTTP client for the Cloudflare API.
All requests go through this client to ensure consistent security practices.
"""

import logging
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
            response = await client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
            )
        except httpx.TimeoutException as e:
            raise CloudflareApiError(0, f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise CloudflareApiError(0, f"Request failed: {e}") from e

        # Check response size before parsing
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise CloudflareApiError(0, "Response too large")

        # Parse response
        try:
            data = response.json()
        except ValueError as e:
            raise CloudflareApiError(
                response.status_code, f"Invalid JSON response: {e}"
            ) from e

        # Handle error responses
        if not response.is_success:
            self._handle_error_response(response.status_code, data)

        return data  # type: ignore[no-any-return]

    def _handle_error_response(
        self, status_code: int, data: dict[str, Any]
    ) -> None:
        """Handle error responses from the API.

        Args:
            status_code: HTTP status code
            data: Response data

        Raises:
            Various UserError subclasses based on error type
        """
        # Extract error details
        errors = data.get("errors", [])
        error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
        error_code = errors[0].get("code", 0) if errors else 0

        # Handle specific status codes
        if status_code == 401:
            raise PermissionDeniedError("Valid API token")
        if status_code == 403:
            raise PermissionDeniedError("Required permission scope")
        if status_code == 404:
            raise ZoneNotFoundError(error_msg)
        if status_code == 429:
            retry_after = data.get("retry_after")
            raise RateLimitError(retry_after)

        raise CloudflareApiError(error_code, error_msg)

    # Convenience methods for HTTP verbs

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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


# Global client instance
_client: CloudflareClient | None = None


def get_client() -> CloudflareClient:
    """Get the global Cloudflare client instance."""
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client
