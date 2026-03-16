from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

TraceArtifactKind = Literal["file", "connector", "domain", "output", "handoff", "other"]
TraceArtifactStatus = Literal["observed", "produced", "consumed", "blocked"]
TraceArtifactAction = Literal["read", "write", "call", "egress", "produce", "reuse", "handoff", "blocked"]


class TraceArtifactLineageSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_count: int
    side_effect_count: int
    blocked_count: int
    kinds: dict[str, int]
    top_domains: list[str] | None = None
    top_connectors: list[str] | None = None
    top_outputs: list[str] | None = None
    has_handoff: bool | None = None
    has_writes: bool | None = None
    has_blocked_side_effects: bool | None = None


class TraceArtifactRef(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: str
    kind: TraceArtifactKind
    label: str
    locator: str | None = None
    status: TraceArtifactStatus | None = None
    chronos_entity_id: str | None = None
    chronos_anchor: str | None = None
    metadata: dict[str, Any] | None = None


class TraceArtifactLineageEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    artifact_id: str
    action: TraceArtifactAction
    actor: str | None = None
    tool: str | None = None
    timestamp: str | None = None
    related_artifact_id: str | None = None
    metadata: dict[str, Any] | None = None


class TraceArtifactLineageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    trace_id: str
    summary: TraceArtifactLineageSummary
    artifacts: list[TraceArtifactRef]
    events: list[TraceArtifactLineageEvent]
