"""Alert lifecycle example."""

from sentinos import SentinosClient


def run_alert_lifecycle(client: SentinosClient) -> None:
    alerts = client.alerts.list_alerts(status="FIRING", limit=25)
    if not alerts:
        print("No firing alerts")
        return

    alert = alerts[0]
    acknowledged = client.alerts.acknowledge_alert(alert.alert_id, note="investigating")
    resolved = client.alerts.resolve_alert(acknowledged.alert_id, note="fixed")
    print(f"Resolved alert: {resolved.alert_id}")
