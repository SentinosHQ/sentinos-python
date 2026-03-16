from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .cost import TraceCostBreakdown, TraceCostEvent
from .lineage import TraceArtifactLineageSummary


class DecisionTraceIntent(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    tool: str
    args: dict[str, Any] | None = None


class DecisionTraceEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    rule: str | None = None
    snippet: str | None = None
    hit: bool | None = None
    confidence: float | None = None


Decision = Literal["ALLOW", "DENY", "ESCALATE", "SHADOW"]
DecisionTraceCheckCategory = Literal[
    "permission",
    "approval",
    "budget",
    "privacy",
    "handoff",
    "identity",
    "tool",
    "context",
    "other",
]
DecisionTraceCheckStatus = Literal["CHECKED", "ALLOWED", "DENIED", "ESCALATED", "SHADOWED"]


class DecisionTracePolicyCheck(BaseModel):
    model_config = ConfigDict(extra="allow")

    key: str
    label: str
    category: DecisionTraceCheckCategory
    status: DecisionTraceCheckStatus
    reason: str | None = None
    matched: bool | None = None
    metadata: dict[str, Any] | None = None


class DecisionTracePolicyEvaluation(BaseModel):
    model_config = ConfigDict(extra="allow")

    policy_id: str
    policy_version: str | None = None
    decision: Decision
    reason: str | None = None
    evidence: list[DecisionTraceEvidenceItem] | None = None
    explain_plan: dict[str, Any] | None = None
    checks: list[DecisionTracePolicyCheck] | None = None


PolicyEvaluation = DecisionTracePolicyEvaluation


class DecisionTraceSignatures(BaseModel):
    model_config = ConfigDict(extra="allow")

    signed_by: str | None = None
    key_id: str | None = None
    alg: str | None = None
    sig: str | None = None  # base64


class DecisionTrace(BaseModel):
    """
    Canonical Decision Trace (decision-trace.v1).

    This is a pydantic wrapper around the generated core models, with helpers for:
    - deterministic JSON serialization
    - signature verification
    """

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["decision-trace.v1"] = "decision-trace.v1"

    trace_id: str
    timestamp: datetime
    tenant_id: str

    agent_id: str | None = None
    session_id: str | None = None

    intent: DecisionTraceIntent
    tool_call: DecisionTraceIntent | None = None

    context_snapshot_id: str | None = None
    context_snapshot: dict[str, Any] | None = None

    policy_evaluation: DecisionTracePolicyEvaluation
    outcome: dict[str, Any] | None = None
    provenance: list[Any] | None = None
    signatures: DecisionTraceSignatures | None = None
    distributed_trace_id: str | None = None
    distributed_span_id: str | None = None
    cost_breakdown: TraceCostBreakdown | None = None
    cost_events: list[TraceCostEvent] | None = None
    artifact_lineage_summary: TraceArtifactLineageSummary | None = None

    @property
    def decision(self) -> Decision:
        return self.policy_evaluation.decision

    @classmethod
    def from_core(cls, core_obj: Any) -> DecisionTrace:
        if hasattr(core_obj, "to_dict") and callable(getattr(core_obj, "to_dict")):
            return cls.model_validate(core_obj.to_dict())
        if isinstance(core_obj, dict):
            return cls.model_validate(core_obj)
        raise TypeError("unsupported core object for DecisionTrace.from_core")

    def _canonical_json_bytes(self, obj: Any) -> bytes:
        # Match Go's canonicalizeJSON behavior closely:
        # - sort keys
        # - compact separators
        # - do not ASCII-escape unicode
        # - escape <, >, & (Go encoding/json default EscapeHTML=true)
        s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        s = s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        return s.encode("utf-8")

    def to_json(self) -> str:
        return self._canonical_json_bytes(self.model_dump(mode="json", exclude_none=True)).decode("utf-8")

    def _payload_for_signature(self) -> bytes:
        d = self.model_dump(mode="json", exclude_none=True)
        sigs = d.get("signatures")
        if isinstance(sigs, dict):
            sigs = dict(sigs)
            sigs["sig"] = ""
            d["signatures"] = sigs
        return self._canonical_json_bytes(d)

    def verify_signature(
        self,
        public_key_provider: Callable[[str], str | bytes],
        *,
        require_alg: str = "RS256",
    ) -> bool:
        """
        Verify `signatures.sig` over canonical JSON of the trace with `signatures.sig` blanked.

        `public_key_provider(key_id)` must return an RSA public key PEM (bytes or str).
        """
        if self.signatures is None or not self.signatures.sig:
            raise ValueError("missing signatures.sig")
        if not self.signatures.key_id:
            raise ValueError("missing signatures.key_id")
        if require_alg and (self.signatures.alg or "") != require_alg:
            raise ValueError(f"unsupported signatures.alg: {self.signatures.alg!r}")

        pem = public_key_provider(self.signatures.key_id)
        if isinstance(pem, str):
            pem_bytes = pem.encode("utf-8")
        else:
            pem_bytes = pem

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils
        except Exception as e:  # pragma: no cover
            raise ImportError("cryptography is required for signature verification") from e

        pub = serialization.load_pem_public_key(pem_bytes)
        if not isinstance(pub, rsa.RSAPublicKey):
            raise ValueError("public key must be an RSA public key for RS256 verification")
        sig = base64.b64decode(self.signatures.sig)

        payload = self._payload_for_signature()
        digest = hashlib.sha256(payload).digest()
        pub.verify(sig, digest, padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
        return True
