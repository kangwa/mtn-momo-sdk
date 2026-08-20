import httpx
import pytest
import respx

from mtn_momo.exceptions import MomoConnectionError, MomoTimeoutError
from mtn_momo.http.async_transport import AsyncHttpTransport
from mtn_momo.http.base import PreparedRequest


class TestAsyncHttpTransport:
    @respx.mock
    async def test_send_returns_response(self) -> None:
        respx.get("https://example.test/ping").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        transport = AsyncHttpTransport()
        response = await transport.send(
            PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        )
        assert response.status_code == 200

    @respx.mock
    async def test_timeout_raises_momo_timeout_error(self) -> None:
        respx.get("https://example.test/ping").mock(side_effect=httpx.TimeoutException("timed out"))
        transport = AsyncHttpTransport()
        request = PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        with pytest.raises(MomoTimeoutError):
            await transport.send(request)

    @respx.mock
    async def test_connection_error_raises_momo_connection_error(self) -> None:
        respx.get("https://example.test/ping").mock(side_effect=httpx.ConnectError("boom"))
        transport = AsyncHttpTransport()
        request = PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        with pytest.raises(MomoConnectionError):
            await transport.send(request)

    async def test_aclose_closes_underlying_client(self) -> None:
        transport = AsyncHttpTransport()
        await transport.aclose()
        assert transport._client.is_closed

    async def test_context_manager_closes_on_exit(self) -> None:
        async with AsyncHttpTransport() as transport:
            pass
        assert transport._client.is_closed
