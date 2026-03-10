from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async, require_tenant


@dataclass
class PrivacyClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _tenant(self, tenant_id: str | None) -> str:
        return require_tenant(self.tenant_id, tenant_id)

    def get_policy(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(self._core, "GET", "/v1/trace/privacy/policy", tenant_id=self._tenant(tenant_id))

    def update_policy(self, *, policy: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "PATCH", "/v1/trace/privacy/policy", tenant_id=self._tenant(tenant_id), body=policy
        )

    async def get_policy_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core, "GET", "/v1/trace/privacy/policy", tenant_id=self._tenant(tenant_id)
        )

    async def update_policy_async(self, *, policy: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "PATCH",
            "/v1/trace/privacy/policy",
            tenant_id=self._tenant(tenant_id),
            body=policy,
        )

    def scan(self, *, payload: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "POST", "/v1/trace/privacy/scan", tenant_id=self._tenant(tenant_id), body=payload
        )

    async def scan_async(self, *, payload: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core, "POST", "/v1/trace/privacy/scan", tenant_id=self._tenant(tenant_id), body=payload
        )
