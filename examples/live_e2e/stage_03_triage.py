"""Stage 03: triage alerts/anomalies, handle escalations, and run incident lifecycle."""

from __future__ import annotations

import time
from typing import Any

from sentinos.models.alert import Alert

if __package__ in (None, ""):
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))

from common import (  # noqa: E402
    LiveE2EConfig,
    build_sentinos_client,
    info,
    load_config,
    load_state,
    save_state,
    write_artifact,
)


def _wait_for_matching_alerts(config: LiveE2EConfig, rule_ids: set[str], timeout_seconds: int = 90) -> list[Alert]:
    client = build_sentinos_client(config)
    tenant_id = (config.tenant_id or client.config.tenant_id or "").strip() or None
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        alerts = client.alerts.list_alerts(limit=200, tenant_id=tenant_id)
        matched = [a for a in alerts if a.rule_id and a.rule_id in rule_ids]
        if matched:
            return matched
        time.sleep(4)
    return []


def run_stage(config: LiveE2EConfig) -> dict[str, Any]:
    client = build_sentinos_client(config)
    tenant_id = (config.tenant_id or client.config.tenant_id or "").strip() or None
    state = load_state(config)

    rule_ids = {
        str(v)
        for v in (state.get("rule_ids") or {}).values()
        if isinstance(v, str) and v.strip()
    }

    alerts = _wait_for_matching_alerts(config, rule_ids)
    info(f"Matched alerts for run: {len(alerts)}")

    triage_actions: list[dict[str, Any]] = []
    for alert in alerts:
        action_record: dict[str, Any] = {
            "alert_id": alert.alert_id,
            "severity": alert.severity,
            "initial_status": alert.status,
            "rule_id": alert.rule_id,
            "steps": [],
        }

        current = alert
        if current.status == "FIRING":
            current = client.alerts.acknowledge_alert(
                current.alert_id,
                note=f"Live E2E triage acknowledged ({config.run_id})",
                tenant_id=tenant_id,
            )
            action_record["steps"].append({"action": "acknowledge", "status": current.status})

        if current.severity in {"HIGH", "CRITICAL"} and current.status in {"FIRING", "ACKNOWLEDGED"}:
            current = client.alerts.escalate_alert(
                current.alert_id,
                escalated_to="soc-oncall@sentinos.dev",
                note=f"Live E2E escalate ({config.run_id})",
                tenant_id=tenant_id,
            )
            action_record["steps"].append({"action": "escalate", "status": current.status, "escalated_to": current.escalated_to})
        elif current.status != "RESOLVED":
            current = client.alerts.resolve_alert(
                current.alert_id,
                note=f"Live E2E resolved ({config.run_id})",
                tenant_id=tenant_id,
            )
            action_record["steps"].append({"action": "resolve", "status": current.status})

        action_record["final_status"] = current.status
        triage_actions.append(action_record)

    anomalies = client.alerts.list_anomalies(limit=50, tenant_id=tenant_id)
    anomaly_updates: list[dict[str, Any]] = []
    for anomaly in anomalies[:1]:
        updated = client.alerts.investigate_anomaly(
            anomaly.anomaly_id,
            notes=f"Live E2E reviewed anomaly for run {config.run_id}",
            false_positive=False,
            tenant_id=tenant_id,
        )
        anomaly_updates.append(
            {
                "anomaly_id": updated.anomaly_id,
                "status": updated.status,
                "false_positive": updated.false_positive,
            }
        )

    incident_source = "AUTO" if alerts else "MANUAL"
    incident_severity = "HIGH"
    if alerts:
        severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        incident_severity = max((a.severity for a in alerts), key=lambda s: severity_order.get(s, 0))

    created_incident = client.incidents.create_incident(
        incident={
            "title": f"Live E2E OpenAI Governance Incident ({config.run_id})",
            "severity": incident_severity,
            "source": incident_source,
            "description": "Automated incident created during live OpenAI governance validation.",
            "tags": ["live-e2e", config.run_id],
            "metadata": {"run_id": config.run_id, "suite": "live_e2e"},
        },
        tenant_id=tenant_id,
    )
    investigating = client.incidents.update_incident(
        created_incident.incident_id,
        patch={"status": "INVESTIGATING", "description": "Analyst investigation in progress"},
        tenant_id=tenant_id,
    )
    mitigating = client.incidents.update_incident(
        investigating.incident_id,
        patch={"status": "MITIGATING", "description": "Mitigation controls applied"},
        tenant_id=tenant_id,
    )
    resolved = client.incidents.resolve_incident(
        mitigating.incident_id,
        note=f"Live E2E validation completed for {config.run_id}",
        tenant_id=tenant_id,
    )
    resolved_incident, timeline = client.incidents.get_incident(resolved.incident_id, tenant_id=tenant_id)

    escalation_updates: list[dict[str, Any]] = []
    pending = client.kernel.list_escalations(
        status="PENDING",
        session_id=state.get("session_id") or config.session_id,
        limit=25,
        tenant_id=tenant_id,
    ).escalations
    for esc in pending[:1]:
        client.kernel.resolve_escalation(
            escalation_id=esc.escalation_id,
            status="APPROVED",
            tenant_id=tenant_id,
        )
        escalation_updates.append({"escalation_id": str(esc.escalation_id), "resolution": "APPROVED"})

    state.update(
        {
            "incident_id": resolved_incident.incident_id,
            "incident_status": resolved_incident.status,
        }
    )
    save_state(config, state)

    artifact = {
        "stage": "stage_03_triage",
        "run_id": config.run_id,
        "tenant_id": tenant_id,
        "matched_alert_count": len(alerts),
        "triage_actions": triage_actions,
        "anomaly_updates": anomaly_updates,
        "incident": {
            "incident_id": resolved_incident.incident_id,
            "status": resolved_incident.status,
            "severity": resolved_incident.severity,
            "timeline_events": len(timeline),
        },
        "escalation_updates": escalation_updates,
    }
    artifact_path = write_artifact(config, "stage_03_triage", artifact)
    info(f"Stage 03 complete -> {artifact_path}")
    return artifact


def main() -> None:
    config = load_config(require_openai_key=False)
    run_stage(config)


if __name__ == "__main__":
    main()
