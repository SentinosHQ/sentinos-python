from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sentinos_core import AuthenticatedClient, Client
from sentinos_core.api.default import (
    kernel_append_session_event as core_kernel_append_session_event,
)
from sentinos_core.api.default import (
    kernel_create_autonomy_session as core_kernel_create_autonomy_session,
)
from sentinos_core.api.default import (
    kernel_execute as core_kernel_execute,
)
from sentinos_core.api.default import (
    kernel_get_autonomy_session as core_kernel_get_autonomy_session,
)
from sentinos_core.api.default import (
    kernel_get_escalation as core_kernel_get_escalation,
)
from sentinos_core.api.default import (
    kernel_get_runtime_metrics as core_kernel_get_runtime_metrics,
)
from sentinos_core.api.default import (
    kernel_get_session as core_kernel_get_session,
)
from sentinos_core.api.default import (
    kernel_get_trace as core_kernel_get_trace,
)
from sentinos_core.api.default import (
    kernel_list_autonomy_sessions as core_kernel_list_autonomy_sessions,
)
from sentinos_core.api.default import (
    kernel_list_escalations as core_kernel_list_escalations,
)
from sentinos_core.api.default import (
    kernel_patch_autonomy_session as core_kernel_patch_autonomy_session,
)
from sentinos_core.api.default import (
    kernel_pause_autonomy_session as core_kernel_pause_autonomy_session,
)
from sentinos_core.api.default import (
    kernel_purge_wasm_cache as core_kernel_purge_wasm_cache,
)
from sentinos_core.api.default import (
    kernel_resolve_escalation as core_kernel_resolve_escalation,
)
from sentinos_core.api.default import (
    kernel_resume_autonomy_session as core_kernel_resume_autonomy_session,
)
from sentinos_core.api.default import (
    kernel_terminate_autonomy_session as core_kernel_terminate_autonomy_session,
)
from sentinos_core.models.autonomy_risk_budget import AutonomyRiskBudget
from sentinos_core.models.autonomy_session_action_request import AutonomySessionActionRequest
from sentinos_core.models.autonomy_session_create_request import AutonomySessionCreateRequest
from sentinos_core.models.autonomy_session_create_request_metadata import AutonomySessionCreateRequestMetadata
from sentinos_core.models.autonomy_session_patch_request import AutonomySessionPatchRequest
from sentinos_core.models.autonomy_session_patch_request_metadata import AutonomySessionPatchRequestMetadata
from sentinos_core.models.decision_trace_intent import DecisionTraceIntent
from sentinos_core.models.kernel_create_autonomy_session_response_201 import KernelCreateAutonomySessionResponse201
from sentinos_core.models.kernel_execute_request import KernelExecuteRequest
from sentinos_core.models.kernel_execute_request_metadata import KernelExecuteRequestMetadata
from sentinos_core.models.kernel_get_autonomy_session_response_200 import KernelGetAutonomySessionResponse200
from sentinos_core.models.kernel_get_escalation_response_200 import KernelGetEscalationResponse200
from sentinos_core.models.kernel_get_session_response_200 import KernelGetSessionResponse200
from sentinos_core.models.kernel_list_autonomy_sessions_response_200 import KernelListAutonomySessionsResponse200
from sentinos_core.models.kernel_list_autonomy_sessions_status import KernelListAutonomySessionsStatus
from sentinos_core.models.kernel_list_escalations_response_200 import KernelListEscalationsResponse200
from sentinos_core.models.kernel_patch_autonomy_session_response_200 import KernelPatchAutonomySessionResponse200
from sentinos_core.models.kernel_pause_autonomy_session_response_200 import KernelPauseAutonomySessionResponse200
from sentinos_core.models.kernel_resolve_escalation_body import KernelResolveEscalationBody
from sentinos_core.models.kernel_resume_autonomy_session_response_200 import KernelResumeAutonomySessionResponse200
from sentinos_core.models.kernel_terminate_autonomy_session_response_200 import (
    KernelTerminateAutonomySessionResponse200,
)
from sentinos_core.models.ok_response import OkResponse
from sentinos_core.models.session_event import SessionEvent
from sentinos_core.types import UNSET, Unset

from .models.api_key import APIKeyRecord
from .models.cost import (
    KernelCostAnomaliesResponse,
    KernelCostAvoidedResponse,
    KernelCostEventsResponse,
    KernelCostSummaryResponse,
)
from .models.decision_trace import DecisionTrace
from .models.otel import OtelExportConfig, OtelExportStatus, OtelExportTestResult


@dataclass
class KernelClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_tenant(self, tenant_id: str | None) -> str:
        t = (tenant_id or self.tenant_id or "").strip()
        if not t:
            raise ValueError("tenant_id is required (set it on SentinosClient or pass it per call)")
        return t

    def _core_with_headers(self, *, tenant_id: str, agent_id: str | None = None) -> Client | AuthenticatedClient:
        headers: dict[str, str] = {"x-tenant-id": tenant_id}
        if agent_id:
            headers["x-agent-id"] = agent_id
        return self._core.with_headers(headers)

    def execute(
        self,
        *,
        agent_id: str,
        intent: dict[str, Any],
        session_id: str,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> DecisionTrace:
        """Execute via Kernel, then fetch the full DecisionTrace by trace_id."""
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t, agent_id=agent_id)

        req = KernelExecuteRequest(
            tenant_id=t,
            agent_id=agent_id,
            session_id=session_id,
            intent=DecisionTraceIntent.from_dict(intent),
            metadata=(KernelExecuteRequestMetadata.from_dict(metadata) if metadata else UNSET),
        )
        exec_resp = core_kernel_execute.sync(client=c, body=req)
        if exec_resp is None:
            raise RuntimeError("kernel.execute returned no parsed response")

        trace = core_kernel_get_trace.sync(trace_id=exec_resp.trace_id, client=c)
        if trace is None:
            raise RuntimeError("kernel.get_trace returned no parsed response")
        return DecisionTrace.from_core(trace)

    async def execute_async(
        self,
        *,
        agent_id: str,
        intent: dict[str, Any],
        session_id: str,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> DecisionTrace:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t, agent_id=agent_id)

        req = KernelExecuteRequest(
            tenant_id=t,
            agent_id=agent_id,
            session_id=session_id,
            intent=DecisionTraceIntent.from_dict(intent),
            metadata=(KernelExecuteRequestMetadata.from_dict(metadata) if metadata else UNSET),
        )
        exec_resp = await core_kernel_execute.asyncio(client=c, body=req)
        if exec_resp is None:
            raise RuntimeError("kernel.execute returned no parsed response")

        trace = await core_kernel_get_trace.asyncio(trace_id=exec_resp.trace_id, client=c)
        if trace is None:
            raise RuntimeError("kernel.get_trace returned no parsed response")
        return DecisionTrace.from_core(trace)

    def get_trace(self, *, trace_id: UUID | str, tenant_id: str | None = None) -> DecisionTrace:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        trace = core_kernel_get_trace.sync(trace_id=UUID(str(trace_id)), client=c)
        if trace is None:
            raise RuntimeError("kernel.get_trace returned no parsed response")
        return DecisionTrace.from_core(trace)

    async def get_trace_async(self, *, trace_id: UUID | str, tenant_id: str | None = None) -> DecisionTrace:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        trace = await core_kernel_get_trace.asyncio(trace_id=UUID(str(trace_id)), client=c)
        if trace is None:
            raise RuntimeError("kernel.get_trace returned no parsed response")
        return DecisionTrace.from_core(trace)

    def get_session(self, *, session_id: str, tenant_id: str | None = None) -> KernelGetSessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_get_session.sync(session_id=session_id, client=c)
        if out is None:
            raise RuntimeError("kernel.get_session returned no parsed response")
        return out

    async def get_session_async(self, *, session_id: str, tenant_id: str | None = None) -> KernelGetSessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_get_session.asyncio(session_id=session_id, client=c)
        if out is None:
            raise RuntimeError("kernel.get_session returned no parsed response")
        return out

    def append_session_event(
        self,
        *,
        session_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
        tenant_id: str | None = None,
    ) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        d: dict[str, Any] = {"type": event_type, "payload": payload or {}}
        if timestamp is not None:
            d["timestamp"] = timestamp
        ev = SessionEvent.from_dict(d)
        out = core_kernel_append_session_event.sync(session_id=session_id, client=c, body=ev)
        if out is None:
            raise RuntimeError("kernel.append_session_event returned no parsed response")
        return out

    def list_autonomy_sessions(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelListAutonomySessionsResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        st: KernelListAutonomySessionsStatus | Unset = UNSET
        if status is not None:
            st = KernelListAutonomySessionsStatus(str(status).upper())
        out = core_kernel_list_autonomy_sessions.sync(
            client=c,
            status=st,
            limit=(limit if limit is not None else UNSET),
        )
        if out is None:
            raise RuntimeError("kernel.list_autonomy_sessions returned no parsed response")
        return out

    async def list_autonomy_sessions_async(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelListAutonomySessionsResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        st: KernelListAutonomySessionsStatus | Unset = UNSET
        if status is not None:
            st = KernelListAutonomySessionsStatus(str(status).upper())
        out = await core_kernel_list_autonomy_sessions.asyncio(
            client=c,
            status=st,
            limit=(limit if limit is not None else UNSET),
        )
        if out is None:
            raise RuntimeError("kernel.list_autonomy_sessions_async returned no parsed response")
        return out

    def create_autonomy_session(
        self,
        *,
        agent_id: str,
        session_id: str | None = None,
        risk_budget_snapshot: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> KernelCreateAutonomySessionResponse201:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t, agent_id=agent_id)
        snapshot: AutonomyRiskBudget | Unset = (
            AutonomyRiskBudget.from_dict(risk_budget_snapshot) if risk_budget_snapshot else UNSET
        )
        meta: AutonomySessionCreateRequestMetadata | Unset = (
            AutonomySessionCreateRequestMetadata.from_dict(metadata) if metadata else UNSET
        )
        req = AutonomySessionCreateRequest(
            tenant_id=t,
            agent_id=agent_id,
            session_id=(session_id if session_id is not None else UNSET),
            risk_budget_snapshot=snapshot,
            metadata=meta,
        )
        out = core_kernel_create_autonomy_session.sync(client=c, body=req)
        if out is None:
            raise RuntimeError("kernel.create_autonomy_session returned no parsed response")
        return out

    async def create_autonomy_session_async(
        self,
        *,
        agent_id: str,
        session_id: str | None = None,
        risk_budget_snapshot: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> KernelCreateAutonomySessionResponse201:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t, agent_id=agent_id)
        snapshot: AutonomyRiskBudget | Unset = (
            AutonomyRiskBudget.from_dict(risk_budget_snapshot) if risk_budget_snapshot else UNSET
        )
        meta: AutonomySessionCreateRequestMetadata | Unset = (
            AutonomySessionCreateRequestMetadata.from_dict(metadata) if metadata else UNSET
        )
        req = AutonomySessionCreateRequest(
            tenant_id=t,
            agent_id=agent_id,
            session_id=(session_id if session_id is not None else UNSET),
            risk_budget_snapshot=snapshot,
            metadata=meta,
        )
        out = await core_kernel_create_autonomy_session.asyncio(client=c, body=req)
        if out is None:
            raise RuntimeError("kernel.create_autonomy_session_async returned no parsed response")
        return out

    def get_autonomy_session(
        self,
        *,
        session_id: str,
        tenant_id: str | None = None,
    ) -> KernelGetAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_get_autonomy_session.sync(session_id=session_id, client=c)
        if out is None:
            raise RuntimeError("kernel.get_autonomy_session returned no parsed response")
        return out

    async def get_autonomy_session_async(
        self, *, session_id: str, tenant_id: str | None = None
    ) -> KernelGetAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_get_autonomy_session.asyncio(session_id=session_id, client=c)
        if out is None:
            raise RuntimeError("kernel.get_autonomy_session_async returned no parsed response")
        return out

    def patch_autonomy_session(
        self,
        *,
        session_id: str,
        risk_budget_snapshot: dict[str, Any] | None = None,
        budget_violation_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> KernelPatchAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        snapshot: AutonomyRiskBudget | Unset = (
            AutonomyRiskBudget.from_dict(risk_budget_snapshot) if risk_budget_snapshot else UNSET
        )
        meta: AutonomySessionPatchRequestMetadata | Unset = (
            AutonomySessionPatchRequestMetadata.from_dict(metadata) if metadata else UNSET
        )
        req = AutonomySessionPatchRequest(
            risk_budget_snapshot=snapshot,
            budget_violation_reason=(budget_violation_reason if budget_violation_reason is not None else UNSET),
            metadata=meta,
        )
        out = core_kernel_patch_autonomy_session.sync(session_id=session_id, client=c, body=req)
        if out is None:
            raise RuntimeError("kernel.patch_autonomy_session returned no parsed response")
        return out

    async def patch_autonomy_session_async(
        self,
        *,
        session_id: str,
        risk_budget_snapshot: dict[str, Any] | None = None,
        budget_violation_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> KernelPatchAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        snapshot: AutonomyRiskBudget | Unset = (
            AutonomyRiskBudget.from_dict(risk_budget_snapshot) if risk_budget_snapshot else UNSET
        )
        meta: AutonomySessionPatchRequestMetadata | Unset = (
            AutonomySessionPatchRequestMetadata.from_dict(metadata) if metadata else UNSET
        )
        req = AutonomySessionPatchRequest(
            risk_budget_snapshot=snapshot,
            budget_violation_reason=(budget_violation_reason if budget_violation_reason is not None else UNSET),
            metadata=meta,
        )
        out = await core_kernel_patch_autonomy_session.asyncio(session_id=session_id, client=c, body=req)
        if out is None:
            raise RuntimeError("kernel.patch_autonomy_session_async returned no parsed response")
        return out

    def pause_autonomy_session(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelPauseAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = core_kernel_pause_autonomy_session.sync(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.pause_autonomy_session returned no parsed response")
        return out

    async def pause_autonomy_session_async(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelPauseAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = await core_kernel_pause_autonomy_session.asyncio(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.pause_autonomy_session_async returned no parsed response")
        return out

    def resume_autonomy_session(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelResumeAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = core_kernel_resume_autonomy_session.sync(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.resume_autonomy_session returned no parsed response")
        return out

    async def resume_autonomy_session_async(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelResumeAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = await core_kernel_resume_autonomy_session.asyncio(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.resume_autonomy_session_async returned no parsed response")
        return out

    def terminate_autonomy_session(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelTerminateAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = core_kernel_terminate_autonomy_session.sync(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.terminate_autonomy_session returned no parsed response")
        return out

    async def terminate_autonomy_session_async(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelTerminateAutonomySessionResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: AutonomySessionActionRequest | Unset = UNSET
        if reason is not None:
            body = AutonomySessionActionRequest.from_dict({"reason": reason})
        out = await core_kernel_terminate_autonomy_session.asyncio(session_id=session_id, client=c, body=body)
        if out is None:
            raise RuntimeError("kernel.terminate_autonomy_session_async returned no parsed response")
        return out

    async def append_session_event_async(
        self,
        *,
        session_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
        tenant_id: str | None = None,
    ) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        d: dict[str, Any] = {"type": event_type, "payload": payload or {}}
        if timestamp is not None:
            d["timestamp"] = timestamp
        ev = SessionEvent.from_dict(d)
        out = await core_kernel_append_session_event.asyncio(session_id=session_id, client=c, body=ev)
        if out is None:
            raise RuntimeError("kernel.append_session_event returned no parsed response")
        return out

    def list_escalations(
        self,
        *,
        status: str | None = None,
        session_id: str | None = None,
        trace_id: UUID | str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelListEscalationsResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        tid: UUID | Unset = UNSET
        if trace_id:
            tid = UUID(str(trace_id))
        out = core_kernel_list_escalations.sync(
            client=c,
            status=(status if status is not None else UNSET),
            session_id=(session_id if session_id is not None else UNSET),
            trace_id=tid,
            limit=(limit if limit is not None else UNSET),
        )
        if out is None:
            raise RuntimeError("kernel.list_escalations returned no parsed response")
        return out

    async def list_escalations_async(
        self,
        *,
        status: str | None = None,
        session_id: str | None = None,
        trace_id: UUID | str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelListEscalationsResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        tid: UUID | Unset = UNSET
        if trace_id:
            tid = UUID(str(trace_id))
        out = await core_kernel_list_escalations.asyncio(
            client=c,
            status=(status if status is not None else UNSET),
            session_id=(session_id if session_id is not None else UNSET),
            trace_id=tid,
            limit=(limit if limit is not None else UNSET),
        )
        if out is None:
            raise RuntimeError("kernel.list_escalations returned no parsed response")
        return out

    def get_escalation(
        self,
        *,
        escalation_id: UUID | str,
        tenant_id: str | None = None,
    ) -> KernelGetEscalationResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_get_escalation.sync(escalation_id=UUID(str(escalation_id)), client=c)
        if out is None:
            raise RuntimeError("kernel.get_escalation returned no parsed response")
        return out

    async def get_escalation_async(
        self,
        *,
        escalation_id: UUID | str,
        tenant_id: str | None = None,
    ) -> KernelGetEscalationResponse200:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_get_escalation.asyncio(escalation_id=UUID(str(escalation_id)), client=c)
        if out is None:
            raise RuntimeError("kernel.get_escalation returned no parsed response")
        return out

    def resolve_escalation(
        self,
        *,
        escalation_id: UUID | str,
        status: str,
        tenant_id: str | None = None,
    ) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_resolve_escalation.sync(
            escalation_id=UUID(str(escalation_id)),
            client=c,
            body=KernelResolveEscalationBody.from_dict({"status": status}),
        )
        if out is None:
            raise RuntimeError("kernel.resolve_escalation returned no parsed response")
        return out

    def list_api_keys(self, *, tenant_id: str | None = None) -> list[APIKeyRecord]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/kernel/api-keys")
        resp.raise_for_status()
        data = resp.json()
        keys = data.get("keys") or []
        return [APIKeyRecord.from_dict(k) for k in keys]

    async def list_api_keys_async(self, *, tenant_id: str | None = None) -> list[APIKeyRecord]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/kernel/api-keys")
        resp.raise_for_status()
        data = resp.json()
        keys = data.get("keys") or []
        return [APIKeyRecord.from_dict(k) for k in keys]

    def create_api_key(
        self,
        *,
        name: str,
        scopes: list[str] | None = None,
        expires_at: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[APIKeyRecord, str]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"name": name}
        if scopes is not None:
            body["scopes"] = scopes
        if expires_at is not None:
            body["expires_at"] = expires_at
        resp = c.get_httpx_client().post("/v1/kernel/api-keys", json=body)
        resp.raise_for_status()
        data = resp.json()
        rec = APIKeyRecord.from_dict(data.get("key") or {})
        secret = str(data.get("secret") or "")
        return rec, secret

    async def create_api_key_async(
        self,
        *,
        name: str,
        scopes: list[str] | None = None,
        expires_at: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[APIKeyRecord, str]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"name": name}
        if scopes is not None:
            body["scopes"] = scopes
        if expires_at is not None:
            body["expires_at"] = expires_at
        resp = await c.get_async_httpx_client().post("/v1/kernel/api-keys", json=body)
        resp.raise_for_status()
        data = resp.json()
        rec = APIKeyRecord.from_dict(data.get("key") or {})
        secret = str(data.get("secret") or "")
        return rec, secret

    def revoke_api_key(self, *, key_id: str, tenant_id: str | None = None) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post(f"/v1/kernel/api-keys/{key_id}/revoke", json={})
        resp.raise_for_status()
        out = resp.json()
        return OkResponse.from_dict(out)

    async def revoke_api_key_async(self, *, key_id: str, tenant_id: str | None = None) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post(f"/v1/kernel/api-keys/{key_id}/revoke", json={})
        resp.raise_for_status()
        out = resp.json()
        return OkResponse.from_dict(out)

    async def resolve_escalation_async(
        self,
        *,
        escalation_id: UUID | str,
        status: str,
        tenant_id: str | None = None,
    ) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_resolve_escalation.asyncio(
            escalation_id=UUID(str(escalation_id)),
            client=c,
            body=KernelResolveEscalationBody.from_dict({"status": status}),
        )
        if out is None:
            raise RuntimeError("kernel.resolve_escalation returned no parsed response")
        return out

    def get_runtime_metrics(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_get_runtime_metrics.sync(client=c)
        if out is None:
            raise RuntimeError("kernel.get_runtime_metrics returned no parsed response")
        return out.to_dict()

    async def get_runtime_metrics_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_get_runtime_metrics.asyncio(client=c)
        if out is None:
            raise RuntimeError("kernel.get_runtime_metrics returned no parsed response")
        return out.to_dict()

    def get_cost_summary(
        self,
        *,
        group_by: str = "day",
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostSummaryResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"group_by": group_by}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = c.get_httpx_client().get("/v1/kernel/cost/summary", params=params)
        resp.raise_for_status()
        return KernelCostSummaryResponse.model_validate(resp.json() or {})

    async def get_cost_summary_async(
        self,
        *,
        group_by: str = "day",
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostSummaryResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"group_by": group_by}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = await c.get_async_httpx_client().get("/v1/kernel/cost/summary", params=params)
        resp.raise_for_status()
        return KernelCostSummaryResponse.model_validate(resp.json() or {})

    def list_cost_events(
        self,
        *,
        trace_id: str | None = None,
        session_id: str | None = None,
        actor: str | None = None,
        agent_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        tool: str | None = None,
        kind: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostEventsResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if trace_id:
            params["trace_id"] = trace_id
        if session_id:
            params["session_id"] = session_id
        if actor:
            params["actor"] = actor
        if agent_id:
            params["agent_id"] = agent_id
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model
        if tool:
            params["tool"] = tool
        if kind:
            params["kind"] = kind
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/kernel/cost/events", params=params)
        resp.raise_for_status()
        return KernelCostEventsResponse.model_validate(resp.json() or {})

    async def list_cost_events_async(
        self,
        *,
        trace_id: str | None = None,
        session_id: str | None = None,
        actor: str | None = None,
        agent_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        tool: str | None = None,
        kind: str | None = None,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostEventsResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if trace_id:
            params["trace_id"] = trace_id
        if session_id:
            params["session_id"] = session_id
        if actor:
            params["actor"] = actor
        if agent_id:
            params["agent_id"] = agent_id
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model
        if tool:
            params["tool"] = tool
        if kind:
            params["kind"] = kind
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/kernel/cost/events", params=params)
        resp.raise_for_status()
        return KernelCostEventsResponse.model_validate(resp.json() or {})

    def get_cost_avoided(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostAvoidedResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = c.get_httpx_client().get("/v1/kernel/cost/avoided", params=params)
        resp.raise_for_status()
        return KernelCostAvoidedResponse.model_validate(resp.json() or {})

    async def get_cost_avoided_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostAvoidedResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = await c.get_async_httpx_client().get("/v1/kernel/cost/avoided", params=params)
        resp.raise_for_status()
        return KernelCostAvoidedResponse.model_validate(resp.json() or {})

    def list_cost_anomalies(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostAnomaliesResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = c.get_httpx_client().get("/v1/kernel/cost/anomalies", params=params)
        resp.raise_for_status()
        return KernelCostAnomaliesResponse.model_validate(resp.json() or {})

    async def list_cost_anomalies_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> KernelCostAnomaliesResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = await c.get_async_httpx_client().get("/v1/kernel/cost/anomalies", params=params)
        resp.raise_for_status()
        return KernelCostAnomaliesResponse.model_validate(resp.json() or {})

    def get_otel_export_config(self, *, tenant_id: str | None = None) -> OtelExportConfig:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/integrations/otel/config")
        resp.raise_for_status()
        return OtelExportConfig.model_validate(resp.json() or {})

    async def get_otel_export_config_async(self, *, tenant_id: str | None = None) -> OtelExportConfig:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/integrations/otel/config")
        resp.raise_for_status()
        return OtelExportConfig.model_validate(resp.json() or {})

    def update_otel_export_config(
        self,
        *,
        config: dict[str, Any],
        tenant_id: str | None = None,
    ) -> OtelExportConfig:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().put("/v1/integrations/otel/config", json=config)
        resp.raise_for_status()
        return OtelExportConfig.model_validate(resp.json() or {})

    async def update_otel_export_config_async(
        self,
        *,
        config: dict[str, Any],
        tenant_id: str | None = None,
    ) -> OtelExportConfig:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().put("/v1/integrations/otel/config", json=config)
        resp.raise_for_status()
        return OtelExportConfig.model_validate(resp.json() or {})

    def get_otel_export_status(self, *, tenant_id: str | None = None) -> OtelExportStatus:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/integrations/otel/status")
        resp.raise_for_status()
        return OtelExportStatus.model_validate(resp.json() or {})

    async def get_otel_export_status_async(self, *, tenant_id: str | None = None) -> OtelExportStatus:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/integrations/otel/status")
        resp.raise_for_status()
        return OtelExportStatus.model_validate(resp.json() or {})

    def test_otel_export(self, *, tenant_id: str | None = None) -> OtelExportTestResult:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post("/v1/integrations/otel/test", json={})
        resp.raise_for_status()
        return OtelExportTestResult.model_validate(resp.json() or {})

    async def test_otel_export_async(self, *, tenant_id: str | None = None) -> OtelExportTestResult:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post("/v1/integrations/otel/test", json={})
        resp.raise_for_status()
        return OtelExportTestResult.model_validate(resp.json() or {})

    def purge_wasm_cache(self, *, tenant_id: str | None = None) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_kernel_purge_wasm_cache.sync(client=c)
        if out is None:
            raise RuntimeError("kernel.purge_wasm_cache returned no parsed response")
        return out

    async def purge_wasm_cache_async(self, *, tenant_id: str | None = None) -> OkResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_kernel_purge_wasm_cache.asyncio(client=c)
        if out is None:
            raise RuntimeError("kernel.purge_wasm_cache returned no parsed response")
        return out

    def events_stream(
        self,
        *,
        tenant_id: str | None = None,
        last_event_id: str | None = None,
        event_filter: str | None = None,
        timeout_seconds: float | None = None,
    ) -> Iterator[str]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        headers: dict[str, str] = {"Accept": "text/event-stream"}
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id
        params: dict[str, Any] = {}
        if event_filter:
            params["type"] = event_filter
        if timeout_seconds is None:
            timeout_seconds = 300.0

        with c.get_httpx_client().stream(
            "GET",
            "/v1/events/stream",
            params=params,
            headers=headers,
            timeout=timeout_seconds,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield line

    def create_notification_channel(
        self,
        *,
        kind: str,
        name: str,
        config: dict[str, Any] | None = None,
        enabled: bool | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"kind": kind, "name": name}
        if config is not None:
            body["config"] = config
        if enabled is not None:
            body["enabled"] = enabled
        resp = c.get_httpx_client().post("/v1/integrations/channels", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def create_notification_channel_async(
        self,
        *,
        kind: str,
        name: str,
        config: dict[str, Any] | None = None,
        enabled: bool | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"kind": kind, "name": name}
        if config is not None:
            body["config"] = config
        if enabled is not None:
            body["enabled"] = enabled
        resp = await c.get_async_httpx_client().post("/v1/integrations/channels", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def list_notification_channels(
        self,
        *,
        kind: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if kind:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/integrations/channels", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("channels") or []

    async def list_notification_channels_async(
        self,
        *,
        kind: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[dict[str, Any]]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if kind:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/integrations/channels", params=params)
        resp.raise_for_status()
        payload = resp.json() or {}
        return payload.get("channels") or []

    def get_notification_channel(self, channel_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/integrations/channels/{channel_id}")
        resp.raise_for_status()
        return resp.json() or {}

    async def get_notification_channel_async(self, channel_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/integrations/channels/{channel_id}")
        resp.raise_for_status()
        return resp.json() or {}

    def update_notification_channel(
        self,
        channel_id: str,
        *,
        patch: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().put(f"/v1/integrations/channels/{channel_id}", json=patch)
        resp.raise_for_status()
        return resp.json() or {}

    async def update_notification_channel_async(
        self,
        channel_id: str,
        *,
        patch: dict[str, Any],
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().put(f"/v1/integrations/channels/{channel_id}", json=patch)
        resp.raise_for_status()
        return resp.json() or {}

    def delete_notification_channel(self, channel_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().delete(f"/v1/integrations/channels/{channel_id}")
        resp.raise_for_status()
        return resp.json() or {}

    async def delete_notification_channel_async(
        self,
        channel_id: str,
        *,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().delete(f"/v1/integrations/channels/{channel_id}")
        resp.raise_for_status()
        return resp.json() or {}

    def test_notification_channel(
        self,
        channel_id: str,
        *,
        message: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if message:
            body["message"] = message
        resp = c.get_httpx_client().post(f"/v1/integrations/channels/{channel_id}/test", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def test_notification_channel_async(
        self,
        channel_id: str,
        *,
        message: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if message:
            body["message"] = message
        resp = await c.get_async_httpx_client().post(f"/v1/integrations/channels/{channel_id}/test", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def validate_notification_channel_config(
        self,
        *,
        kind: str,
        config: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> bool:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"kind": kind}
        if config is not None:
            body["config"] = config
        resp = c.get_httpx_client().post("/v1/integrations/channels/validate", json=body)
        resp.raise_for_status()
        payload = resp.json() or {}
        return bool(payload.get("ok"))

    async def validate_notification_channel_config_async(
        self,
        *,
        kind: str,
        config: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> bool:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"kind": kind}
        if config is not None:
            body["config"] = config
        resp = await c.get_async_httpx_client().post("/v1/integrations/channels/validate", json=body)
        resp.raise_for_status()
        payload = resp.json() or {}
        return bool(payload.get("ok"))

    def integrations_health(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/integrations/health")
        resp.raise_for_status()
        return resp.json() or {}

    async def integrations_health_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/integrations/health")
        resp.raise_for_status()
        return resp.json() or {}

    def export_datadog(
        self,
        *,
        api_key: str,
        app_key: str | None = None,
        api_base_url: str | None = None,
        site: str | None = None,
        metric_prefix: str | None = None,
        include_events: bool | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"api_key": api_key}
        if app_key is not None:
            body["app_key"] = app_key
        if api_base_url is not None:
            body["api_base_url"] = api_base_url
        if site is not None:
            body["site"] = site
        if metric_prefix is not None:
            body["metric_prefix"] = metric_prefix
        if include_events is not None:
            body["include_events"] = include_events
        if limit is not None:
            body["limit"] = limit
        resp = c.get_httpx_client().post("/v1/integrations/datadog/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def export_datadog_async(
        self,
        *,
        api_key: str,
        app_key: str | None = None,
        api_base_url: str | None = None,
        site: str | None = None,
        metric_prefix: str | None = None,
        include_events: bool | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"api_key": api_key}
        if app_key is not None:
            body["app_key"] = app_key
        if api_base_url is not None:
            body["api_base_url"] = api_base_url
        if site is not None:
            body["site"] = site
        if metric_prefix is not None:
            body["metric_prefix"] = metric_prefix
        if include_events is not None:
            body["include_events"] = include_events
        if limit is not None:
            body["limit"] = limit
        resp = await c.get_async_httpx_client().post("/v1/integrations/datadog/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def export_siem(
        self,
        *,
        export_format: str = "JSON",
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        destination: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"format": export_format}
        if from_time:
            body["from"] = from_time
        if to_time:
            body["to"] = to_time
        if limit is not None:
            body["limit"] = limit
        if destination is not None:
            body["destination"] = destination
        resp = c.get_httpx_client().post("/v1/integrations/siem/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def export_siem_async(
        self,
        *,
        export_format: str = "JSON",
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        destination: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"format": export_format}
        if from_time:
            body["from"] = from_time
        if to_time:
            body["to"] = to_time
        if limit is not None:
            body["limit"] = limit
        if destination is not None:
            body["destination"] = destination
        resp = await c.get_async_httpx_client().post("/v1/integrations/siem/export", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def soc2_report(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = c.get_httpx_client().get("/v1/compliance/reports/soc2", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    async def soc2_report_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = await c.get_async_httpx_client().get("/v1/compliance/reports/soc2", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    def compliance_control_evidence_report(
        self,
        *,
        framework: str = "SOC2",
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"framework": framework}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = c.get_httpx_client().get("/v1/compliance/evidence/controls", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    async def compliance_control_evidence_report_async(
        self,
        *,
        framework: str = "SOC2",
        from_time: str | None = None,
        to_time: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"framework": framework}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        resp = await c.get_async_httpx_client().get("/v1/compliance/evidence/controls", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    def get_chronos_ingest(self, ingest_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/kernel/chronos/ingest/{ingest_id}")
        resp.raise_for_status()
        return resp.json() or {}

    async def get_chronos_ingest_async(self, ingest_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/kernel/chronos/ingest/{ingest_id}")
        resp.raise_for_status()
        return resp.json() or {}

    def jsonrpc(
        self,
        *,
        method: str,
        params: Any | None = None,
        request_id: Any | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if request_id is not None:
            body["id"] = request_id
        resp = c.get_httpx_client().post("/v1/kernel/jsonrpc", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def jsonrpc_async(
        self,
        *,
        method: str,
        params: Any | None = None,
        request_id: Any | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if request_id is not None:
            body["id"] = request_id
        resp = await c.get_async_httpx_client().post("/v1/kernel/jsonrpc", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def mcp(
        self,
        *,
        method: str,
        params: Any | None = None,
        request_id: Any | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if request_id is not None:
            body["id"] = request_id
        resp = c.get_httpx_client().post("/v1/kernel/mcp", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def mcp_async(
        self,
        *,
        method: str,
        params: Any | None = None,
        request_id: Any | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if request_id is not None:
            body["id"] = request_id
        resp = await c.get_async_httpx_client().post("/v1/kernel/mcp", json=body)
        resp.raise_for_status()
        return resp.json() or {}
