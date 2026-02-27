from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from sentinos.alerts import AlertsClient
from sentinos.incidents import IncidentsClient


def _ts() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None, dict[str, Any] | None]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("GET", path, params, None))
        if path == "/v1/alerts/rules":
            return FakeResponse({"rules": []})
        if path.startswith("/v1/alerts/rules/"):
            return FakeResponse(
                {
                    "rule_id": "r1",
                    "tenant_id": "acme",
                    "name": "High latency",
                    "description": "Latency spike",
                    "rule_type": "THRESHOLD",
                    "enabled": True,
                    "severity": "HIGH",
                    "metric_key": "latency_ms",
                    "comparator": ">",
                    "threshold_value": 500,
                    "notification_channels": [],
                    "cooldown_sec": 30,
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        if path == "/v1/alerts":
            return FakeResponse(
                {
                    "alerts": [
                        {
                            "alert_id": "a1",
                            "tenant_id": "acme",
                            "status": "FIRING",
                            "severity": "HIGH",
                            "title": "Threshold breached",
                            "created_at": _ts(),
                            "updated_at": _ts(),
                        }
                    ]
                }
            )
        if path.startswith("/v1/alerts/"):
            return FakeResponse(
                {
                    "alert_id": "a1",
                    "tenant_id": "acme",
                    "status": "FIRING",
                    "severity": "HIGH",
                    "title": "Threshold breached",
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        if path == "/v1/anomalies":
            return FakeResponse(
                {
                    "anomalies": [
                        {
                            "anomaly_id": "n1",
                            "tenant_id": "acme",
                            "type": "ZSCORE",
                            "status": "OPEN",
                            "false_positive": False,
                            "metric_key": "latency_ms",
                            "observed_value": 920,
                            "expected_value": 200,
                            "z_score": 3.2,
                            "confidence": 0.91,
                            "created_at": _ts(),
                            "updated_at": _ts(),
                        }
                    ]
                }
            )
        if path.startswith("/v1/anomalies/"):
            return FakeResponse(
                {
                    "anomaly_id": "n1",
                    "tenant_id": "acme",
                    "type": "ZSCORE",
                    "status": "OPEN",
                    "false_positive": False,
                    "metric_key": "latency_ms",
                    "observed_value": 920,
                    "expected_value": 200,
                    "z_score": 3.2,
                    "confidence": 0.91,
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        if path.startswith("/v1/incidents/"):
            return FakeResponse(
                {
                    "incident": {
                        "incident_id": "i1",
                        "tenant_id": "acme",
                        "title": "Incident",
                        "severity": "HIGH",
                        "status": "OPEN",
                        "source": "MANUAL",
                        "created_at": _ts(),
                        "updated_at": _ts(),
                    },
                    "timeline": [],
                }
            )
        return FakeResponse({"rules": [], "incidents": [], "anomalies": []})

    def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("POST", path, None, json))
        if path == "/v1/alerts/rules":
            return FakeResponse(
                {
                    "rule_id": "r1",
                    "tenant_id": "acme",
                    "name": "High latency",
                    "description": "Latency spike",
                    "rule_type": "THRESHOLD",
                    "enabled": True,
                    "severity": "HIGH",
                    "metric_key": "latency_ms",
                    "comparator": ">",
                    "threshold_value": 500,
                    "notification_channels": [],
                    "cooldown_sec": 30,
                    "created_at": _ts(),
                    "updated_at": _ts(),
                },
                status_code=201,
            )
        if path.startswith("/v1/alerts/"):
            return FakeResponse(
                {
                    "alert_id": "a1",
                    "tenant_id": "acme",
                    "status": "ACKNOWLEDGED" if path.endswith("/acknowledge") else "RESOLVED",
                    "severity": "HIGH",
                    "title": "Threshold breached",
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        if path.startswith("/v1/anomalies/"):
            return FakeResponse(
                {
                    "anomaly_id": "n1",
                    "tenant_id": "acme",
                    "type": "ZSCORE",
                    "status": "INVESTIGATING",
                    "false_positive": (json or {}).get("false_positive", False),
                    "metric_key": "latency_ms",
                    "observed_value": 920,
                    "expected_value": 200,
                    "z_score": 3.2,
                    "confidence": 0.91,
                    "created_at": _ts(),
                    "updated_at": _ts(),
                    "investigation_notes": (json or {}).get("notes"),
                }
            )
        if path == "/v1/incidents":
            return FakeResponse(
                {
                    "incident_id": "i1",
                    "tenant_id": "acme",
                    "title": "Incident",
                    "severity": "HIGH",
                    "status": "OPEN",
                    "source": "MANUAL",
                    "created_at": _ts(),
                    "updated_at": _ts(),
                },
                status_code=201,
            )
        if path.endswith("/resolve"):
            return FakeResponse(
                {
                    "incident_id": "i1",
                    "tenant_id": "acme",
                    "title": "Incident",
                    "severity": "HIGH",
                    "status": "RESOLVED",
                    "source": "MANUAL",
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        return FakeResponse({})

    def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        self.calls.append(("PUT", path, None, json))
        if path.startswith("/v1/alerts/rules/"):
            return FakeResponse(
                {
                    "rule_id": "r1",
                    "tenant_id": "acme",
                    "name": "High latency",
                    "description": "Latency spike",
                    "rule_type": "THRESHOLD",
                    "enabled": True,
                    "severity": "HIGH",
                    "metric_key": "latency_ms",
                    "comparator": ">",
                    "threshold_value": 500,
                    "notification_channels": [],
                    "cooldown_sec": 30,
                    "created_at": _ts(),
                    "updated_at": _ts(),
                }
            )
        return FakeResponse(
            {
                "incident_id": "i1",
                "tenant_id": "acme",
                "title": json.get("title", "Incident") if json else "Incident",
                "severity": "HIGH",
                "status": json.get("status", "INVESTIGATING") if json else "INVESTIGATING",
                "source": "MANUAL",
                "created_at": _ts(),
                "updated_at": _ts(),
            }
        )

    def delete(self, path: str) -> FakeResponse:
        self.calls.append(("DELETE", path, None, None))
        return FakeResponse({"ok": True})


class FakeCore:
    def __init__(self, http: FakeHTTP, headers: dict[str, str] | None = None) -> None:
        self._http = http
        self._headers = headers or {}

    def with_headers(self, headers: dict[str, str]) -> FakeCore:
        merged = dict(self._headers)
        merged.update(headers)
        return FakeCore(self._http, merged)

    def get_httpx_client(self) -> FakeHTTP:
        return self._http

    def get_async_httpx_client(self) -> AsyncFakeHTTP:
        return AsyncFakeHTTP(self._http)


class AsyncFakeHTTP:
    def __init__(self, http: FakeHTTP) -> None:
        self._http = http

    async def get(self, path: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.get(path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.post(path, json=json)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> FakeResponse:
        return self._http.put(path, json=json)

    async def delete(self, path: str) -> FakeResponse:
        return self._http.delete(path)


def test_alerts_client_requires_tenant() -> None:
    c = AlertsClient(FakeCore(FakeHTTP()))
    with pytest.raises(ValueError):
        c.list_alerts()


def test_alerts_client_lifecycle_calls() -> None:
    http = FakeHTTP()
    c = AlertsClient(FakeCore(http), tenant_id="acme")

    alerts = c.list_alerts(limit=50)
    assert len(alerts) == 1
    assert alerts[0].status == "FIRING"

    ack = c.acknowledge_alert("a1", note="looking")
    assert ack.status == "ACKNOWLEDGED"

    resolved = c.resolve_alert("a1", note="done")
    assert resolved.status == "RESOLVED"

    assert any(call[0] == "GET" and call[1] == "/v1/alerts" and call[2] == {"limit": 50} for call in http.calls)


def test_incidents_client_basic_flow() -> None:
    http = FakeHTTP()
    c = IncidentsClient(FakeCore(http), tenant_id="acme")

    created = c.create_incident(incident={"title": "Incident", "severity": "HIGH"})
    assert created.incident_id == "i1"

    updated = c.update_incident("i1", patch={"status": "INVESTIGATING", "title": "Incident-2"})
    assert updated.status == "INVESTIGATING"

    resolved = c.resolve_incident("i1", note="fixed")
    assert resolved.status == "RESOLVED"

    incident, timeline = c.get_incident("i1")
    assert incident.incident_id == "i1"
    assert timeline == []


def test_alerts_client_async_surface() -> None:
    c = AlertsClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        created_rule = await c.create_rule_async(rule={"name": "High latency"})
        listed_rules = await c.list_rules_async(limit=10)
        fetched_rule = await c.get_rule_async("r1")
        updated_rule = await c.update_rule_async("r1", rule={"enabled": True})
        delete_result = await c.delete_rule_async("r1")
        listed_alerts = await c.list_alerts_async(limit=10)
        fetched_alert = await c.get_alert_async("a1")
        acked = await c.acknowledge_alert_async("a1", note="investigating")
        resolved = await c.resolve_alert_async("a1")
        escalated = await c.escalate_alert_async("a1", escalated_to="oncall")
        anomalies = await c.list_anomalies_async(limit=5)
        anomaly = await c.get_anomaly_async("n1")
        investigated = await c.investigate_anomaly_async("n1", notes="validated", false_positive=False)

        assert created_rule.rule_id == "r1"
        assert listed_rules == []
        assert fetched_rule.rule_id == "r1"
        assert updated_rule.rule_id == "r1"
        assert delete_result["ok"] is True
        assert listed_alerts[0].alert_id == "a1"
        assert fetched_alert.alert_id == "a1"
        assert acked.status == "ACKNOWLEDGED"
        assert resolved.status == "RESOLVED"
        assert escalated.status == "RESOLVED"
        assert anomalies[0].anomaly_id == "n1"
        assert anomaly.anomaly_id == "n1"
        assert investigated.status == "INVESTIGATING"

    asyncio.run(run())


def test_incidents_client_async_flow() -> None:
    c = IncidentsClient(FakeCore(FakeHTTP()), tenant_id="acme")

    async def run() -> None:
        listed = await c.list_incidents_async(limit=20)
        created = await c.create_incident_async(incident={"title": "Incident", "severity": "HIGH"})
        updated = await c.update_incident_async("i1", patch={"status": "INVESTIGATING"})
        resolved = await c.resolve_incident_async("i1", note="fixed")
        incident, timeline = await c.get_incident_async("i1")

        assert listed == []
        assert created.incident_id == "i1"
        assert updated.status == "INVESTIGATING"
        assert resolved.status == "RESOLVED"
        assert incident.incident_id == "i1"
        assert timeline == []

    asyncio.run(run())
