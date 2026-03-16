from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .cost import TraceCostBreakdown, TraceCostEvent
from .decision_trace import (
    DecisionTraceEvidenceItem,
    DecisionTracePolicyCheck,
)

TraceReplayProfile = Literal[
    "active_policy_chain",
    "original_policy",
    "original_snapshot",
    "original_policy_and_snapshot",
    "current_policy_with_original_snapshot",
]
TraceReplayPolicySource = Literal[
    "active_policy_chain",
    "original_trace_policy",
    "explicit_policy_keys",
    "unavailable",
]
TraceReplaySnapshotSource = Literal[
    "original_snapshot",
    "current_context",
    "bounded_assumptions",
    "unavailable",
]
TraceReplayFidelity = Literal[
    "deterministic",
    "bounded",
    "best_effort",
    "unsupported",
]


class TraceReplayDecision(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: str | None = None
    policy_id: str | None = None
    policy_version: str | None = None
    policy_key: str | None = None
    reason: str | None = None
    evidence: list[DecisionTraceEvidenceItem] | list[dict[str, Any]] | None = None
    explain_plan: dict[str, Any] | None = None
    checks: list[DecisionTracePolicyCheck] | None = None
    cost_breakdown: TraceCostBreakdown | None = None
    cost_events: list[TraceCostEvent] | None = None


class TraceReplayComparison(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision_changed: bool | None = None
    policy_changed: bool | None = None
    reason_changed: bool | None = None
    checks_added: int | None = None
    checks_removed: int | None = None
    checks_changed: int | None = None
    cost_changed: bool | None = None
    total_cost_delta_usd: float | None = None
    avoided_cost_delta_usd: float | None = None


class TraceReplayReconstructionBasis(BaseModel):
    model_config = ConfigDict(extra="allow")

    policy_keys: list[str] | None = None
    original_policy_key: str | None = None
    original_policy_id: str | None = None
    original_policy_version: str | None = None
    snapshot_id: str | None = None
    environment_assumptions: dict[str, Any] | None = None


class TraceReplayResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_id: str
    tenant_id: str
    replayed_at: str
    policy_keys: list[str] | None = None
    drift_detected: bool | None = None
    profile: TraceReplayProfile | None = None
    policy_source: TraceReplayPolicySource | None = None
    snapshot_source: TraceReplaySnapshotSource | None = None
    fidelity: TraceReplayFidelity | None = None
    fidelity_reasons: list[str] | None = None
    reconstruction_basis: TraceReplayReconstructionBasis | None = None
    evidence_export_ready: bool | None = None
    evidence_export_hints: list[str] | None = None
    original: TraceReplayDecision | None = None
    replay: TraceReplayDecision | None = None
    comparison: TraceReplayComparison | None = None
    ledger_verification: dict[str, Any] | None = None


class TraceReplayMatrixEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile: TraceReplayProfile
    response: TraceReplayResponse | None = None


class TraceReplayMatrixResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_id: str
    tenant_id: str
    generated_at: str
    entries: list[TraceReplayMatrixEntry]


class TraceReplayExportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_id: str
    tenant_id: str
    profile: TraceReplayProfile
    export_job: dict[str, Any]
    replay: TraceReplayResponse
