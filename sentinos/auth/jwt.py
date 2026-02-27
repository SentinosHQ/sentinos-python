from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass

import httpx

TokenProvider = Callable[[], str]


class _HTTPXDynamicBearerAuth(httpx.Auth):
    def __init__(
        self,
        token_provider: TokenProvider,
        header_name: str = "Authorization",
        prefix: str = "Bearer",
    ) -> None:
        self._token_provider = token_provider
        self._header_name = header_name
        self._prefix = prefix

    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        tok = self._token_provider()
        if self._prefix:
            request.headers[self._header_name] = f"{self._prefix} {tok}"
        else:
            request.headers[self._header_name] = tok
        yield request


@dataclass(frozen=True)
class JWTAuth:
    """
    JWT bearer auth helper.

    - If `token_provider` is a callable, it will be called for every request (supports refresh).
    - If `token_provider` is a string, it will be used as a constant token.
    """

    token_provider: TokenProvider | str
    header_name: str = "Authorization"
    prefix: str = "Bearer"

    def _provider(self) -> TokenProvider:
        if callable(self.token_provider):
            return self.token_provider
        tok = str(self.token_provider)
        return lambda: tok

    def as_httpx_auth(self) -> httpx.Auth:
        return _HTTPXDynamicBearerAuth(self._provider(), header_name=self.header_name, prefix=self.prefix)
