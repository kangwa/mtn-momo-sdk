"""Asynchronous HTTP transport wrapping httpx.AsyncClient."""

from __future__ import annotations

from typing import Any

import httpx

from mtn_momo.exceptions import MomoConnectionError, MomoTimeoutError
from mtn_momo.http.base import PreparedRequest


class AsyncHttpTransport:
    """Sends PreparedRequest objects over an asynchronous httpx.AsyncClient."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)

    async def send(self, request: PreparedRequest) -> httpx.Response:
        """Execute a prepared request and return the raw response.

        Raises:
            MomoTimeoutError: If the request times out.
            MomoConnectionError: If the request fails for any other network reason.
        """
        try:
            return await self._client.request(
                request.method,
                request.url,
                headers=request.headers,
                params=request.params,
                json=request.json,
            )
        except httpx.TimeoutException as exc:
            raise MomoTimeoutError(f"Request to {request.url} timed out") from exc
        except httpx.TransportError as exc:
            raise MomoConnectionError(f"Request to {request.url} failed: {exc}") from exc

    async def aclose(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpTransport:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()
