"""Stage 00: create/login a controlplane account and emit auth env exports for SDK flows."""

from __future__ import annotations

if __package__ in (None, ""):
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))

from common import (  # noqa: E402
    bootstrap_account_if_needed,
    info,
    load_config,
    write_artifact,
)


def main() -> None:
    config = load_config(require_openai_key=False)
    if config.auth_mode != "bootstrap":
        raise SystemExit(
            "stage_00_bootstrap_account requires SENTINOS_E2E_AUTH_MODE=bootstrap and "
            "SENTINOS_BOOTSTRAP_EMAIL/SENTINOS_BOOTSTRAP_PASSWORD"
        )

    result = bootstrap_account_if_needed(config)
    artifact = {
        "stage": "stage_00_bootstrap_account",
        "run_id": config.run_id,
        "result": result,
        "tenant_id": config.tenant_id,
    }
    artifact_path = write_artifact(config, "stage_00_bootstrap_account", artifact)

    print("")
    print("# Export these for subsequent SDK E2E stages:")
    print(f"export SENTINOS_ORG_ID='{config.tenant_id}'  # alias: SENTINOS_TENANT_ID")
    print(f"export SENTINOS_ACCESS_TOKEN='{config.access_token}'")
    print("export SENTINOS_E2E_AUTH_MODE='token'")
    print("")
    info(f"Stage 00 complete -> {artifact_path}")


if __name__ == "__main__":
    main()
