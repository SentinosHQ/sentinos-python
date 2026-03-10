from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    reset_timeout_seconds: float = 30.0
    on_open: Callable[[], None] | None = None
    on_close: Callable[[], None] | None = None

    _failures: int = 0
    _open_until: float = 0.0

    def is_open(self) -> bool:
        now = time.time()
        return now < self._open_until

    def record_success(self) -> None:
        was_open = self.is_open()
        self._failures = 0
        self._open_until = 0.0
        if was_open and self.on_close:
            self.on_close()

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            if not self.is_open():
                self._open_until = time.time() + self.reset_timeout_seconds
                if self.on_open:
                    self.on_open()

    def call(self, fn: Callable[[], T]) -> T:
        if self.is_open():
            raise CircuitOpenError("circuit breaker open")
        try:
            out = fn()
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return out
