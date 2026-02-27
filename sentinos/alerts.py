from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sentinos_core import AuthenticatedClient, Client

from .models.alert import Alert, AlertRule, Anomaly


@dataclass
class AlertsClient:
    _core: Client | AuthenticatedClient
    tenant_id: str | None = None

    def _require_tenant(self, tenant_id: str | None) -> str:
        t = (tenant_id or self.tenant_id or "").strip()
        if not t:
            raise ValueError("tenant_id is required (set it on SentinosClient or pass it per call)")
        return t

    def _core_with_headers(self, *, tenant_id: str) -> Client | AuthenticatedClient:
        return self._core.with_headers({"x-tenant-id": tenant_id})

    def create_rule(self, *, rule: dict[str, Any], tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().post("/v1/alerts/rules", json=rule)
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    async def create_rule_async(self, *, rule: dict[str, Any], tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().post("/v1/alerts/rules", json=rule)
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    def list_rules(
        self,
        *,
        enabled: bool | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[AlertRule]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/alerts/rules", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("rules") or []
        return [AlertRule.model_validate(x) for x in rows]

    async def list_rules_async(
        self,
        *,
        enabled: bool | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[AlertRule]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if enabled is not None:
            params["enabled"] = str(enabled).lower()
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/alerts/rules", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("rules") or []
        return [AlertRule.model_validate(x) for x in rows]

    def get_rule(self, rule_id: str, *, tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/alerts/rules/{rule_id}")
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    async def get_rule_async(self, rule_id: str, *, tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/alerts/rules/{rule_id}")
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    def update_rule(self, rule_id: str, *, rule: dict[str, Any], tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().put(f"/v1/alerts/rules/{rule_id}", json=rule)
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    async def update_rule_async(self, rule_id: str, *, rule: dict[str, Any], tenant_id: str | None = None) -> AlertRule:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().put(f"/v1/alerts/rules/{rule_id}", json=rule)
        resp.raise_for_status()
        return AlertRule.model_validate(resp.json())

    def delete_rule(self, rule_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().delete(f"/v1/alerts/rules/{rule_id}")
        resp.raise_for_status()
        return resp.json()

    async def delete_rule_async(self, rule_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().delete(f"/v1/alerts/rules/{rule_id}")
        resp.raise_for_status()
        return resp.json()

    def list_alerts(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        incident_id: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Alert]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if rule_id:
            params["rule_id"] = rule_id
        if incident_id:
            params["incident_id"] = incident_id
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/alerts", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("alerts") or []
        return [Alert.model_validate(x) for x in rows]

    async def list_alerts_async(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        rule_id: str | None = None,
        incident_id: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Alert]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if rule_id:
            params["rule_id"] = rule_id
        if incident_id:
            params["incident_id"] = incident_id
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/alerts", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("alerts") or []
        return [Alert.model_validate(x) for x in rows]

    def get_alert(self, alert_id: str, *, tenant_id: str | None = None) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/alerts/{alert_id}")
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    async def get_alert_async(self, alert_id: str, *, tenant_id: str | None = None) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/alerts/{alert_id}")
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    def acknowledge_alert(self, alert_id: str, *, note: str | None = None, tenant_id: str | None = None) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = c.get_httpx_client().post(f"/v1/alerts/{alert_id}/acknowledge", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    async def acknowledge_alert_async(
        self,
        alert_id: str,
        *,
        note: str | None = None,
        tenant_id: str | None = None,
    ) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = await c.get_async_httpx_client().post(f"/v1/alerts/{alert_id}/acknowledge", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    def resolve_alert(self, alert_id: str, *, note: str | None = None, tenant_id: str | None = None) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = c.get_httpx_client().post(f"/v1/alerts/{alert_id}/resolve", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    async def resolve_alert_async(
        self,
        alert_id: str,
        *,
        note: str | None = None,
        tenant_id: str | None = None,
    ) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {}
        if note is not None:
            body["note"] = note
        resp = await c.get_async_httpx_client().post(f"/v1/alerts/{alert_id}/resolve", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    def escalate_alert(
        self,
        alert_id: str,
        *,
        escalated_to: str,
        note: str | None = None,
        tenant_id: str | None = None,
    ) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"escalated_to": escalated_to}
        if note is not None:
            body["note"] = note
        resp = c.get_httpx_client().post(f"/v1/alerts/{alert_id}/escalate", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    async def escalate_alert_async(
        self,
        alert_id: str,
        *,
        escalated_to: str,
        note: str | None = None,
        tenant_id: str | None = None,
    ) -> Alert:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"escalated_to": escalated_to}
        if note is not None:
            body["note"] = note
        resp = await c.get_async_httpx_client().post(f"/v1/alerts/{alert_id}/escalate", json=body)
        resp.raise_for_status()
        return Alert.model_validate(resp.json())

    def list_anomalies(
        self,
        *,
        status: str | None = None,
        anomaly_type: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Anomaly]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if anomaly_type:
            params["type"] = anomaly_type
        if limit is not None:
            params["limit"] = limit
        resp = c.get_httpx_client().get("/v1/anomalies", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("anomalies") or []
        return [Anomaly.model_validate(x) for x in rows]

    async def list_anomalies_async(
        self,
        *,
        status: str | None = None,
        anomaly_type: str | None = None,
        limit: int | None = None,
        tenant_id: str | None = None,
    ) -> list[Anomaly]:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if anomaly_type:
            params["type"] = anomaly_type
        if limit is not None:
            params["limit"] = limit
        resp = await c.get_async_httpx_client().get("/v1/anomalies", params=params)
        resp.raise_for_status()
        rows = (resp.json() or {}).get("anomalies") or []
        return [Anomaly.model_validate(x) for x in rows]

    def get_anomaly(self, anomaly_id: str, *, tenant_id: str | None = None) -> Anomaly:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = c.get_httpx_client().get(f"/v1/anomalies/{anomaly_id}")
        resp.raise_for_status()
        return Anomaly.model_validate(resp.json())

    async def get_anomaly_async(self, anomaly_id: str, *, tenant_id: str | None = None) -> Anomaly:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        resp = await c.get_async_httpx_client().get(f"/v1/anomalies/{anomaly_id}")
        resp.raise_for_status()
        return Anomaly.model_validate(resp.json())

    def investigate_anomaly(
        self,
        anomaly_id: str,
        *,
        notes: str | None = None,
        false_positive: bool = False,
        tenant_id: str | None = None,
    ) -> Anomaly:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"false_positive": false_positive}
        if notes is not None:
            body["notes"] = notes
        resp = c.get_httpx_client().post(f"/v1/anomalies/{anomaly_id}/investigate", json=body)
        resp.raise_for_status()
        return Anomaly.model_validate(resp.json())

    async def investigate_anomaly_async(
        self,
        anomaly_id: str,
        *,
        notes: str | None = None,
        false_positive: bool = False,
        tenant_id: str | None = None,
    ) -> Anomaly:
        t = self._require_tenant(tenant_id)
        c = self._core_with_headers(tenant_id=t)
        body: dict[str, Any] = {"false_positive": false_positive}
        if notes is not None:
            body["notes"] = notes
        resp = await c.get_async_httpx_client().post(f"/v1/anomalies/{anomaly_id}/investigate", json=body)
        resp.raise_for_status()
        return Anomaly.model_validate(resp.json())
