from mtn_momo.client import AsyncMomoClient, MomoClient
from mtn_momo.config import ProductConfig

BASE_URL = "https://sandbox.momodeveloper.mtn.com"


def _config() -> ProductConfig:
    return ProductConfig(
        base_url=BASE_URL,
        subscription_key="sub-key",
        api_user="api-user",
        api_key="api-key",
    )


class TestMomoClient:
    def test_only_configured_products_are_instantiated(self) -> None:
        client = MomoClient(collections=_config())
        assert client.collections is not None
        assert client.disbursements is None
        assert client.remittance is None

    def test_close_closes_all_configured_transports(self) -> None:
        client = MomoClient(collections=_config(), disbursements=_config())
        client.close()
        assert client.collections is not None
        assert client.disbursements is not None
        assert client.collections._transport._client.is_closed
        assert client.disbursements._transport._client.is_closed

    def test_context_manager_closes_on_exit(self) -> None:
        with MomoClient(collections=_config()) as client:
            pass
        assert client.collections is not None
        assert client.collections._transport._client.is_closed


class TestAsyncMomoClient:
    async def test_only_configured_products_are_instantiated(self) -> None:
        client = AsyncMomoClient(remittance=_config())
        assert client.remittance is not None
        assert client.collections is None
        assert client.disbursements is None

    async def test_aclose_closes_all_configured_transports(self) -> None:
        client = AsyncMomoClient(collections=_config(), remittance=_config())
        await client.aclose()
        assert client.collections is not None
        assert client.remittance is not None
        assert client.collections._transport._client.is_closed
        assert client.remittance._transport._client.is_closed

    async def test_context_manager_closes_on_exit(self) -> None:
        async with AsyncMomoClient(disbursements=_config()) as client:
            pass
        assert client.disbursements is not None
        assert client.disbursements._transport._client.is_closed
