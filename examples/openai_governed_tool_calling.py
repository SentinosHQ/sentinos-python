"""Example application code for governed OpenAI Responses calls with Sentinos."""

from __future__ import annotations

import json
import os

from openai import OpenAI

from sentinos import LLMGuard, SentinosClient, create_openai_responses_adapter


def main() -> None:
    client = SentinosClient.from_env(org_id=os.getenv("SENTINOS_ORG_ID"))

    guard = LLMGuard(
        kernel=client.kernel,
        agent_id=os.getenv("SENTINOS_AGENT_ID", "support-agent"),
        session_id=os.getenv("SENTINOS_SESSION_ID", "sess-python-eval"),
    )

    adapter = create_openai_responses_adapter(
        guard=guard,
        client=OpenAI(api_key=os.environ["OPENAI_API_KEY"]),
    )

    result = adapter.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {
                "role": "user",
                "content": (
                    "Summarize this customer request and explain whether a refund "
                    "tool should be called."
                ),
            }
        ],
        metadata={
            "domain": "support",
            "workflow": "refund-review",
            "riskTier": "medium",
        },
    )

    print(
        json.dumps(
            {
                "traceId": result.trace.trace_id,
                "decision": result.trace.policy_evaluation.decision,
                "reason": result.trace.policy_evaluation.reason,
                "rationaleMode": (
                    result.trace.agent_rationale.capture_mode
                    if result.trace.agent_rationale
                    else None
                ),
                "rationaleSummary": (
                    result.trace.agent_rationale.summary
                    if result.trace.agent_rationale
                    else None
                ),
                "nextStep": (
                    "Open the Sentinos console, go to Traces, and search for the "
                    "traceId above, then inspect Agent Rationale."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
