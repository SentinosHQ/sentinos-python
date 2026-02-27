from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int
    message: str
    snippet: str
    suggestion: str

    def to_json(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "snippet": self.snippet,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class Rule:
    rule_id: str
    message: str
    suggestion: str
    exts: set[str]
    pattern: re.Pattern[str]

    def match_line(self, *, path: Path, line: str) -> bool:
        if path.suffix.lower() not in self.exts:
            return False
        return bool(self.pattern.search(line))


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".venv-sdk-quality",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}


RULES: list[Rule] = [
    Rule(
        rule_id="DX008-PY001",
        message="Prefer org_id/from_env over tenant_id-first SentinosClient initialization.",
        suggestion="Use SentinosClient.from_env(org_id=...) or SentinosClient.simple(base_url=..., org_id=...).",
        exts={".py", ".md"},
        pattern=re.compile(r"\bSentinosClient\s*\([^)]*\btenant_id\s*="),
    ),
    Rule(
        rule_id="DX008-PY002",
        message="Prefer base_url over api_url/url aliases in new code and docs.",
        suggestion="Use base_url=... (or SentinosClient.simple(base_url=..., ...)).",
        exts={".py", ".md"},
        pattern=re.compile(r"\bSentinosClient\s*\([^)]*\b(api_url|url)\s*="),
    ),
    Rule(
        rule_id="DX008-ENV001",
        message="Prefer SENTINOS_ORG_ID over SENTINOS_TENANT_ID in docs and examples (alias remains supported).",
        suggestion="Replace SENTINOS_TENANT_ID with SENTINOS_ORG_ID and add '(alias: SENTINOS_TENANT_ID)' if needed.",
        exts={".md", ".py"},
        pattern=re.compile(r"\bSENTINOS_TENANT_ID\b"),
    ),
]


def _iter_files(paths: Iterable[Path], *, exclude_dirs: set[str]) -> Iterable[Path]:
    for p in paths:
        if p.is_file():
            yield p
            continue
        if not p.exists():
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for name in files:
                yield Path(root) / name


def lint_paths(
    paths: list[str],
    *,
    exts: set[str] | None = None,
    exclude_dirs: set[str] | None = None,
) -> list[Finding]:
    exclude = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    wanted_exts = exts or {".py", ".md"}
    findings: list[Finding] = []

    for file_path in _iter_files([Path(p) for p in paths], exclude_dirs=exclude):
        if file_path.suffix.lower() not in wanted_exts:
            continue

        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError:
            continue

        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            # Avoid flagging the compatibility note where we explicitly document the alias.
            if "alias:" in stripped.lower() and "sentinos_tenant_id" in stripped.lower():
                continue
            if "SENTINOS_ORG_ID" in stripped and "SENTINOS_TENANT_ID" in stripped:
                # Explicitly acknowledging the alias; that's the preferred docs pattern.
                continue
            for rule in RULES:
                if rule.match_line(path=file_path, line=stripped):
                    findings.append(
                        Finding(
                            rule_id=rule.rule_id,
                            path=str(file_path),
                            line=idx,
                            message=rule.message,
                            snippet=stripped[:200],
                            suggestion=rule.suggestion,
                        )
                    )
    return findings


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sentinos SDK migration lint (DX-008)")
    parser.add_argument("paths", nargs="+", help="File or directory paths to scan.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail", action="store_true", help="Exit non-zero if any findings are detected.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    findings = lint_paths(args.paths)

    if args.format == "json":
        print(json.dumps({"findings": [f.to_json() for f in findings]}, indent=2, sort_keys=True))
    else:
        for f in findings:
            print(f"{f.rule_id} {f.path}:{f.line}: {f.message}")
            print(f"  found: {f.snippet}")
            print(f"  suggest: {f.suggestion}")
        print(f"scan complete: {len(findings)} finding(s)")

    if args.fail and findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
