"""Run the full live Sentinos + OpenAI end-to-end suite."""

from __future__ import annotations

import argparse
import json
from typing import Any

if __package__ in (None, ""):
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))

from common import info, load_config, write_artifact  # noqa: E402
from stage_01_setup import run_stage as run_stage_01  # noqa: E402
from stage_02_openai_traffic import run_stage as run_stage_02  # noqa: E402
from stage_03_triage import run_stage as run_stage_03  # noqa: E402
from stage_04_verify import run_stage as run_stage_04  # noqa: E402


STAGE_ORDER = ("setup", "traffic", "triage", "verify")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run live Sentinos OpenAI E2E suite")
    parser.add_argument(
        "--stages",
        default="setup,traffic,triage,verify",
        help="Comma-separated list of stages to run (setup,traffic,triage,verify)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running later stages when an earlier stage fails",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    selected = tuple(part.strip().lower() for part in args.stages.split(",") if part.strip())
    unknown = [name for name in selected if name not in STAGE_ORDER]
    if unknown:
        raise SystemExit(f"Unknown stages: {unknown}. Allowed stages: {STAGE_ORDER}")

    require_openai = "traffic" in selected
    config = load_config(require_openai_key=require_openai)
    info(f"Running live E2E suite run_id={config.run_id} stages={selected}")

    stage_map = {
        "setup": run_stage_01,
        "traffic": run_stage_02,
        "triage": run_stage_03,
        "verify": run_stage_04,
    }

    summary: dict[str, Any] = {
        "run_id": config.run_id,
        "tenant_id": config.tenant_id,
        "org_id": config.tenant_id,
        "stages_requested": selected,
        "stages_completed": [],
        "stages_failed": [],
    }

    for stage_name in STAGE_ORDER:
        if stage_name not in selected:
            continue
        stage_fn = stage_map[stage_name]
        info(f"Starting stage: {stage_name}")
        try:
            result = stage_fn(config)
            summary["tenant_id"] = config.tenant_id
            summary["org_id"] = config.tenant_id
            summary["stages_completed"].append(
                {
                    "stage": stage_name,
                    "artifact": f"{config.artifacts_dir}/{result.get('stage')}.json",
                }
            )
        except Exception as exc:  # noqa: BLE001
            summary["tenant_id"] = config.tenant_id
            summary["org_id"] = config.tenant_id
            summary["stages_failed"].append({"stage": stage_name, "error": str(exc)})
            info(f"Stage failed: {stage_name} -> {exc}")
            if not args.continue_on_error:
                break

    summary_path = write_artifact(config, "run_summary", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    info(f"Run summary -> {summary_path}")

    if summary["stages_failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
