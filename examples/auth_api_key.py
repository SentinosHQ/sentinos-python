"""Show how to pair an API key with the canonical environment setup."""

import os

from sentinos import SentinosClient
from sentinos.auth.api_key import APIKeyAuth


def run_example() -> None:
    api_key = os.getenv("SENTINOS_API_KEY")
    if not api_key:
        raise SystemExit("Set SENTINOS_API_KEY along with the standard environment variables before running.")
    client = SentinosClient.from_env(auth=APIKeyAuth(api_key))
    metrics = client.kernel.get_runtime_metrics()
    print("Authenticated with API key.", "Kernel metrics:", metrics)


if __name__ == "__main__":
    run_example()
