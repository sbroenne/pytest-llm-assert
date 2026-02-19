# pytest-llm-assert

[![PyPI version](https://img.shields.io/pypi/v/pytest-llm-assert)](https://pypi.org/project/pytest-llm-assert/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-llm-assert)](https://pypi.org/project/pytest-llm-assert/)
[![CI](https://github.com/sbroenne/pytest-llm-assert/actions/workflows/ci.yml/badge.svg)](https://github.com/sbroenne/pytest-llm-assert/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Natural language assertions for pytest.**

Testing a text-to-SQL agent? Validating LLM-generated code? Checking if error messages are helpful? Now you can:

```python
def test_sql_agent_output(llm):
    sql = my_agent.generate("Get names of users over 21")
    
    assert llm(sql, "Is this a valid SQL query that selects user names filtered by age > 21?")
```

The LLM evaluates your criterion and returns pass/fail — no regex, no parsing, no exact string matching.

## Features

- **Semantic assertions** — Assert meaning, not exact strings
- **Multiple LLM providers** — OpenAI, Azure, Anthropic, Gemini, Groq via [Pydantic AI](https://ai.pydantic.dev/)
- **pytest native** — Works as a standard pytest plugin/fixture
- **Response introspection** — Access tokens and reasoning via `llm.response`
- **Type-safe** — Built with Pydantic for structured outputs

## Installation

```bash
pip install pytest-llm-assert
```

## Quick Start

```python
# conftest.py
import pytest
from pytest_llm_assert import LLMAssert

@pytest.fixture
def llm():
    return LLMAssert(model="openai:gpt-4o-mini")
```

```python
# test_my_agent.py
def test_generated_sql_is_correct(llm):
    sql = "SELECT name FROM users WHERE age > 21 ORDER BY name"
    assert llm(sql, "Is this a valid SELECT query that returns names of users over 21?")

def test_error_message_is_helpful(llm):
    error = "ValidationError: 'port' must be an integer, got 'abc'"
    assert llm(error, "Does this explain what went wrong and how to fix it?")

def test_summary_captures_key_points(llm):
    summary = generate_summary(document)
    assert llm(summary, "Does this mention the contract duration and parties involved?")
```

## Setup

Works out of the box with cloud identity — no API keys to manage:

```bash
# Azure (Entra ID)
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
az login

# Google Cloud (Vertex AI)
gcloud auth application-default login

# AWS (Bedrock)
aws configure  # Uses IAM credentials
```

Supports multiple providers via [Pydantic AI](https://ai.pydantic.dev/) — including API key auth for OpenAI, Anthropic, and more.

## Documentation

- **[Configuration](configuration.md)** — All providers, CLI options, environment variables
- **[API Reference](api-reference.md)** — Full API documentation
- **[Comparing Judge Models](comparing-models.md)** — Evaluate which LLM works best for your assertions

## Related

- **[pytest-aitest](https://github.com/sbroenne/pytest-aitest)** — Full framework for testing MCP servers, CLIs, and AI agents
- **[Contributing](https://github.com/sbroenne/pytest-llm-assert/blob/main/CONTRIBUTING.md)** — Development setup and guidelines

## Requirements

- Python 3.11+
- pytest 9.0+
- An LLM (OpenAI, Azure, Anthropic, etc.) or local Ollama

## Security

- **Sensitive data**: Test content is sent to LLM providers — consider data policies

## License

MIT
