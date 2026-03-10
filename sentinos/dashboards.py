from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async, require_tenant

DashboardQueryService = str


@dataclass
class DashboardsClient:
    _metadata_core: Client | AuthenticatedClient
    _query_cores: Mapping[str, Client | AuthenticatedClient]
    tenant_id: str | None = None

    def _require_org(self, org_id: str | None) -> str:
        return require_tenant(self.tenant_id, org_id, field_name="org_id")

    def _query_core(self, source_service: DashboardQueryService) -> Client | AuthenticatedClient:
        key = str(source_service).strip().lower()
        if key not in self._query_cores:
            raise ValueError(f"unsupported source_service: {source_service}")
        return self._query_cores[key]

    def list(
        self,
        *,
        org_id: str | None = None,
        q: str | None = None,
        tags: str | None = None,
        include_deleted: bool | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core,
            "GET",
            f"/v1/orgs/{oid}/dashboards",
            params={"q": q, "tags": tags, "include_deleted": include_deleted, "limit": limit},
        )

    async def list_async(
        self,
        *,
        org_id: str | None = None,
        q: str | None = None,
        tags: str | None = None,
        include_deleted: bool | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "GET",
            f"/v1/orgs/{oid}/dashboards",
            params={"q": q, "tags": tags, "include_deleted": include_deleted, "limit": limit},
        )

    def create(self, *, dashboard: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards", body=dashboard)

    async def create_async(self, *, dashboard: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards", body=dashboard)

    def get(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}")

    async def get_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}")

    def update(self, dashboard_id: str, *, dashboard: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "PATCH", f"/v1/orgs/{oid}/dashboards/{dashboard_id}", body=dashboard)

    async def update_async(
        self, dashboard_id: str, *, dashboard: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "PATCH",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}",
            body=dashboard,
        )

    def delete(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "DELETE", f"/v1/orgs/{oid}/dashboards/{dashboard_id}")

    async def delete_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._metadata_core, "DELETE", f"/v1/orgs/{oid}/dashboards/{dashboard_id}")

    def clone(
        self, dashboard_id: str, *, org_id: str | None = None, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/clone", body=body or {}
        )

    async def clone_async(
        self,
        dashboard_id: str,
        *,
        org_id: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "POST",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/clone",
            body=body or {},
        )

    def list_versions(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/versions")

    async def list_versions_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/versions"
        )

    def restore_version(self, dashboard_id: str, version: str | int, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/restore/{version}", body={}
        )

    async def restore_version_async(
        self, dashboard_id: str, version: str | int, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "POST",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/restore/{version}",
            body={},
        )

    def list_saved_views(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views")

    async def list_saved_views_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views"
        )

    def create_saved_view(
        self, dashboard_id: str, *, view: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views", body=view
        )

    async def create_saved_view_async(
        self,
        dashboard_id: str,
        *,
        view: dict[str, Any],
        org_id: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "POST",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views",
            body=view,
        )

    def delete_saved_view(self, dashboard_id: str, view_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core, "DELETE", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views/{view_id}"
        )

    async def delete_saved_view_async(
        self,
        dashboard_id: str,
        view_id: str,
        *,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "DELETE",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/saved-views/{view_id}",
        )

    def list_permissions(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/permissions")

    async def list_permissions_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/permissions"
        )

    def update_permissions(
        self, dashboard_id: str, *, permissions: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core, "PUT", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/permissions", body=permissions
        )

    async def update_permissions_async(
        self,
        dashboard_id: str,
        *,
        permissions: dict[str, Any],
        org_id: str | None = None,
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "PUT",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/permissions",
            body=permissions,
        )

    def set_favorite(self, dashboard_id: str, *, favorite: bool, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(
            self._metadata_core,
            "POST",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/favorite",
            body={"favorite": favorite},
        )

    async def set_favorite_async(
        self, dashboard_id: str, *, favorite: bool, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(
            self._metadata_core,
            "POST",
            f"/v1/orgs/{oid}/dashboards/{dashboard_id}/favorite",
            body={"favorite": favorite},
        )

    def import_definition(self, *, payload: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards/import", body=payload)

    async def import_definition_async(self, *, payload: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._metadata_core, "POST", f"/v1/orgs/{oid}/dashboards/import", body=payload)

    def export_definition(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return request_json(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/export")

    async def export_definition_async(self, dashboard_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await request_json_async(self._metadata_core, "GET", f"/v1/orgs/{oid}/dashboards/{dashboard_id}/export")

    def query(self, *, source_service: DashboardQueryService = "controlplane", body: dict[str, Any]) -> dict[str, Any]:
        return request_json(self._query_core(source_service), "POST", "/v1/dashboard/query", body=body)

    async def query_async(
        self, *, source_service: DashboardQueryService = "controlplane", body: dict[str, Any]
    ) -> dict[str, Any]:
        return await request_json_async(self._query_core(source_service), "POST", "/v1/dashboard/query", body=body)
