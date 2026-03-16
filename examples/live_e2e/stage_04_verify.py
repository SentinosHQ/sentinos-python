"""Stage 04: verify cross-module outcomes and export evidence artifacts."""

from __future__ import annotations

import os
import time
from typing import Any

if __package__ in (None, ""):
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))

from common import (  # noqa: E402
    LiveE2EConfig,
    build_sentinos_client,
    info,
    iso_utc,
    iso_utc_minus,
    load_config,
    load_state,
    write_artifact,
)


def _safe_call(fn, *args, **kwargs) -> dict[str, Any]:
    try:
        return {"ok": True, "payload": fn(*args, **kwargs)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def run_stage(config: LiveE2EConfig) -> dict[str, Any]:
    client = build_sentinos_client(config)
    tenant_id = (config.tenant_id or client.config.tenant_id or "").strip() or None
    state = load_state(config)

    agent_id = str(state.get("agent_id") or config.agent_id)
    session_id = str(state.get("session_id") or config.session_id)

    trace_counts: dict[str, int] = {}
    for decision in ("ALLOW", "SHADOW", "ESCALATE", "DENY"):
        traces = client.traces.list_traces(agent_id=agent_id, decision=decision, tenant_id=tenant_id)
        trace_counts[decision] = len(traces)

    export_payload: dict[str, Any] = {"limit": 200}
    export_request = client.traces.export_traces(request=export_payload, tenant_id=tenant_id)
    export_job_id = str(export_request.get("job_id") or "")
    export_status: dict[str, Any] = {"job_id": export_job_id}
    if export_job_id:
        for _ in range(20):
            status = client.traces.export_status(export_job_id, tenant_id=tenant_id)
            export_status = status
            if str(status.get("status") or "").upper() in {"DONE", "COMPLETED", "FAILED"}:
                break
            time.sleep(1)

    governance_dashboard = client.arbiter.governance_dashboard(tenant_id=tenant_id)
    governance_violations = client.arbiter.governance_violations(
        from_time=iso_utc_minus(240),
        to_time=iso_utc(),
        limit=100,
        tenant_id=tenant_id,
    )
    governance_report = client.arbiter.governance_report(
        from_time=iso_utc_minus(240),
        to_time=iso_utc(),
        limit=150,
        tenant_id=tenant_id,
    )
    runtime_metrics = client.kernel.get_runtime_metrics(tenant_id=tenant_id)
    channels = client.kernel.list_notification_channels(limit=100, tenant_id=tenant_id)
    integrations_health = _safe_call(client.kernel.integrations_health, tenant_id=tenant_id)
    soc2_report = _safe_call(client.kernel.soc2_report, from_time=iso_utc_minus(240), to_time=iso_utc(), tenant_id=tenant_id)
    siem_export = _safe_call(client.kernel.export_siem, export_format="JSON", limit=200, tenant_id=tenant_id)

    dd_api_key = (os.getenv("SENTINOS_E2E_DATADOG_API_KEY") or "").strip()
    if dd_api_key:
        datadog_export = _safe_call(
            client.kernel.export_datadog,
            api_key=dd_api_key,
            site=(os.getenv("SENTINOS_E2E_DATADOG_SITE") or "datadoghq.com"),
            limit=100,
            tenant_id=tenant_id,
        )
    else:
        datadog_export = {"ok": False, "error": "SENTINOS_E2E_DATADOG_API_KEY not set (optional)"}

    alerts = client.alerts.list_alerts(limit=200, tenant_id=tenant_id)
    anomalies = client.alerts.list_anomalies(limit=200, tenant_id=tenant_id)
    incidents = client.incidents.list_incidents(limit=100, tenant_id=tenant_id)
    escalations_pending = client.kernel.list_escalations(
        status="PENDING",
        session_id=session_id,
        limit=50,
        tenant_id=tenant_id,
    ).escalations
    session_details = _safe_call(client.kernel.get_session, session_id=session_id, tenant_id=tenant_id)

    artifact = {
        "stage": "stage_04_verify",
        "run_id": config.run_id,
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "session_id": session_id,
        "trace_counts": trace_counts,
        "counts": {
            "alerts": len(alerts),
            "anomalies": len(anomalies),
            "incidents": len(incidents),
            "channels": len(channels),
            "pending_escalations_for_session": len(escalations_pending),
            "governance_violations": len(governance_violations),
        },
        "runtime_metrics": runtime_metrics,
        "governance_dashboard": governance_dashboard,
        "governance_report_summary_keys": sorted((governance_report or {}).keys()),
        "integrations_health": integrations_health,
        "soc2_report": soc2_report,
        "siem_export": siem_export,
        "datadog_export": datadog_export,
        "trace_export": {
            "request": export_request,
            "status": export_status,
        },
        "session_details": session_details,
        "console_views": {
            "dashboard": f"{config.console_url.rstrip('/')}/#dashboard",
            "alerts": f"{config.console_url.rstrip('/')}/#alerts",
            "incidents": f"{config.console_url.rstrip('/')}/#incidents",
            "traces": f"{config.console_url.rstrip('/')}/#traces",
            "kernel": f"{config.console_url.rstrip('/')}/#kernel",
            "workforce": f"{config.console_url.rstrip('/')}/#workforce",
            "analytics": f"{config.console_url.rstrip('/')}/#analytics",
        },
    }
    artifact_path = write_artifact(config, "stage_04_verify", artifact)
    info(f"Stage 04 complete -> {artifact_path}")
    return artifact


def main() -> None:
    config = load_config(require_openai_key=False)
    run_stage(config)


if __name__ == "__main__":
    main()
