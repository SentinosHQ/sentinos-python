from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# The live E2E suite is intentionally runnable from a source checkout without installing
# the examples as a Python package. For tests, we add the examples directory to sys.path
# so we can import the live_e2e package (it contains __init__.py).
EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

live_e2e_common = importlib.import_module("live_e2e.common")
LiveE2EError = live_e2e_common.LiveE2EError
_rego_package_from_policy_id = live_e2e_common._rego_package_from_policy_id
load_config = live_e2e_common.load_config


def test_live_e2e_load_config_token_mode_accepts_org_id_alias(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SENTINOS_E2E_AUTH_MODE", "token")
    monkeypatch.setenv("SENTINOS_ORG_ID", "acme")
    monkeypatch.setenv("SENTINOS_ACCESS_TOKEN", "token-1")
    monkeypatch.setenv("SENTINOS_E2E_ARTIFACTS_DIR", str(tmp_path / "artifacts"))

    cfg = load_config(require_openai_key=False)
    assert cfg.tenant_id == "acme"
    assert cfg.artifacts_dir.exists()


def test_live_e2e_load_config_requires_openai_key_when_requested(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SENTINOS_E2E_AUTH_MODE", "token")
    monkeypatch.setenv("SENTINOS_ORG_ID", "acme")
    monkeypatch.setenv("SENTINOS_ACCESS_TOKEN", "token-1")
    monkeypatch.setenv("SENTINOS_E2E_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LiveE2EError, match="OPENAI_API_KEY is required"):
        load_config(require_openai_key=True)


def test_live_e2e_rego_package_from_policy_id_is_sanitized() -> None:
    pkg = _rego_package_from_policy_id("sentinos/live-e2e/openai-governance-2026-02-17")
    assert pkg.startswith("sentinos.sentinos.")
    assert "live_e2e" in pkg
    assert "-" not in pkg
