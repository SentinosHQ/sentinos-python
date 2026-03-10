from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async


@dataclass
class A2AClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def authorize_handoff(self, *, handoff: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "POST", "/v1/a2a/handoffs/authorize", tenant_id=tenant_id or self.tenant_id, body=handoff
        )

    async def authorize_handoff_async(self, *, handoff: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "POST",
            "/v1/a2a/handoffs/authorize",
            tenant_id=tenant_id or self.tenant_id,
            body=handoff,
        )

    def forward_handoff(self, *, handoff: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "POST", "/v1/a2a/handoffs/forward", tenant_id=tenant_id or self.tenant_id, body=handoff
        )

    async def forward_handoff_async(self, *, handoff: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "POST",
            "/v1/a2a/handoffs/forward",
            tenant_id=tenant_id or self.tenant_id,
            body=handoff,
        )

    def get_receipt(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "GET", f"/v1/a2a/handoffs/{handoff_id}/receipt", tenant_id=tenant_id or self.tenant_id
        )

    async def get_receipt_async(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            f"/v1/a2a/handoffs/{handoff_id}/receipt",
            tenant_id=tenant_id or self.tenant_id,
        )

    def get_lineage(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "GET", f"/v1/a2a/handoffs/{handoff_id}/lineage", tenant_id=tenant_id or self.tenant_id
        )

    async def get_lineage_async(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            f"/v1/a2a/handoffs/{handoff_id}/lineage",
            tenant_id=tenant_id or self.tenant_id,
        )

    def verify_receipt(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return request_json(
            self._core, "GET", f"/v1/a2a/handoffs/{handoff_id}/verify", tenant_id=tenant_id or self.tenant_id
        )

    async def verify_receipt_async(self, handoff_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            f"/v1/a2a/handoffs/{handoff_id}/verify",
            tenant_id=tenant_id or self.tenant_id,
        )

    def list_trust_scores(
        self, *, agents: list[str] | None = None, limit: int | None = None, tenant_id: str | None = None
    ) -> dict[str, Any]:
        return request_json(
            self._core,
            "GET",
            "/v1/a2a/trust-scores",
            tenant_id=tenant_id or self.tenant_id,
            params={"agents": ",".join(agents) if agents else None, "limit": limit},
        )

    async def list_trust_scores_async(
        self, *, agents: list[str] | None = None, limit: int | None = None, tenant_id: str | None = None
    ) -> dict[str, Any]:
        return await request_json_async(
            self._core,
            "GET",
            "/v1/a2a/trust-scores",
            tenant_id=tenant_id or self.tenant_id,
            params={"agents": ",".join(agents) if agents else None, "limit": limit},
        )
