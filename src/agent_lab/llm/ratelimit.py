import json
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock


def _quota_day() -> str:
    """
    Gemini daily quotas reset at midnight Pacific time, so usage is
    bucketed by the Pacific calendar day.
    """

    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("America/Los_Angeles"))
    except Exception:
        now = datetime.now(timezone(timedelta(hours=-8)))

    return now.date().isoformat()


class RateLimiter:
    """
    Sliding-window requests-per-minute limiter.

    acquire() blocks until another request is allowed, so callers
    never trigger 429 errors by going too fast.
    """

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = max(1, requests_per_minute)
        self._timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()

                while (
                    self._timestamps
                    and now - self._timestamps[0] >= 60
                ):
                    self._timestamps.popleft()

                if len(self._timestamps) < self.requests_per_minute:
                    self._timestamps.append(now)
                    return

                wait = 60 - (now - self._timestamps[0]) + 0.05

            time.sleep(wait)


class UsageTracker:
    """
    Persists how many real API requests were sent per model per day.

    Cached responses are not counted because they never reach the API.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}

        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def record(self, model: str) -> None:
        with self._lock:
            data = self._read()
            day = _quota_day()

            today = data.setdefault(day, {})
            today[model] = today.get(model, 0) + 1

            # Keep the file small: only the last week matters.
            for old_day in sorted(data)[:-7]:
                del data[old_day]

            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )

    def today(self) -> dict[str, int]:
        with self._lock:
            return dict(self._read().get(_quota_day(), {}))
