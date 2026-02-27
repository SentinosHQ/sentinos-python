from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelemetryConfig:
    enabled: bool = True
    service_name: str = "sentinos-sdk"


def httpx_event_hooks(
    span_prefix: str,
    *,
    extra_attributes: dict[str, Any] | None = None,
) -> dict[str, list[Callable[..., Any]]]:
    """
    Return httpx event hooks for OpenTelemetry spans.

    Attach these via `httpx_args={"event_hooks": ...}` when constructing the generated core client.
    """
    extra_attributes = extra_attributes or {}

    def on_request(request: Any) -> None:
        if not extra_attributes:
            return
        try:
            request.extensions.setdefault("sentinos_attrs", {}).update(extra_attributes)
        except Exception:
            return

    def on_response(response: Any) -> None:
        # Best-effort: create span per request if opentelemetry is installed.
        try:
            from opentelemetry import trace as otel_trace
        except Exception:
            return
        tracer = otel_trace.get_tracer("sentinos-sdk")
        req = response.request
        name = f"{span_prefix} {req.method} {req.url.path}"
        with tracer.start_as_current_span(name) as span:
            span.set_attribute("http.method", req.method)
            span.set_attribute("http.url", str(req.url))
            span.set_attribute("http.status_code", response.status_code)
            attrs = req.extensions.get("sentinos_attrs") if hasattr(req, "extensions") else None
            if isinstance(attrs, dict):
                for k, v in attrs.items():
                    span.set_attribute(str(k), v)

    return {"request": [on_request], "response": [on_response]}
