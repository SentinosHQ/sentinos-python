from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from ._http import request_json, request_json_async, require_tenant


def _items(body: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        value = body.get(key)
        if isinstance(value, list):
            return list(value)
    return []


@dataclass
class ControlplaneClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_org(self, org_id: str | None) -> str:
        return require_tenant(self.tenant_id, org_id, field_name="org_id")

    def _request(
        self,
        method: str,
        path: str,
        *,
        org_id: str | None = None,
        tenant_required: bool = False,
        params: dict[str, Any] | None = None,
        body: Any = None,
    ) -> dict[str, Any]:
        tenant_id = self._require_org(org_id) if tenant_required else (org_id or self.tenant_id)
        return request_json(self._core, method, path, tenant_id=tenant_id, params=params, body=body)

    async def _request_async(
        self,
        method: str,
        path: str,
        *,
        org_id: str | None = None,
        tenant_required: bool = False,
        params: dict[str, Any] | None = None,
        body: Any = None,
    ) -> dict[str, Any]:
        tenant_id = self._require_org(org_id) if tenant_required else (org_id or self.tenant_id)
        return await request_json_async(self._core, method, path, tenant_id=tenant_id, params=params, body=body)

    def list_organizations(self) -> list[dict[str, Any]]:
        body = self._request("GET", "/v1/orgs")
        return _items(body, "organizations", "orgs")

    async def list_organizations_async(self) -> list[dict[str, Any]]:
        body = await self._request_async("GET", "/v1/orgs")
        return _items(body, "organizations", "orgs")

    def create_organization(self, *, organization: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/orgs", body=organization)

    async def create_organization_async(self, *, organization: dict[str, Any]) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/orgs", body=organization)

    def get_organization(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}", org_id=oid, tenant_required=True)

    async def get_organization_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async("GET", f"/v1/orgs/{oid}", org_id=oid, tenant_required=True)

    def patch_organization(self, *, organization: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("PATCH", f"/v1/orgs/{oid}", org_id=oid, tenant_required=True, body=organization)

    async def patch_organization_async(
        self, *, organization: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}",
            org_id=oid,
            tenant_required=True,
            body=organization,
        )

    def switch_context_token(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/switch-context-token", org_id=oid, tenant_required=True)

    async def switch_context_token_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/switch-context-token",
            org_id=oid,
            tenant_required=True,
        )

    def register(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/register", body=payload)

    async def register_async(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/auth/register", body=payload)

    def login_password(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/login/password", body=payload)

    async def login_password_async(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/auth/login/password", body=payload)

    def refresh_token(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/token/refresh", body=payload)

    async def refresh_token_async(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/auth/token/refresh", body=payload)

    def auth_me(self) -> dict[str, Any]:
        return self._request("GET", "/v1/auth/me")

    async def auth_me_async(self) -> dict[str, Any]:
        return await self._request_async("GET", "/v1/auth/me")

    def logout(self, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/logout", body=payload)

    async def logout_async(self, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/auth/logout", body=payload)

    def list_sessions(self) -> list[dict[str, Any]]:
        body = self._request("GET", "/v1/auth/sessions")
        return _items(body, "sessions", "items")

    async def list_sessions_async(self) -> list[dict[str, Any]]:
        body = await self._request_async("GET", "/v1/auth/sessions")
        return _items(body, "sessions", "items")

    def revoke_other_sessions(self) -> dict[str, Any]:
        return self._request("POST", "/v1/auth/sessions/revoke-others")

    async def revoke_other_sessions_async(self) -> dict[str, Any]:
        return await self._request_async("POST", "/v1/auth/sessions/revoke-others")

    def delete_session(self, session_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/auth/sessions/{session_id}")

    async def delete_session_async(self, session_id: str) -> dict[str, Any]:
        return await self._request_async("DELETE", f"/v1/auth/sessions/{session_id}")

    def list_members(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/members", org_id=oid, tenant_required=True)
        return _items(body, "members", "items")

    async def list_members_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/members", org_id=oid, tenant_required=True)
        return _items(body, "members", "items")

    def patch_member(
        self, membership_id: str, *, membership: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
            body=membership,
        )

    async def patch_member_async(
        self, membership_id: str, *, membership: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
            body=membership,
        )

    def remove_member(self, membership_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("DELETE", f"/v1/orgs/{oid}/members/{membership_id}", org_id=oid, tenant_required=True)

    async def remove_member_async(self, membership_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    def list_invites(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/invites", org_id=oid, tenant_required=True)
        return _items(body, "invites", "invitations", "items")

    async def list_invites_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/invites", org_id=oid, tenant_required=True)
        return _items(body, "invites", "invitations", "items")

    def create_invite(self, *, invite: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/invites", org_id=oid, tenant_required=True, body=invite)

    async def create_invite_async(self, *, invite: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/invites",
            org_id=oid,
            tenant_required=True,
            body=invite,
        )

    def get_invite(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/invites/{invitation_id}", org_id=oid, tenant_required=True)

    async def get_invite_async(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/invites/{invitation_id}",
            org_id=oid,
            tenant_required=True,
        )

    def resend_invite(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/invites/{invitation_id}/resend",
            org_id=oid,
            tenant_required=True,
        )

    async def resend_invite_async(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/invites/{invitation_id}/resend",
            org_id=oid,
            tenant_required=True,
        )

    def cancel_invite(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/invites/{invitation_id}/cancel",
            org_id=oid,
            tenant_required=True,
        )

    async def cancel_invite_async(self, invitation_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/invites/{invitation_id}/cancel",
            org_id=oid,
            tenant_required=True,
        )

    def list_permissions(self) -> list[dict[str, Any]]:
        body = self._request("GET", "/v1/permissions")
        return _items(body, "permissions", "items")

    async def list_permissions_async(self) -> list[dict[str, Any]]:
        body = await self._request_async("GET", "/v1/permissions")
        return _items(body, "permissions", "items")

    def list_roles(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/roles", org_id=oid, tenant_required=True)
        return _items(body, "roles", "items")

    async def list_roles_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/roles", org_id=oid, tenant_required=True)
        return _items(body, "roles", "items")

    def create_role(self, *, role: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/roles", org_id=oid, tenant_required=True, body=role)

    async def create_role_async(self, *, role: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/roles",
            org_id=oid,
            tenant_required=True,
            body=role,
        )

    def patch_role(self, role_id: str, *, role: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/roles/{role_id}",
            org_id=oid,
            tenant_required=True,
            body=role,
        )

    async def patch_role_async(
        self, role_id: str, *, role: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/roles/{role_id}",
            org_id=oid,
            tenant_required=True,
            body=role,
        )

    def delete_role(self, role_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("DELETE", f"/v1/orgs/{oid}/roles/{role_id}", org_id=oid, tenant_required=True)

    async def delete_role_async(self, role_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/roles/{role_id}",
            org_id=oid,
            tenant_required=True,
        )

    def get_role_permissions(self, role_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "GET",
            f"/v1/orgs/{oid}/roles/{role_id}/permissions",
            org_id=oid,
            tenant_required=True,
        )

    async def get_role_permissions_async(self, role_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/roles/{role_id}/permissions",
            org_id=oid,
            tenant_required=True,
        )

    def put_role_permissions(
        self, role_id: str, *, permissions: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PUT",
            f"/v1/orgs/{oid}/roles/{role_id}/permissions",
            org_id=oid,
            tenant_required=True,
            body=permissions,
        )

    async def put_role_permissions_async(
        self, role_id: str, *, permissions: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PUT",
            f"/v1/orgs/{oid}/roles/{role_id}/permissions",
            org_id=oid,
            tenant_required=True,
            body=permissions,
        )

    def assign_role_to_member(
        self, role_id: str, membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/roles/{role_id}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def assign_role_to_member_async(
        self, role_id: str, membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/roles/{role_id}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    def unassign_role_from_member(
        self, role_id: str, membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/roles/{role_id}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def unassign_role_from_member_async(
        self, role_id: str, membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/roles/{role_id}/members/{membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    def list_teams(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/teams", org_id=oid, tenant_required=True)
        return _items(body, "teams", "items")

    async def list_teams_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/teams", org_id=oid, tenant_required=True)
        return _items(body, "teams", "items")

    def create_team(self, *, team: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/teams", org_id=oid, tenant_required=True, body=team)

    async def create_team_async(self, *, team: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/teams",
            org_id=oid,
            tenant_required=True,
            body=team,
        )

    def patch_team(self, team_id: str, *, team: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/teams/{team_id}",
            org_id=oid,
            tenant_required=True,
            body=team,
        )

    async def patch_team_async(
        self, team_id: str, *, team: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/teams/{team_id}",
            org_id=oid,
            tenant_required=True,
            body=team,
        )

    def delete_team(self, team_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("DELETE", f"/v1/orgs/{oid}/teams/{team_id}", org_id=oid, tenant_required=True)

    async def delete_team_async(self, team_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/teams/{team_id}",
            org_id=oid,
            tenant_required=True,
        )

    def list_team_memberships(self, team_id: str, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request(
            "GET",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships",
            org_id=oid,
            tenant_required=True,
        )
        return _items(body, "memberships", "items")

    async def list_team_memberships_async(self, team_id: str, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships",
            org_id=oid,
            tenant_required=True,
        )
        return _items(body, "memberships", "items")

    def create_team_membership(
        self, team_id: str, *, membership: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships",
            org_id=oid,
            tenant_required=True,
            body=membership,
        )

    async def create_team_membership_async(
        self, team_id: str, *, membership: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships",
            org_id=oid,
            tenant_required=True,
            body=membership,
        )

    def delete_team_membership(
        self, team_id: str, team_membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships/{team_membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def delete_team_membership_async(
        self, team_id: str, team_membership_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/teams/{team_id}/memberships/{team_membership_id}",
            org_id=oid,
            tenant_required=True,
        )

    def get_team_settings(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/teams/settings", org_id=oid, tenant_required=True)

    async def get_team_settings_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async("GET", f"/v1/orgs/{oid}/teams/settings", org_id=oid, tenant_required=True)

    def patch_team_settings(self, *, settings: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/teams/settings",
            org_id=oid,
            tenant_required=True,
            body=settings,
        )

    async def patch_team_settings_async(
        self, *, settings: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/teams/settings",
            org_id=oid,
            tenant_required=True,
            body=settings,
        )

    def list_service_accounts(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/service-accounts", org_id=oid, tenant_required=True)
        return _items(body, "service_accounts", "accounts", "items")

    async def list_service_accounts_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/service-accounts", org_id=oid, tenant_required=True)
        return _items(body, "service_accounts", "accounts", "items")

    def create_service_account(self, *, account: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/service-accounts",
            org_id=oid,
            tenant_required=True,
            body=account,
        )

    async def create_service_account_async(
        self, *, account: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/service-accounts",
            org_id=oid,
            tenant_required=True,
            body=account,
        )

    def patch_service_account(
        self, service_account_id: str, *, account: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}",
            org_id=oid,
            tenant_required=True,
            body=account,
        )

    async def patch_service_account_async(
        self, service_account_id: str, *, account: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}",
            org_id=oid,
            tenant_required=True,
            body=account,
        )

    def create_service_account_token(
        self, service_account_id: str, *, token: dict[str, Any] | None = None, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}/tokens",
            org_id=oid,
            tenant_required=True,
            body=token,
        )

    async def create_service_account_token_async(
        self, service_account_id: str, *, token: dict[str, Any] | None = None, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}/tokens",
            org_id=oid,
            tenant_required=True,
            body=token,
        )

    def revoke_service_account_token(
        self, service_account_id: str, token_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}/tokens/{token_id}/revoke",
            org_id=oid,
            tenant_required=True,
        )

    async def revoke_service_account_token_async(
        self, service_account_id: str, token_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/service-accounts/{service_account_id}/tokens/{token_id}/revoke",
            org_id=oid,
            tenant_required=True,
        )

    def get_login_methods(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/settings/login-methods", org_id=oid, tenant_required=True)

    async def get_login_methods_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/settings/login-methods",
            org_id=oid,
            tenant_required=True,
        )

    def patch_login_methods(self, *, settings: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/settings/login-methods",
            org_id=oid,
            tenant_required=True,
            body=settings,
        )

    async def patch_login_methods_async(
        self, *, settings: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/settings/login-methods",
            org_id=oid,
            tenant_required=True,
            body=settings,
        )

    def get_user_login_method_override(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "GET",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
        )

    async def get_user_login_method_override_async(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
        )

    def patch_user_login_method_override(
        self, user_id: str, *, override: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
            body=override,
        )

    async def patch_user_login_method_override_async(
        self, user_id: str, *, override: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
            body=override,
        )

    def delete_user_login_method_override(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
        )

    async def delete_user_login_method_override_async(
        self, user_id: str, *, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/users/{user_id}/login-method-override",
            org_id=oid,
            tenant_required=True,
        )

    def get_saml_config(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/saml/config", org_id=oid, tenant_required=True)

    async def get_saml_config_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async("GET", f"/v1/orgs/{oid}/saml/config", org_id=oid, tenant_required=True)

    def patch_saml_config(self, *, config: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("PATCH", f"/v1/orgs/{oid}/saml/config", org_id=oid, tenant_required=True, body=config)

    async def patch_saml_config_async(self, *, config: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/saml/config",
            org_id=oid,
            tenant_required=True,
            body=config,
        )

    def get_saml_metadata(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/saml/metadata", org_id=oid, tenant_required=True)

    async def get_saml_metadata_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async("GET", f"/v1/orgs/{oid}/saml/metadata", org_id=oid, tenant_required=True)

    def post_saml_acs(self, *, payload: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/saml/acs", org_id=oid, tenant_required=True, body=payload)

    async def post_saml_acs_async(self, *, payload: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/saml/acs",
            org_id=oid,
            tenant_required=True,
            body=payload,
        )

    def list_authn_mappings(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/authn-mappings", org_id=oid, tenant_required=True)
        return _items(body, "mappings", "items")

    async def list_authn_mappings_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async("GET", f"/v1/orgs/{oid}/authn-mappings", org_id=oid, tenant_required=True)
        return _items(body, "mappings", "items")

    def create_authn_mapping(self, *, mapping: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/authn-mappings",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    async def create_authn_mapping_async(
        self, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/authn-mappings",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    def patch_authn_mapping(
        self, mapping_id: str, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/authn-mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    async def patch_authn_mapping_async(
        self, mapping_id: str, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/authn-mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    def delete_authn_mapping(self, mapping_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/authn-mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def delete_authn_mapping_async(self, mapping_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/authn-mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
        )

    def get_scim_config(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/scim/config", org_id=oid, tenant_required=True)

    async def get_scim_config_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async("GET", f"/v1/orgs/{oid}/scim/config", org_id=oid, tenant_required=True)

    def create_scim_token(self, *, token: dict[str, Any] | None = None, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("POST", f"/v1/orgs/{oid}/scim/tokens", org_id=oid, tenant_required=True, body=token)

    async def create_scim_token_async(
        self, *, token: dict[str, Any] | None = None, org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/scim/tokens",
            org_id=oid,
            tenant_required=True,
            body=token,
        )

    def delete_scim_token(self, token_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/scim/tokens/{token_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def delete_scim_token_async(self, token_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/scim/tokens/{token_id}",
            org_id=oid,
            tenant_required=True,
        )

    def scim_list_users(
        self,
        *,
        start_index: int | None = None,
        count: int | None = None,
        filter: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"startIndex": start_index, "count": count, "filter": filter}
        return self._request("GET", "/scim/v2/Users", org_id=org_id, params=params)

    async def scim_list_users_async(
        self,
        *,
        start_index: int | None = None,
        count: int | None = None,
        filter: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"startIndex": start_index, "count": count, "filter": filter}
        return await self._request_async("GET", "/scim/v2/Users", org_id=org_id, params=params)

    def scim_create_user(self, *, user: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        return self._request("POST", "/scim/v2/Users", org_id=org_id, body=user)

    async def scim_create_user_async(self, *, user: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        return await self._request_async("POST", "/scim/v2/Users", org_id=org_id, body=user)

    def scim_get_user(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return self._request("GET", f"/scim/v2/Users/{user_id}", org_id=org_id)

    async def scim_get_user_async(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return await self._request_async("GET", f"/scim/v2/Users/{user_id}", org_id=org_id)

    def scim_patch_user(self, user_id: str, *, patch: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        return self._request("PATCH", f"/scim/v2/Users/{user_id}", org_id=org_id, body=patch)

    async def scim_patch_user_async(
        self, user_id: str, *, patch: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        return await self._request_async("PATCH", f"/scim/v2/Users/{user_id}", org_id=org_id, body=patch)

    def scim_delete_user(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return self._request("DELETE", f"/scim/v2/Users/{user_id}", org_id=org_id)

    async def scim_delete_user_async(self, user_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return await self._request_async("DELETE", f"/scim/v2/Users/{user_id}", org_id=org_id)

    def scim_list_groups(
        self,
        *,
        start_index: int | None = None,
        count: int | None = None,
        filter: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"startIndex": start_index, "count": count, "filter": filter}
        return self._request("GET", "/scim/v2/Groups", org_id=org_id, params=params)

    async def scim_list_groups_async(
        self,
        *,
        start_index: int | None = None,
        count: int | None = None,
        filter: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"startIndex": start_index, "count": count, "filter": filter}
        return await self._request_async("GET", "/scim/v2/Groups", org_id=org_id, params=params)

    def scim_create_group(self, *, group: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        return self._request("POST", "/scim/v2/Groups", org_id=org_id, body=group)

    async def scim_create_group_async(self, *, group: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        return await self._request_async("POST", "/scim/v2/Groups", org_id=org_id, body=group)

    def scim_patch_group(
        self, group_id: str, *, patch: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        return self._request("PATCH", f"/scim/v2/Groups/{group_id}", org_id=org_id, body=patch)

    async def scim_patch_group_async(
        self, group_id: str, *, patch: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        return await self._request_async("PATCH", f"/scim/v2/Groups/{group_id}", org_id=org_id, body=patch)

    def scim_delete_group(self, group_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return self._request("DELETE", f"/scim/v2/Groups/{group_id}", org_id=org_id)

    async def scim_delete_group_async(self, group_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        return await self._request_async("DELETE", f"/scim/v2/Groups/{group_id}", org_id=org_id)

    def get_workforce_policy(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/workforce/policy", org_id=oid, tenant_required=True)

    async def get_workforce_policy_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/policy",
            org_id=oid,
            tenant_required=True,
        )

    def update_workforce_policy(self, *, policy: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/policy",
            org_id=oid,
            tenant_required=True,
            body=policy,
        )

    async def update_workforce_policy_async(
        self, *, policy: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/policy",
            org_id=oid,
            tenant_required=True,
            body=policy,
        )

    def list_workforce_mappings(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request("GET", f"/v1/orgs/{oid}/workforce/mappings", org_id=oid, tenant_required=True)
        return _items(body, "mappings", "items")

    async def list_workforce_mappings_async(self, *, org_id: str | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/mappings",
            org_id=oid,
            tenant_required=True,
        )
        return _items(body, "mappings", "items")

    def create_workforce_mapping(self, *, mapping: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/workforce/mappings",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    async def create_workforce_mapping_async(
        self, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/workforce/mappings",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    def update_workforce_mapping(
        self, mapping_id: str, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    async def update_workforce_mapping_async(
        self, mapping_id: str, *, mapping: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
            body=mapping,
        )

    def delete_workforce_mapping(self, mapping_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "DELETE",
            f"/v1/orgs/{oid}/workforce/mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
        )

    async def delete_workforce_mapping_async(self, mapping_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "DELETE",
            f"/v1/orgs/{oid}/workforce/mappings/{mapping_id}",
            org_id=oid,
            tenant_required=True,
        )

    def list_workforce_subjects(self, *, org_id: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request(
            "GET",
            f"/v1/orgs/{oid}/workforce/subjects",
            org_id=oid,
            tenant_required=True,
            params={"limit": limit},
        )
        return _items(body, "subjects", "items")

    async def list_workforce_subjects_async(
        self, *, org_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/subjects",
            org_id=oid,
            tenant_required=True,
            params={"limit": limit},
        )
        return _items(body, "subjects", "items")

    def list_workforce_sessions(self, *, org_id: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request(
            "GET",
            f"/v1/orgs/{oid}/workforce/sessions",
            org_id=oid,
            tenant_required=True,
            params={"limit": limit},
        )
        return _items(body, "sessions", "items")

    async def list_workforce_sessions_async(
        self, *, org_id: str | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/sessions",
            org_id=oid,
            tenant_required=True,
            params={"limit": limit},
        )
        return _items(body, "sessions", "items")

    def revoke_workforce_session(self, session_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/workforce/sessions/{session_id}/revoke",
            org_id=oid,
            tenant_required=True,
        )

    async def revoke_workforce_session_async(self, session_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/workforce/sessions/{session_id}/revoke",
            org_id=oid,
            tenant_required=True,
        )

    def list_workforce_audit(
        self,
        *,
        org_id: str | None = None,
        actor: str | None = None,
        action: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = self._request(
            "GET",
            f"/v1/orgs/{oid}/workforce/audit",
            org_id=oid,
            tenant_required=True,
            params={"actor": actor, "action": action, "limit": limit, "cursor": cursor},
        )
        return _items(body, "events", "audit", "items")

    async def list_workforce_audit_async(
        self,
        *,
        org_id: str | None = None,
        actor: str | None = None,
        action: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        oid = self._require_org(org_id)
        body = await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/audit",
            org_id=oid,
            tenant_required=True,
            params={"actor": actor, "action": action, "limit": limit, "cursor": cursor},
        )
        return _items(body, "events", "audit", "items")

    def create_workforce_rollout_wave(self, *, wave: dict[str, Any], org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/workforce/rollout/waves",
            org_id=oid,
            tenant_required=True,
            body=wave,
        )

    async def create_workforce_rollout_wave_async(
        self, *, wave: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/workforce/rollout/waves",
            org_id=oid,
            tenant_required=True,
            body=wave,
        )

    def update_workforce_rollout_wave(
        self, wave_id: str, *, wave: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/rollout/waves/{wave_id}",
            org_id=oid,
            tenant_required=True,
            body=wave,
        )

    async def update_workforce_rollout_wave_async(
        self, wave_id: str, *, wave: dict[str, Any], org_id: str | None = None
    ) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "PATCH",
            f"/v1/orgs/{oid}/workforce/rollout/waves/{wave_id}",
            org_id=oid,
            tenant_required=True,
            body=wave,
        )

    def rollback_workforce_rollout_wave(self, wave_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request(
            "POST",
            f"/v1/orgs/{oid}/workforce/rollout/waves/{wave_id}/rollback",
            org_id=oid,
            tenant_required=True,
        )

    async def rollback_workforce_rollout_wave_async(self, wave_id: str, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "POST",
            f"/v1/orgs/{oid}/workforce/rollout/waves/{wave_id}/rollback",
            org_id=oid,
            tenant_required=True,
        )

    def get_workforce_rollout_status(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return self._request("GET", f"/v1/orgs/{oid}/workforce/rollout/status", org_id=oid, tenant_required=True)

    async def get_workforce_rollout_status_async(self, *, org_id: str | None = None) -> dict[str, Any]:
        oid = self._require_org(org_id)
        return await self._request_async(
            "GET",
            f"/v1/orgs/{oid}/workforce/rollout/status",
            org_id=oid,
            tenant_required=True,
        )
