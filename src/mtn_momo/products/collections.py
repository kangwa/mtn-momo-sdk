"""Synchronous client for the MoMo Collections product."""

from __future__ import annotations

from typing import ClassVar

from mtn_momo._internal.utils import new_reference_id
from mtn_momo.models.common import Party
from mtn_momo.models.requests import RequestToPayRequest
from mtn_momo.products.base import _AsyncExecMixin, _SyncExecMixin


class CollectionsClient(_SyncExecMixin):
    """Synchronous client for requesting and tracking payments from a payer."""

    resource: ClassVar[str] = "requesttopay"
    party_role: ClassVar[str] = "payer"
    product_path: ClassVar[str] = "collection"
    request_model = RequestToPayRequest

    def request_to_pay(
        self,
        *,
        amount: str,
        currency: str,
        payer: Party,
        payer_message: str = "",
        payee_note: str = "",
        external_id: str | None = None,
    ) -> str:
        """Ask a payer to authorize a payment.

        Args:
            amount: The amount to request, as a string, e.g. "500".
            currency: The ISO 4217 currency code, e.g. "EUR".
            payer: The party being asked to approve the payment.
            payer_message: An optional message shown to the payer.
            payee_note: An optional note for your own records.
            external_id: A correlation ID; a UUID4 is generated if omitted.

        Returns:
            The reference ID this request was submitted under — pass it to
            get_transaction_status() to check the outcome.
        """
        external_id = external_id or new_reference_id()
        access_token = self._ensure_token()
        request = self._build_payment_request(
            amount=amount,
            currency=currency,
            external_id=external_id,
            party=payer,
            payer_message=payer_message,
            payee_note=payee_note,
            access_token=access_token,
        )
        self._execute(request)
        return external_id


class AsyncCollectionsClient(_AsyncExecMixin):
    """Asynchronous client for requesting and tracking payments from a payer."""

    resource: ClassVar[str] = "requesttopay"
    party_role: ClassVar[str] = "payer"
    product_path: ClassVar[str] = "collection"
    request_model = RequestToPayRequest

    async def request_to_pay(
        self,
        *,
        amount: str,
        currency: str,
        payer: Party,
        payer_message: str = "",
        payee_note: str = "",
        external_id: str | None = None,
    ) -> str:
        """Ask a payer to authorize a payment.

        Args:
            amount: The amount to request, as a string, e.g. "500".
            currency: The ISO 4217 currency code, e.g. "EUR".
            payer: The party being asked to approve the payment.
            payer_message: An optional message shown to the payer.
            payee_note: An optional note for your own records.
            external_id: A correlation ID; a UUID4 is generated if omitted.

        Returns:
            The reference ID this request was submitted under — pass it to
            get_transaction_status() to check the outcome.
        """
        external_id = external_id or new_reference_id()
        access_token = await self._ensure_token()
        request = self._build_payment_request(
            amount=amount,
            currency=currency,
            external_id=external_id,
            party=payer,
            payer_message=payer_message,
            payee_note=payee_note,
            access_token=access_token,
        )
        await self._execute(request)
        return external_id
