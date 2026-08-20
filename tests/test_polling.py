import pytest

from mtn_momo.constants import TransactionStatusValue
from mtn_momo.exceptions import PollTimeoutError
from mtn_momo.models.responses import TransactionStatus
from mtn_momo.polling import PollConfig, poll_until_complete_async, poll_until_complete_sync


class _FakeClock:
    def __init__(self, *, now: float = 0.0) -> None:
        self._now = now

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def _status(value: TransactionStatusValue) -> TransactionStatus:
    return TransactionStatus(status=value)


def _make_async_get_status(*values: TransactionStatusValue):
    iterator = iter(values)

    async def _get_status() -> TransactionStatus:
        return _status(next(iterator))

    return _get_status


class TestPollUntilCompleteSync:
    def test_returns_immediately_if_already_terminal(self) -> None:
        result = poll_until_complete_sync(
            lambda: _status(TransactionStatusValue.SUCCESSFUL),
            sleep=lambda _: None,
        )
        assert result.status == TransactionStatusValue.SUCCESSFUL

    def test_polls_until_terminal_status(self) -> None:
        responses = iter(
            [
                _status(TransactionStatusValue.PENDING),
                _status(TransactionStatusValue.PENDING),
                _status(TransactionStatusValue.SUCCESSFUL),
            ]
        )
        sleeps: list[float] = []
        result = poll_until_complete_sync(
            lambda: next(responses),
            PollConfig(interval=1.0, backoff=2.0, max_interval=5.0),
            sleep=sleeps.append,
        )
        assert result.status == TransactionStatusValue.SUCCESSFUL
        assert sleeps == [1.0, 2.0]

    def test_raises_poll_timeout_error_when_deadline_passes(self) -> None:
        clock = _FakeClock()

        def _advance_and_sleep(seconds: float) -> None:
            clock.advance(seconds)

        with pytest.raises(PollTimeoutError) as exc_info:
            poll_until_complete_sync(
                lambda: _status(TransactionStatusValue.PENDING),
                PollConfig(interval=10.0, timeout=15.0),
                sleep=_advance_and_sleep,
                clock=clock,
            )
        assert exc_info.value.last_status.status == TransactionStatusValue.PENDING


class TestPollUntilCompleteAsync:
    async def test_returns_immediately_if_already_terminal(self) -> None:
        get_status = _make_async_get_status(TransactionStatusValue.SUCCESSFUL)

        async def _sleep(_: float) -> None:
            return None

        result = await poll_until_complete_async(get_status, sleep=_sleep)
        assert result.status == TransactionStatusValue.SUCCESSFUL

    async def test_polls_until_terminal_status(self) -> None:
        get_status = _make_async_get_status(
            TransactionStatusValue.PENDING,
            TransactionStatusValue.PENDING,
            TransactionStatusValue.SUCCESSFUL,
        )
        sleeps: list[float] = []

        async def _sleep(seconds: float) -> None:
            sleeps.append(seconds)

        result = await poll_until_complete_async(
            get_status, PollConfig(interval=1.0, backoff=2.0, max_interval=5.0), sleep=_sleep
        )
        assert result.status == TransactionStatusValue.SUCCESSFUL
        assert sleeps == [1.0, 2.0]

    async def test_raises_poll_timeout_error_when_deadline_passes(self) -> None:
        clock = _FakeClock()

        async def _get_status() -> TransactionStatus:
            return _status(TransactionStatusValue.PENDING)

        async def _advance_and_sleep(seconds: float) -> None:
            clock.advance(seconds)

        with pytest.raises(PollTimeoutError) as exc_info:
            await poll_until_complete_async(
                _get_status,
                PollConfig(interval=10.0, timeout=15.0),
                sleep=_advance_and_sleep,
                clock=clock,
            )
        assert exc_info.value.last_status.status == TransactionStatusValue.PENDING
