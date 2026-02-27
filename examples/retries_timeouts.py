"""Retry and timeout configuration example."""

from sentinos import SentinosClient
from sentinos.utils.retry import retry


@retry(max_attempts=3, base_delay=0.2)
def fetch_soc2_report(client: SentinosClient) -> dict:
    return client.kernel.soc2_report()
