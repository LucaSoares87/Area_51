import time

from src.auth.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("client1") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False

    def test_separate_clients(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False
        assert limiter.is_allowed("client2") is True

    def test_remaining_count(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.remaining("client1") == 5
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.remaining("client1") == 3

    def test_remaining_zero_when_exhausted(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.remaining("client1") == 0

    def test_window_expiry(self):
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False
        time.sleep(1.1)
        assert limiter.is_allowed("client1") is True

    def test_reset_client(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        assert limiter.is_allowed("client1") is False
        limiter.reset("client1")
        assert limiter.is_allowed("client1") is True

    def test_reset_all(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        assert limiter.is_allowed("client1") is False
        assert limiter.is_allowed("client2") is False
        limiter.reset_all()
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True

    def test_defaults_from_config(self):
        limiter = RateLimiter()
        assert limiter.max_requests > 0
        assert limiter.window_seconds > 0
