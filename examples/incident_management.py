"""Incident lifecycle example."""

from sentinos import SentinosClient


def run_incident_flow(client: SentinosClient) -> None:
    incident = client.incidents.create_incident(
        incident={
            "title": "Payment API degradation",
            "severity": "HIGH",
            "source": "MANUAL",
            "summary": "Increased error rate detected",
        }
    )
    updated = client.incidents.update_incident(
        incident.incident_id,
        patch={"status": "INVESTIGATING", "summary": "On-call engaged"},
    )
    resolved = client.incidents.resolve_incident(updated.incident_id, note="Issue mitigated")
    print(f"Resolved incident: {resolved.incident_id}")
