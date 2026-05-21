"""Helpers for destination-specific OTLP bridge configuration."""

from __future__ import annotations

from typing import Literal, cast

from sentinos.models.otel import OtelExportConfig

HoneycombRegion = Literal["us", "eu"]

HONEYCOMB_OTLP_ENDPOINTS: dict[HoneycombRegion, str] = {
    "us": "https://api.honeycomb.io:443",
    "eu": "https://api.eu1.honeycomb.io:443",
}


def build_honeycomb_otel_export_config(
    *,
    api_key: str,
    dataset: str | None = None,
    region: HoneycombRegion | str = "us",
    endpoint: str | None = None,
    service_name: str | None = None,
    environment: str | None = None,
    resource_attributes: dict[str, str] | None = None,
    deep_link_template: str | None = None,
    enabled: bool = True,
    traces_enabled: bool = True,
    metrics_enabled: bool = True,
    include_sentinos_extensions: bool = True,
    include_internal_service_spans: bool = False,
) -> OtelExportConfig:
    api_key_value = api_key.strip()
    if not api_key_value:
        raise ValueError("Honeycomb API key is required")
    region_value = _normalize_honeycomb_region(region)

    resource_map = dict(resource_attributes or {})
    if service_name and service_name.strip():
        resource_map["service.name"] = service_name.strip()
    if environment and environment.strip():
        resource_map["deployment.environment"] = environment.strip()

    headers = {"x-honeycomb-team": api_key_value}
    if dataset and dataset.strip():
        headers["x-honeycomb-dataset"] = dataset.strip()

    payload = {
        "enabled": enabled,
        "endpoint": (endpoint or HONEYCOMB_OTLP_ENDPOINTS[region_value]).strip(),
        "protocol": "http/protobuf",
        "traces_enabled": traces_enabled,
        "metrics_enabled": metrics_enabled,
        "include_sentinos_extensions": include_sentinos_extensions,
        "include_internal_service_spans": include_internal_service_spans,
        "resource_attributes": resource_map,
        "header_values_write_only": headers,
        "privacy_mode": "policy_enforced",
    }
    if deep_link_template and deep_link_template.strip():
        payload["deep_link_template"] = deep_link_template.strip()

    return OtelExportConfig(**payload)


def build_datadog_metrics_otel_export_config(
    *,
    endpoint: str,
    api_key: str,
    metric_config_header: str | None = None,
    service_name: str | None = None,
    environment: str | None = None,
    resource_attributes: dict[str, str] | None = None,
    enabled: bool = True,
    metrics_enabled: bool = True,
    include_sentinos_extensions: bool = True,
    include_internal_service_spans: bool = False,
) -> OtelExportConfig:
    endpoint_value = endpoint.strip()
    if not endpoint_value:
        raise ValueError("Datadog OTLP metrics endpoint is required")
    api_key_value = api_key.strip()
    if not api_key_value:
        raise ValueError("Datadog API key is required")
    if not metrics_enabled:
        raise ValueError("Datadog metrics helper requires metrics_enabled to remain true")

    resource_map = dict(resource_attributes or {})
    if service_name and service_name.strip():
        resource_map["service.name"] = service_name.strip()
    if environment and environment.strip():
        resource_map["deployment.environment"] = environment.strip()

    headers = {"dd-api-key": api_key_value}
    if metric_config_header and metric_config_header.strip():
        headers["dd-otel-metric-config"] = metric_config_header.strip()

    return OtelExportConfig(
        enabled=enabled,
        endpoint=endpoint_value,
        protocol="http/protobuf",
        traces_enabled=False,
        metrics_enabled=True,
        include_sentinos_extensions=include_sentinos_extensions,
        include_internal_service_spans=include_internal_service_spans,
        resource_attributes=resource_map,
        header_values_write_only=headers,
        privacy_mode="policy_enforced",
    )


def _normalize_honeycomb_region(region: HoneycombRegion | str) -> HoneycombRegion:
    region_value = str(region or "us").strip().lower()
    if region_value in HONEYCOMB_OTLP_ENDPOINTS:
        return cast(HoneycombRegion, region_value)
    raise ValueError(f'Unsupported Honeycomb region "{region}". Use "us" or "eu".')
