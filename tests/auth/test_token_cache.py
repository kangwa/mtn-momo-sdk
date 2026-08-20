from mtn_momo.auth.token_cache import CachedToken, TokenCache


class _FakeClock:
    def __init__(self, *, now: float) -> None:
        self._now = now

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class TestTokenCache:
    def test_get_valid_returns_none_when_empty(self) -> None:
        cache = TokenCache()
        assert cache.get_valid() is None

    def test_store_then_get_valid_returns_token(self) -> None:
        cache = TokenCache(clock=_FakeClock(now=0.0))
        cache.store("abc123", expires_in=3600)
        assert cache.get_valid() == "abc123"

    def test_token_expires_after_ttl_minus_leeway(self) -> None:
        clock = _FakeClock(now=0.0)
        cache = TokenCache(leeway=30.0, clock=clock)
        cache.store("abc123", expires_in=3600)

        clock.advance(3600 - 30)
        assert cache.get_valid() is None

    def test_token_still_valid_just_before_leeway_adjusted_expiry(self) -> None:
        clock = _FakeClock(now=0.0)
        cache = TokenCache(leeway=30.0, clock=clock)
        cache.store("abc123", expires_in=3600)

        clock.advance(3600 - 31)
        assert cache.get_valid() == "abc123"

    def test_clear_removes_cached_token(self) -> None:
        cache = TokenCache(clock=_FakeClock(now=0.0))
        cache.store("abc123", expires_in=3600)
        cache.clear()
        assert cache.get_valid() is None


class TestCachedToken:
    def test_holds_expected_fields(self) -> None:
        token = CachedToken(access_token="abc", expires_at=123.0)
        assert token.access_token == "abc"
        assert token.expires_at == 123.0
