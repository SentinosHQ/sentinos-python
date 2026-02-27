from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def _base_url(value: str | None) -> str:
    if value and value.strip():
        return value.strip().rstrip("/")
    env = (
        os.getenv("SENTINOS_CONTROLPLANE_URL", "").strip()
        or os.getenv("SENTINOS_APP_URL", "").strip()
        or os.getenv("SENTINOS_CONSOLE_URL", "").strip()
    )
    if not env:
        raise SystemExit("SENTINOS_CONTROLPLANE_URL is required (or set SENTINOS_APP_URL, or pass --controlplane-url)")
    return env.rstrip("/")


def _post_json(url: str, payload: dict[str, Any], *, bearer: str | None = None) -> dict[str, Any]:
    headers = {"content-type": "application/json"}
    if bearer and bearer.strip():
        headers["authorization"] = f"Bearer {bearer.strip()}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = ""
        raise SystemExit(f"HTTP {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"request failed: {exc}") from exc

    try:
        payload_out = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"non-JSON response: {raw}") from exc
    if not isinstance(payload_out, dict):
        raise SystemExit("expected JSON object response")
    return payload_out


def _print_json(value: dict[str, Any]) -> None:
    json.dump(value, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def cmd_exchange(args: argparse.Namespace) -> int:
    controlplane_url = _base_url(args.controlplane_url)
    payload: dict[str, Any] = {
        "org_id": args.org_id or os.getenv("SENTINOS_ORG_ID", "").strip(),
        "idp_issuer": args.idp_issuer
        or os.getenv("SENTINOS_WORKFORCE_IDP_ISSUER", "").strip()
        or os.getenv("SENTINOS_WORKFORCE_AUTH_MODE", "").strip(),
        "external_subject": args.external_subject,
    }
    if not payload["org_id"] or not payload["idp_issuer"] or not payload["external_subject"]:
        raise SystemExit("org_id, idp_issuer, and external_subject are required")
    if args.email:
        payload["email"] = args.email
    if args.display_name:
        payload["display_name"] = args.display_name
    if args.groups:
        payload["groups"] = [g.strip() for g in args.groups.split(",") if g.strip()]
    if args.audience:
        payload["audience"] = args.audience
    if args.requested_ttl_minutes:
        payload["requested_ttl_minutes"] = args.requested_ttl_minutes
    if args.assertion_token:
        payload["assertion_token"] = args.assertion_token
    if args.token_binding_value:
        payload["token_binding_value"] = args.token_binding_value
    if args.device_id:
        payload["device_id"] = args.device_id

    out = _post_json(f"{controlplane_url}/v1/workforce/token/exchange", payload)
    _print_json(out)
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    controlplane_url = _base_url(args.controlplane_url)
    out = _post_json(
        f"{controlplane_url}/v1/workforce/token/refresh",
        {"refresh_token": args.refresh_token},
    )
    _print_json(out)
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    controlplane_url = _base_url(args.controlplane_url)
    if not args.access_token:
        raise SystemExit("--access-token is required for revoke")
    payload: dict[str, Any] = {}
    if args.session_id:
        payload["session_id"] = args.session_id
    out = _post_json(
        f"{controlplane_url}/v1/workforce/token/revoke",
        payload,
        bearer=args.access_token,
    )
    _print_json(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sentinos-workforce-auth",
        description="Workforce token exchange utilities for enterprise Sentinos deployments.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("exchange", help="Exchange enterprise identity assertion for Sentinos workforce token")
    ex.add_argument("--controlplane-url", help="Controlplane base URL")
    ex.add_argument("--org-id", help="Organization ID")
    ex.add_argument("--idp-issuer", help="Trusted IdP issuer URL")
    ex.add_argument("--external-subject", required=True, help="External workforce subject (IdP sub)")
    ex.add_argument("--email")
    ex.add_argument("--display-name")
    ex.add_argument("--groups", help="Comma-separated group list")
    ex.add_argument("--audience", help="Expected audience claim")
    ex.add_argument("--requested-ttl-minutes", type=int)
    ex.add_argument("--assertion-token", help="Signed IdP JWT assertion")
    ex.add_argument("--token-binding-value")
    ex.add_argument("--device-id")
    ex.set_defaults(func=cmd_exchange)

    rf = sub.add_parser("refresh", help="Refresh workforce access token")
    rf.add_argument("--controlplane-url", help="Controlplane base URL")
    rf.add_argument("--refresh-token", required=True)
    rf.set_defaults(func=cmd_refresh)

    rv = sub.add_parser("revoke", help="Revoke workforce session")
    rv.add_argument("--controlplane-url", help="Controlplane base URL")
    rv.add_argument("--access-token", required=True, help="Current Sentinos access token")
    rv.add_argument("--session-id", help="Optional session id (defaults to current)")
    rv.set_defaults(func=cmd_revoke)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
