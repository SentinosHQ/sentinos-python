"""Govern a mocked x402 agentic payment before payment proof is attached."""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from sentinos import SentinosClient


@dataclass(frozen=True)
class MockX402Response:
    status: int
    headers: dict[str, str]
    body: dict[str, Any]


class MockX402Service:
    merchant = "agentic-market-demo"

    def __init__(self) -> None:
        self.requirement = {
            "x402Version": 1,
            "accepts": [
                {
                    "scheme": "exact",
                    "network": "base-sepolia",
                    "asset": "USDC",
                    "maxAmountRequired": "0.25",
                    "resource": "https://api.agentic-market.example/search/company-risk",
                    "payTo": "0x1111111111111111111111111111111111111111",
                    "description": "Company risk dataset lookup",
                }
            ],
        }

    def request(self, headers: dict[str, str] | None = None) -> MockX402Response:
        headers = headers or {}
        payment = headers.get("PAYMENT-SIGNATURE") or headers.get("PAYMENT") or headers.get("X-PAYMENT")
        if not payment:
            encoded = base64.urlsafe_b64encode(json.dumps(self.requirement).encode("utf-8")).decode("ascii").rstrip("=")
            return MockX402Response(
                status=402,
                headers={"PAYMENT-REQUIRED": encoded},
                body={"error": "payment_required", "merchant": self.merchant},
            )
        return MockX402Response(
            status=200,
            headers={"PAYMENT-RESPONSE": "settlement_mock_x402_base_sepolia_usdc_001"},
            body={"merchant": self.merchant, "risk_score": "low", "records": 3},
        )


def _decode_payment_required(header: str) -> dict[str, Any]:
    padded = header + "=" * (-len(header) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def _mock_payment_proof(requirement: dict[str, Any], wallet_id: str) -> str:
    proof = {
        "x402Version": 1,
        "scheme": requirement["scheme"],
        "network": requirement["network"],
        "asset": requirement["asset"],
        "resource": requirement["resource"],
        "wallet_id": wallet_id,
        "authorization": "mock-signature-for-governed-example",
    }
    return base64.urlsafe_b64encode(json.dumps(proof).encode("utf-8")).decode("ascii").rstrip("=")


def main() -> None:
    client = SentinosClient.from_env(org_id=os.getenv("SENTINOS_ORG_ID"))
    service = MockX402Service()
    tenant_id = os.getenv("SENTINOS_ORG_ID", "acme")
    agent_id = os.getenv("SENTINOS_AGENT_ID", "procurement-agent")
    session_id = os.getenv("SENTINOS_SESSION_ID", f"sess-x402-{int(time.time())}")

    first_response = service.request()
    if first_response.status != 402:
        raise RuntimeError(f"expected mocked x402 service to return 402, got {first_response.status}")

    payment_required = _decode_payment_required(first_response.headers["PAYMENT-REQUIRED"])
    requirement = payment_required["accepts"][0]
    payment_context = {
        "protocol": "x402",
        "merchant": service.merchant,
        "resource": requirement["resource"],
        "scheme": requirement["scheme"],
        "network": requirement["network"],
        "asset": requirement["asset"],
        "amount": requirement["maxAmountRequired"],
        "pay_to": requirement["payTo"],
        "budget_window": {
            "max_usd": "1.00",
            "expires_in_seconds": 300,
        },
    }

    trace = client.kernel.execute(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        intent={
            "type": "payment_authorization",
            "tool": "payment.x402",
            "args": payment_context,
        },
        metadata={
            "skip_connector": True,
            "integration_kind": "agentic_payment",
            "payment_context": payment_context,
            "agent_rationale": {
                "capture_mode": "workflow_supplied",
                "summary": "Authorize x402 payment proof attachment before requesting the paid resource.",
                "goal": "Fetch the company risk dataset within the session budget.",
                "decision_basis": [
                    "Payment protocol: x402",
                    f"Merchant: {service.merchant}",
                    f"Resource: {requirement['resource']}",
                    f"Amount: {requirement['maxAmountRequired']} {requirement['asset']}",
                ],
                "expected_outcome": "Attach payment proof only after Sentinos allows or shadows the authorization.",
                "confidence": 0.82,
                "risk_context": {
                    "data_class": "business",
                    "side_effects": ["payment_authorization", "external_api_access"],
                    "external_domains": ["api.agentic-market.example"],
                    "requires_approval": False,
                },
            },
        },
    )
    decision = str(trace.decision).upper()

    settlement_reference = ""
    if decision in {"ALLOW", "SHADOW"}:
        proof = _mock_payment_proof(requirement, os.getenv("X402_WALLET_ID", "wallet_mock_agentic_payments"))
        paid_response = service.request({"PAYMENT-SIGNATURE": proof})
        settlement_reference = paid_response.headers.get("PAYMENT-RESPONSE", "")
        client.kernel.append_session_event(
            session_id=session_id,
            event_type="payment.x402",
            payload={
                "provider": "x402",
                "operation": "pay",
                "decision": decision,
                "trace_id": trace.trace_id,
                "summary": {
                    "merchant": service.merchant,
                    "resource": requirement["resource"],
                    "amount": requirement["maxAmountRequired"],
                    "asset": requirement["asset"],
                    "network": requirement["network"],
                    "settlement_reference": settlement_reference,
                    "response_status": paid_response.status,
                },
            },
            tenant_id=tenant_id,
        )

    print(
        json.dumps(
            {
                "traceId": trace.trace_id,
                "decision": decision,
                "rationaleMode": (
                    trace.agent_rationale.capture_mode
                    if trace.agent_rationale
                    else None
                ),
                "rationaleSummary": (
                    trace.agent_rationale.summary
                    if trace.agent_rationale
                    else None
                ),
                "protocol": "x402",
                "merchant": service.merchant,
                "resource": requirement["resource"],
                "amount": requirement["maxAmountRequired"],
                "network": requirement["network"],
                "asset": requirement["asset"],
                "settlementReference": settlement_reference,
                "nextStep": (
                    "Open the Sentinos console, search for the traceId in Traces, and inspect "
                    "Agent Rationale before enabling live wallet settlement."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
