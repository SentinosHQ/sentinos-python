from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

OtelExportProtocol = Literal["http/protobuf"]
OtelExportPrivacyMode = Literal["policy_enforced"]


class OtelExportConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    endpoint: str = ""
    protocol: OtelExportProtocol = "http/protobuf"
    traces_enabled: bool = True
    metrics_enabled: bool = True
    include_sentinos_extensions: bool = True
    include_internal_service_spans: bool = False
    resource_attributes: dict[str, str] | None = None
    header_values_write_only: dict[str, str] | None = None
    header_keys_masked: list[str] | None = None
    deep_link_template: str | None = None
    privacy_mode: OtelExportPrivacyMode = "policy_enforced"
    updated_at: str | None = None


class OtelExportStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    last_successful_export_at: str | None = None
    last_error_summary: str | None = None
    queue_depth: int = 0
    dropped_batch_count: int = 0
    traces_exported: int = 0
    metrics_exported: int = 0
    updated_at: str | None = None


class OtelExportTestResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    ok: bool
    trace_delivered: bool | None = None
    metrics_delivered: bool | None = None
    status_code: int | None = None
    message: str | None = None
    error: str | None = None
    endpoint: str | None = None
    tested_at: str | None = None
