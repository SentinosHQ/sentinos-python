"""Chronos observability analysis example."""

from sentinos import SentinosClient


def run_observability_queries(client: SentinosClient) -> dict:
    traces = client.chronos.observability_traces(limit=200)
    anomalies = client.chronos.observability_anomalies(threshold=0.8)
    patterns = client.chronos.observability_patterns()
    return {
        "traces": traces,
        "anomalies": anomalies,
        "patterns": patterns,
    }
