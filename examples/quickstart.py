"""Quickstart SDK example that only relies on the canonical environment setup."""

import os

from sentinos import SentinosClient


def _validate_env() -> None:
    required = [
        "SENTINOS_BASE_URL",
        "SENTINOS_ORG_ID",
        "SENTINOS_ACCESS_TOKEN",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Set {', '.join(missing)} before running this example.")


def run_example() -> None:
    _validate_env()
    client = SentinosClient.from_env()
    metrics = client.kernel.get_runtime_metrics()
    traces = client.traces.list_traces(limit=3)
    print("Connected to Sentinos kernel.", "Metrics:", metrics)
    print("Latest traces:", [trace.trace_id for trace in traces])


if __name__ == "__main__":
    run_example()
