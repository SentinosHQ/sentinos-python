from __future__ import annotations

import json
from typing import Any

from sentinos.auth import workforce_cli


class _FakeHTTPResponse:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeHTTPResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_cli_exchange_posts_expected_payload(monkeypatch, capsys) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(req, timeout=15.0):  # noqa: ARG001
        seen["url"] = req.full_url
        seen["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeHTTPResponse({"tokens": {"access_token": "a1", "refresh_token": "r1"}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    rc = workforce_cli.main(
        [
            "exchange",
            "--controlplane-url",
            "https://cp.example",
            "--org-id",
            "org-1",
            "--idp-issuer",
            "https://idp.example",
            "--external-subject",
            "emp-1",
            "--groups",
            "AI_USERS,FINANCE",
            "--audience",
            "sentinos-workforce",
        ]
    )
    assert rc == 0
    assert seen["url"] == "https://cp.example/v1/workforce/token/exchange"
    assert seen["payload"]["org_id"] == "org-1"
    assert seen["payload"]["groups"] == ["AI_USERS", "FINANCE"]
    out = capsys.readouterr().out
    assert '"access_token": "a1"' in out


def test_cli_refresh_posts_refresh_token(monkeypatch, capsys) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(req, timeout=15.0):  # noqa: ARG001
        seen["url"] = req.full_url
        seen["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeHTTPResponse({"access_token": "a2"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    rc = workforce_cli.main(
        [
            "refresh",
            "--controlplane-url",
            "https://cp.example",
            "--refresh-token",
            "refresh-123",
        ]
    )
    assert rc == 0
    assert seen["url"] == "https://cp.example/v1/workforce/token/refresh"
    assert seen["payload"] == {"refresh_token": "refresh-123"}
    out = capsys.readouterr().out
    assert '"access_token": "a2"' in out

