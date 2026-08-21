from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from mtn_momo.exceptions import (
    ERROR_CODE_MAP,
    AuthenticationError,
    DuplicateReferenceError,
    MomoAPIError,
    ResourceNotFoundError,
    ServerError,
    UnknownMomoAPIError,
    ValidationError,
)


@dataclass(frozen=True)
class PreparedRequest:
    """A fully-built HTTP request, ready to hand to a sync or async client.

    Attributes:
        method: The HTTP method e.g. `GET` or `POST`
        url: the full request URL
        headers: Request headers
        params: Optional query parameters
        json: Optional JSON request body
    """

    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, str] | None = None
    json: dict[str, Any] | None = None


def raise_for_response(response: httpx.Response) -> None:
    """Raise a typed MomoAPIError subclass if the response is a MoMo API failure.

    Args:
        response: The httpx.Response already returned by a sync or async transport.

    Raises:
        MomoAPIError: Or one of its subclasses, based on the HTTP status and,
        when available, MoMo's error code.
    """
    if response.is_success:
        return

    status_code = response.status_code
    message = f"MoMo API request failed with status {status_code}"

    try:
        body: Any = response.json()
    except ValueError:
        body = None

    error_code: str | None = None

    if isinstance(body, dict):
        error_code = body.get("code")
        message = body.get("message", message)

    if status_code == 409:
        raise DuplicateReferenceError(
            message, status_code=status_code, error_code=error_code, raw_body=body
        )

    if status_code == 401:
        raise AuthenticationError(
            message, status_code=status_code, error_code=error_code, raw_body=body
        )

    if status_code == 404:
        raise ResourceNotFoundError(
            message, status_code=status_code, error_code=error_code, raw_body=body
        )

    if error_code is not None:
        exc_type = ERROR_CODE_MAP.get(error_code, UnknownMomoAPIError)
        raise exc_type(message, status_code=status_code, error_code=error_code, raw_body=body)

    if status_code >= 500:
        raise ServerError(message, status_code=status_code, raw_body=body)

    raise ValidationError(message, status_code=status_code, raw_body=body)


def parse_json_response(response: httpx.Response) -> Any:
    """Parse a response body as JSON, raising a typed error if it isn't valid JSON.

    A successful HTTP status doesn't guarantee a JSON body — an edge proxy or
    WAF in front of the real API can return an HTML error page with a 2xx
    status. Use this instead of calling response.json() directly when parsing
    a response already confirmed successful by raise_for_response().

    Raises:
        MomoAPIError: If the body can't be parsed as JSON.
    """
    try:
        return response.json()
    except ValueError as exc:
        raise MomoAPIError(
            "MoMo API returned a non-JSON response body",
            status_code=response.status_code,
            raw_body=response.text,
        ) from exc
