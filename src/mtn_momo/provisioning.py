"""Sandbox provisioning: create an API user and API key for testing against MoMo's sandbox."""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from typing import cast

import httpx

from mtn_momo.constants import SANDBOX_BASE_URL
from mtn_momo.http.base import raise_for_response
from mtn_momo.models.responses import ApiUserInfo


@dataclass(frozen=True)
class ProvisionedCredentials:
    """The api_user/api_key pair produced by provision().

    Attributes:
        api_user: The generated API user UUID.
        api_key: The generated API key for that user.
    """

    api_user: str
    api_key: str


class SandboxProvisioner:
    """Creates a sandbox API user and key against the MoMo developer sandbox.

    Uses subscription-key-only authentication — there's no bearer token yet,
    since the whole point of this class is to create the credentials that
    later get exchanged for one.
    """

    def __init__(self, subscription_key: str, *, base_url: str = SANDBOX_BASE_URL) -> None:
        self._subscription_key = subscription_key
        self._base_url = base_url
        self._client = httpx.Client(timeout=10.0)

    def create_api_user(self, callback_host: str = "") -> str:
        """Create a new sandbox API user and return its generated UUID."""
        api_user = str(uuid.uuid4())
        response = self._client.post(
            f"{self._base_url}/v1_0/apiuser",
            headers={
                "X-Reference-Id": api_user,
                "Ocp-Apim-Subscription-Key": self._subscription_key,
                "Content-Type": "application/json",
            },
            json={"providerCallbackHost": callback_host},
        )
        raise_for_response(response)
        return api_user

    def create_api_key(self, api_user: str) -> str:
        """Generate an API key for an existing API user."""
        response = self._client.post(
            f"{self._base_url}/v1_0/apiuser/{api_user}/apikey",
            headers={"Ocp-Apim-Subscription-Key": self._subscription_key},
        )
        raise_for_response(response)
        return cast(str, response.json()["apiKey"])

    def get_api_user_info(self, api_user: str) -> ApiUserInfo:
        """Fetch details about an existing API user."""
        response = self._client.get(
            f"{self._base_url}/v1_0/apiuser/{api_user}",
            headers={"Ocp-Apim-Subscription-Key": self._subscription_key},
        )
        raise_for_response(response)
        return ApiUserInfo.model_validate(response.json())

    def provision(self, callback_host: str = "") -> ProvisionedCredentials:
        """Create an API user and key in one call — the common case."""
        api_user = self.create_api_user(callback_host)
        api_key = self.create_api_key(api_user)
        return ProvisionedCredentials(api_user=api_user, api_key=api_key)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> SandboxProvisioner:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncSandboxProvisioner:
    """Async equivalent of SandboxProvisioner."""

    def __init__(self, subscription_key: str, *, base_url: str = SANDBOX_BASE_URL) -> None:
        self._subscription_key = subscription_key
        self._base_url = base_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def create_api_user(self, callback_host: str = "") -> str:
        """Create a new sandbox API user and return its generated UUID."""
        api_user = str(uuid.uuid4())
        response = await self._client.post(
            f"{self._base_url}/v1_0/apiuser",
            headers={
                "X-Reference-Id": api_user,
                "Ocp-Apim-Subscription-Key": self._subscription_key,
                "Content-Type": "application/json",
            },
            json={"providerCallbackHost": callback_host},
        )
        raise_for_response(response)
        return api_user

    async def create_api_key(self, api_user: str) -> str:
        """Generate an API key for an existing API user."""
        response = await self._client.post(
            f"{self._base_url}/v1_0/apiuser/{api_user}/apikey",
            headers={"Ocp-Apim-Subscription-Key": self._subscription_key},
        )
        raise_for_response(response)
        return cast(str, response.json()["apiKey"])

    async def get_api_user_info(self, api_user: str) -> ApiUserInfo:
        """Fetch details about an existing API user."""
        response = await self._client.get(
            f"{self._base_url}/v1_0/apiuser/{api_user}",
            headers={"Ocp-Apim-Subscription-Key": self._subscription_key},
        )
        raise_for_response(response)
        return ApiUserInfo.model_validate(response.json())

    async def provision(self, callback_host: str = "") -> ProvisionedCredentials:
        """Create an API user and key in one call — the common case."""
        api_user = await self.create_api_user(callback_host)
        api_key = await self.create_api_key(api_user)
        return ProvisionedCredentials(api_user=api_user, api_key=api_key)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncSandboxProvisioner:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: provision a sandbox API user/key and print the result."""
    parser = argparse.ArgumentParser(
        prog="mtn-momo-provision",
        description="Provision a MoMo sandbox API user and API key.",
    )
    parser.add_argument("--subscription-key", required=True, help="Sandbox subscription key")
    parser.add_argument("--callback-host", default="", help="Provider callback host")
    parser.add_argument("--base-url", default=SANDBOX_BASE_URL, help="API base URL")
    args = parser.parse_args(argv)

    with SandboxProvisioner(args.subscription_key, base_url=args.base_url) as provisioner:
        credentials = provisioner.provision(args.callback_host)

    print(f"API_USER={credentials.api_user}")
    print(f"API_KEY={credentials.api_key}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
