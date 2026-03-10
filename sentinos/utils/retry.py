from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 0.1
    max_delay_seconds: float = 5.0
    exponential_base: float = 2.0
    jitter: bool = True

    def _sleep(self, attempt: int) -> None:
        d = self.base_delay_seconds * (self.exponential_base**attempt)
        if self.jitter:
            d += random.random() * self.base_delay_seconds
        d = min(d, self.max_delay_seconds)
        time.sleep(d)

    def run(self, fn: Callable[[], T], *, should_retry: Callable[[Exception], bool] | None = None) -> T:
        last: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except Exception as e:
                last = e
                if attempt >= self.max_retries:
                    raise
                if should_retry is not None and not should_retry(e):
                    raise
                self._sleep(attempt)
        assert last is not None
        raise last
