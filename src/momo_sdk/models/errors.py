"""Models for error bodies returned by the MoMo API."""

from momo_sdk.models.common import MomoModel


class MomoErrorBody(MomoModel):
    """The error envelope MoMo returns in failed API responses.

    Attributes:
        code: MoMo's machine-readable error code, e.g. PAYER_NOT_FOUND.
        message: A human-readable description of the error.
    """

    code: str
    message: str
