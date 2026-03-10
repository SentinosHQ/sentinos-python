from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async, require_tenant


@dataclass
class AuditClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_org(self, org_id: str | None) -> str:
        return require_tenant(self.tenant_id, org_id, field_name="org_id")

    def list_events(
        self,
        *,
        org_id: str | None = None,
        from_: str | None = None,
        to: str | None = None,
        q: str | None = None,
        category: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        resource_type: str | None = None,
        outcome: str | None = None,
        source_service: str | None = None,
        tags: str | list[str] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        params: dict[str, Any] = {
            "from": from_,
            "to": to,
            "q": q,
            "category": category,
            "action": action,
            "actor": actor,
            "resource_type": resource_type,
            "outcome": outcome,
            "source_service": source_service,
            "limit": limit,
            "cursor": cursor,
        }
        if isinstance(tags, list):
            params["tags"] = ",".join(tags)
        else:
            params["tags"] = tags
        return request_json(self._core, "GET", f"/v1/orgs/{oid}/audit/events", params=params)

    async def list_events_async(self, **kwargs: Any) -> dict[str, Any]:
        oid = self._require_org(kwargs.pop("org_id", None))
        tags = kwargs.pop("tags", None)
        params = dict(kwargs)
        if isinstance(tags, list):
            params["tags"] = ",".join(tags)
        elif tags is not None:
            params["tags"] = tags
        return await request_json_async(self._core, "GET", f"/v1/orgs/{oid}/audit/events", params=params)

    def get_event(self, event_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "GET", f"/v1/orgs/{oid}/audit/events/{event_id}")

    async def get_event_async(self, event_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "GET", f"/v1/orgs/{oid}/audit/events/{event_id}")

    def export_events(self, *, org_id: str | None = None, export: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "POST", f"/v1/orgs/{oid}/audit/events/export", body=export)

    async def export_events_async(self, *, org_id: str | None = None, export: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "POST", f"/v1/orgs/{oid}/audit/events/export", body=export)

    def list_saved_views(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = request_json(self._core, "GET", f"/v1/orgs/{oid}/audit/saved-views")
        return list(body.get("views") or body.get("saved_views") or [])

    async def list_saved_views_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await request_json_async(self._core, "GET", f"/v1/orgs/{oid}/audit/saved-views")
        return list(body.get("views") or body.get("saved_views") or [])

    def create_saved_view(self, *, org_id: str | None = None, view: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "POST", f"/v1/orgs/{oid}/audit/saved-views", body=view)

    async def create_saved_view_async(self, *, org_id: str | None = None, view: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "POST", f"/v1/orgs/{oid}/audit/saved-views", body=view)

    def update_saved_view(self, view_id: str, *, org_id: str | None = None, view: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "PATCH", f"/v1/orgs/{oid}/audit/saved-views/{view_id}", body=view)

    async def update_saved_view_async(
        self,
        view_id: str,
        *,
        org_id: str | None = None,
        view: dict[str, Any],
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "PATCH", f"/v1/orgs/{oid}/audit/saved-views/{view_id}", body=view)

    def delete_saved_view(self, view_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "DELETE", f"/v1/orgs/{oid}/audit/saved-views/{view_id}")

    async def delete_saved_view_async(self, view_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "DELETE", f"/v1/orgs/{oid}/audit/saved-views/{view_id}")

    def create_notable_rule(self, *, org_id: str | None = None, rule: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._core, "POST", f"/v1/orgs/{oid}/audit/notable-rules", body=rule)

    async def create_notable_rule_async(self, *, org_id: str | None = None, rule: dict[str, Any]) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._core, "POST", f"/v1/orgs/{oid}/audit/notable-rules", body=rule)

    def list_notable_events(
        self,
        *,
        org_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._core,
            "GET",
            f"/v1/orgs/{oid}/audit/notable-events",
            params={"limit": limit, "cursor": cursor},
        )

    async def list_notable_events_async(
        self,
        *,
        org_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._core,
            "GET",
            f"/v1/orgs/{oid}/audit/notable-events",
            params={"limit": limit, "cursor": cursor},
        )
