import httpx
import pytest
import respx

from mtn_momo.exceptions import MomoConnectionError, MomoTimeoutError
from mtn_momo.http.base import PreparedRequest
from mtn_momo.http.sync_transport import SyncHttpTransport


class TestSyncHttpTransport:
    @respx.mock
    def test_send_returns_response(self) -> None:
        respx.get("https://example.test/ping").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        transport = SyncHttpTransport()
        response = transport.send(
            PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        )
        assert response.status_code == 200

    @respx.mock
    def test_timeout_raises_momo_timeout_error(self) -> None:
        respx.get("https://example.test/ping").mock(side_effect=httpx.TimeoutException("timed out"))
        transport = SyncHttpTransport()
        request = PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        with pytest.raises(MomoTimeoutError):
            transport.send(request)

    @respx.mock
    def test_connection_error_raises_momo_connection_error(self) -> None:
        respx.get("https://example.test/ping").mock(side_effect=httpx.ConnectError("boom"))
        transport = SyncHttpTransport()
        request = PreparedRequest(method="GET", url="https://example.test/ping", headers={})
        with pytest.raises(MomoConnectionError):
            transport.send(request)

    def test_close_closes_underlying_client(self) -> None:
        transport = SyncHttpTransport()
        transport.close()
        assert transport._client.is_closed

    def test_context_manager_closes_on_exit(self) -> None:
        with SyncHttpTransport() as transport:
            pass
        assert transport._client.is_closed
