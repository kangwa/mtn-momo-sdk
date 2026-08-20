"""Models for responses returned by the MoMo API."""

from momo_sdk.constants import TransactionStatusValue
from momo_sdk.models.common import MomoModel
from momo_sdk.models.errors import MomoErrorBody


class TransactionStatus(MomoModel):
    """The current state of a payment started with request_to_pay() or transfer().

    Check status to see whether it succeeded, failed, or is still pending.

    Attributes:
        status: The transaction's current lifecycle status.
        amount: The transaction amount, when available.
        currency: The ISO 4217 currency code, when available.
        financial_transaction_id: MoMo's ID for the underlying financial transaction.
        external_id: The caller-generated ID the transaction was created with.
        reason: The error that caused a FAILED status, if applicable.
    """

    status: TransactionStatusValue
    amount: str | None = None
    currency: str | None = None
    financial_transaction_id: str | None = None
    external_id: str | None = None
    reason: MomoErrorBody | None = None


class BalanceInfo(MomoModel):
    """How much money is available in an account, and in what currency.

    Attributes:
        available_balance: The available balance, as a string.
        currency: The ISO 4217 currency code the balance is denominated in.
    """

    available_balance: str
    currency: str


class TokenResponse(MomoModel):
    """The access token MoMo hands back after authenticating.

    Use this as the Bearer token on every call until it expires.

    Attributes:
        access_token: The bearer token to send on subsequent requests.
        token_type: The token type returned by MoMo (commonly "access_token").
        expires_in: Seconds until the token expires.
    """

    access_token: str
    token_type: str
    expires_in: int


class ApiUserInfo(MomoModel):
    """Details about a sandbox API user, returned after you provision one.

    Attributes:
        provider_callback_host: The callback host registered for this API user.
        target_environment: The environment this API user was provisioned in.
    """

    provider_callback_host: str
    target_environment: str


class BasicUserInfo(MomoModel):
    """Basic KYC details MoMo has on file for a payer.

    Fields may be missing — what's available depends on what the subscriber
    has shared with MTN.

    Attributes:
        given_name: The payer's given name, if known.
        family_name: The payer's family name, if known.
        birthdate: The payer's birthdate, if known.
        locale: The payer's locale, if known.
        gender: The payer's gender, if known.
        status: The payer's account status, if known.
    """

    given_name: str | None = None
    family_name: str | None = None
    birthdate: str | None = None
    locale: str | None = None
    gender: str | None = None
    status: str | None = None
