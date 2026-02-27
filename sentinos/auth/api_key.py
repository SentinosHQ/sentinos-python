from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass

import httpx


class _HTTPXAPIKeyAuth(httpx.Auth):
    def __init__(self, key_provider: Callable[[], str], header_name: str) -> None:
        self._key_provider = key_provider
        self._header_name = header_name

    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers[self._header_name] = self._key_provider()
        yield request


@dataclass(frozen=True)
class APIKeyAuth:
    """
    Simple API-key header auth helper.
    """

    api_key: str | Callable[[], str]
    header_name: str = "x-api-key"

    def _provider(self) -> Callable[[], str]:
        if callable(self.api_key):
            return self.api_key
        key = str(self.api_key)
        return lambda: key

    def as_httpx_auth(self) -> httpx.Auth:
        return _HTTPXAPIKeyAuth(self._provider(), header_name=self.header_name)
