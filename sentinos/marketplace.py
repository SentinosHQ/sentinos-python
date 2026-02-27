from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from .models.marketplace import InstallResult, MarketplacePack, PackInstall


@dataclass
class MarketplaceClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _tenant_or_empty(self, tenant_id: str | None) -> str:
        return (tenant_id or self.tenant_id or "").strip()

    def _core_with_headers(self, *, tenant_id: str | None) -> Client | AuthenticatedClient:
        headers: dict[str, str] = {}
        t = self._tenant_or_empty(tenant_id)
        if t:
            headers["x-tenant-id"] = t
        return self._core.with_headers(headers) if headers else self._core

    def list_packs(
        self,
        *,
        search: str | None = None,
        tags: list[str] | None = None,
        verified_only: bool = False,
        tenant_id: str | None = None,
    ) -> list[MarketplacePack]:
        c = self._core_with_headers(tenant_id=tenant_id)
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if tags:
            params["tags"] = tags
        if verified_only:
            params["verified_only"] = "true"
        resp = c.get_httpx_client().get("/v1/marketplace/packs", params=params)
        resp.raise_for_status()
        data = resp.json()
        packs = data.get("packs") or []
        return [MarketplacePack.model_validate(p) for p in packs]

    async def list_packs_async(
        self,
        *,
        search: str | None = None,
        tags: list[str] | None = None,
        verified_only: bool = False,
        tenant_id: str | None = None,
    ) -> list[MarketplacePack]:
        c = self._core_with_headers(tenant_id=tenant_id)
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if tags:
            params["tags"] = tags
        if verified_only:
            params["verified_only"] = "true"
        resp = await c.get_async_httpx_client().get("/v1/marketplace/packs", params=params)
        resp.raise_for_status()
        data = resp.json()
        packs = data.get("packs") or []
        return [MarketplacePack.model_validate(p) for p in packs]

    def get_pack(self, *, pack_id: str, tenant_id: str | None = None) -> MarketplacePack:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = c.get_httpx_client().get(f"/v1/marketplace/packs/{pack_id}")
        resp.raise_for_status()
        return MarketplacePack.model_validate(resp.json())

    async def get_pack_async(self, *, pack_id: str, tenant_id: str | None = None) -> MarketplacePack:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = await c.get_async_httpx_client().get(f"/v1/marketplace/packs/{pack_id}")
        resp.raise_for_status()
        return MarketplacePack.model_validate(resp.json())

    def install_pack(
        self,
        *,
        pack_id: str,
        target_status: str = "staging",
        skip_simulation: bool = False,
        trace_limit: int = 100,
        tenant_id: str | None = None,
    ) -> InstallResult:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = c.get_httpx_client().post(
            f"/v1/marketplace/packs/{pack_id}/install",
            json={"target_status": target_status, "skip_simulation": skip_simulation, "trace_limit": trace_limit},
        )
        resp.raise_for_status()
        data = resp.json()
        return InstallResult.model_validate(
            {
                "install_id": data.get("install_id"),
                "simulation_job_ids": data.get("simulation_job_ids") or [],
                "raw": data,
            }
        )

    async def install_pack_async(
        self,
        *,
        pack_id: str,
        target_status: str = "staging",
        skip_simulation: bool = False,
        trace_limit: int = 100,
        tenant_id: str | None = None,
    ) -> InstallResult:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = await c.get_async_httpx_client().post(
            f"/v1/marketplace/packs/{pack_id}/install",
            json={"target_status": target_status, "skip_simulation": skip_simulation, "trace_limit": trace_limit},
        )
        resp.raise_for_status()
        data = resp.json()
        return InstallResult.model_validate(
            {
                "install_id": data.get("install_id"),
                "simulation_job_ids": data.get("simulation_job_ids") or [],
                "raw": data,
            }
        )

    def list_installs(self, *, tenant_id: str | None = None) -> list[PackInstall]:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = c.get_httpx_client().get("/v1/marketplace/installs")
        resp.raise_for_status()
        data = resp.json()
        installs = data.get("installs") or []
        return [PackInstall.model_validate(i) for i in installs]

    async def list_installs_async(self, *, tenant_id: str | None = None) -> list[PackInstall]:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = await c.get_async_httpx_client().get("/v1/marketplace/installs")
        resp.raise_for_status()
        data = resp.json()
        installs = data.get("installs") or []
        return [PackInstall.model_validate(i) for i in installs]

    def uninstall_pack(self, *, pack_id: str, tenant_id: str | None = None) -> None:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = c.get_httpx_client().delete(f"/v1/marketplace/installs/{pack_id}")
        resp.raise_for_status()

    async def uninstall_pack_async(self, *, pack_id: str, tenant_id: str | None = None) -> None:
        c = self._core_with_headers(tenant_id=tenant_id)
        resp = await c.get_async_httpx_client().delete(f"/v1/marketplace/installs/{pack_id}")
        resp.raise_for_status()
