import pytest

from mtn_momo.client import AsyncMomoClient, MomoClient
from mtn_momo.config import ProductConfig
from mtn_momo.exceptions import MomoConfigError

BASE_URL = "https://sandbox.momodeveloper.mtn.com"


def _config() -> ProductConfig:
    return ProductConfig(
        base_url=BASE_URL,
        subscription_key="sub-key",
        api_user="api-user",
        api_key="api-key",
    )


@pytest.fixture(autouse=True)
def _clear_momo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for prefix in ("MOMO_COL_", "MOMO_DIS_", "MOMO_REM_"):
        for name in ("SUBSCRIPTION_KEY", "API_USER", "API_KEY", "BASE_URL", "TARGET_ENVIRONMENT"):
            monkeypatch.delenv(f"{prefix}{name}", raising=False)


class TestMomoClient:
    def test_explicit_config_builds_the_client(self) -> None:
        client = MomoClient(collections=_config(), disbursements=_config(), remittance=_config())
        assert client.collections is not None
        assert client.disbursements is not None
        assert client.remittance is not None

    def test_unconfigured_product_raises_on_access(self) -> None:
        client = MomoClient(collections=_config())
        with pytest.raises(MomoConfigError):
            _ = client.disbursements

    def test_builds_from_env_vars_when_no_explicit_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MOMO_COL_SUBSCRIPTION_KEY", "sub-key")
        monkeypatch.setenv("MOMO_COL_API_USER", "api-user")
        monkeypatch.setenv("MOMO_COL_API_KEY", "api-key")

        client = MomoClient()

        assert client.collections is not None

    def test_property_access_is_memoized(self) -> None:
        client = MomoClient(collections=_config())
        assert client.collections is client.collections

    def test_close_closes_only_accessed_clients(self) -> None:
        client = MomoClient(collections=_config(), disbursements=_config())
        collections_client = client.collections  # trigger construction
        # disbursements never accessed, so it should never be built or closed
        client.close()
        assert collections_client._transport._client.is_closed

    def test_context_manager_closes_on_exit(self) -> None:
        with MomoClient(collections=_config()) as client:
            collections_client = client.collections
        assert collections_client._transport._client.is_closed


class TestAsyncMomoClient:
    async def test_unconfigured_product_raises_on_access(self) -> None:
        client = AsyncMomoClient(remittance=_config())
        with pytest.raises(MomoConfigError):
            _ = client.collections

    async def test_builds_from_env_vars_when_no_explicit_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MOMO_REM_SUBSCRIPTION_KEY", "sub-key")
        monkeypatch.setenv("MOMO_REM_API_USER", "api-user")
        monkeypatch.setenv("MOMO_REM_API_KEY", "api-key")

        client = AsyncMomoClient()

        assert client.remittance is not None

    async def test_property_access_is_memoized(self) -> None:
        client = AsyncMomoClient(collections=_config())
        assert client.collections is client.collections

    async def test_aclose_closes_only_accessed_clients(self) -> None:
        client = AsyncMomoClient(collections=_config(), remittance=_config())
        collections_client = client.collections
        await client.aclose()
        assert collections_client._transport._client.is_closed

    async def test_context_manager_closes_on_exit(self) -> None:
        async with AsyncMomoClient(disbursements=_config()) as client:
            disbursements_client = client.disbursements
        assert disbursements_client._transport._client.is_closed
