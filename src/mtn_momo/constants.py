"""Shared constants and enums used across the MoMo SDK."""

from enum import Enum

SANDBOX_BASE_URL = "https://sandbox.momodeveloper.mtn.com"


class PartyIdType(str, Enum):
    """Identifier type for a Party (payer or payee) in a MoMo transaction."""

    MSISDN = "MSISDN"
    EMAIL = "EMAIL"
    PARTY_CODE = "PARTY_CODE"


class TransactionStatusValue(str, Enum):
    """Lifecycle status of a request-to-pay or transfer, as reported by MoMo."""

    PENDING = "PENDING"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
