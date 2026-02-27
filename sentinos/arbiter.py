from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, cast

from sentinos_core import AuthenticatedClient, Client
from sentinos_core.api.default import (
    arbiter_promote_policy as core_arbiter_promote_policy,
)
from sentinos_core.api.default import (
    arbiter_simulate as core_arbiter_simulate,
)
from sentinos_core.api.default import (
    arbiter_upsert_policy as core_arbiter_upsert_policy,
)
from sentinos_core.api.default import (
    arbiter_verify as core_arbiter_verify,
)
from sentinos_core.models.arbiter_promote_policy_body import ArbiterPromotePolicyBody
from sentinos_core.models.arbiter_promote_policy_body_status import ArbiterPromotePolicyBodyStatus
from sentinos_core.models.arbiter_simulate_body import ArbiterSimulateBody
from sentinos_core.models.arbiter_simulate_response_200 import ArbiterSimulateResponse200
from sentinos_core.models.arbiter_upsert_policy_body import ArbiterUpsertPolicyBody
from sentinos_core.models.arbiter_upsert_policy_body_status import ArbiterUpsertPolicyBodyStatus
from sentinos_core.models.arbiter_verify_body import ArbiterVerifyBody
from sentinos_core.models.arbiter_verify_response_200 import ArbiterVerifyResponse200
from sentinos_core.models.ok_response import OkResponse
from sentinos_core.models.policy_metadata_schema import PolicyMetadataSchema
from sentinos_core.models.policy_metadata_schema_language import PolicyMetadataSchemaLanguage
from sentinos_core.models.policy_metadata_schema_scope import PolicyMetadataSchemaScope
from sentinos_core.models.policy_metadata_schema_source import PolicyMetadataSchemaSource
from sentinos_core.types import UNSET, Response


@dataclass
class ArbiterClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_tenant(self, tenant_id: str | None) -> str:
        t = (tenant_id or self.tenant_id or "").strip()
        if not t:
            raise ValueError("tenant_id is required (set it on SentinosClient or pass it per call)")
        return t

    def _core_with_headers(self, *, tenant_id: str) -> Client | AuthenticatedClient:
        return self._core.with_headers({"x-tenant-id": tenant_id})

    @staticmethod
    def _decode_error_content(content: bytes) -> str:
        if not content:
            return ""
        decoded = content.decode("utf-8", errors="replace").strip()
        if not decoded:
            return ""
        if len(decoded) > 800:
            return decoded[:800] + "...(truncated)"
        return decoded

    def _raise_unparsed_response(self, operation: str, response: Response[Any]) -> None:
        status_code = int(response.status_code)
        detail = self._decode_error_content(response.content)
        hint = ""
        if status_code == HTTPStatus.FORBIDDEN:
            hint = (
                "Caller lacks required policy-write authorization. "
                "Use a token with `role:Admin` or `role:PolicyAuthor` (or equivalent claims), "
                "and ensure `x-tenant-id` / tenant claim matches the target organization."
            )
        elif status_code == HTTPStatus.UNAUTHORIZED:
            hint = "Authentication failed. Verify bearer token validity, issuer/audience config, and expiry."
        elif status_code == HTTPStatus.BAD_REQUEST:
            hint = "Request payload/tenant input was rejected. Check metadata fields, status value, and tenant scope."
        message = f"{operation} failed with HTTP {status_code}"
        if detail:
            message += f": {detail}"
        if hint:
            message += f" Hint: {hint}"
        raise RuntimeError(message)

    def create_policy(
        self,
        *,
        policy_id: str,
        rego: str,
        version: str = "v0.1.0",
        target_tools: list[str] | None = None,
        tenants: list[str] | None = None,
        source: str = "rego",
        status: str = "draft",
        tenant_id: str | None = None,
    ) -> OkResponse:
        """Create or update a policy version (rego source)."""
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)

        scope = PolicyMetadataSchemaScope.from_dict(
            {
                "target_tools": target_tools or ["*"],
                "tenants": tenants or [t],
            }
        )
        md = PolicyMetadataSchema(
            policy_id=policy_id,
            version=version,
            scope=scope,
            language=PolicyMetadataSchemaLanguage.REGO,
            source=(PolicyMetadataSchemaSource.NL if source == "nl" else PolicyMetadataSchemaSource.REGO),
            created_at=_dt.datetime.now(tz=_dt.timezone.utc),
        )
        body = ArbiterUpsertPolicyBody(
            metadata=md,
            rego=rego,
            status=(ArbiterUpsertPolicyBodyStatus(status) if status else UNSET),
        )
        response = core_arbiter_upsert_policy.sync_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.upsert_policy", response)
        return cast(OkResponse, response.parsed)

    async def create_policy_async(self, **kwargs: Any) -> OkResponse:
        # thin async shim; keeps the wrapper API stable while avoiding duplicated logic
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)

        scope = PolicyMetadataSchemaScope.from_dict(
            {
                "target_tools": kwargs.get("target_tools") or ["*"],
                "tenants": kwargs.get("tenants") or [t],
            }
        )
        md = PolicyMetadataSchema(
            policy_id=kwargs["policy_id"],
            version=kwargs.get("version", "v0.1.0"),
            scope=scope,
            language=PolicyMetadataSchemaLanguage.REGO,
            source=(PolicyMetadataSchemaSource.NL if kwargs.get("source") == "nl" else PolicyMetadataSchemaSource.REGO),
            created_at=_dt.datetime.now(tz=_dt.timezone.utc),
        )
        body = ArbiterUpsertPolicyBody(
            metadata=md,
            rego=kwargs["rego"],
            status=(ArbiterUpsertPolicyBodyStatus(kwargs.get("status", "draft")) if kwargs.get("status") else UNSET),
        )
        response = await core_arbiter_upsert_policy.asyncio_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.upsert_policy", response)
        return cast(OkResponse, response.parsed)

    def simulate_policy(
        self,
        *,
        candidate_rego: str,
        trace_limit: int | None = None,
        policy_id: str | None = None,
        version: str | None = None,
        tenant_id: str | None = None,
    ) -> ArbiterSimulateResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = ArbiterSimulateBody.from_dict(
            {
                "tenant_id": t,
                "candidate_rego": candidate_rego,
                "trace_limit": trace_limit,
                "policy_id": policy_id,
                "version": version,
            }
        )
        response = core_arbiter_simulate.sync_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.simulate", response)
        return cast(ArbiterSimulateResponse200, response.parsed)

    async def simulate_policy_async(self, **kwargs: Any) -> ArbiterSimulateResponse200:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        body = ArbiterSimulateBody.from_dict(
            {
                "tenant_id": t,
                "candidate_rego": kwargs["candidate_rego"],
                "trace_limit": kwargs.get("trace_limit"),
                "policy_id": kwargs.get("policy_id"),
                "version": kwargs.get("version"),
            }
        )
        response = await core_arbiter_simulate.asyncio_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.simulate", response)
        return cast(ArbiterSimulateResponse200, response.parsed)

    def promote_policy(
        self,
        *,
        policy_id: str,
        version: str,
        target: str,
        simulation_job_id: str | None = None,
        tenant_id: str | None = None,
    ) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = ArbiterPromotePolicyBody(
            version=version,
            status=ArbiterPromotePolicyBodyStatus(target),
            simulation_job_id=(simulation_job_id if simulation_job_id else UNSET),
        )
        response = core_arbiter_promote_policy.sync_detailed(policy_id=policy_id, client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.promote_policy", response)
        return cast(OkResponse, response.parsed)

    async def promote_policy_async(self, **kwargs: Any) -> OkResponse:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        sim_job_id = kwargs.get("simulation_job_id")
        simulation_job_id: str | Any = UNSET
        if sim_job_id is not None:
            simulation_job_id = str(sim_job_id)
        body = ArbiterPromotePolicyBody(
            version=str(kwargs["version"]),
            status=ArbiterPromotePolicyBodyStatus(str(kwargs["target"])),
            simulation_job_id=simulation_job_id,
        )
        response = await core_arbiter_promote_policy.asyncio_detailed(
            policy_id=kwargs["policy_id"],
            client=c,
            body=body,
        )
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.promote_policy", response)
        return cast(OkResponse, response.parsed)

    def verify_policy(
        self,
        *,
        policy_dsl: dict[str, Any],
        candidate_rego: str,
        testcases: dict[str, Any],
        policy_id: str | None = None,
        version: str | None = None,
        tenant_id: str | None = None,
    ) -> ArbiterVerifyResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = ArbiterVerifyBody.from_dict(
            {
                "policy_dsl": policy_dsl,
                "candidate_rego": candidate_rego,
                "testcases": testcases,
                "policy_id": policy_id,
                "version": version,
            }
        )
        response = core_arbiter_verify.sync_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.verify", response)
        return cast(ArbiterVerifyResponse200, response.parsed)

    async def verify_policy_async(self, **kwargs: Any) -> ArbiterVerifyResponse200:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        body = ArbiterVerifyBody.from_dict(
            {
                "policy_dsl": kwargs["policy_dsl"],
                "candidate_rego": kwargs["candidate_rego"],
                "testcases": kwargs["testcases"],
                "policy_id": kwargs.get("policy_id"),
                "version": kwargs.get("version"),
            }
        )
        response = await core_arbiter_verify.asyncio_detailed(client=c, body=body)
        if response.parsed is None:
            self._raise_unparsed_response("arbiter.verify", response)
        return cast(ArbiterVerifyResponse200, response.parsed)

    def governance_dashboard(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/arbitr/governance/dashboard")
        resp.raise_for_status()
        return resp.json() or {}

    async def governance_dashboard_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/arbitr/governance/dashboard")
        resp.raise_for_status()
        return resp.json() or {}

    def governance_violations(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/arbitr/governance/violations", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("violations") or []

    async def governance_violations_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/arbitr/governance/violations", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("violations") or []

    def governance_report(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if from_time:
            body["from"] = from_time
        if to_time:
            body["to"] = to_time
        if limit is not None:
            body["limit"] = limit
        resp = c.get_httpx_client().post("/v1/arbitr/governance/reports", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def governance_report_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if from_time:
            body["from"] = from_time
        if to_time:
            body["to"] = to_time
        if limit is not None:
            body["limit"] = limit
        resp = await c.get_async_httpx_client().post("/v1/arbitr/governance/reports", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def evaluate(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post("/v1/arbitr/evaluate", json=request)
        resp.raise_for_status()
        return resp.json() or {}

    async def evaluate_async(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post("/v1/arbitr/evaluate", json=request)
        resp.raise_for_status()
        return resp.json() or {}

    def compile(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post("/v1/arbitr/compile", json=request)
        resp.raise_for_status()
        return resp.json() or {}

    async def compile_async(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post("/v1/arbitr/compile", json=request)
        resp.raise_for_status()
        return resp.json() or {}

    def list_policies(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/arbitr/policies")
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("policies") or []

    async def list_policies_async(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/arbitr/policies")
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("policies") or []

    def active_policies(
        self,
        *,
        tool: str,
        env: str | None = None,
        tag: str | None = None,
        tenant_id: str | None = None,
    ) -> list[str]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"tenant_id": t, "tool": tool}
        if env:
            params["env"] = env
        if tag:
            params["tag"] = tag
        resp = c.get_httpx_client().get("/v1/arbitr/policies/active", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("keys") or []

    async def active_policies_async(
        self,
        *,
        tool: str,
        env: str | None = None,
        tag: str | None = None,
        tenant_id: str | None = None,
    ) -> list[str]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"tenant_id": t, "tool": tool}
        if env:
            params["env"] = env
        if tag:
            params["tag"] = tag
        resp = await c.get_async_httpx_client().get("/v1/arbitr/policies/active", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("keys") or []

    def get_tenant_config(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/arbitr/tenants/{t}")
        resp.raise_for_status()
        return resp.json() or {}

    async def get_tenant_config_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/arbitr/tenants/{t}")
        resp.raise_for_status()
        return resp.json() or {}

    def upsert_tenant_config(self, *, config: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().put(f"/v1/arbitr/tenants/{t}", json=config)
        resp.raise_for_status()
        return resp.json() or {}

    async def upsert_tenant_config_async(
        self,
        *,
        config: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().put(f"/v1/arbitr/tenants/{t}", json=config)
        resp.raise_for_status()
        return resp.json() or {}

    def get_policy_bundle(self, *, policy_id: str, version: str, tenant_id: str | None = None) -> bytes:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/arbitr/policies/{policy_id}/versions/{version}/bundle")
        resp.raise_for_status()
        return resp.content

    async def get_policy_bundle_async(
        self,
        *,
        policy_id: str,
        version: str,
        tenant_id: str | None = None,
    ) -> bytes:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/arbitr/policies/{policy_id}/versions/{version}/bundle")
        resp.raise_for_status()
        return resp.content

    def get_simulation_job(self, job_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/arbitr/simulate/{job_id}")
        resp.raise_for_status()
        return resp.json() or {}

    async def get_simulation_job_async(self, job_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/arbitr/simulate/{job_id}")
        resp.raise_for_status()
        return resp.json() or {}
