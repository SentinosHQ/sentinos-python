from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class APIKeyRecord:
    key_id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: list[str]
    created_at: str
    expires_at: str | None = None
    revoked_at: str | None = None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> APIKeyRecord:
        return APIKeyRecord(
            key_id=str(d.get("key_id") or ""),
            tenant_id=str(d.get("tenant_id") or ""),
            name=str(d.get("name") or ""),
            key_prefix=str(d.get("key_prefix") or ""),
            scopes=[str(x) for x in (d.get("scopes") or [])],
            created_at=str(d.get("created_at") or ""),
            expires_at=(str(d["expires_at"]) if d.get("expires_at") is not None else None),
            revoked_at=(str(d["revoked_at"]) if d.get("revoked_at") is not None else None),
        )
