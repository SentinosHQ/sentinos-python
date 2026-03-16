from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from sentinos.arbiter import ArbiterClient
from sentinos.chronos import ChronosClient
from sentinos.kernel import KernelClient
from sentinos.marketplace import MarketplaceClient
from sentinos.traces import TracesClient


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200
    raw_content: bytes | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self.payload

    @property
    def content(self) -> bytes:
        if self.raw_content is not None:
            return self.raw_content
        return json.dumps(self.payload).encode("utf-8")

    def iter_lines(self) -> list[str]:
        lines = self.payload.get("lines") or []
        return [str(x) for x in lines]


class FakeStreamResponse(FakeResponse):
    def __enter__(self) -> FakeStreamResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("GET", path, params, None))
        if path == "/v1/trace/search":
            return FakeResponse({"next_cursor": "", "traces": None})
        if path.startswith("/v1/traces/") and path.endswith("/lineage"):
            return FakeResponse(
                {
                    "trace_id": "11111111-1111-1111-1111-111111111111",
                    "summary": {
                        "artifact_count": 4,
                        "side_effect_count": 3,
                        "blocked_count": 1,
                        "kinds": {"file": 1, "connector": 1, "domain": 1, "handoff": 1},
                        "top_domains": ["api.stripe.com"],
                        "top_connectors": ["stripe.refund"],
                        "top_outputs": ["refund.result"],
                        "has_handoff": True,
                        "has_writes": True,
                        "has_blocked_side_effects": True,
                    },
                    "artifacts": [
                        {
                            "artifact_id": "art-1",
                            "kind": "file",
                            "label": "refund_request.json",
                            "locator": "s3://acme/refund_request.json",
                            "status": "consumed",
                            "chronos_anchor": "file:refund_request.json",
                        },
                        {
                            "artifact_id": "art-2",
                            "kind": "domain",
                            "label": "api.stripe.com",
                            "locator": "https://api.stripe.com/v1/refunds",
                            "status": "blocked",
                            "metadata": {"related_trace_id": "22222222-2222-2222-2222-222222222222"},
                        },
                    ],
                    "events": [
                        {
                            "event_id": "evt-lineage-1",
                            "artifact_id": "art-1",
                            "action": "read",
                            "actor": "finance_bot",
                            "tool": "stripe.refund",
                            "timestamp": "2026-01-01T00:00:00Z",
                        },
                        {
                            "event_id": "evt-lineage-2",
                            "artifact_id": "art-2",
                            "action": "blocked",
                            "actor": "finance_bot",
                            "tool": "stripe.refund",
                            "timestamp": "2026-01-01T00:00:01Z",
                        },
                    ],
                }
            )
        if path == "/v1/trace/observability/distributed":
            return FakeResponse(
                {
                    "traces": [
                        {
                            "trace_id": "11111111-1111-1111-1111-111111111111",
                            "tenant_id": "acme",
                            "distributed_trace_id": "dd-trace-1",
                            "created_at": "2026-01-01T00:00:00Z",
                            "agent_id": "agent-1",
                            "policy_id": "policy-1",
                            "decision": "ALLOW",
                            "distributed_span_id": "span-1",
                        }
                    ]
                }
            )
        if path.startswith("/v1/trace/") and path.endswith("/verify"):
            return FakeResponse({"ok": True})
        if path.startswith("/v1/trace/") and path.endswith("/ledger"):
            return FakeResponse(
                {
                    "trace_id": "11111111-1111-1111-1111-111111111111",
                    "tenant_id": "acme",
                    "canonical_match": True,
                    "chain_match": True,
                    "chain_continuity_ok": True,
                    "verified": True,
                    "reason": "ok",
                }
            )
        if path == "/v1/trace/retention":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "trace_days": 30,
                    "export_days": 90,
                    "ledger_days": 365,
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            )
        if path.startswith("/v1/trace/export/job/"):
            return FakeResponse({"job_id": "j1", "status": "done"})
        if path == "/v1/arbitr/policies":
            return FakeResponse({"policies": [{"policy_id": "p1"}]})
        if path == "/v1/arbitr/policies/active":
            return FakeResponse({"keys": ["p1@v1"]})
        if path.startswith("/v1/arbitr/tenants/"):
            return FakeResponse({"tenant_id": "acme", "config": {}})
        if path.startswith("/v1/arbitr/simulate/"):
            return FakeResponse({"job_id": "sim-1", "status": "done"})
        if "/bundle" in path:
            return FakeResponse({"bundle": "ok"}, raw_content=b"bundle-bytes")
        if path == "/v1/arbitr/governance/dashboard":
            return FakeResponse({"violations_24h": 0})
        if path == "/v1/arbitr/governance/violations":
            return FakeResponse({"violations": [{"trace_id": "t1"}]})
        if path == "/v1/chronos/observability/traces":
            return FakeResponse({"traces": []})
        if path == "/v1/chronos/observability/anomalies":
            return FakeResponse({"anomalies": []})
        if path == "/v1/chronos/observability/anomalies/stats":
            return FakeResponse({"count": 0})
        if path == "/v1/chronos/observability/compliance":
            return FakeResponse({"score": 1.0})
        if path == "/v1/chronos/observability/patterns":
            return FakeResponse({"patterns": []})
        if path == "/v1/chronos/snapshot":
            return FakeResponse({"snapshot_id": "s1", "nodes": [], "edges": []})
        if path.startswith("/v1/chronos/ingest/"):
            return FakeResponse(
                {
                    "ingest": {
                        "ingest_id": "11111111-1111-1111-1111-111111111111",
                        "tenant_id": "acme",
                        "body_hash": "abc123",
                        "status": "accepted",
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:01Z",
                    }
                }
            )
        if path == "/v1/chronos/observability/entities/e1/risk":
            return FakeResponse({"entity_id": "e1", "risk_score": 0.0})
        if path == "/v1/integrations/channels":
            return FakeResponse({"channels": []})
        if path == "/v1/marketplace/packs":
            return FakeResponse(
                {
                    "packs": [
                        {
                            "pack_id": "pack-1",
                            "tenant_id": "acme",
                            "name": "Starter Pack",
                            "description": "Starter",
                            "author": "sentinos",
                            "version": "1.0.0",
                            "verified": True,
                            "tags": ["starter"],
                            "policies": [],
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ]
                }
            )
        if path == "/v1/marketplace/installs":
            return FakeResponse({"installs": []})
        if path.startswith("/v1/marketplace/packs/"):
            return FakeResponse(
                {
                    "pack_id": "pack-1",
                    "tenant_id": "acme",
                    "name": "Starter Pack",
                    "description": "Starter",
                    "author": "sentinos",
                    "version": "1.0.0",
                    "verified": True,
                    "tags": ["starter"],
                    "policies": [],
                    "created_at": "2026-01-01T00:00:00Z",
                }
            )
        if path == "/v1/integrations/health":
            return FakeResponse({"summary": {"healthy": 1}})
        if path == "/v1/integrations/otel/config":
            return FakeResponse(
                {
                    "enabled": True,
                    "endpoint": "https://collector.example.com",
                    "protocol": "http/protobuf",
                    "traces_enabled": True,
                    "metrics_enabled": True,
                    "include_sentinos_extensions": True,
                    "include_internal_service_spans": False,
                    "resource_attributes": {"service.name": "sentinos"},
                    "header_keys_masked": ["authorization"],
                    "deep_link_template": "https://observability.example.com/trace/{trace_id}",
                    "privacy_mode": "policy_enforced",
                }
            )
        if path == "/v1/integrations/otel/status":
            return FakeResponse(
                {
                    "enabled": True,
                    "last_successful_export_at": "2026-01-01T00:00:00Z",
                    "queue_depth": 2,
                    "dropped_batch_count": 1,
                    "traces_exported": 14,
                    "metrics_exported": 14,
                }
            )
        if path == "/v1/compliance/reports/soc2":
            return FakeResponse({"tenant_id": "acme", "metrics": {}})
        if path == "/v1/compliance/evidence/controls":
            framework = str((params or {}).get("framework") or "SOC2").upper()
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "framework": framework,
                    "summary": {"controls_total": 2, "controls_passing": 2, "controls_attention": 0},
                    "controls": [],
                    "bundle_sha256": "abc123",
                }
            )
        if path == "/v1/kernel/cost/summary":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "from": "2026-01-01T00:00:00Z",
                    "to": "2026-01-02T00:00:00Z",
                    "group_by": (params or {}).get("group_by") or "day",
                    "rows": [
                        {
                            "label": "openai/gpt-4.1-mini",
                            "total_usd": 12.4,
                            "reported_total_usd": 10.1,
                            "estimated_total_usd": 2.3,
                            "pricing_source": "mixed",
                            "total_tokens": 420000,
                            "blocked_cost_avoided_usd": 1.2,
                            "blocked_token_avoided": 8000,
                            "trace_count": 23,
                        }
                    ],
                }
            )
        if path == "/v1/kernel/cost/events":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "from": "2026-01-01T00:00:00Z",
                    "to": "2026-01-02T00:00:00Z",
                    "events": [
                        {
                            "event_id": "evt-1",
                            "kind": "llm",
                            "label": "Primary model call",
                            "provider": "openai",
                            "model": "gpt-4.1-mini",
                            "total_tokens": 1420,
                            "reported_usd": 0.031,
                            "pricing_source": "reported",
                        }
                    ],
                }
            )
        if path == "/v1/kernel/cost/avoided":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "from": "2026-01-01T00:00:00Z",
                    "to": "2026-01-02T00:00:00Z",
                    "rows": [
                        {
                            "label": "budget_guardrail",
                            "total_usd": 1.2,
                            "total_tokens": 8000,
                            "event_count": 3,
                        }
                    ],
                }
            )
        if path == "/v1/kernel/cost/anomalies":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "from": "2026-01-01T00:00:00Z",
                    "to": "2026-01-02T00:00:00Z",
                    "anomalies": [
                        {
                            "anomaly_id": "anom-1",
                            "kind": "model_spike",
                            "severity": "high",
                            "dimension": "openai/gpt-4.1-mini",
                            "baseline": 1.4,
                            "observed": 4.7,
                            "delta": 3.3,
                            "trace_id": "11111111-1111-1111-1111-111111111111",
                            "detected_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                }
            )
        return FakeResponse({})

    def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("POST", path, None, json))
        if path == "/v1/trace/export":
            return FakeResponse({"job_id": "j1", "status": "queued"})
        if path.startswith("/v1/trace/") and path.endswith("/replay"):
            return FakeResponse(
                {
                    "trace_id": "11111111-1111-1111-1111-111111111111",
                    "tenant_id": "acme",
                    "replayed_at": "2026-01-01T00:00:00Z",
                    "profile": (json or {}).get("profile", "active_policy_chain"),
                    "policy_source": "original_trace_policy",
                    "snapshot_source": "original_snapshot",
                    "fidelity": "deterministic",
                    "fidelity_reasons": ["Original policy metadata and snapshot were available."],
                    "reconstruction_basis": {
                        "policy_keys": ["sentinos/demo@v1"],
                        "original_policy_key": "sentinos/demo@v1",
                        "original_policy_id": "sentinos/demo@v1",
                        "original_policy_version": "v1",
                        "snapshot_id": "snap-1",
                    },
                    "evidence_export_ready": True,
                    "evidence_export_hints": ["Replay can be exported with ledger and privacy snapshots."],
                    "policy_keys": ["sentinos/demo@v1"],
                    "drift_detected": False,
                    "original": {
                        "decision": "ALLOW",
                        "policy_id": "sentinos/demo@v1",
                        "cost_breakdown": {
                            "total_usd": 0.031,
                            "reported_total_usd": 0.031,
                            "pricing_source": "reported",
                            "provider": "openai",
                            "model": "gpt-4.1-mini",
                            "total_tokens": 1420,
                        },
                        "cost_events": [
                            {
                                "event_id": "evt-1",
                                "kind": "llm",
                                "label": "Primary model call",
                                "provider": "openai",
                                "model": "gpt-4.1-mini",
                                "total_tokens": 1420,
                                "reported_usd": 0.031,
                                "pricing_source": "reported",
                            }
                        ],
                        "checks": [
                            {
                                "key": "tool.stripe_refund",
                                "label": "Tool access: stripe.refund",
                                "category": "tool",
                                "status": "ALLOWED",
                                "reason": "Allowed for finance workflow",
                                "matched": True,
                            }
                        ],
                    },
                    "replay": {
                        "decision": "ALLOW",
                        "policy_id": "sentinos/demo@v1",
                        "cost_breakdown": {
                            "total_usd": 0.044,
                            "estimated_total_usd": 0.044,
                            "pricing_source": "estimated",
                            "provider": "openai",
                            "model": "gpt-4.1-mini",
                            "total_tokens": 1800,
                        },
                        "cost_events": [
                            {
                                "event_id": "evt-2",
                                "kind": "retry",
                                "label": "Replay retry",
                                "provider": "openai",
                                "model": "gpt-4.1-mini",
                                "retry_index": 1,
                                "total_tokens": 1800,
                                "estimated_usd": 0.044,
                                "pricing_source": "estimated",
                            }
                        ],
                        "checks": [
                            {
                                "key": "tool.stripe_refund",
                                "label": "Tool access: stripe.refund",
                                "category": "tool",
                                "status": "ALLOWED",
                                "reason": "Allowed for finance workflow",
                                "matched": True,
                            }
                        ],
                    },
                    "comparison": {
                        "decision_changed": False,
                        "policy_changed": False,
                        "reason_changed": False,
                        "checks_added": 0,
                        "checks_removed": 0,
                        "checks_changed": 0,
                        "cost_changed": True,
                        "total_cost_delta_usd": 0.013,
                        "avoided_cost_delta_usd": 0.0,
                    },
                }
            )
        if path.startswith("/v1/trace/") and path.endswith("/replay/matrix"):
            return FakeResponse(
                {
                    "trace_id": "11111111-1111-1111-1111-111111111111",
                    "tenant_id": "acme",
                    "generated_at": "2026-01-01T00:00:00Z",
                    "entries": [
                        {
                            "profile": "active_policy_chain",
                            "response": {
                                "trace_id": "11111111-1111-1111-1111-111111111111",
                                "tenant_id": "acme",
                                "replayed_at": "2026-01-01T00:00:00Z",
                                "profile": "active_policy_chain",
                                "fidelity": "best_effort",
                                "fidelity_reasons": [
                                    "Original snapshot was unavailable; current policy chain was used."
                                ],
                                "drift_detected": True,
                                "replay": {"decision": "ESCALATE"},
                            },
                        },
                        {
                            "profile": "original_policy_and_snapshot",
                            "response": {
                                "trace_id": "11111111-1111-1111-1111-111111111111",
                                "tenant_id": "acme",
                                "replayed_at": "2026-01-01T00:00:00Z",
                                "profile": "original_policy_and_snapshot",
                                "fidelity": "deterministic",
                                "fidelity_reasons": ["Original policy metadata and snapshot were available."],
                                "drift_detected": False,
                                "replay": {"decision": "ALLOW"},
                            },
                        },
                    ],
                }
            )
        if path.startswith("/v1/trace/") and path.endswith("/replay/export"):
            return FakeResponse(
                {
                    "trace_id": "11111111-1111-1111-1111-111111111111",
                    "tenant_id": "acme",
                    "profile": (json or {}).get("profile", "original_policy_and_snapshot"),
                    "export_job": {
                        "job_id": "job-replay-1",
                        "payload_sha256": "sha256:abc123",
                        "retention_until": "2026-04-01T00:00:00Z",
                    },
                    "replay": {
                        "trace_id": "11111111-1111-1111-1111-111111111111",
                        "tenant_id": "acme",
                        "replayed_at": "2026-01-01T00:00:00Z",
                        "profile": (json or {}).get("profile", "original_policy_and_snapshot"),
                        "policy_source": "original_trace_policy",
                        "snapshot_source": "original_snapshot",
                        "fidelity": "deterministic",
                        "fidelity_reasons": ["Original policy metadata and snapshot were available."],
                        "evidence_export_ready": True,
                        "policy_keys": ["sentinos/demo@v1"],
                        "drift_detected": False,
                        "replay": {"decision": "ALLOW"},
                    },
                }
            )
        if path == "/v1/trace/retention/enforce":
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "dry_run": bool((json or {}).get("dry_run", False)),
                    "traces_cutoff": "2025-01-01T00:00:00Z",
                    "exports_cutoff": "2025-01-01T00:00:00Z",
                    "ledger_cutoff": "2025-01-01T00:00:00Z",
                    "traces_affected": 12,
                    "exports_affected": 3,
                    "ledger_anchors_affected": 0,
                }
            )
        if path == "/v1/chronos/query":
            return FakeResponse(
                {
                    "query_id": "q1",
                    "generated_at": "2026-01-01T00:00:00Z",
                    "hits": None,
                    "ranking": None,
                    "nodes": None,
                    "edges": None,
                }
            )
        if path == "/v1/arbitr/governance/reports":
            return FakeResponse({"report_id": "r1"})
        if path in ("/v1/arbitr/evaluate", "/v1/arbitr/compile"):
            return FakeResponse({"ok": True})
        if path == "/v1/chronos/observability/traces/analyze":
            return FakeResponse({"score": 0.42})
        if path == "/v1/chronos/observability/compliance/report":
            return FakeResponse({"report_id": "c1"})
        if path == "/v1/chronos/ingest":
            return FakeResponse({"ok": True})
        if path == "/v1/reprocess":
            return FakeResponse({"accepted": 2, "reprocessed": 2})
        if path == "/v1/integrations/channels":
            return FakeResponse({"channel_id": "ch1", "kind": "SLACK", "name": "ops"}, status_code=201)
        if path.endswith("/install") and "/v1/marketplace/packs/" in path:
            return FakeResponse({"install_id": "inst-1", "simulation_job_ids": []})
        if path == "/v1/integrations/channels/validate":
            return FakeResponse({"ok": True})
        if path == "/v1/integrations/otel/test":
            return FakeResponse(
                {
                    "ok": True,
                    "message": "collector responded with 202",
                    "trace_delivered": True,
                    "metrics_delivered": True,
                }
            )
        if path == "/v1/integrations/datadog/export":
            return FakeResponse({"exported_metrics": 12})
        if path == "/v1/integrations/siem/export":
            return FakeResponse({"exported_records": 7})
        if path.endswith("/test"):
            return FakeResponse({"success": True})
        return FakeResponse({})

    def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("PUT", path, None, json))
        if path == "/v1/integrations/otel/config":
            payload = dict(json or {})
            payload.setdefault("header_keys_masked", sorted((payload.get("header_values_write_only") or {}).keys()))
            return FakeResponse(payload)
        if path.startswith("/v1/arbitr/tenants/"):
            return FakeResponse({"tenant_id": "acme", "config": json or {}})
        return FakeResponse({"channel_id": "ch1", "enabled": True})

    def patch(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("PATCH", path, None, json))
        if path == "/v1/trace/retention":
            trace_days = int((json or {}).get("trace_days", 30))
            export_days = int((json or {}).get("export_days", 90))
            ledger_days = int((json or {}).get("ledger_days", 365))
            return FakeResponse(
                {
                    "tenant_id": "acme",
                    "trace_days": trace_days,
                    "export_days": export_days,
                    "ledger_days": ledger_days,
                    "updated_at": "2026-01-01T00:00:01Z",
                }
            )
        return FakeResponse({})

    def delete(self, path: str) -> FakeResponse:
        self.calls.append(("DELETE", path, None, None))
        return FakeResponse({"ok": True})

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> FakeResponse:
        _ = headers
        method = method.upper()
        if method == "GET":
            return self.get(url, params=params)
        if method == "POST":
            return self.post(url, json=json)
        if method == "PUT":
            return self.put(url, json=json)
        if method == "PATCH":
            return self.patch(url, json=json)
        if method == "DELETE":
            return self.delete(url)
        raise RuntimeError(f"unsupported method {method}")

    def stream(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> FakeStreamResponse:
        _ = headers, timeout
        self.calls.append((method, path, params, None))
        return FakeStreamResponse({"lines": ["event: alert", "data: {}"]})


class FakeAsyncHTTP:
    def __init__(self, http: FakeHTTP) -> None:
        self._http = http

    async def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.get(path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.post(path, json=json)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.put(path, json=json)

    async def patch(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.patch(path, json=json)

    async def delete(self, path: str) -> FakeResponse:
        return self._http.delete(path)

    async def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> FakeResponse:
        _ = headers
        method = method.upper()
        if method == "GET":
            return self._http.get(url, params=params)
        if method == "POST":
            return self._http.post(url, json=json)
        if method == "PUT":
            return self._http.put(url, json=json)
        if method == "PATCH":
            return self._http.patch(url, json=json)
        if method == "DELETE":
            return self._http.delete(url)
        raise RuntimeError(f"unsupported method {method}")


class FakeCore:
    def __init__(self, http: FakeHTTP, headers: dict[str, str] | None = None) -> None:
        self._http = http
        self._headers = headers or {}

    def with_headers(self, headers: dict[str, str]) -> FakeCore:
        merged = dict(self._headers)
        merged.update(headers)
        return FakeCore(self._http, merged)

    def get_httpx_client(self) -> FakeHTTP:
        return self._http

    def get_async_httpx_client(self) -> FakeAsyncHTTP:
        return FakeAsyncHTTP(self._http)


def test_traces_handles_null_list_payload() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")
    traces = c.list_traces()
    assert traces == []


def test_chronos_query_normalizes_nullable_arrays() -> None:
    c = ChronosClient(FakeCore(FakeHTTP()), tenant_id="acme")
    out = c.query(query="test", limit=5)
    assert out.hits == []
    assert out.nodes == []
    assert out.edges == []
    assert out.additional_properties.get("ranking") == []


def test_arbiter_governance_endpoints() -> None:
    c = ArbiterClient(FakeCore(FakeHTTP()), tenant_id="acme")
    dashboard = c.governance_dashboard()
    violations = c.governance_violations(limit=100)
    report = c.governance_report(limit=200)

    assert dashboard["violations_24h"] == 0
    assert len(violations) == 1
    assert report["report_id"] == "r1"


def test_kernel_integrations_compliance_and_sse() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    created = c.create_notification_channel(kind="SLACK", name="ops", config={"webhook_url": "https://x"})
    listed = c.list_notification_channels()
    tested = c.test_notification_channel("ch1", message="ping")
    valid = c.validate_notification_channel_config(kind="SLACK", config={"webhook_url": "https://x"})
    health = c.integrations_health()
    dd = c.export_datadog(api_key="dd", app_key="app")
    siem = c.export_siem(export_format="JSON")
    soc2 = c.soc2_report()
    controls = c.compliance_control_evidence_report(framework="FEDRAMP")
    stream_lines = list(c.events_stream())

    assert created["channel_id"] == "ch1"
    assert listed == []
    assert tested["success"] is True
    assert valid is True
    assert health["summary"]["healthy"] == 1
    assert dd["exported_metrics"] == 12
    assert siem["exported_records"] == 7
    assert soc2["tenant_id"] == "acme"
    assert controls["framework"] == "FEDRAMP"
    assert stream_lines == ["event: alert", "data: {}"]


def test_kernel_cost_observability_methods() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    summary = c.get_cost_summary(group_by="provider_model")
    events = c.list_cost_events(provider="openai", limit=5)
    avoided = c.get_cost_avoided()
    anomalies = c.list_cost_anomalies()

    assert summary.group_by == "provider_model"
    assert summary.rows[0].pricing_source == "mixed"
    assert events.events[0].kind == "llm"
    assert events.events[0].reported_usd == 0.031
    assert avoided.rows[0].label == "budget_guardrail"
    assert anomalies.anomalies[0].kind == "model_spike"


def test_kernel_otel_bridge_methods() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    config = c.get_otel_export_config()
    updated = c.update_otel_export_config(
        config={
            "enabled": True,
            "endpoint": "https://collector.example.com",
            "protocol": "http/protobuf",
            "traces_enabled": True,
            "metrics_enabled": True,
            "include_sentinos_extensions": True,
            "include_internal_service_spans": False,
            "resource_attributes": {"service.name": "sentinos"},
            "header_values_write_only": {"authorization": "Bearer token"},
            "privacy_mode": "policy_enforced",
        }
    )
    status = c.get_otel_export_status()
    tested = c.test_otel_export()

    assert config.enabled is True
    assert updated.header_keys_masked == ["authorization"]
    assert status.queue_depth == 2
    assert tested.ok is True
    assert tested.trace_delivered is True


def test_kernel_integrations_compliance_and_sse_async() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        listed = await c.list_notification_channels_async()
        created = await c.create_notification_channel_async(
            kind="SLACK", name="ops", config={"webhook_url": "https://x"}
        )
        tested = await c.test_notification_channel_async("ch1", message="ping")
        valid = await c.validate_notification_channel_config_async(kind="SLACK", config={"webhook_url": "https://x"})
        health = await c.integrations_health_async()
        dd = await c.export_datadog_async(api_key="dd")
        siem = await c.export_siem_async()
        soc2 = await c.soc2_report_async()
        controls = await c.compliance_control_evidence_report_async(framework="HIPAA")

        assert listed == []
        assert created["channel_id"] == "ch1"
        assert tested["success"] is True
        assert valid is True
        assert health["summary"]["healthy"] == 1
        assert dd["exported_metrics"] == 12
        assert siem["exported_records"] == 7
        assert soc2["tenant_id"] == "acme"
        assert controls["framework"] == "HIPAA"

    asyncio.run(run())


def test_kernel_cost_observability_methods_async() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        summary = await c.get_cost_summary_async(group_by="actor")
        events = await c.list_cost_events_async(actor="finance_bot")
        avoided = await c.get_cost_avoided_async()
        anomalies = await c.list_cost_anomalies_async()

        assert summary.group_by == "actor"
        assert summary.rows[0].total_tokens == 420000
        assert events.events[0].provider == "openai"
        assert avoided.rows[0].total_usd == 1.2
        assert anomalies.anomalies[0].severity == "high"

    asyncio.run(run())


def test_kernel_otel_bridge_methods_async() -> None:
    c = KernelClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        config = await c.get_otel_export_config_async()
        updated = await c.update_otel_export_config_async(
            config={
                "enabled": True,
                "endpoint": "https://collector.example.com",
                "protocol": "http/protobuf",
                "traces_enabled": True,
                "metrics_enabled": True,
                "include_sentinos_extensions": True,
                "include_internal_service_spans": False,
                "resource_attributes": {"service.name": "sentinos"},
                "header_values_write_only": {"x-api-key": "secret"},
                "privacy_mode": "policy_enforced",
            }
        )
        status = await c.get_otel_export_status_async()
        tested = await c.test_otel_export_async()

        assert config.deep_link_template == "https://observability.example.com/trace/{trace_id}"
        assert updated.header_keys_masked == ["x-api-key"]
        assert status.traces_exported == 14
        assert tested.metrics_delivered is True

    asyncio.run(run())


def test_arbiter_async_surface_methods() -> None:
    c = ArbiterClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        dashboard = await c.governance_dashboard_async()
        violations = await c.governance_violations_async(limit=10)
        report = await c.governance_report_async(limit=20)
        evaluate = await c.evaluate_async(request={"tenant_id": "acme"})
        compiled = await c.compile_async(request={"rego": "package x"})
        policies = await c.list_policies_async()
        active = await c.active_policies_async(tool="stripe.transfer")
        tenant = await c.get_tenant_config_async()
        updated = await c.upsert_tenant_config_async(config={"tenant_id": "acme"})
        bundle = await c.get_policy_bundle_async(policy_id="p1", version="v1")
        job = await c.get_simulation_job_async("sim-1")

        assert dashboard["violations_24h"] == 0
        assert len(violations) == 1
        assert report["report_id"] == "r1"
        assert evaluate["ok"] is True
        assert compiled["ok"] is True
        assert policies[0]["policy_id"] == "p1"
        assert active == ["p1@v1"]
        assert tenant["tenant_id"] == "acme"
        assert updated["tenant_id"] == "acme"
        assert bundle
        assert job["job_id"] == "sim-1"

    asyncio.run(run())


def test_chronos_async_surface_methods() -> None:
    c = ChronosClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        traces = await c.observability_traces_async()
        analyzed = await c.analyze_traces_async()
        anomalies = await c.observability_anomalies_async()
        stats = await c.observability_anomaly_stats_async()
        compliance = await c.observability_compliance_async()
        report = await c.observability_compliance_report_async()
        patterns = await c.observability_patterns_async()
        risk = await c.entity_risk_async("e1")
        ingest = await c.get_ingest_status_async("11111111-1111-1111-1111-111111111111")
        event = await c.ingest_event_async(event={"event_type": "trace.indexed"})
        reprocess = await c.reprocess_traces_async(request={"trace_ids": []})
        legacy = await c.get_snapshot_legacy_async(anchor="agent:foo")

        assert traces["traces"] == []
        assert analyzed["score"] == 0.42
        assert anomalies["anomalies"] == []
        assert stats["count"] == 0
        assert compliance["score"] == 1.0
        assert report["report_id"] == "c1"
        assert patterns["patterns"] == []
        assert risk["entity_id"] == "e1"
        assert ingest["ingest"]["status"] == "accepted"
        assert event["ok"] is True
        assert reprocess["reprocessed"] == 2
        assert legacy.snapshot_id == "s1"

    asyncio.run(run())


def test_traces_async_export_verify_and_status() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        verified = await c.verify_trace_async("11111111-1111-1111-1111-111111111111")
        exported = await c.export_traces_async(request={})
        status = await c.export_status_async("11111111-1111-1111-1111-111111111111")
        assert verified["ok"] is True
        assert exported["job_id"] == "j1"
        assert status["status"] == "done"

    asyncio.run(run())


def test_traces_export_omits_tenant_id_from_body() -> None:
    http = FakeHTTP()
    c = TracesClient(FakeCore(http), tenant_id="acme")

    c.export_traces(request={"limit": 10, "tenant_id": "wrong"})

    export_calls = [call for call in http.calls if call[0] == "POST" and call[1] == "/v1/trace/export"]
    assert len(export_calls) == 1
    _, _, _, payload = export_calls[0]
    assert isinstance(payload, dict)
    assert payload.get("limit") == 10
    assert "tenant_id" not in payload


def test_traces_replay_ledger_retention_and_distributed_methods() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")

    replayed = c.replay_trace(
        "11111111-1111-1111-1111-111111111111",
        request={
            "profile": "original_policy_and_snapshot",
            "include_explain": True,
            "include_evidence_hints": True,
        },
    )
    matrix = c.replay_trace_matrix(
        "11111111-1111-1111-1111-111111111111",
        request={"include_explain": True},
    )
    exported_replay = c.export_replay_evidence(
        "11111111-1111-1111-1111-111111111111",
        request={"profile": "original_policy_and_snapshot", "include_explain": True},
    )
    verified = c.ledger_verify("11111111-1111-1111-1111-111111111111")
    retention_before = c.get_retention_policy()
    retention_after = c.update_retention_policy(request={"trace_days": 45, "export_days": 120, "ledger_days": 730})
    enforced = c.enforce_retention(request={"dry_run": True})
    distributed = c.distributed_trace_summaries(limit=25)

    assert replayed.drift_detected is False
    assert replayed.tenant_id == "acme"
    assert replayed.profile == "original_policy_and_snapshot"
    assert replayed.fidelity == "deterministic"
    assert replayed.original.checks[0].label == "Tool access: stripe.refund"
    assert replayed.original.checks[0].status == "ALLOWED"
    assert replayed.comparison.checks_changed == 0
    assert replayed.original.cost_breakdown.total_usd == 0.031
    assert replayed.replay.cost_events[0].kind == "retry"
    assert replayed.comparison.cost_changed is True
    assert matrix.entries[0].profile == "active_policy_chain"
    assert matrix.entries[1].response.fidelity == "deterministic"
    assert exported_replay.export_job["job_id"] == "job-replay-1"
    assert exported_replay.replay.evidence_export_ready is True
    assert verified.verified is True
    assert retention_before.trace_days == 30
    assert retention_after.trace_days == 45
    assert enforced.dry_run is True
    assert enforced.traces_affected == 12
    assert len(distributed) == 1
    assert distributed[0].distributed_trace_id == "dd-trace-1"


def test_traces_lineage_methods() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")

    lineage = c.get_trace_lineage("11111111-1111-1111-1111-111111111111")

    assert lineage.summary.artifact_count == 4
    assert lineage.summary.top_domains == ["api.stripe.com"]
    assert lineage.artifacts[0].kind == "file"
    assert lineage.events[1].action == "blocked"


def test_traces_lineage_methods_async() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        lineage = await c.get_trace_lineage_async("11111111-1111-1111-1111-111111111111")
        assert lineage.summary.has_blocked_side_effects is True
        assert lineage.artifacts[1].status == "blocked"

    asyncio.run(run())


def test_traces_replay_ledger_retention_and_distributed_methods_async() -> None:
    c = TracesClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        replayed = await c.replay_trace_async(
            "11111111-1111-1111-1111-111111111111",
            request={
                "profile": "original_policy",
                "policy_keys": ["sentinos/demo@v1"],
            },
        )
        matrix = await c.replay_trace_matrix_async(
            "11111111-1111-1111-1111-111111111111",
            request={"include_explain": True},
        )
        exported_replay = await c.export_replay_evidence_async(
            "11111111-1111-1111-1111-111111111111",
            request={"profile": "original_policy_and_snapshot", "include_explain": True},
        )
        verified = await c.ledger_verify_async("11111111-1111-1111-1111-111111111111")
        retention_before = await c.get_retention_policy_async()
        retention_after = await c.update_retention_policy_async(
            request={"trace_days": 60, "export_days": 150, "ledger_days": 730}
        )
        enforced = await c.enforce_retention_async(request={"dry_run": False})
        distributed = await c.distributed_trace_summaries_async(limit=50)

        assert replayed.drift_detected is False
        assert replayed.profile == "original_policy"
        assert replayed.replay.checks[0].category == "tool"
        assert replayed.comparison.decision_changed is False
        assert replayed.replay.cost_breakdown.pricing_source == "estimated"
        assert replayed.comparison.total_cost_delta_usd == 0.013
        assert matrix.entries[0].response.fidelity == "best_effort"
        assert exported_replay.profile == "original_policy_and_snapshot"
        assert verified.chain_continuity_ok is True
        assert retention_before.trace_days == 30
        assert retention_after.trace_days == 60
        assert enforced.dry_run is False
        assert distributed[0].decision == "ALLOW"

    asyncio.run(run())


def test_marketplace_sync_and_async_methods() -> None:
    c = MarketplaceClient(FakeCore(FakeHTTP()), tenant_id="acme")

    packs = c.list_packs()
    fetched = c.get_pack(pack_id="pack-1")
    install = c.install_pack(pack_id="pack-1")
    installs = c.list_installs()
    c.uninstall_pack(pack_id="pack-1")

    assert packs[0].pack_id == "pack-1"
    assert fetched.pack_id == "pack-1"
    assert install.install_id == "inst-1"
    assert installs == []

    async def run() -> None:
        packs_async = await c.list_packs_async()
        fetched_async = await c.get_pack_async(pack_id="pack-1")
        install_async = await c.install_pack_async(pack_id="pack-1")
        installs_async = await c.list_installs_async()
        await c.uninstall_pack_async(pack_id="pack-1")

        assert packs_async[0].pack_id == "pack-1"
        assert fetched_async.pack_id == "pack-1"
        assert install_async.install_id == "inst-1"
        assert installs_async == []

    asyncio.run(run())
