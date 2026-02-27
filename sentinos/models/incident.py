from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

IncidentStatus = Literal["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"]
IncidentSource = Literal["AUTO", "MANUAL"]
AlertSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class Incident(BaseModel):
    model_config = ConfigDict(extra="allow")

    incident_id: str
    tenant_id: str
    title: str
    severity: AlertSeverity
    status: IncidentStatus
    source: IncidentSource
    created_at: datetime
    updated_at: datetime

    description: str | None = None
    correlation_key: str | None = None
    started_at: datetime | None = None
    detected_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    mttd_seconds: int | None = None
    mttr_seconds: int | None = None
    created_by: str | None = None
    updated_by: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class IncidentTimelineEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str
    incident_id: str
    tenant_id: str
    event_type: str
    created_at: datetime

    actor: str | None = None
    details: dict[str, Any] | None = None
