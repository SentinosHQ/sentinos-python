"""API key authentication example."""

from sentinos import SentinosClient
from sentinos.auth.api_key import APIKeyAuth


def build_client(api_key: str) -> SentinosClient:
    # Works in local dev with SDK defaults (localhost ports), and in production when
    # SENTINOS_BASE_URL / SENTINOS_*_URL env vars are set.
    return SentinosClient.from_env(org_id="acme", auth=APIKeyAuth(api_key))
