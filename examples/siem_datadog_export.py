"""SIEM and Datadog export example."""

from sentinos import SentinosClient


def export_security_data(client: SentinosClient) -> None:
    siem_result = client.kernel.export_siem(export_format="JSON", limit=1000)
    datadog_result = client.kernel.export_datadog(api_key="${DATADOG_API_KEY}", include_events=True)
    print("SIEM export:", siem_result)
    print("Datadog export:", datadog_result)
