"""Pure in-memory cache for a MoMo access token, with expiry tracking."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CachedToken:
    """An access token paired with the monotonic time it expires at.

    Attributes:
        access_token: The bearer token value.
        expires_at: The clock value after which this token should be considered stale.
    """

    access_token: str
    expires_at: float


class TokenCache:
    """Holds a single cached access token, expiring it slightly early to
    avoid edge-of-window 401s from clock drift or in-flight requests.
    """

    def __init__(
        self, *, leeway: float = 30.0, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._leeway = leeway
        self._clock = clock
        self._token: CachedToken | None = None

    def get_valid(self) -> str | None:
        """Return the cached access token if it's still valid, else None."""
        if self._token is None:
            return None
        if self._clock() >= self._token.expires_at:
            return None
        return self._token.access_token

    def store(self, access_token: str, expires_in: int) -> None:
        """Cache a newly fetched token.

        Args:
            access_token: The bearer token value.
            expires_in: Seconds until MoMo considers the token expired.
        """
        expires_at = self._clock() + max(expires_in - self._leeway, 0)
        self._token = CachedToken(access_token=access_token, expires_at=expires_at)

    def clear(self) -> None:
        """Discard the cached token, if any."""
        self._token = None
