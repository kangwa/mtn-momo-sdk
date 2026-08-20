"""Polling helpers for the MoMo request-then-poll pattern."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from mtn_momo.constants import TransactionStatusValue
from mtn_momo.exceptions import PollTimeoutError
from mtn_momo.models.responses import TransactionStatus

_TERMINAL_STATUSES = frozenset({TransactionStatusValue.SUCCESSFUL, TransactionStatusValue.FAILED})


@dataclass(frozen=True)
class PollConfig:
    """Controls how poll_until_complete waits for a transaction to finish.

    Attributes:
        interval: Seconds to wait between polls, before backoff is applied.
        max_interval: The interval will never grow past this many seconds.
        backoff: Multiplier applied to the interval after each poll. 1.0 keeps
            it fixed; values above 1.0 grow it (exponential backoff).
        timeout: Total seconds to keep polling before giving up.
    """

    interval: float = 2.0
    max_interval: float = 10.0
    backoff: float = 1.0
    timeout: float = 60.0


DEFAULT_POLL_CONFIG = PollConfig()


def poll_until_complete_sync(
    get_status: Callable[[], TransactionStatus],
    config: PollConfig = DEFAULT_POLL_CONFIG,
    *,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> TransactionStatus:
    """Repeatedly call get_status() until it reports a terminal status.

    Args:
        get_status: Called on each poll; typically client.get_transaction_status.
        config: Poll timing configuration.
        sleep: Injectable sleep function, for testability.
        clock: Injectable monotonic clock function, for testability.

    Returns:
        The first TransactionStatus with a SUCCESSFUL or FAILED status.

    Raises:
        PollTimeoutError: If config.timeout elapses before a terminal status is seen.
    """
    deadline = clock() + config.timeout
    interval = config.interval
    status = get_status()
    while status.status not in _TERMINAL_STATUSES:
        if clock() >= deadline:
            raise PollTimeoutError("Timed out waiting for a terminal status", last_status=status)
        sleep(interval)
        interval = min(interval * config.backoff, config.max_interval)
        status = get_status()
    return status


async def poll_until_complete_async(
    get_status: Callable[[], Awaitable[TransactionStatus]],
    config: PollConfig = DEFAULT_POLL_CONFIG,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> TransactionStatus:
    """Async equivalent of poll_until_complete_sync.

    Args:
        get_status: Awaited on each poll; typically client.get_transaction_status.
        config: Poll timing configuration.
        sleep: Injectable async sleep function, for testability.
        clock: Injectable monotonic clock function, for testability.

    Returns:
        The first TransactionStatus with a SUCCESSFUL or FAILED status.

    Raises:
        PollTimeoutError: If config.timeout elapses before a terminal status is seen.
    """
    deadline = clock() + config.timeout
    interval = config.interval
    status = await get_status()
    while status.status not in _TERMINAL_STATUSES:
        if clock() >= deadline:
            raise PollTimeoutError("Timed out waiting for a terminal status", last_status=status)
        await sleep(interval)
        interval = min(interval * config.backoff, config.max_interval)
        status = await get_status()
    return status
