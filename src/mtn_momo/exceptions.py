"""Exception hierarchy for errors raised by the MoMo SDK."""

from typing import Any


class MomoError(Exception):
    """Base class for every error raised by mtn-momo."""


class MomoConfigError(MomoError):
    """Raised when a ProductConfig is missing required values or has invalid ones."""


class MomoConnectionError(MomoError):
    """Raised when a request never reaches the MoMo API — a network failure, not a rejection."""


class MomoTimeoutError(MomoError):
    """Raised when a request to the MoMo API times out before a response is received."""


class PollTimeoutError(MomoError):
    """Raised when poll_until_complete gives up waiting for a terminal transaction status.

    Attributes:
        last_status: The most recent status observed before giving up, if any.
    """

    def __init__(self, message: str, *, last_status: Any = None) -> None:
        super().__init__(message)
        self.last_status = last_status


class MomoAPIError(MomoError):
    """Raised when the MoMo API rejects a request.

    Attributes:
        status_code: The HTTP status code returned by the MoMo API.
        error_code: MoMo's machine-readable error code, when available.
        raw_body: The raw, unparsed response body, for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_code: str | None = None,
        raw_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.raw_body = raw_body


class AuthenticationError(MomoAPIError):
    """Raised on a 401 — credentials are missing, invalid, or expired."""


class DuplicateReferenceError(MomoAPIError):
    """Raised on a 409 — this X-Reference-Id/external_id was already used for a previous request."""


class ResourceNotFoundError(MomoAPIError):
    """Raised on a 404 — the requested resource doesn't exist."""


class ValidationError(MomoAPIError):
    """Raised on a 400 with no more specific MoMo error code recognized."""


class PayerNotFoundError(MomoAPIError):
    """Raised when the MoMo API can't find an account for the given payer."""


class PayeeNotFoundError(MomoAPIError):
    """Raised when the MoMo API can't find an account for the given payee."""


class NotAllowedError(MomoAPIError):
    """Raised when the account isn't permitted to perform this operation."""


class NotEnoughFundsError(MomoAPIError):
    """Raised when the payer's account doesn't have sufficient balance to cover the payment."""


class ExpiredError(MomoAPIError):
    """Raised when the transaction expires before it's approved or completed."""


class ApprovalRejectedError(MomoAPIError):
    """Raised when the payer declines the payment request."""


class InternalProcessingError(MomoAPIError):
    """Raised when the MoMo API fails to process the request due to an internal error."""


class ServerError(MomoAPIError):
    """Raised on a 5xx with no recognized error body to classify further."""


class UnknownMomoAPIError(MomoAPIError):
    """Raised when the MoMo API returns an error code this SDK has no specific exception for."""


ERROR_CODE_MAP: dict[str, type[MomoAPIError]] = {
    "PAYER_NOT_FOUND": PayerNotFoundError,
    "PAYEE_NOT_FOUND": PayeeNotFoundError,
    "NOT_ALLOWED": NotAllowedError,
    "NOT_ENOUGH_FUNDS": NotEnoughFundsError,
    "EXPIRED": ExpiredError,
    "APPROVAL_REJECTED": ApprovalRejectedError,
    "INTERNAL_PROCESSING_ERROR": InternalProcessingError,
}
