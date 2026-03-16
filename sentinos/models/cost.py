from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

CostPricingSource = Literal["reported", "estimated", "mixed", "unknown"]
CostEventKind = Literal["llm", "tool", "retry", "replay", "export", "blocked", "approval_wait", "other"]


class TraceCostProviderModelBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: str
    model: str
    usd: float | None = None
    tokens: int | None = None


class TraceCostRetryBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    retry_index: int
    usd: float | None = None
    tokens: int | None = None


class TraceCostToolBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    tool: str
    usd: float | None = None
    tokens: int | None = None


class TraceCostActorBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    actor: str
    usd: float | None = None
    tokens: int | None = None


class TraceCostBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_usd: float | None = None
    reported_total_usd: float | None = None
    estimated_total_usd: float | None = None
    pricing_source: CostPricingSource | None = None
    provider: str | None = None
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    total_tokens: int | None = None
    retry_count: int | None = None
    tool_call_count: int | None = None
    blocked_cost_avoided_usd: float | None = None
    blocked_token_avoided: int | None = None
    by_category: dict[str, float] | None = None
    by_provider_model: list[TraceCostProviderModelBreakdown] | None = None
    by_retry: list[TraceCostRetryBreakdown] | None = None
    by_tool: list[TraceCostToolBreakdown] | None = None
    by_actor: list[TraceCostActorBreakdown] | None = None


class TraceCostEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    kind: CostEventKind
    label: str
    provider: str | None = None
    model: str | None = None
    tool: str | None = None
    actor: str | None = None
    retry_index: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_tokens: int | None = None
    total_tokens: int | None = None
    reported_usd: float | None = None
    estimated_usd: float | None = None
    pricing_source: CostPricingSource | None = None
    avoided_usd: float | None = None
    avoided_tokens: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    metadata: dict[str, Any] | None = None


class KernelCostSummaryRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str
    total_usd: float | None = None
    reported_total_usd: float | None = None
    estimated_total_usd: float | None = None
    pricing_source: CostPricingSource | None = None
    total_tokens: int | None = None
    blocked_cost_avoided_usd: float | None = None
    blocked_token_avoided: int | None = None
    trace_count: int | None = None


class KernelCostSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    from_: str | None = None
    to: str | None = None
    group_by: Literal["session", "actor", "agent", "provider_model", "tool", "day"]
    rows: list[KernelCostSummaryRow]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = dict(obj)
            obj["from_"] = obj.pop("from")
        return super().model_validate(obj, *args, **kwargs)


class KernelCostAvoidedRow(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str
    total_usd: float | None = None
    total_tokens: int | None = None
    event_count: int | None = None


class KernelCostAvoidedResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    from_: str | None = None
    to: str | None = None
    rows: list[KernelCostAvoidedRow]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = dict(obj)
            obj["from_"] = obj.pop("from")
        return super().model_validate(obj, *args, **kwargs)


class KernelCostEventsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    from_: str | None = None
    to: str | None = None
    events: list[TraceCostEvent]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = dict(obj)
            obj["from_"] = obj.pop("from")
        return super().model_validate(obj, *args, **kwargs)


class KernelCostAnomaly(BaseModel):
    model_config = ConfigDict(extra="allow")

    anomaly_id: str
    kind: str
    severity: Literal["low", "medium", "high", "critical"]
    dimension: str
    baseline: float
    observed: float
    delta: float
    trace_id: str | None = None
    session_id: str | None = None
    actor: str | None = None
    agent_id: str | None = None
    provider: str | None = None
    model: str | None = None
    detected_at: str


class KernelCostAnomaliesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    tenant_id: str
    from_: str | None = None
    to: str | None = None
    anomalies: list[KernelCostAnomaly]

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any):
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = dict(obj)
            obj["from_"] = obj.pop("from")
        return super().model_validate(obj, *args, **kwargs)
