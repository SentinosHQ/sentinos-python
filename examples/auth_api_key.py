"""API key authentication example."""

from sentinos import SentinosClient
from sentinos.auth.api_key import APIKeyAuth


def build_client(api_key: str) -> SentinosClient:
    # Configure SENTINOS_BASE_URL / SENTINOS_*_URL in your environment before running.
    return SentinosClient.from_env(org_id="acme", auth=APIKeyAuth(api_key))
