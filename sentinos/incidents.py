from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from .models.incident import Incident, IncidentTimelineEvent


@dataclass
class IncidentsClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_tenant(self, tenant_id: str | None) -> str:
        t = (tenant_id or self.tenant_id or "").strip()
        if not t:
            raise ValueError("tenant_id is required (set it on SentinosClient or pass it per call)")
        return t

    def _core_with_headers(self, *, tenant_id: str) -> Client | AuthenticatedClient:
        return self._core.with_headers({"x-tenant-id": tenant_id})

    def list_incidents(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Incident]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if source:
            params["source"] = source
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/incidents", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("incidents") or []
        return [Incident.model_validate(x) for x in rows]

    async def list_incidents_async(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Incident]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if source:
            params["source"] = source
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/incidents", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("incidents") or []
        return [Incident.model_validate(x) for x in rows]

    def create_incident(self, *, incident: dict[str, Any], tenant_id: str | None = None) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post("/v1/incidents", json=incident)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())

    async def create_incident_async(self, *, incident: dict[str, Any], tenant_id: str | None = None) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post("/v1/incidents", json=incident)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())

    def get_incident(
        self,
        incident_id: str,
        *,
        tenant_id: str | None = None,
    ) -> tuple[Incident, list[IncidentTimelineEvent]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/incidents/{incident_id}")
        resp.raise_for_status()
        data = resp.json() or {}
        incident = Incident.model_validate(data.get("incident") or data)
        timeline = [IncidentTimelineEvent.model_validate(x) for x in (data.get("timeline") or [])]
        return incident, timeline

    async def get_incident_async(
        self,
        incident_id: str,
        *,
        tenant_id: str | None = None,
    ) -> tuple[Incident, list[IncidentTimelineEvent]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/incidents/{incident_id}")
        resp.raise_for_status()
        data = resp.json() or {}
        incident = Incident.model_validate(data.get("incident") or data)
        timeline = [IncidentTimelineEvent.model_validate(x) for x in (data.get("timeline") or [])]
        return incident, timeline

    def update_incident(self, incident_id: str, *, patch: dict[str, Any], tenant_id: str | None = None) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().put(f"/v1/incidents/{incident_id}", json=patch)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())

    async def update_incident_async(
        self,
        incident_id: str,
        *,
        patch: dict[str, Any],
        tenant_id: str | None = None,
    ) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().put(f"/v1/incidents/{incident_id}", json=patch)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())

    def resolve_incident(self, incident_id: str, *, note: str | None = None, tenant_id: str | None = None) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = c.get_httpx_client().post(f"/v1/incidents/{incident_id}/resolve", json=body)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())

    async def resolve_incident_async(
        self,
        incident_id: str,
        *,
        note: str | None = None,
        tenant_id: str | None = None,
    ) -> Incident:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = await c.get_async_httpx_client().post(f"/v1/incidents/{incident_id}/resolve", json=body)
        resp.raise_for_status()
        return Incident.model_validate(resp.json())
