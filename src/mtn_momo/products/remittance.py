"""Synchronous and asynchronous clients for the MoMo Remittance product."""

from __future__ import annotations

from typing import ClassVar

from mtn_momo._internal.utils import new_reference_id
from mtn_momo.models.common import Party
from mtn_momo.models.requests import TransferRequest
from mtn_momo.models.responses import TransactionStatus
from mtn_momo.products.base import _AsyncExecMixin, _SyncExecMixin


class RemittanceClient(_SyncExecMixin):
    """Synchronous client for cross-border transfers to a payee."""

    resource: ClassVar[str] = "transfer"
    party_role: ClassVar[str] = "payee"
    product_path: ClassVar[str] = "remittance"
    request_model = TransferRequest

    def transfer(
        self,
        *,
        amount: str,
        currency: str,
        payee: Party,
        payer_message: str = "",
        payee_note: str = "",
        external_id: str | None = None,
    ) -> str:
        """Send a cross-border payout to a payee. No approval from the recipient is required.

        Args:
            amount: The amount to send, as a string, e.g. "500".
            currency: The ISO 4217 currency code, e.g. "EUR".
            payee: The party receiving the payout.
            payer_message: An optional message shown to the payee.
            payee_note: An optional note for your own records.
            external_id: A correlation ID; a UUID4 is generated if omitted.

        Returns:
            The reference ID this transfer was submitted under — pass it to
            get_transaction_status() to check the outcome.
        """
        external_id = external_id or new_reference_id()
        access_token = self._ensure_token()
        request = self._build_payment_request(
            amount=amount,
            currency=currency,
            external_id=external_id,
            party=payee,
            payer_message=payer_message,
            payee_note=payee_note,
            access_token=access_token,
        )
        self._execute(request)
        return external_id

    def get_transaction_status(self, reference_id: str) -> TransactionStatus:
        """Check the status of a previously submitted transfer()."""
        access_token = self._ensure_token()
        request = self._build_status_request(reference_id, access_token)
        response = self._execute(request)
        return self._parse_status_response(response)


class AsyncRemittanceClient(_AsyncExecMixin):
    """Asynchronous client for cross-border transfers to a payee."""

    resource: ClassVar[str] = "transfer"
    party_role: ClassVar[str] = "payee"
    product_path: ClassVar[str] = "remittance"
    request_model = TransferRequest

    async def transfer(
        self,
        *,
        amount: str,
        currency: str,
        payee: Party,
        payer_message: str = "",
        payee_note: str = "",
        external_id: str | None = None,
    ) -> str:
        """Send a cross-border payout to a payee. No approval from the recipient is required.

        Args:
            amount: The amount to send, as a string, e.g. "500".
            currency: The ISO 4217 currency code, e.g. "EUR".
            payee: The party receiving the payout.
            payer_message: An optional message shown to the payee.
            payee_note: An optional note for your own records.
            external_id: A correlation ID; a UUID4 is generated if omitted.

        Returns:
            The reference ID this transfer was submitted under — pass it to
            get_transaction_status() to check the outcome.
        """
        external_id = external_id or new_reference_id()
        access_token = await self._ensure_token()
        request = self._build_payment_request(
            amount=amount,
            currency=currency,
            external_id=external_id,
            party=payee,
            payer_message=payer_message,
            payee_note=payee_note,
            access_token=access_token,
        )
        await self._execute(request)
        return external_id

    async def get_transaction_status(self, reference_id: str) -> TransactionStatus:
        """Check the status of a previously submitted transfer()."""
        access_token = await self._ensure_token()
        request = self._build_status_request(reference_id, access_token)
        response = await self._execute(request)
        return self._parse_status_response(response)
