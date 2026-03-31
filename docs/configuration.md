# Configuration

## LLM Providers

pytest-llm-assert uses [Pydantic AI](https://ai.pydantic.dev/) for LLM access. Pydantic AI supports multiple providers including OpenAI, Azure OpenAI, Anthropic, Google Gemini, and Groq.

## Model Specification

Models are specified using the `provider:model` format:

- **OpenAI**: `openai:gpt-4o-mini`, `openai:gpt-4o`, `openai:gpt-4-turbo`
- **Azure OpenAI**: `azure:gpt-4o` (requires `AZURE_OPENAI_ENDPOINT` env var)
- **Anthropic**: `anthropic:claude-3-5-sonnet`, `anthropic:claude-3-opus`
- **Google Gemini**: `gemini:gemini-2.0-flash`, `gemini:gemini-1.5-pro`
- **Groq**: `groq:llama-3.3-70b-versatile`

## Authentication

### OpenAI
```bash
export OPENAI_API_KEY=sk-...
```

### Azure OpenAI (Entra ID)
```bash
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
az login
```

### Anthropic
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Google Gemini
```bash
export GEMINI_API_KEY=...
# or use Google Cloud credentials
gcloud auth application-default login
```

## Fixture Configuration

```python
# conftest.py
import pytest
from pytest_llm_assert import LLMAssert

@pytest.fixture
def llm():
    return LLMAssert(
        model="openai:gpt-4o-mini",  # Required: Pydantic AI model string
        api_key="...",                # Optional: override env var
    )
```

## Custom System Prompt

The default system prompt is in [`src/pytest_llm_assert/prompts/system_prompt.md`](https://github.com/sbroenne/pytest-llm-assert/blob/main/src/pytest_llm_assert/prompts/system_prompt.md).

Override it at runtime for domain-specific assertions:

```python
llm = LLMAssert(model="openai:gpt-4o-mini")

llm.system_prompt = """You are a strict security reviewer.
Be conservative - if in doubt, fail the test.
Respond in JSON: {"result": "PASS" or "FAIL", "reasoning": "..."}"""

assert llm(code, "Does this avoid SQL injection?")
```
