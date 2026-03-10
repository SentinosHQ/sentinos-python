from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from sentinos.a2a import A2AClient
from sentinos.audit import AuditClient
from sentinos.billing import BillingClient
from sentinos.client import SentinosClient
from sentinos.controlplane import ControlplaneClient
from sentinos.dashboards import DashboardsClient
from sentinos.privacy import PrivacyClient


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeHTTP:
    def __init__(self, label: str) -> None:
        self.label = label
        self.calls: list[tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]] = []

    def request(
        self, *, method: str, url: str, params: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> FakeResponse:
        self.calls.append((method.upper(), url, params, json))
        if url == "/v1/auth/register":
            return FakeResponse({"user_id": "user-1", "org_id": "org-1"})
        if url == "/v1/auth/login/password":
            return FakeResponse({"access_token": "access-1", "refresh_token": "refresh-1"})
        if url == "/v1/auth/token/refresh":
            return FakeResponse({"access_token": "access-2"})
        if url == "/v1/auth/me":
            return FakeResponse({"user": {"user_id": "user-1"}})
        if url == "/v1/auth/logout":
            return FakeResponse({"ok": True})
        if url == "/v1/auth/sessions":
            return FakeResponse({"sessions": [{"session_id": "sess-1"}]})
        if url == "/v1/auth/sessions/revoke-others":
            return FakeResponse({"revoked": 2})
        if "/v1/auth/sessions/" in url:
            return FakeResponse({"ok": True})
        if url == "/v1/orgs":
            return FakeResponse({"organizations": [{"org_id": "org-1"}]})
        if url.endswith("/switch-context-token"):
            return FakeResponse({"access_token": "switched-1"})
        if url.endswith("/members") and method.upper() == "GET":
            return FakeResponse({"members": [{"membership_id": "m-1"}]})
        if "/members/" in url and method.upper() == "PATCH":
            return FakeResponse({"member": {"membership_id": "m-1"}})
        if "/members/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/invites") and method.upper() == "GET":
            return FakeResponse({"invites": [{"invitation_id": "inv-1"}]})
        if url.endswith("/invites") and method.upper() == "POST":
            return FakeResponse({"invite": {"invitation_id": "inv-1"}})
        if "/invites/" in url and url.endswith("/resend"):
            return FakeResponse({"invite": {"invitation_id": "inv-1", "resent": True}})
        if "/invites/" in url and url.endswith("/cancel"):
            return FakeResponse({"invite": {"invitation_id": "inv-1", "status": "cancelled"}})
        if "/invites/" in url:
            return FakeResponse({"invite": {"invitation_id": "inv-1"}})
        if url == "/v1/permissions":
            return FakeResponse({"permissions": [{"slug": "audit.events.read"}]})
        if url.endswith("/roles") and method.upper() == "GET":
            return FakeResponse({"roles": [{"role_id": "role-1"}]})
        if url.endswith("/roles") and method.upper() == "POST":
            return FakeResponse({"role": {"role_id": "role-1"}})
        if "/roles/" in url and url.endswith("/permissions") and method.upper() == "GET":
            return FakeResponse({"permissions": [{"slug": "dashboards.read"}]})
        if "/roles/" in url and url.endswith("/permissions") and method.upper() == "PUT":
            return FakeResponse({"permissions": [{"slug": "dashboards.write"}]})
        if "/roles/" in url and "/members/" in url:
            return FakeResponse({"ok": True})
        if "/roles/" in url and method.upper() == "PATCH":
            return FakeResponse({"role": {"role_id": "role-1", "name": "Ops"}})
        if "/roles/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/teams") and method.upper() == "GET":
            return FakeResponse({"teams": [{"team_id": "team-1"}]})
        if url.endswith("/teams") and method.upper() == "POST":
            return FakeResponse({"team": {"team_id": "team-1"}})
        if "/teams/" in url and url.endswith("/memberships") and method.upper() == "GET":
            return FakeResponse({"memberships": [{"team_membership_id": "tm-1"}]})
        if "/teams/" in url and url.endswith("/memberships") and method.upper() == "POST":
            return FakeResponse({"membership": {"team_membership_id": "tm-1"}})
        if "/teams/" in url and "/memberships/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/teams/settings") and method.upper() == "GET":
            return FakeResponse({"default_role": "viewer"})
        if url.endswith("/teams/settings") and method.upper() == "PATCH":
            return FakeResponse({"default_role": "editor"})
        if "/teams/" in url and method.upper() == "PATCH":
            return FakeResponse({"team": {"team_id": "team-1", "name": "Security"}})
        if "/teams/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/service-accounts") and method.upper() == "GET":
            return FakeResponse({"service_accounts": [{"service_account_id": "sa-1"}]})
        if url.endswith("/service-accounts") and method.upper() == "POST":
            return FakeResponse({"service_account": {"service_account_id": "sa-1"}})
        if "/service-accounts/" in url and url.endswith("/tokens") and method.upper() == "POST":
            return FakeResponse({"token": {"token_id": "tok-1"}})
        if "/tokens/" in url and url.endswith("/revoke"):
            return FakeResponse({"ok": True})
        if "/service-accounts/" in url and method.upper() == "PATCH":
            return FakeResponse({"service_account": {"service_account_id": "sa-1", "name": "CI"}})
        if url.endswith("/settings/login-methods"):
            return FakeResponse({"password": True, "saml": False})
        if url.endswith("/login-method-override") and method.upper() == "GET":
            return FakeResponse({"password": False})
        if url.endswith("/login-method-override") and method.upper() == "PATCH":
            return FakeResponse({"password": True})
        if url.endswith("/login-method-override") and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/saml/config") and method.upper() == "GET":
            return FakeResponse({"enabled": True})
        if url.endswith("/saml/config") and method.upper() == "PATCH":
            return FakeResponse({"enabled": True, "idp_entity_id": "https://idp.example.com"})
        if url.endswith("/saml/metadata"):
            return FakeResponse({"metadata_url": "https://sentinoshq.com/metadata.xml"})
        if url.endswith("/saml/acs"):
            return FakeResponse({"assertion_consumed": True})
        if url.endswith("/authn-mappings") and method.upper() == "GET":
            return FakeResponse({"mappings": [{"mapping_id": "map-1"}]})
        if url.endswith("/authn-mappings") and method.upper() == "POST":
            return FakeResponse({"mapping": {"mapping_id": "map-1"}})
        if "/authn-mappings/" in url and method.upper() == "PATCH":
            return FakeResponse({"mapping": {"mapping_id": "map-1", "enabled": True}})
        if "/authn-mappings/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/scim/config"):
            return FakeResponse({"base_url": "https://app.sentinoshq.com/scim/v2"})
        if url.endswith("/scim/tokens") and method.upper() == "POST":
            return FakeResponse({"token": {"token_id": "scim-1"}})
        if "/scim/tokens/" in url and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url == "/scim/v2/Users" and method.upper() == "GET":
            return FakeResponse({"Resources": [{"id": "u-1"}], "totalResults": 1})
        if url == "/scim/v2/Users" and method.upper() == "POST":
            return FakeResponse({"id": "u-1"})
        if url.startswith("/scim/v2/Users/") and method.upper() == "GET":
            return FakeResponse({"id": "u-1"})
        if url.startswith("/scim/v2/Users/") and method.upper() == "PATCH":
            return FakeResponse({"id": "u-1", "active": True})
        if url.startswith("/scim/v2/Users/") and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url == "/scim/v2/Groups" and method.upper() == "GET":
            return FakeResponse({"Resources": [{"id": "g-1"}], "totalResults": 1})
        if url == "/scim/v2/Groups" and method.upper() == "POST":
            return FakeResponse({"id": "g-1"})
        if url.startswith("/scim/v2/Groups/") and method.upper() == "PATCH":
            return FakeResponse({"id": "g-1", "displayName": "Security"})
        if url.startswith("/scim/v2/Groups/") and method.upper() == "DELETE":
            return FakeResponse({"ok": True})
        if url.endswith("/workforce/rollout/status"):
            return FakeResponse({"waves": [{"wave_id": "w-1"}]})
        if url.endswith("/workforce/rollout/waves") and method.upper() == "POST":
            return FakeResponse({"wave_id": "w-1", "name": "Pilot"})
        if url.endswith("/workforce/audit"):
            return FakeResponse({"events": [{"event_id": "evt-1"}]})
        if url == "/v1/chronos/connectors/health":
            return FakeResponse({"sources": [{"source_id": "slack", "status": "healthy"}]})
        if "/v1/chronos/connectors/" in url and url.endswith("/ingest"):
            return FakeResponse({"accepted": True, "source_id": "slack"})
        if url.endswith("/audit/events/export"):
            return FakeResponse({"job_id": "exp-1"})
        if url.endswith("/audit/events"):
            return FakeResponse({"events": [{"event_id": "ae-1"}], "next_cursor": ""})
        if "/audit/events/" in url:
            return FakeResponse({"event": {"event_id": "ae-1"}})
        if url.endswith("/audit/saved-views"):
            return FakeResponse({"views": [{"view_id": "v-1"}]})
        if "/audit/saved-views/" in url:
            return FakeResponse({"view": {"view_id": "v-1"}})
        if url.endswith("/audit/notable-rules"):
            return FakeResponse({"rule": {"rule_id": "nr-1"}})
        if url.endswith("/audit/notable-events"):
            return FakeResponse({"events": [{"event_id": "ne-1"}]})
        if url.endswith("/dashboards") and method.upper() == "GET":
            return FakeResponse({"dashboards": [{"dashboard_id": "d-1"}]})
        if url.endswith("/dashboards") and method.upper() == "POST":
            return FakeResponse({"dashboard": {"dashboard_id": "d-1"}})
        if "/dashboards/" in url and url.endswith("/favorite"):
            return FakeResponse({"ok": True})
        if "/dashboards/" in url and url.endswith("/permissions"):
            return FakeResponse({"permissions": [{"role_slug": "admin", "can_view": True, "can_edit": True}]})
        if "/dashboards/" in url and url.endswith("/export"):
            return FakeResponse({"dashboard": {"dashboard_id": "d-1"}})
        if "/dashboards/" in url and url.endswith("/versions"):
            return FakeResponse({"versions": [{"version": 1}]})
        if "/dashboards/" in url and "/restore/" in url:
            return FakeResponse({"dashboard": {"dashboard_id": "d-1"}})
        if "/dashboards/" in url and url.endswith("/saved-views"):
            return FakeResponse({"views": [{"view_id": "sv-1"}]})
        if "/dashboards/" in url and "/saved-views/" in url:
            return FakeResponse({"ok": True})
        if url.endswith("/dashboards/import"):
            return FakeResponse({"dashboard": {"dashboard_id": "d-2"}})
        if url.endswith("/v1/dashboard/query"):
            return FakeResponse({"source": self.label, "series": []})
        if url.endswith("/v1/kernel/billing/entitlements"):
            return FakeResponse({"plan": "CORE", "status": "ACTIVE"})
        if url.endswith("/v1/kernel/billing/usage/summary"):
            return FakeResponse({"usage": {"governed_executions": 42}})
        if url.endswith("/v1/kernel/billing/usage/events"):
            return FakeResponse({"events": [{"event_id": "be-1"}]})
        if url.endswith("/v1/trace/privacy/policy"):
            return FakeResponse({"telemetry_mode": "redact"})
        if url.endswith("/v1/trace/privacy/scan"):
            return FakeResponse({"redactions": [{"field": "prompt"}]})
        if url.endswith("/v1/a2a/handoffs/authorize"):
            return FakeResponse({"decision": "ALLOW"})
        if url.endswith("/v1/a2a/handoffs/forward"):
            return FakeResponse({"forwarded": True})
        if url.endswith("/receipt"):
            return FakeResponse({"receipt_id": "r-1"})
        if url.endswith("/lineage"):
            return FakeResponse({"events": [{"handoff_id": "h-1"}]})
        if url.endswith("/verify"):
            return FakeResponse({"verified": True})
        if url.endswith("/v1/a2a/trust-scores"):
            return FakeResponse({"scores": [{"agent_id": "agent-1", "score": 0.97}]})
        return FakeResponse({})

    def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return self.request(method="GET", url=path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self.request(method="POST", url=path, json=json)

    def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self.request(method="PUT", url=path, json=json)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self.request(method="PATCH", url=path, json=json)

    def delete(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return self.request(method="DELETE", url=path, params=params)


class FakeAsyncHTTP(FakeHTTP):
    async def request(
        self, *, method: str, url: str, params: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> FakeResponse:
        return super().request(method=method, url=url, params=params, json=json)

    async def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return super().get(path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return super().post(path, json=json)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return super().put(path, json=json)

    async def patch(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return super().patch(path, json=json)

    async def delete(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return super().delete(path, params=params)


class FakeCore:
    def __init__(self, label: str = "default") -> None:
        self.http = FakeHTTP(label)
        self.async_http = FakeAsyncHTTP(label)
        self.headers: dict[str, str] = {}

    def with_headers(self, headers: dict[str, str]) -> FakeCore:
        nxt = FakeCore(self.http.label)
        nxt.http = self.http
        nxt.async_http = self.async_http
        nxt.headers = self.headers | headers
        return nxt

    def get_httpx_client(self) -> FakeHTTP:
        return self.http

    def get_async_httpx_client(self) -> FakeAsyncHTTP:
        return self.async_http


def test_sentinos_client_exposes_new_runtime_and_admin_clients() -> None:
    client = SentinosClient(base_url="https://api.sentinoshq.com")

    assert client.config.meshgate_url == "https://api.sentinoshq.com"
    assert isinstance(client.controlplane, ControlplaneClient)
    assert isinstance(client.audit, AuditClient)
    assert isinstance(client.dashboards, DashboardsClient)
    assert isinstance(client.billing, BillingClient)
    assert isinstance(client.privacy, PrivacyClient)
    assert isinstance(client.a2a, A2AClient)


def test_sentinos_client_local_base_url_uses_meshgate_default() -> None:
    client = SentinosClient(base_url="http://localhost:8081")
    assert client.config.meshgate_url == "http://localhost:8085"


def test_controlplane_client_covers_rollout_and_audit_admin_paths() -> None:
    core = FakeCore("controlplane")
    client = ControlplaneClient(core, tenant_id="org-1")

    assert client.list_organizations()[0]["org_id"] == "org-1"
    assert client.get_workforce_rollout_status()["waves"][0]["wave_id"] == "w-1"
    assert client.create_workforce_rollout_wave(wave={"name": "Pilot"})["wave_id"] == "w-1"
    assert client.list_workforce_audit(limit=25)[0]["event_id"] == "evt-1"

    assert core.http.calls[0] == ("GET", "/v1/orgs", None, None)
    assert core.http.calls[1][1] == "/v1/orgs/org-1/workforce/rollout/status"
    assert core.http.calls[2][1] == "/v1/orgs/org-1/workforce/rollout/waves"
    assert core.http.calls[3][1] == "/v1/orgs/org-1/workforce/audit"


def test_controlplane_client_covers_auth_and_org_admin_surfaces() -> None:
    core = FakeCore("controlplane")
    client = ControlplaneClient(core, tenant_id="org-1")

    assert client.register(payload={"email": "ops@sentinoshq.com"})["user_id"] == "user-1"
    assert (
        client.login_password(payload={"email": "ops@sentinoshq.com", "password": "secret"})["access_token"]
        == "access-1"
    )
    assert client.auth_me()["user"]["user_id"] == "user-1"
    assert client.list_sessions()[0]["session_id"] == "sess-1"
    assert client.revoke_other_sessions()["revoked"] == 2
    assert client.delete_session("sess-1")["ok"] is True
    assert client.switch_context_token()["access_token"] == "switched-1"
    assert client.list_members()[0]["membership_id"] == "m-1"
    assert client.list_invites()[0]["invitation_id"] == "inv-1"
    assert client.list_permissions()[0]["slug"] == "audit.events.read"
    assert client.list_roles()[0]["role_id"] == "role-1"
    assert client.get_role_permissions("role-1")["permissions"][0]["slug"] == "dashboards.read"
    assert client.list_teams()[0]["team_id"] == "team-1"
    assert client.get_team_settings()["default_role"] == "viewer"
    assert client.list_service_accounts()[0]["service_account_id"] == "sa-1"
    assert client.get_login_methods()["password"] is True
    assert client.get_user_login_method_override("user-1")["password"] is False
    assert client.get_saml_config()["enabled"] is True
    assert client.get_saml_metadata()["metadata_url"].endswith("metadata.xml")
    assert client.list_authn_mappings()[0]["mapping_id"] == "map-1"
    assert client.get_scim_config()["base_url"].endswith("/scim/v2")
    assert client.scim_list_users()["Resources"][0]["id"] == "u-1"
    assert client.scim_list_groups()["Resources"][0]["id"] == "g-1"

    assert core.http.calls[0][1] == "/v1/auth/register"
    assert core.http.calls[1][1] == "/v1/auth/login/password"
    assert core.http.calls[6][1] == "/v1/orgs/org-1/switch-context-token"
    assert core.http.calls[-2][1] == "/scim/v2/Users"
    assert core.http.calls[-1][1] == "/scim/v2/Groups"


def test_audit_client_covers_events_saved_views_and_notables() -> None:
    core = FakeCore("controlplane")
    client = AuditClient(core, tenant_id="org-1")

    events = client.list_events(q="risk*", category="runtime", tags=["signed", "mesh"], limit=50)
    assert events["events"][0]["event_id"] == "ae-1"
    assert client.get_event("ae-1")["event"]["event_id"] == "ae-1"
    assert client.export_events(export={"format": "json"})["job_id"] == "exp-1"
    assert client.list_saved_views()[0]["view_id"] == "v-1"
    assert client.create_notable_rule(rule={"name": "High risk"})["rule"]["rule_id"] == "nr-1"
    assert client.list_notable_events(limit=10)["events"][0]["event_id"] == "ne-1"

    assert core.http.calls[0][1] == "/v1/orgs/org-1/audit/events"
    assert core.http.calls[0][2]["tags"] == "signed,mesh"


def test_dashboards_client_routes_metadata_and_query_to_correct_service() -> None:
    metadata = FakeCore("controlplane")
    query_cores = {
        "controlplane": FakeCore("controlplane"),
        "kernel": FakeCore("kernel"),
        "arbiter": FakeCore("arbiter"),
        "chronos": FakeCore("chronos"),
    }
    client = DashboardsClient(metadata, query_cores, tenant_id="org-1")

    assert client.list(include_deleted=True, limit=20)["dashboards"][0]["dashboard_id"] == "d-1"
    assert client.set_favorite("d-1", favorite=True)["ok"] is True
    assert client.query(source_service="arbiter", body={"queries": []})["source"] == "arbiter"

    assert metadata.http.calls[0][1] == "/v1/orgs/org-1/dashboards"
    assert metadata.http.calls[1][1] == "/v1/orgs/org-1/dashboards/d-1/favorite"
    assert query_cores["arbiter"].http.calls[0][1] == "/v1/dashboard/query"


def test_billing_privacy_and_a2a_clients_cover_new_runtime_surfaces() -> None:
    kernel = FakeCore("kernel")
    meshgate = FakeCore("meshgate")

    billing = BillingClient(kernel, tenant_id="org-1")
    privacy = PrivacyClient(kernel, tenant_id="org-1")
    a2a = A2AClient(meshgate, tenant_id="org-1")

    assert billing.get_entitlements()["plan"] == "CORE"
    assert billing.get_usage_summary(period_at="2026-03-01T00:00:00Z")["usage"]["governed_executions"] == 42
    assert privacy.scan(payload={"prompt": "hello"})["redactions"][0]["field"] == "prompt"
    assert a2a.authorize_handoff(handoff={"from_agent": "a", "to_agent": "b"})["decision"] == "ALLOW"
    assert a2a.list_trust_scores(agents=["a", "b"], limit=5)["scores"][0]["agent_id"] == "agent-1"

    assert kernel.http.calls[0][1] == "/v1/kernel/billing/entitlements"
    assert kernel.http.calls[1][2]["period_at"] == "2026-03-01T00:00:00Z"
    assert meshgate.http.calls[-1][2]["agents"] == "a,b"


def test_chronos_client_covers_connector_surfaces() -> None:
    from sentinos.chronos import ChronosClient

    chronos = FakeCore("chronos")
    client = ChronosClient(chronos, tenant_id="org-1")

    assert client.connector_health()["sources"][0]["source_id"] == "slack"
    assert client.ingest_connector_event(source_id="slack", event={"message": "hello"})["accepted"] is True

    assert chronos.http.calls[0][1] == "/v1/chronos/connectors/health"
    assert chronos.http.calls[1][1] == "/v1/chronos/connectors/slack/ingest"


def test_async_admin_and_runtime_clients_work() -> None:
    async def run() -> None:
        core = FakeCore("controlplane")
        meshgate = FakeCore("meshgate")
        kernel = FakeCore("kernel")

        controlplane = ControlplaneClient(core, tenant_id="org-1")
        audit = AuditClient(core, tenant_id="org-1")
        dashboards = DashboardsClient(
            core, {"controlplane": core, "kernel": kernel, "arbiter": core, "chronos": core}, tenant_id="org-1"
        )
        billing = BillingClient(kernel, tenant_id="org-1")
        privacy = PrivacyClient(kernel, tenant_id="org-1")
        a2a = A2AClient(meshgate, tenant_id="org-1")

        assert (await controlplane.get_workforce_rollout_status_async())["waves"][0]["wave_id"] == "w-1"
        assert (await controlplane.auth_me_async())["user"]["user_id"] == "user-1"
        assert (await audit.get_event_async("ae-1"))["event"]["event_id"] == "ae-1"
        assert (await dashboards.query_async(source_service="kernel", body={"queries": []}))["source"] == "kernel"
        assert (await billing.get_entitlements_async())["plan"] == "CORE"
        assert (await privacy.scan_async(payload={"prompt": "hello"}))["redactions"][0]["field"] == "prompt"
        assert (await a2a.verify_receipt_async("h-1"))["verified"] is True

    asyncio.run(run())
