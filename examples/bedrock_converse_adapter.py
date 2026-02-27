"""Amazon Bedrock Converse governance examples using Sentinos SDK adapters."""

from __future__ import annotations

from sentinos import LLMGuard, SentinosClient, create_bedrock_converse_adapter


class _FakeBedrockClient:
    @staticmethod
    def converse(**kwargs):
        return {
            "output": {"message": {"content": [{"text": "Bedrock sync answer"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 12, "outputTokens": 5, "totalTokens": 17},
            "metrics": {"latencyMs": 31},
            "request": kwargs,
        }

    @staticmethod
    def converse_stream(**kwargs):
        return {
            "stream": iter(
                [
                    {"contentBlockDelta": {"delta": {"text": "Hello "}}},
                    {"contentBlockDelta": {"delta": {"text": "from Bedrock"}}},
                    {"messageStop": {"stopReason": "end_turn"}},
                    {
                        "metadata": {
                            "usage": {"inputTokens": 6, "outputTokens": 3},
                            "metrics": {"latencyMs": 22},
                        }
                    },
                ]
            ),
            "request": kwargs,
        }


def run_bedrock_examples() -> None:
    client = SentinosClient.from_env(org_id="acme")
    guard = LLMGuard(kernel=client.kernel, agent_id="ops-agent", session_id="sess-bedrock-1")

    adapter = create_bedrock_converse_adapter(
        guard=guard,
        client=_FakeBedrockClient(),
    )

    result = adapter.converse(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[{"role": "user", "content": [{"text": "summarize incidents"}]}],
        inference_config={"temperature": 0.2},
    )
    print(result.trace.trace_id, result.trace.decision, result.response["stopReason"])

    streamed = adapter.converse_stream(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[{"role": "user", "content": [{"text": "stream this"}]}],
    )
    print(streamed.trace.trace_id, streamed.decision, streamed.output_text)


if __name__ == "__main__":
    run_bedrock_examples()
