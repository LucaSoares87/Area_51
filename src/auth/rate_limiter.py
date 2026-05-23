from datetime import datetime, timezone


class RateLimiter:

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[datetime]] = {}

    def is_allowed(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        if key not in self._requests:
            self._requests[key] = []
        self._requests[key] = [
            t for t in self._requests[key]
            if (now - t).total_seconds() < self.window_seconds
        ]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = datetime.now(timezone.utc)
        if key not in self._requests:
            return self.max_requests
        active = [
            t for t in self._requests[key]
            if (now - t).total_seconds() < self.window_seconds
        ]
        self._requests[key] = active
        result = self.max_requests - len(active)
        return max(result, 0)

    def reset(self, key: str) -> None:
        self._requests.pop(key, None)

    def reset_all(self) -> None:
        self._requests.clear()
