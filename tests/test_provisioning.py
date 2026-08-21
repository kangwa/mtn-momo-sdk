import json

import httpx
import pytest
import respx

from mtn_momo.constants import SANDBOX_BASE_URL
from mtn_momo.provisioning import (
    AsyncSandboxProvisioner,
    ProvisionedCredentials,
    SandboxProvisioner,
    main,
)


class TestSandboxProvisioner:
    @respx.mock
    def test_default_callback_host_is_not_empty(self) -> None:
        # MTN's real sandbox rejects an empty providerCallbackHost with a bare
        # 400, so the default here must never regress to "".
        route = respx.post(f"{SANDBOX_BASE_URL}/v1_0/apiuser").mock(
            return_value=httpx.Response(201)
        )

        SandboxProvisioner("sub-key").create_api_user()

        request = route.calls.last.request
        assert json.loads(request.content)["providerCallbackHost"] != ""

    @respx.mock
    def test_create_api_user_returns_generated_uuid(self) -> None:
        route = respx.post(f"{SANDBOX_BASE_URL}/v1_0/apiuser").mock(
            return_value=httpx.Response(201)
        )

        provisioner = SandboxProvisioner("sub-key")
        api_user = provisioner.create_api_user(callback_host="https://example.test/callback")

        request = route.calls.last.request
        assert request.headers["X-Reference-Id"] == api_user
        assert request.headers["Ocp-Apim-Subscription-Key"] == "sub-key"
        assert json.loads(request.content) == {
            "providerCallbackHost": "https://example.test/callback"
        }

    @respx.mock
    def test_create_api_key_returns_key(self) -> None:
        respx.post(f"{SANDBOX_BASE_URL}/v1_0/apiuser/user-1/apikey").mock(
            return_value=httpx.Response(201, json={"apiKey": "secret-key"})
        )

        provisioner = SandboxProvisioner("sub-key")
        api_key = provisioner.create_api_key("user-1")

        assert api_key == "secret-key"

    @respx.mock
    def test_get_api_user_info_parses_response(self) -> None:
        respx.get(f"{SANDBOX_BASE_URL}/v1_0/apiuser/user-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "providerCallbackHost": "https://example.test",
                    "targetEnvironment": "sandbox",
                },
            )
        )

        provisioner = SandboxProvisioner("sub-key")
        info = provisioner.get_api_user_info("user-1")

        assert info.provider_callback_host == "https://example.test"
        assert info.target_environment == "sandbox"

    def test_provision_creates_user_then_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        provisioner = SandboxProvisioner("sub-key")
        monkeypatch.setattr(provisioner, "create_api_user", lambda callback_host="": "user-1")
        monkeypatch.setattr(provisioner, "create_api_key", lambda api_user: "secret-key")

        credentials = provisioner.provision()

        assert credentials == ProvisionedCredentials(api_user="user-1", api_key="secret-key")

    def test_close_closes_client(self) -> None:
        provisioner = SandboxProvisioner("sub-key")
        provisioner.close()
        assert provisioner._client.is_closed

    def test_context_manager_closes_on_exit(self) -> None:
        with SandboxProvisioner("sub-key") as provisioner:
            pass
        assert provisioner._client.is_closed


class TestAsyncSandboxProvisioner:
    @respx.mock
    async def test_create_api_user_returns_generated_uuid(self) -> None:
        route = respx.post(f"{SANDBOX_BASE_URL}/v1_0/apiuser").mock(
            return_value=httpx.Response(201)
        )

        provisioner = AsyncSandboxProvisioner("sub-key")
        api_user = await provisioner.create_api_user(callback_host="https://example.test/callback")

        request = route.calls.last.request
        assert request.headers["X-Reference-Id"] == api_user
        assert json.loads(request.content) == {
            "providerCallbackHost": "https://example.test/callback"
        }

    @respx.mock
    async def test_create_api_key_returns_key(self) -> None:
        respx.post(f"{SANDBOX_BASE_URL}/v1_0/apiuser/user-1/apikey").mock(
            return_value=httpx.Response(201, json={"apiKey": "secret-key"})
        )

        provisioner = AsyncSandboxProvisioner("sub-key")
        api_key = await provisioner.create_api_key("user-1")

        assert api_key == "secret-key"

    @respx.mock
    async def test_get_api_user_info_parses_response(self) -> None:
        respx.get(f"{SANDBOX_BASE_URL}/v1_0/apiuser/user-1").mock(
            return_value=httpx.Response(
                200,
                json={
                    "providerCallbackHost": "https://example.test",
                    "targetEnvironment": "sandbox",
                },
            )
        )

        provisioner = AsyncSandboxProvisioner("sub-key")
        info = await provisioner.get_api_user_info("user-1")

        assert info.provider_callback_host == "https://example.test"
        assert info.target_environment == "sandbox"

    async def test_provision_creates_user_then_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        provisioner = AsyncSandboxProvisioner("sub-key")

        async def _fake_create_api_user(callback_host: str = "") -> str:
            return "user-1"

        async def _fake_create_api_key(api_user: str) -> str:
            return "secret-key"

        monkeypatch.setattr(provisioner, "create_api_user", _fake_create_api_user)
        monkeypatch.setattr(provisioner, "create_api_key", _fake_create_api_key)

        credentials = await provisioner.provision()

        assert credentials == ProvisionedCredentials(api_user="user-1", api_key="secret-key")

    async def test_aclose_closes_client(self) -> None:
        provisioner = AsyncSandboxProvisioner("sub-key")
        await provisioner.aclose()
        assert provisioner._client.is_closed

    async def test_context_manager_closes_on_exit(self) -> None:
        async with AsyncSandboxProvisioner("sub-key") as provisioner:
            pass
        assert provisioner._client.is_closed


class TestMain:
    def test_main_prints_credentials(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        class _FakeProvisioner:
            def __init__(self, subscription_key: str, *, base_url: str) -> None:
                pass

            def provision(self, callback_host: str = "") -> ProvisionedCredentials:
                return ProvisionedCredentials(api_user="user-1", api_key="secret-key")

            def close(self) -> None:
                pass

            def __enter__(self) -> "_FakeProvisioner":
                return self

            def __exit__(self, *exc: object) -> None:
                self.close()

        monkeypatch.setattr("mtn_momo.provisioning.SandboxProvisioner", _FakeProvisioner)

        exit_code = main(["--product", "collections", "--subscription-key", "sub-key"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "MOMO_COL_SUBSCRIPTION_KEY=sub-key" in captured.out
        assert "MOMO_COL_API_USER=user-1" in captured.out
        assert "MOMO_COL_API_KEY=secret-key" in captured.out

    def test_main_uses_product_specific_prefix(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        class _FakeProvisioner:
            def __init__(self, subscription_key: str, *, base_url: str) -> None:
                pass

            def provision(self, callback_host: str = "") -> ProvisionedCredentials:
                return ProvisionedCredentials(api_user="user-1", api_key="secret-key")

            def close(self) -> None:
                pass

            def __enter__(self) -> "_FakeProvisioner":
                return self

            def __exit__(self, *exc: object) -> None:
                self.close()

        monkeypatch.setattr("mtn_momo.provisioning.SandboxProvisioner", _FakeProvisioner)

        exit_code = main(["--product", "disbursements", "--subscription-key", "sub-key"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "MOMO_DIS_API_USER=user-1" in captured.out

    def test_main_requires_subscription_key(self) -> None:
        with pytest.raises(SystemExit):
            main(["--product", "collections"])

    def test_main_requires_product(self) -> None:
        with pytest.raises(SystemExit):
            main(["--subscription-key", "sub-key"])

    def test_main_rejects_unknown_product(self) -> None:
        with pytest.raises(SystemExit):
            main(["--product", "loans", "--subscription-key", "sub-key"])
