from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sentinos_core import AuthenticatedClient, Client
from sentinos_core.api.default import trace_distributed_summaries as core_trace_distributed_summaries
from sentinos_core.api.default import trace_get as core_trace_get
from sentinos_core.api.default import trace_ledger_verify as core_trace_ledger_verify
from sentinos_core.api.default import trace_retention_enforce as core_trace_retention_enforce
from sentinos_core.api.default import trace_retention_get as core_trace_retention_get
from sentinos_core.api.default import trace_retention_update as core_trace_retention_update
from sentinos_core.models.distributed_trace_summary import DistributedTraceSummary
from sentinos_core.models.trace_ledger_verification import TraceLedgerVerification
from sentinos_core.models.trace_retention_enforce_body import TraceRetentionEnforceBody
from sentinos_core.models.trace_retention_enforcement_result import TraceRetentionEnforcementResult
from sentinos_core.models.trace_retention_policy import TraceRetentionPolicy
from sentinos_core.models.trace_retention_update_body import TraceRetentionUpdateBody
from sentinos_core.models.trace_summary import TraceSummary
from sentinos_core.types import UNSET, Unset

from .models.decision_trace import DecisionTrace
from .models.lineage import TraceArtifactLineageResponse
from .models.replay import (
    TraceReplayExportResponse,
    TraceReplayMatrixResponse,
    TraceReplayResponse,
)


@dataclass
class TracesClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_tenant(self, tenant_id: str | None) -> str:
        t = (tenant_id or self.tenant_id or "").strip()
        if not t:
            raise ValueError("tenant_id is required (set it on SentinosClient or pass it per call)")
        return t

    def _core_with_headers(self, *, tenant_id: str) -> Client | AuthenticatedClient:
        return self._core.with_headers({"x-tenant-id": tenant_id})

    def get_trace(self, trace_id: UUID | str, *, tenant_id: str | None = None) -> DecisionTrace:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_trace_get.sync(trace_id=UUID(str(trace_id)), client=c)
        if out is None:
            raise RuntimeError("trace.get returned no parsed response")
        return DecisionTrace.from_core(out)

    async def get_trace_async(self, trace_id: UUID | str, *, tenant_id: str | None = None) -> DecisionTrace:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_trace_get.asyncio(trace_id=UUID(str(trace_id)), client=c)
        if out is None:
            raise RuntimeError("trace.get returned no parsed response")
        return DecisionTrace.from_core(out)

    def get_trace_lineage(
        self,
        trace_id: UUID | str,
        *,
        tenant_id: str | None = None,
    ) -> TraceArtifactLineageResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/traces/{trace_id}/lineage")
        resp.raise_for_status()
        return TraceArtifactLineageResponse.model_validate(resp.json() or {})

    async def get_trace_lineage_async(
        self,
        trace_id: UUID | str,
        *,
        tenant_id: str | None = None,
    ) -> TraceArtifactLineageResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/traces/{trace_id}/lineage")
        resp.raise_for_status()
        return TraceArtifactLineageResponse.model_validate(resp.json() or {})

    def list_traces(
        self,
        *,
        agent_id: str | None = None,
        policy_id: str | None = None,
        decision: str | None = None,
        tenant_id: str | None = None,
    ) -> list[TraceSummary]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"tenant_id": t}
        if agent_id:
            params["agent_id"] = agent_id
        if policy_id:
            params["policy_id"] = policy_id
        if decision:
            params["decision"] = decision

        resp = c.get_httpx_client().get("/v1/trace/search", params=params)
        resp.raise_for_status()
        data = resp.json() or {}
        traces = data.get("traces") or []
        return [TraceSummary.from_dict(row) for row in traces]

    async def list_traces_async(self, **kwargs: Any) -> list[TraceSummary]:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"tenant_id": t}
        if kwargs.get("agent_id"):
            params["agent_id"] = kwargs["agent_id"]
        if kwargs.get("policy_id"):
            params["policy_id"] = kwargs["policy_id"]
        if kwargs.get("decision"):
            params["decision"] = kwargs["decision"]

        resp = await c.get_async_httpx_client().get("/v1/trace/search", params=params)
        resp.raise_for_status()
        data = resp.json() or {}
        traces = data.get("traces") or []
        return [TraceSummary.from_dict(row) for row in traces]

    def verify_trace(self, trace_id: UUID | str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/trace/{trace_id}/verify")
        resp.raise_for_status()
        return resp.json() or {}

    async def verify_trace_async(self, trace_id: UUID | str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/trace/{trace_id}/verify")
        resp.raise_for_status()
        return resp.json() or {}

    def ledger_verify(self, trace_id: UUID | str, *, tenant_id: str | None = None) -> TraceLedgerVerification:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_trace_ledger_verify.sync(trace_id=UUID(str(trace_id)), client=c)
        if out is None:
            raise RuntimeError("trace.ledger_verify returned no parsed response")
        return out

    async def ledger_verify_async(
        self,
        trace_id: UUID | str,
        *,
        tenant_id: str | None = None,
    ) -> TraceLedgerVerification:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_trace_ledger_verify.asyncio(trace_id=UUID(str(trace_id)), client=c)
        if out is None:
            raise RuntimeError("trace.ledger_verify returned no parsed response")
        return out

    def replay_trace(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post(f"/v1/trace/{trace_id}/replay", json=request or {})
        resp.raise_for_status()
        return TraceReplayResponse.model_validate(resp.json() or {})

    async def replay_trace_async(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post(f"/v1/trace/{trace_id}/replay", json=request or {})
        resp.raise_for_status()
        return TraceReplayResponse.model_validate(resp.json() or {})

    def replay_trace_matrix(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayMatrixResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post(f"/v1/trace/{trace_id}/replay/matrix", json=request or {})
        resp.raise_for_status()
        return TraceReplayMatrixResponse.model_validate(resp.json() or {})

    async def replay_trace_matrix_async(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayMatrixResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post(f"/v1/trace/{trace_id}/replay/matrix", json=request or {})
        resp.raise_for_status()
        return TraceReplayMatrixResponse.model_validate(resp.json() or {})

    def export_replay_evidence(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayExportResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post(f"/v1/trace/{trace_id}/replay/export", json=request or {})
        resp.raise_for_status()
        return TraceReplayExportResponse.model_validate(resp.json() or {})

    async def export_replay_evidence_async(
        self,
        trace_id: UUID | str,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceReplayExportResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post(f"/v1/trace/{trace_id}/replay/export", json=request or {})
        resp.raise_for_status()
        return TraceReplayExportResponse.model_validate(resp.json() or {})

    def get_retention_policy(self, *, tenant_id: str | None = None) -> TraceRetentionPolicy:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_trace_retention_get.sync(client=c)
        if out is None:
            raise RuntimeError("trace.retention.get returned no parsed response")
        return out

    async def get_retention_policy_async(self, *, tenant_id: str | None = None) -> TraceRetentionPolicy:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_trace_retention_get.asyncio(client=c)
        if out is None:
            raise RuntimeError("trace.retention.get returned no parsed response")
        return out

    def update_retention_policy(
        self,
        *,
        request: dict[str, Any],
        tenant_id: str | None = None,
    ) -> TraceRetentionPolicy:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_trace_retention_update.sync(
            client=c,
            body=TraceRetentionUpdateBody.from_dict(dict(request)),
        )
        if out is None:
            raise RuntimeError("trace.retention.update returned no parsed response")
        return out

    async def update_retention_policy_async(
        self,
        *,
        request: dict[str, Any],
        tenant_id: str | None = None,
    ) -> TraceRetentionPolicy:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_trace_retention_update.asyncio(
            client=c,
            body=TraceRetentionUpdateBody.from_dict(dict(request)),
        )
        if out is None:
            raise RuntimeError("trace.retention.update returned no parsed response")
        return out

    def enforce_retention(
        self,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceRetentionEnforcementResult:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: TraceRetentionEnforceBody | Unset = UNSET
        if request is not None:
            body = TraceRetentionEnforceBody.from_dict(dict(request))
        out = core_trace_retention_enforce.sync(client=c, body=body)
        if out is None:
            raise RuntimeError("trace.retention.enforce returned no parsed response")
        return out

    async def enforce_retention_async(
        self,
        *,
        request: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> TraceRetentionEnforcementResult:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: TraceRetentionEnforceBody | Unset = UNSET
        if request is not None:
            body = TraceRetentionEnforceBody.from_dict(dict(request))
        out = await core_trace_retention_enforce.asyncio(client=c, body=body)
        if out is None:
            raise RuntimeError("trace.retention.enforce returned no parsed response")
        return out

    def distributed_trace_summaries(
        self,
        *,
        limit: int = 50,
        tenant_id: str | None = None,
    ) -> list[DistributedTraceSummary]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_trace_distributed_summaries.sync(client=c, limit=limit)
        if out is None:
            raise RuntimeError("trace.distributed_summaries returned no parsed response")
        return out.traces

    async def distributed_trace_summaries_async(
        self,
        *,
        limit: int = 50,
        tenant_id: str | None = None,
    ) -> list[DistributedTraceSummary]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_trace_distributed_summaries.asyncio(client=c, limit=limit)
        if out is None:
            raise RuntimeError("trace.distributed_summaries returned no parsed response")
        return out.traces

    def export_traces(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(request)
        # Tenant is resolved from auth claims / headers; kernel export body does not accept tenant_id.
        body.pop("tenant_id", None)
        resp = c.get_httpx_client().post("/v1/trace/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def export_traces_async(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(request)
        # Tenant is resolved from auth claims / headers; kernel export body does not accept tenant_id.
        body.pop("tenant_id", None)
        resp = await c.get_async_httpx_client().post("/v1/trace/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def export_status(self, job_id: UUID | str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/trace/export/job/{job_id}")
        resp.raise_for_status()
        return resp.json() or {}

    async def export_status_async(self, job_id: UUID | str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/trace/export/job/{job_id}")
        resp.raise_for_status()
        return resp.json() or {}
