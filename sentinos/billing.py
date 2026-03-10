from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async, require_tenant


@dataclass
class BillingClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _tenant(self, tenant_id: str | None) -> str:
        return require_tenant(self.tenant_id, tenant_id)

    def get_entitlements(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(self._core, "GET", "/v1/kernel/billing/entitlements", tenant_id=self._tenant(tenant_id))

    def patch_entitlements(self, *, patch: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "PATCH", "/v1/kernel/billing/entitlements", tenant_id=self._tenant(tenant_id), body=patch
        )

    async def get_entitlements_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core, "GET", "/v1/kernel/billing/entitlements", tenant_id=self._tenant(tenant_id)
        )

    async def patch_entitlements_async(self, *, patch: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "PATCH",
            "/v1/kernel/billing/entitlements",
            tenant_id=self._tenant(tenant_id),
            body=patch,
        )

    def get_usage_summary(self, *, tenant_id: str | None = None, period_at: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core,
            "GET",
            "/v1/kernel/billing/usage/summary",
            tenant_id=self._tenant(tenant_id),
            params={"period_at": period_at},
        )

    async def get_usage_summary_async(
        self, *, tenant_id: str | None = None, period_at: str | None = None
    ) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            "/v1/kernel/billing/usage/summary",
            tenant_id=self._tenant(tenant_id),
            params={"period_at": period_at},
        )

    def list_usage_events(
        self,
        *,
        tenant_id: str | None = None,
        metric_key: str | None = None,
        result: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return request_json(
            self._core,
            "GET",
            "/v1/kernel/billing/usage/events",
            tenant_id=self._tenant(tenant_id),
            params={"metric_key": metric_key, "result": result, "limit": limit},
        )

    async def list_usage_events_async(
        self,
        *,
        tenant_id: str | None = None,
        metric_key: str | None = None,
        result: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            "/v1/kernel/billing/usage/events",
            tenant_id=self._tenant(tenant_id),
            params={"metric_key": metric_key, "result": result, "limit": limit},
        )
