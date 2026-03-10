from __future__ import annotations

from pathlib import Path

from sentinos.tools.sdk_migration_lint import lint_paths


def test_sdk_migration_lint_flags_tenant_id_first_constructor(tmp_path: Path) -> None:
    p = tmp_path / "example.py"
    p.write_text('from sentinos import SentinosClient\nclient = SentinosClient(tenant_id="acme")\n', encoding="utf-8")

    findings = lint_paths([str(tmp_path)])
    assert any(f.rule_id == "DX008-PY001" for f in findings)


def test_sdk_migration_lint_ignores_alias_documentation_lines(tmp_path: Path) -> None:
    p = tmp_path / "doc.md"
    p.write_text("export SENTINOS_ORG_ID=acme  # alias: SENTINOS_TENANT_ID\n", encoding="utf-8")

    findings = lint_paths([str(tmp_path)])
    assert not any(f.rule_id == "DX008-ENV001" for f in findings)


def test_sdk_migration_lint_flags_api_url_alias_usage(tmp_path: Path) -> None:
    p = tmp_path / "example.md"
    p.write_text('```python\nclient = SentinosClient(api_url="https://api.sentinos.ai")\n```\n', encoding="utf-8")

    findings = lint_paths([str(tmp_path)])
    assert any(f.rule_id == "DX008-PY002" for f in findings)
