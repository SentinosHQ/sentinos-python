## Amazon Bedrock Converse integration (native IAM/SigV4)

Use this cookbook for enterprise AWS-hosted model inference via Bedrock `converse` and `converse_stream` while keeping Sentinos governance in front of each provider call.

## Prerequisites

- AWS credentials available through the standard SDK provider chain.
- Bedrock model access enabled in your AWS account/region.
- IAM permissions for Bedrock Runtime inference APIs.

## Adapter example

```python
from sentinos import LLMGuard, SentinosClient, create_bedrock_converse_adapter

client = SentinosClient.from_env(org_id="acme")
guard = LLMGuard(kernel=client.kernel, agent_id="agent1", session_id="sess-bedrock-1")

adapter = create_bedrock_converse_adapter(
    guard=guard,
    region_name="us-east-1",
)

result = adapter.converse(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    messages=[{"role": "user", "content": [{"text": "Summarize active incidents"}]}],
    inference_config={"temperature": 0.2},
)
print(result.trace.trace_id, result.trace.decision)

streamed = adapter.converse_stream(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    messages=[{"role": "user", "content": [{"text": "Stream a short update"}]}],
)
print(streamed.trace.trace_id, streamed.output_text)
```

## Notes

- Bedrock provider identity is `bedrock` and operation names are `converse` / `converse_stream`.
- Sentinos policy `DENY`/`ESCALATE` blocks provider execution before any Bedrock call.
- Provider-side failures are mapped to typed errors:
  - `BedrockAccessDeniedError`
  - `BedrockThrottlingError`
  - `BedrockValidationError`
  - `BedrockProviderError` (fallback)
