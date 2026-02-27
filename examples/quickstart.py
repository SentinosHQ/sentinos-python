"""Quickstart SDK example."""

from sentinos import SentinosClient
from sentinos.auth.jwt import JWTAuth


def build_client(token: str) -> SentinosClient:
    # Works in local dev with SDK defaults (localhost ports), and in production when
    # SENTINOS_BASE_URL / SENTINOS_*_URL env vars are set.
    return SentinosClient.from_env(org_id="acme", auth=JWTAuth(lambda: token))


def run_example() -> None:
    client = build_client("dev-token")
    traces = client.traces.list_traces()
    print(f"Connected. Traces returned: {len(traces)}")


if __name__ == "__main__":
    run_example()
