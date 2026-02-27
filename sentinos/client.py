from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
from sentinos_core import AuthenticatedClient, Client

from .alerts import AlertsClient
from .arbiter import ArbiterClient
from .auth.api_key import APIKeyAuth
from .auth.jwt import JWTAuth
from .chronos import ChronosClient
from .incidents import IncidentsClient
from .kernel import KernelClient
from .marketplace import MarketplaceClient
from .traces import TracesClient
from .utils.telemetry import TelemetryConfig, httpx_event_hooks


@dataclass(frozen=True)
class SentinosClientConfig:
    base_url: str | None
    kernel_url: str
    arbiter_url: str
    chronos_url: str
    controlplane_url: str
    tenant_id: str | None = None
    timeout_seconds: float = 30.0


class SentinosClient:
    """
    High-level Sentinos SDK client.

    This wraps the auto-generated `sentinos_core` client with ergonomic sub-clients.
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        api_url: str | None = None,
        base_url: str | None = None,
        kernel_url: str | None = None,
        arbiter_url: str | None = None,
        chronos_url: str | None = None,
        controlplane_url: str | None = None,
        tenant_id: str | None = None,
        org_id: str | None = None,
        auth_token: str | None = None,
        kernel_auth_token: str | None = None,
        arbiter_auth_token: str | None = None,
        chronos_auth_token: str | None = None,
        auth: JWTAuth | APIKeyAuth | None = None,
        kernel_auth: JWTAuth | APIKeyAuth | None = None,
        arbiter_auth: JWTAuth | APIKeyAuth | None = None,
        chronos_auth: JWTAuth | APIKeyAuth | None = None,
        telemetry: TelemetryConfig | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if tenant_id is not None and org_id is not None and tenant_id != org_id:
            raise ValueError("tenant_id and org_id must match when both are provided")
        if tenant_id is None and org_id is not None:
            tenant_id = org_id

        # `url` and `api_url` are readability aliases for `base_url`.
        # precedence: base_url > api_url > url
        resolved_base_url = base_url if base_url is not None else (api_url if api_url is not None else url)
        normalized_base_url = resolved_base_url.rstrip("/") if resolved_base_url is not None else None

        def _looks_like_local_runtime_host(u: str) -> bool:
            try:
                parsed = urlparse(u)
            except Exception:
                return False
            host = (parsed.hostname or "").lower()
            port = parsed.port
            if host not in {"localhost", "127.0.0.1"}:
                return False
            return port in {8081, 8082, 8083}

        default_kernel_url = normalized_base_url or "http://localhost:8081"
        default_arbiter_url = normalized_base_url or "http://localhost:8082"
        default_chronos_url = normalized_base_url or "http://localhost:8083"
        # Controlplane is typically separate in local dev (18084). Avoid accidentally pinning it
        # to the Kernel port when users set `base_url=http://localhost:8081`.
        if normalized_base_url is not None and _looks_like_local_runtime_host(normalized_base_url):
            default_controlplane_url = "http://localhost:18084"
        else:
            default_controlplane_url = normalized_base_url or "http://localhost:18084"
        resolved_kernel_url = (kernel_url.rstrip("/") if kernel_url is not None else default_kernel_url)
        resolved_arbiter_url = (arbiter_url.rstrip("/") if arbiter_url is not None else default_arbiter_url)
        resolved_chronos_url = (chronos_url.rstrip("/") if chronos_url is not None else default_chronos_url)
        resolved_controlplane_url = (
            controlplane_url.rstrip("/") if controlplane_url is not None else default_controlplane_url
        )

        self.config = SentinosClientConfig(
            base_url=normalized_base_url,
            kernel_url=resolved_kernel_url,
            arbiter_url=resolved_arbiter_url,
            chronos_url=resolved_chronos_url,
            controlplane_url=resolved_controlplane_url,
            tenant_id=tenant_id,
            timeout_seconds=timeout_seconds,
        )

        def mk_core(
            url: str,
            token: str | None,
            a: JWTAuth | APIKeyAuth | None,
            *,
            span_prefix: str,
        ) -> Client | AuthenticatedClient:
            timeout = httpx.Timeout(timeout_seconds)
            httpx_args: dict[str, Any] = {}
            if telemetry and telemetry.enabled:
                httpx_args["event_hooks"] = httpx_event_hooks(
                    span_prefix,
                    extra_attributes={
                        "sentinos.service": span_prefix,
                        "sentinos.tenant_id": tenant_id or "",
                    },
                )
            if a is not None:
                httpx_args["auth"] = a.as_httpx_auth()
                return Client(base_url=url, timeout=timeout, httpx_args=httpx_args)
            if token:
                return AuthenticatedClient(
                    base_url=url,
                    token=token,
                    timeout=timeout,
                    httpx_args=httpx_args,
                )
            return Client(base_url=url, timeout=timeout, httpx_args=httpx_args)

        self._kernel_core = mk_core(
            resolved_kernel_url,
            kernel_auth_token or auth_token,
            kernel_auth or auth,
            span_prefix="sentinos.kernel",
        )
        self._arbiter_core = mk_core(
            resolved_arbiter_url,
            arbiter_auth_token or auth_token,
            arbiter_auth or auth,
            span_prefix="sentinos.arbiter",
        )
        self._chronos_core = mk_core(
            resolved_chronos_url,
            chronos_auth_token or auth_token,
            chronos_auth or auth,
            span_prefix="sentinos.chronos",
        )

        self.kernel = KernelClient(self._kernel_core, tenant_id=tenant_id)
        self.arbiter = ArbiterClient(self._arbiter_core, tenant_id=tenant_id)
        self.chronos = ChronosClient(self._chronos_core, tenant_id=tenant_id)
        self.traces = TracesClient(self._kernel_core, tenant_id=tenant_id)
        self.marketplace = MarketplaceClient(self._arbiter_core, tenant_id=tenant_id)
        self.alerts = AlertsClient(self._kernel_core, tenant_id=tenant_id)
        self.incidents = IncidentsClient(self._kernel_core, tenant_id=tenant_id)

    @classmethod
    def simple(
        cls,
        base_url: str,
        *,
        tenant_id: str | None = None,
        org_id: str | None = None,
        auth_token: str | None = None,
        auth: JWTAuth | APIKeyAuth | None = None,
        timeout_seconds: float = 30.0,
    ) -> SentinosClient:
        """
        Minimal constructor for the common case:
        one API URL + one auth strategy + optional tenant context.
        """
        return cls(
            base_url=base_url,
            tenant_id=tenant_id,
            org_id=org_id,
            auth_token=auth_token,
            auth=auth,
            timeout_seconds=timeout_seconds,
        )

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        tenant_id: str | None = None,
        org_id: str | None = None,
        auth_token: str | None = None,
        auth: JWTAuth | APIKeyAuth | None = None,
        timeout_seconds: float | None = None,
    ) -> SentinosClient:
        """
        Build a client from standard environment variables.

        Supported variables:
        - SENTINOS_BASE_URL (aliases: SENTINOS_API_URL, SENTINOS_URL)
        - SENTINOS_KERNEL_URL, SENTINOS_ARBITER_URL, SENTINOS_CHRONOS_URL, SENTINOS_CONTROLPLANE_URL
        - SENTINOS_TENANT_ID (alias: SENTINOS_ORG_ID)
        - SENTINOS_ACCESS_TOKEN
        - SENTINOS_TIMEOUT_SECONDS
        """
        if tenant_id is not None and org_id is not None and tenant_id != org_id:
            raise ValueError("tenant_id and org_id must match when both are provided")
        if tenant_id is None and org_id is not None:
            tenant_id = org_id

        def env_first(*names: str) -> str | None:
            for name in names:
                value = os.getenv(name)
                if value is not None and value.strip():
                    return value.strip()
            return None

        resolved_base_url = base_url or env_first("SENTINOS_BASE_URL", "SENTINOS_API_URL", "SENTINOS_URL")
        resolved_tenant_id = tenant_id or env_first("SENTINOS_TENANT_ID", "SENTINOS_ORG_ID")
        resolved_auth_token = auth_token or env_first("SENTINOS_ACCESS_TOKEN")
        timeout_raw = env_first("SENTINOS_TIMEOUT_SECONDS")
        resolved_timeout = timeout_seconds
        if resolved_timeout is None:
            if timeout_raw is None:
                resolved_timeout = 30.0
            else:
                try:
                    resolved_timeout = float(timeout_raw)
                except ValueError:
                    resolved_timeout = 30.0

        return cls(
            base_url=resolved_base_url,
            kernel_url=env_first("SENTINOS_KERNEL_URL"),
            arbiter_url=env_first("SENTINOS_ARBITER_URL"),
            chronos_url=env_first("SENTINOS_CHRONOS_URL"),
            controlplane_url=env_first("SENTINOS_CONTROLPLANE_URL"),
            tenant_id=resolved_tenant_id,
            auth_token=resolved_auth_token,
            auth=auth,
            timeout_seconds=resolved_timeout,
        )
