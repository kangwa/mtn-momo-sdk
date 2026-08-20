"""Synchronous HTTP transport wrapping httpx.Client."""

from __future__ import annotations

from typing import Any

import httpx

from mtn_momo.exceptions import MomoConnectionError, MomoTimeoutError
from mtn_momo.http.base import PreparedRequest


class SyncHttpTransport:
    """Sends PreparedRequest objects over a synchronous httpx.Client."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self._client = httpx.Client(timeout=timeout)

    def send(self, request: PreparedRequest) -> httpx.Response:
        """Execute a prepared request and return the raw response.

        Raises:
            MomoTimeoutError: If the request times out.
            MomoConnectionError: If the request fails for any other network reason.
        """
        try:
            return self._client.request(
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

    def close(self) -> None:
        """Close the underlying httpx.Client."""
        self._client.close()

    def __enter__(self) -> SyncHttpTransport:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
