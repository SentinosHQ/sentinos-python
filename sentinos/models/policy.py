from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

PolicyLanguage = Literal["rego"]
PolicySource = Literal["nl", "rego"]


class PolicyScope(BaseModel):
    model_config = ConfigDict(extra="allow")

    target_tools: list[str]
    tenants: list[str]


class PolicyMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    policy_id: str
    version: str
    scope: PolicyScope
    language: PolicyLanguage
    source: PolicySource
    created_at: datetime

    owner: str | None = None
    tags: list[str] | None = None
    severity: str | None = None
    governance_category: str | None = None
    alert_on_violation: bool | None = None
    alert_severity: str | None = None
    verification_report: dict[str, Any] | None = None

    @classmethod
    def from_core(cls, core_obj: Any) -> PolicyMetadata:
        if hasattr(core_obj, "to_dict") and callable(getattr(core_obj, "to_dict")):
            return cls.model_validate(core_obj.to_dict())
        if isinstance(core_obj, dict):
            return cls.model_validate(core_obj)
        raise TypeError("unsupported core object for PolicyMetadata.from_core")


# Backward-compat alias for older callers.
PolicyItem = PolicyMetadata
