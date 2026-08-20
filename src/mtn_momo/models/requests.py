"""Models for requests sent to the MoMo API."""

from mtn_momo.models.common import MomoModel, Party


class RequestToPayRequest(MomoModel):
    """A payment request sent to a payer for approval.

    Poll the transaction status afterward to see the outcome.

    Attributes:
        amount: The amount to request, as a string (e.g. "500").
        currency: The ISO 4217 currency code, e.g. "EUR".
        external_id: A caller-generated ID correlating this request to your own records.
        payer: The party being asked to approve the payment.
        payer_message: An optional message shown to the payer.
        payee_note: An optional note for the payee's own records.
    """

    amount: str
    currency: str
    external_id: str
    payer: Party
    payer_message: str = ""
    payee_note: str = ""


class TransferRequest(MomoModel):
    """A payout sent to a payee — used for disbursements and remittances.

    No approval from the recipient is required.

    Attributes:
        amount: The amount to send, as a string (e.g. "500").
        currency: The ISO 4217 currency code, e.g. "EUR".
        external_id: A caller-generated ID correlating this transfer to your own records.
        payee: The party receiving the payout.
        payer_message: An optional message shown to the payee.
        payee_note: An optional note for the payer's own records.
    """

    amount: str
    currency: str
    external_id: str
    payee: Party
    payer_message: str = ""
    payee_note: str = ""
