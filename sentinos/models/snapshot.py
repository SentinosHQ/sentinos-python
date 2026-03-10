from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class SnapshotNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    node_id: str
    type: str | None = None
    properties: dict[str, Any] | None = None
    confidence: float | None = None
    provenance: list[Any] | None = None


class SnapshotEdge(BaseModel):
    model_config = ConfigDict(extra="allow")

    edge_id: str | None = None
    from_node: str | None = None
    to_node: str | None = None
    type: str | None = None
    confidence: float | None = None
    provenance: Any | None = None


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="allow")

    snapshot_id: str
    status: Literal["ready", "pending"] | None = None
    generated_at: datetime | None = None
    retrieval_time: datetime | None = None
    anchors: list[str] | None = None
    depth: int | None = None
    valid_time: datetime | None = None
    estimated_nodes: int | None = None

    nodes: list[SnapshotNode] | None = None
    edges: list[SnapshotEdge] | None = None
    decision_traces: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_core(cls, core_obj: Any) -> Snapshot:
        if hasattr(core_obj, "to_dict") and callable(getattr(core_obj, "to_dict")):
            return cls.model_validate(core_obj.to_dict())
        if isinstance(core_obj, dict):
            return cls.model_validate(core_obj)
        raise TypeError("unsupported core object for Snapshot.from_core")
