from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sentinos_core import AuthenticatedClient, Client
from sentinos_core.api.default import (
    chronos_create_snapshot as core_chronos_create_snapshot,
)
from sentinos_core.api.default import (
    chronos_get_ingest_status as core_chronos_get_ingest_status,
)
from sentinos_core.api.default import (
    chronos_get_snapshot as core_chronos_get_snapshot,
)
from sentinos_core.api.default import (
    chronos_ingest_event as core_chronos_ingest_event,
)
from sentinos_core.api.default import (
    chronos_ingest_traces as core_chronos_ingest_traces,
)
from sentinos_core.models.chronos_ingest_accepted_response import ChronosIngestAcceptedResponse
from sentinos_core.models.chronos_ingest_event_body import ChronosIngestEventBody
from sentinos_core.models.chronos_ingest_traces_schema import ChronosIngestTracesSchema
from sentinos_core.models.chronos_query_response import ChronosQueryResponse
from sentinos_core.models.chronos_snapshot_create_response import ChronosSnapshotCreateResponse
from sentinos_core.models.chronos_snapshot_request import ChronosSnapshotRequest
from sentinos_core.models.chronos_snapshot_schema import ChronosSnapshotSchema
from sentinos_core.models.decision_trace_schema import DecisionTraceSchema
from sentinos_core.models.error_response import ErrorResponse

from .models.decision_trace import DecisionTrace
from .models.snapshot import Snapshot


@dataclass
class ChronosClient:
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
    def _normalize_query_payload(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        for k in ("hits", "ranking", "nodes", "edges"):
            if normalized.get(k) is None:
                normalized[k] = []
        return normalized

    def create_snapshot(
        self,
        *,
        anchors: list[str],
        depth: int = 2,
        valid_time: str | None = None,
        include_decision_traces: bool = False,
        tenant_id: str | None = None,
    ) -> ChronosSnapshotCreateResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        d: dict[str, Any] = {
            "tenant_id": t,
            "anchors": anchors,
            "depth": depth,
            "include_decision_traces": include_decision_traces,
        }
        if valid_time is not None:
            d["valid_time"] = valid_time
        body = ChronosSnapshotRequest.from_dict(d)
        out = core_chronos_create_snapshot.sync(client=c, body=body)
        if out is None:
            raise RuntimeError("chronos.create_snapshot returned no parsed response")
        return out

    async def create_snapshot_async(self, **kwargs: Any) -> ChronosSnapshotCreateResponse:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        d: dict[str, Any] = {
            "tenant_id": t,
            "anchors": kwargs["anchors"],
            "depth": kwargs.get("depth", 2),
            "include_decision_traces": kwargs.get("include_decision_traces", False),
        }
        if kwargs.get("valid_time") is not None:
            d["valid_time"] = kwargs["valid_time"]
        body = ChronosSnapshotRequest.from_dict(d)
        out = await core_chronos_create_snapshot.asyncio(client=c, body=body)
        if out is None:
            raise RuntimeError("chronos.create_snapshot returned no parsed response")
        return out

    def get_snapshot(self, *, snapshot_id: str, tenant_id: str | None = None) -> Snapshot:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_chronos_get_snapshot.sync(snapshot_id=snapshot_id, client=c)
        if out is None:
            raise RuntimeError("chronos.get_snapshot returned no parsed response")
        return Snapshot.from_core(out)

    async def get_snapshot_async(self, *, snapshot_id: str, tenant_id: str | None = None) -> Snapshot:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_chronos_get_snapshot.asyncio(snapshot_id=snapshot_id, client=c)
        if out is None:
            raise RuntimeError("chronos.get_snapshot returned no parsed response")
        return Snapshot.from_core(out)

    def get_snapshot_legacy(
        self,
        *,
        anchor: str,
        ts: str | None = None,
        depth: int | None = None,
        include_decision_traces: bool | None = None,
        tenant_id: str | None = None,
    ) -> Snapshot:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(
            "/v1/chronos/snapshot",
            params={
                "anchor": anchor,
                "ts": ts,
                "depth": depth,
                "include_decision_traces": include_decision_traces,
            },
        )
        resp.raise_for_status()
        return Snapshot.from_core(ChronosSnapshotSchema.from_dict(resp.json()))

    async def get_snapshot_legacy_async(
        self,
        *,
        anchor: str,
        ts: str | None = None,
        depth: int | None = None,
        include_decision_traces: bool | None = None,
        tenant_id: str | None = None,
    ) -> Snapshot:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {"anchor": anchor}
        if ts is not None:
            params["ts"] = ts
        if depth is not None:
            params["depth"] = depth
        if include_decision_traces is not None:
            params["include_decision_traces"] = include_decision_traces
        resp = await c.get_async_httpx_client().get("/v1/chronos/snapshot", params=params)
        resp.raise_for_status()
        return Snapshot.from_core(ChronosSnapshotSchema.from_dict(resp.json()))

    def query(
        self,
        *,
        query: str,
        depth: int = 2,
        limit: int = 20,
        include_decision_traces: bool = False,
        tenant_id: str | None = None,
    ) -> ChronosQueryResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = {
            "tenant_id": t,
            "query": query,
            "depth": depth,
            "limit": limit,
            "include_decision_traces": include_decision_traces,
        }
        resp = c.get_httpx_client().post("/v1/chronos/query", json=body)
        resp.raise_for_status()
        payload = self._normalize_query_payload(resp.json() or {})
        return ChronosQueryResponse.from_dict(payload)

    async def query_async(self, **kwargs: Any) -> ChronosQueryResponse:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        body = {
            "tenant_id": t,
            "query": kwargs["query"],
            "depth": kwargs.get("depth", 2),
            "limit": kwargs.get("limit", 20),
            "include_decision_traces": kwargs.get("include_decision_traces", False),
        }
        resp = await c.get_async_httpx_client().post("/v1/chronos/query", json=body)
        resp.raise_for_status()
        payload = self._normalize_query_payload(resp.json() or {})
        return ChronosQueryResponse.from_dict(payload)

    def ingest_traces(
        self,
        *,
        traces: list[DecisionTraceSchema | DecisionTrace | dict[str, Any]],
        ingest_id: str | None = None,
        tenant_id: str | None = None,
    ) -> ChronosIngestAcceptedResponse | ErrorResponse:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        iid = ingest_id or str(uuid4())
        trace_objs: list[dict[str, Any]] = []
        for tr in traces:
            if isinstance(tr, DecisionTraceSchema):
                trace_objs.append(tr.to_dict())
            elif isinstance(tr, DecisionTrace):
                trace_objs.append(tr.model_dump(mode="json"))
            else:
                trace_objs.append(tr)
        body = ChronosIngestTracesSchema.from_dict({"tenant_id": t, "ingest_id": iid, "traces": trace_objs})
        out = core_chronos_ingest_traces.sync(client=c, body=body)
        if out is None:
            raise RuntimeError("chronos.ingest_traces returned no parsed response")
        return out

    async def ingest_traces_async(self, **kwargs: Any) -> ChronosIngestAcceptedResponse | ErrorResponse:
        t = self._require_tenant(kwargs.get("tenant_id"))
        c = self._core_with_headers(tenant_id=t)
        iid = kwargs.get("ingest_id") or str(uuid4())
        trace_objs: list[dict[str, Any]] = []
        for tr in kwargs["traces"]:
            if isinstance(tr, DecisionTraceSchema):
                trace_objs.append(tr.to_dict())
            elif isinstance(tr, DecisionTrace):
                trace_objs.append(tr.model_dump(mode="json"))
            else:
                trace_objs.append(tr)
        body = ChronosIngestTracesSchema.from_dict({"tenant_id": t, "ingest_id": iid, "traces": trace_objs})
        out = await core_chronos_ingest_traces.asyncio(client=c, body=body)
        if out is None:
            raise RuntimeError("chronos.ingest_traces returned no parsed response")
        return out

    def observability_traces(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tool: str | None = None,
        decision: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if tool:
            params["tool"] = tool
        if decision:
            params["decision"] = decision
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/chronos/observability/traces", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_traces_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        tool: str | None = None,
        decision: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time
        if tool:
            params["tool"] = tool
        if decision:
            params["decision"] = decision
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/chronos/observability/traces", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    def analyze_traces(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        anomaly_threshold: float | None = None,
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
        if anomaly_threshold is not None:
            body["anomaly_threshold"] = anomaly_threshold
        resp = c.get_httpx_client().post("/v1/chronos/observability/traces/analyze", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def analyze_traces_async(
        self,
        *,
        from_time: str | None = None,
        to_time: str | None = None,
        limit: int | None = None,
        anomaly_threshold: float | None = None,
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
        if anomaly_threshold is not None:
            body["anomaly_threshold"] = anomaly_threshold
        resp = await c.get_async_httpx_client().post("/v1/chronos/observability/traces/analyze", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def observability_anomalies(
        self,
        *,
        threshold: float | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if threshold is not None:
            params["threshold"] = threshold
        resp = c.get_httpx_client().get("/v1/chronos/observability/anomalies", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_anomalies_async(
        self,
        *,
        threshold: float | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if threshold is not None:
            params["threshold"] = threshold
        resp = await c.get_async_httpx_client().get("/v1/chronos/observability/anomalies", params=params)
        resp.raise_for_status()
        return resp.json() or {}

    def observability_anomaly_stats(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/chronos/observability/anomalies/stats")
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_anomaly_stats_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/chronos/observability/anomalies/stats")
        resp.raise_for_status()
        return resp.json() or {}

    def observability_compliance(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/chronos/observability/compliance")
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_compliance_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/chronos/observability/compliance")
        resp.raise_for_status()
        return resp.json() or {}

    def observability_compliance_report(
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
        resp = c.get_httpx_client().post("/v1/chronos/observability/compliance/report", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_compliance_report_async(
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
        resp = await c.get_async_httpx_client().post("/v1/chronos/observability/compliance/report", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def observability_patterns(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/chronos/observability/patterns")
        resp.raise_for_status()
        return resp.json() or {}

    async def observability_patterns_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/chronos/observability/patterns")
        resp.raise_for_status()
        return resp.json() or {}

    def entity_risk(self, entity_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/chronos/observability/entities/{entity_id}/risk")
        resp.raise_for_status()
        return resp.json() or {}

    async def entity_risk_async(self, entity_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/chronos/observability/entities/{entity_id}/risk")
        resp.raise_for_status()
        return resp.json() or {}

    def get_ingest_status(self, ingest_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = core_chronos_get_ingest_status.sync(ingest_id=UUID(str(ingest_id)), client=c)
        if out is None:
            raise RuntimeError("chronos.get_ingest_status returned no parsed response")
        return out.to_dict()

    async def get_ingest_status_async(self, ingest_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        out = await core_chronos_get_ingest_status.asyncio(ingest_id=UUID(str(ingest_id)), client=c)
        if out is None:
            raise RuntimeError("chronos.get_ingest_status returned no parsed response")
        return out.to_dict()

    def connector_health(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get("/v1/chronos/connectors/health")
        resp.raise_for_status()
        return resp.json() or {}

    async def connector_health_async(self, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get("/v1/chronos/connectors/health")
        resp.raise_for_status()
        return resp.json() or {}

    def ingest_event(self, *, event: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(event)
        body.setdefault("tenant_id", t)
        out = core_chronos_ingest_event.sync(client=c, body=ChronosIngestEventBody.from_dict(body))
        if out is None:
            raise RuntimeError("chronos.ingest_event returned no parsed response")
        return out.to_dict()

    async def ingest_event_async(self, *, event: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(event)
        body.setdefault("tenant_id", t)
        out = await core_chronos_ingest_event.asyncio(client=c, body=ChronosIngestEventBody.from_dict(body))
        if out is None:
            raise RuntimeError("chronos.ingest_event returned no parsed response")
        return out.to_dict()

    def ingest_connector_event(
        self, *, source_id: str, event: dict[str, Any], tenant_id: str | None = None
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(event)
        body.setdefault("tenant_id", t)
        resp = c.get_httpx_client().post(f"/v1/chronos/connectors/{source_id}/ingest", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def ingest_connector_event_async(
        self, *, source_id: str, event: dict[str, Any], tenant_id: str | None = None
    ) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(event)
        body.setdefault("tenant_id", t)
        resp = await c.get_async_httpx_client().post(f"/v1/chronos/connectors/{source_id}/ingest", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    def reprocess_traces(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(request)
        body.setdefault("tenant_id", t)
        resp = c.get_httpx_client().post("/v1/reprocess", json=body)
        resp.raise_for_status()
        return resp.json() or {}

    async def reprocess_traces_async(self, *, request: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body = dict(request)
        body.setdefault("tenant_id", t)
        resp = await c.get_async_httpx_client().post("/v1/reprocess", json=body)
        resp.raise_for_status()
        return resp.json() or {}
