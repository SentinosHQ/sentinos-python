"""Governance reporting example."""

from sentinos import SentinosClient


def fetch_governance_report(client: SentinosClient) -> dict:
    dashboard = client.arbiter.governance_dashboard()
    report = client.arbiter.governance_report(limit=500)
    soc2 = client.kernel.soc2_report()
    controls = client.kernel.compliance_control_evidence_report(framework="FEDRAMP")
    return {
        "dashboard": dashboard,
        "report": report,
        "soc2": soc2,
        "controls": controls,
    }
