# Configuration

## LLM Providers

pytest-llm-assert uses [LiteLLM](https://docs.litellm.ai/) for LLM access. See the [LiteLLM provider docs](https://docs.litellm.ai/docs/providers) for setup instructions.

## Fixture Configuration

```python
# conftest.py
import pytest
from pytest_llm_assert import LLMAssert

@pytest.fixture
def llm():
    return LLMAssert(
        model="azure/gpt-4o",       # Required: LiteLLM model string
        api_key="...",              # Optional: override env var
        api_base="https://...",     # Optional: custom endpoint
        # Any LiteLLM parameter is passed through (temperature, timeout, etc.)
    )
```

## Custom System Prompt

The default system prompt is in [`src/pytest_llm_assert/prompts/system_prompt.md`](../src/pytest_llm_assert/prompts/system_prompt.md).

Override it at runtime for domain-specific assertions:

```python
llm = LLMAssert(model="azure/gpt-4o")

llm.system_prompt = """You are a strict security reviewer.
Be conservative - if in doubt, fail the test.
Respond in JSON: {"result": "PASS" or "FAIL", "reasoning": "..."}"""

assert llm(code, "Does this avoid SQL injection?")
```
