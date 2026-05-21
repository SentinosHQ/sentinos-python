"""LangGraph multi-step workflow with a governed action and operator-review branch."""

from __future__ import annotations

import json
import os
from typing import Any, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ModuleNotFoundError as exc:
    raise ImportError(
        "Optional dependency 'langgraph' is not installed. Install with: pip install 'sentinos[langgraph]'"
    ) from exc

from sentinos import LLMGuard, SentinosClient, make_guarded_tool


class RefundWorkflowState(TypedDict, total=False):
    ticket_id: str
    customer_id: str
    refund_amount: int
    original_reason: str
    risk_tier: str
    request_summary: str
    trace_id: str
    decision: str
    reason: str
    route: str
    workflow_status: str
    next_step: str
    tool_result: dict[str, Any]


def triage_refund_request(state: RefundWorkflowState) -> RefundWorkflowState:
    amount = int(state["refund_amount"])
    risk_tier = "high" if amount >= 1000 else "medium"
    return {"risk_tier": risk_tier}


def collect_context(state: RefundWorkflowState) -> RefundWorkflowState:
    summary = (
        f"Ticket {state['ticket_id']} requests a USD refund of {state['refund_amount']} "
        f"for customer {state['customer_id']} because {state['original_reason']}."
    )
    return {"request_summary": summary}


def build_workflow(*, guard: LLMGuard):
    guarded_refund = make_guarded_tool(
        guard=guard,
        tool_name="stripe.refund",
        execute=lambda **kwargs: {
            "ok": True,
            "refund_id": f"refund-{kwargs['ticket_id']}",
            "amount": kwargs["amount"],
            "currency": kwargs["currency"],
        },
    )

    def governed_refund(state: RefundWorkflowState) -> RefundWorkflowState:
        result = guarded_refund(
            amount=state["refund_amount"],
            currency="USD",
            customer_id=state["customer_id"],
            ticket_id=state["ticket_id"],
            request_summary=state["request_summary"],
            risk_tier=state["risk_tier"],
        )
        decision = str(result["decision"]).upper()
        reason = str(result.get("reason") or "rule-evaluated")
        route = "complete" if decision in {"ALLOW", "SHADOW"} else "operator_review"
        next_step = (
            "Open the Sentinos console, go to Traces, search for the traceId above, and inspect Agent Rationale."
            if route == "complete"
            else "Open the Sentinos console, go to Kernel or Traces, and inspect why the workflow paused."
        )
        update: RefundWorkflowState = {
            "trace_id": str(result["trace_id"]),
            "decision": decision,
            "reason": reason,
            "route": route,
            "next_step": next_step,
        }
        if "result" in result:
            update["tool_result"] = result["result"]
        return update

    def route_after_governance(state: RefundWorkflowState) -> str:
        return state["route"]

    def complete(state: RefundWorkflowState) -> RefundWorkflowState:
        return {"workflow_status": "completed"}

    def operator_review(state: RefundWorkflowState) -> RefundWorkflowState:
        return {"workflow_status": "awaiting_operator_review"}

    graph = StateGraph(RefundWorkflowState)
    graph.add_node("triage_refund_request", triage_refund_request)
    graph.add_node("collect_context", collect_context)
    graph.add_node("governed_refund", governed_refund)
    graph.add_node("complete", complete)
    graph.add_node("operator_review", operator_review)
    graph.add_edge(START, "triage_refund_request")
    graph.add_edge("triage_refund_request", "collect_context")
    graph.add_edge("collect_context", "governed_refund")
    graph.add_conditional_edges(
        "governed_refund",
        route_after_governance,
        {"complete": "complete", "operator_review": "operator_review"},
    )
    graph.add_edge("complete", END)
    graph.add_edge("operator_review", END)
    return graph.compile()


def main() -> None:
    client = SentinosClient.from_env(org_id=os.getenv("SENTINOS_ORG_ID"))
    guard = LLMGuard(
        kernel=client.kernel,
        agent_id=os.getenv("SENTINOS_AGENT_ID", "refund-ops-agent"),
        session_id=os.getenv("SENTINOS_SESSION_ID", "sess-langgraph-eval"),
    )

    workflow = build_workflow(guard=guard)
    final_state = workflow.invoke(
        {
            "ticket_id": os.getenv("SENTINOS_TICKET_ID", "ticket-2048"),
            "customer_id": os.getenv("SENTINOS_CUSTOMER_ID", "cust-2048"),
            "refund_amount": int(os.getenv("SENTINOS_REFUND_AMOUNT", "1200")),
            "original_reason": os.getenv("SENTINOS_REFUND_REASON", "duplicate charge on subscription renewal"),
        }
    )

    print(
        json.dumps(
            {
                "traceId": final_state["trace_id"],
                "decision": final_state["decision"],
                "reason": final_state["reason"],
                "route": final_state["route"],
                "workflowStatus": final_state["workflow_status"],
                "rationaleMode": "sdk_derived",
                "rationaleSummary": "Authorize tool-runtime.stripe.refund before execution.",
                "nextStep": final_state["next_step"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
