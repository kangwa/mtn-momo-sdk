"""Shared, transport-agnostic core for MoMo product clients."""

from __future__ import annotations

import asyncio
import base64
import threading
from typing import Any, ClassVar

import httpx

from mtn_momo.auth.token_cache import TokenCache
from mtn_momo.config import ProductConfig
from mtn_momo.http.async_transport import AsyncHttpTransport
from mtn_momo.http.base import PreparedRequest, raise_for_response
from mtn_momo.http.sync_transport import SyncHttpTransport
from mtn_momo.models.common import Party
from mtn_momo.models.requests import RequestToPayRequest, TransferRequest
from mtn_momo.models.responses import TokenResponse, TransactionStatus
from mtn_momo.polling import (
    DEFAULT_POLL_CONFIG,
    PollConfig,
    poll_until_complete_async,
    poll_until_complete_sync,
)


class _BaseProductCore:
    """Pure request/response building shared by every product client.

    Subclasses set `resource`, `party_role`, `product_path`, and `request_model`
    to select the right endpoints and request shape; everything else here is
    identical across Collections, Disbursements, and Remittance.
    """

    resource: ClassVar[str]
    party_role: ClassVar[str]
    product_path: ClassVar[str]
    request_model: ClassVar[type[RequestToPayRequest] | type[TransferRequest]]

    def __init__(self, config: ProductConfig) -> None:
        self._config = config
        self._token_cache = TokenCache()

    def _basic_auth_header(self) -> str:
        credentials = f"{self._config.api_user}:{self._config.api_key}".encode()
        return "Basic " + base64.b64encode(credentials).decode()

    def _build_token_request(self) -> PreparedRequest:
        return PreparedRequest(
            method="POST",
            url=f"{self._config.base_url}/{self.product_path}/token/",
            headers={
                "Authorization": self._basic_auth_header(),
                "Ocp-Apim-Subscription-Key": self._config.subscription_key,
            },
        )

    def _build_headers(self, *, reference_id: str, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self._config.target_environment,
            "Ocp-Apim-Subscription-Key": self._config.subscription_key,
            "Content-Type": "application/json",
        }

    def _build_payment_request(
        self,
        *,
        amount: str,
        currency: str,
        external_id: str,
        party: Party,
        payer_message: str,
        payee_note: str,
        access_token: str,
    ) -> PreparedRequest:
        body = self.request_model(
            amount=amount,
            currency=currency,
            external_id=external_id,
            payer_message=payer_message,
            payee_note=payee_note,
            **{self.party_role: party},
        )
        return PreparedRequest(
            method="POST",
            url=f"{self._config.base_url}/{self.product_path}/v1_0/{self.resource}",
            headers=self._build_headers(reference_id=external_id, access_token=access_token),
            json=body.model_dump(by_alias=True),
        )

    def _build_status_request(self, reference_id: str, access_token: str) -> PreparedRequest:
        return PreparedRequest(
            method="GET",
            url=f"{self._config.base_url}/{self.product_path}/v1_0/{self.resource}/{reference_id}",
            headers=self._build_headers(reference_id=reference_id, access_token=access_token),
        )

    @staticmethod
    def _parse_token_response(response: httpx.Response) -> TokenResponse:
        return TokenResponse.model_validate(response.json())

    @staticmethod
    def _parse_status_response(response: httpx.Response) -> TransactionStatus:
        return TransactionStatus.model_validate(response.json())


class _SyncExecMixin(_BaseProductCore):
    """Adds synchronous I/O on top of _BaseProductCore's pure request building."""

    def __init__(self, config: ProductConfig) -> None:
        super().__init__(config)
        self._transport = SyncHttpTransport(timeout=config.timeout)
        self._lock = threading.Lock()

    def _ensure_token(self) -> str:
        token = self._token_cache.get_valid()
        if token is not None:
            return token
        with self._lock:
            token = self._token_cache.get_valid()
            if token is not None:
                return token
            response = self._transport.send(self._build_token_request())
            raise_for_response(response)
            token_response = self._parse_token_response(response)
            self._token_cache.store(token_response.access_token, token_response.expires_in)
            return token_response.access_token

    def _execute(self, request: PreparedRequest) -> httpx.Response:
        response = self._transport.send(request)
        raise_for_response(response)
        return response

    def get_transaction_status(self, reference_id: str) -> TransactionStatus:
        """Check the status of a previously submitted payment or transfer."""
        access_token = self._ensure_token()
        request = self._build_status_request(reference_id, access_token)
        response = self._execute(request)
        return self._parse_status_response(response)

    def wait_for_transaction(
        self, reference_id: str, *, poll_config: PollConfig = DEFAULT_POLL_CONFIG
    ) -> TransactionStatus:
        """Poll get_transaction_status() until the transaction reaches a terminal status.

        Args:
            reference_id: The reference ID returned by request_to_pay() or transfer().
            poll_config: Poll timing configuration.

        Returns:
            The terminal TransactionStatus (SUCCESSFUL or FAILED).

        Raises:
            PollTimeoutError: If poll_config.timeout elapses first.
        """
        return poll_until_complete_sync(
            lambda: self.get_transaction_status(reference_id), poll_config
        )

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()

    def __enter__(self) -> _SyncExecMixin:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class _AsyncExecMixin(_BaseProductCore):
    """Adds asynchronous I/O on top of _BaseProductCore's pure request building."""

    def __init__(self, config: ProductConfig) -> None:
        super().__init__(config)
        self._transport = AsyncHttpTransport(timeout=config.timeout)
        self._lock = asyncio.Lock()

    async def _ensure_token(self) -> str:
        token = self._token_cache.get_valid()
        if token is not None:
            return token
        async with self._lock:
            token = self._token_cache.get_valid()
            if token is not None:
                return token
            response = await self._transport.send(self._build_token_request())
            raise_for_response(response)
            token_response = self._parse_token_response(response)
            self._token_cache.store(token_response.access_token, token_response.expires_in)
            return token_response.access_token

    async def _execute(self, request: PreparedRequest) -> httpx.Response:
        response = await self._transport.send(request)
        raise_for_response(response)
        return response

    async def get_transaction_status(self, reference_id: str) -> TransactionStatus:
        """Check the status of a previously submitted payment or transfer."""
        access_token = await self._ensure_token()
        request = self._build_status_request(reference_id, access_token)
        response = await self._execute(request)
        return self._parse_status_response(response)

    async def wait_for_transaction(
        self, reference_id: str, *, poll_config: PollConfig = DEFAULT_POLL_CONFIG
    ) -> TransactionStatus:
        """Poll get_transaction_status() until the transaction reaches a terminal status.

        Args:
            reference_id: The reference ID returned by request_to_pay() or transfer().
            poll_config: Poll timing configuration.

        Returns:
            The terminal TransactionStatus (SUCCESSFUL or FAILED).

        Raises:
            PollTimeoutError: If poll_config.timeout elapses first.
        """
        return await poll_until_complete_async(
            lambda: self.get_transaction_status(reference_id), poll_config
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP transport."""
        await self._transport.aclose()

    async def __aenter__(self) -> _AsyncExecMixin:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()
