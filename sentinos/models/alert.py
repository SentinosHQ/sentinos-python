from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

AlertRuleType = Literal["THRESHOLD", "ANOMALY", "PATTERN", "COMPLIANCE"]
AlertSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AlertStatus = Literal["FIRING", "ACKNOWLEDGED", "RESOLVED", "SUPPRESSED", "ESCALATED"]


class AlertRule(BaseModel):
    model_config = ConfigDict(extra="allow")

    rule_id: str
    tenant_id: str
    name: str
    rule_type: AlertRuleType
    severity: AlertSeverity
    enabled: bool
    created_at: datetime
    updated_at: datetime

    description: str | None = None
    metric_key: str | None = None
    comparator: str | None = None
    threshold_value: float | None = None
    pattern: str | None = None
    compliance_control: str | None = None
    evaluation_window_sec: int | None = None
    cooldown_sec: int | None = None
    notification_channels: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Alert(BaseModel):
    model_config = ConfigDict(extra="allow")

    alert_id: str
    tenant_id: str
    status: AlertStatus
    severity: AlertSeverity
    title: str
    created_at: datetime
    updated_at: datetime

    rule_id: str | None = None
    anomaly_id: str | None = None
    incident_id: str | None = None
    description: str | None = None
    correlation_key: str | None = None
    metric_value: float | None = None
    threshold_value: float | None = None
    labels: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    first_fired_at: datetime | None = None
    last_fired_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    escalated_at: datetime | None = None
    escalated_to: str | None = None


class Anomaly(BaseModel):
    model_config = ConfigDict(extra="allow")

    anomaly_id: str
    tenant_id: str
    type: Literal["ZSCORE", "PATTERN"]
    status: Literal["OPEN", "INVESTIGATING", "CLOSED", "FALSE_POSITIVE"]
    false_positive: bool
    created_at: datetime
    updated_at: datetime

    rule_id: str | None = None
    metric_key: str | None = None
    observed_value: float | None = None
    expected_value: float | None = None
    z_score: float | None = None
    confidence: float | None = None
    investigation_notes: str | None = None
    investigated_by: str | None = None
    investigated_at: datetime | None = None
    linked_alert_id: str | None = None
    context: dict[str, Any] | None = None
