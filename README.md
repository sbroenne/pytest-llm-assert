# pytest-llm-assert

**Natural language assertions for pytest.**

A pytest plugin that lets you write semantic assertions using LLMs. Stop writing brittle string checks — let an LLM understand what you actually mean.

## The Problem

```python
# ❌ These all fail even though they mean "success":
assert "success" in response  # Fails on "Succeeded", "successful", "It worked!"
assert response == "Operation completed successfully"  # Exact match? Really?
assert re.match(r"success|succeeded|worked", response, re.I)  # Regex hell
```

```python
# You're testing a text-to-SQL agent. How do you validate the output?

# ❌ Exact match? There are many valid ways to write the same query:
assert sql == "SELECT name FROM users WHERE age > 21"

# ❌ Regex? Good luck covering all valid SQL syntax:
assert re.match(r"SELECT\s+name\s+FROM\s+users", sql, re.I)

# ❌ Parse it? Now you need a SQL parser as a test dependency:
assert sqlparse.parse(sql)[0].get_type() == "SELECT"
```

## The Solution

```python
# ✅ Just say what you mean:
assert llm(response, "Does this indicate the operation succeeded?")
assert llm(sql, "Is this a valid SELECT query that returns user names for users over 21?")
```

## Why This Works

The LLM evaluates your criterion against the content and returns a judgment. It understands:

- **Synonyms**: "success", "succeeded", "worked", "completed" all mean the same thing
- **Semantics**: Two SQL queries can be equivalent even with different syntax
- **Context**: "The operation failed successfully" is actually a failure
- **Intent**: Generated code can be correct even if it's not identical to a reference


## Installation

```bash
pip install pytest-llm-assert
```

## Setup

This library uses [LiteLLM](https://docs.litellm.ai/) under the hood, giving you access to **100+ LLM providers** with a unified API. 

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Azure OpenAI with Entra ID (no API keys)
export AZURE_API_BASE=https://your-resource.openai.azure.com
export AZURE_API_VERSION=2024-02-15-preview
# Uses DefaultAzureCredential: az login, managed identity, etc.

# Ollama (local)
# Just run: ollama serve
```

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for all providers including Vertex AI, Bedrock, Anthropic, and more.

## Quick Start

```python
from pytest_llm_assert import LLMAssert

llm = LLMAssert(model="openai/gpt-5-mini")  # Uses OPENAI_API_KEY from env

# Semantic assertions - returns True/False
assert llm("Operation completed successfully", "Does this indicate success?")
assert llm("Error: connection refused", "Does this indicate a failure?")
assert not llm("All tests passed", "Does this indicate a failure?")
```

## Real Examples

First, create a fixture in `conftest.py`:

```python
# conftest.py
import pytest
from pytest_llm_assert import LLMAssert

@pytest.fixture
def llm():
    return LLMAssert(model="openai/gpt-5-mini")
```

Then use it in your tests:

### Testing Error Messages

```python
def test_validation_error_is_helpful(llm):
    """Error messages should explain the problem clearly."""
    error_msg = "ValidationError: 'port' must be an integer, got 'not-a-number'"
    
    assert llm(error_msg, "Does this explain that port must be a number?")
    assert llm(error_msg, "Does this indicate which field failed validation?")
```

### Testing Generated SQL

```python
def test_query_builder_generates_valid_sql(llm):
    """Query builder should produce semantically correct SQL."""
    query = "SELECT name FROM users WHERE age > 21 ORDER BY name"
    
    assert llm(query, "Is this a valid SELECT query that returns names of users over 21?")
```

### Testing LLM Output

```python
def test_summary_is_comprehensive(llm):
    """Generated summaries should capture key points."""
    summary = "The contract establishes a 2-year service agreement between..."
    
    assert llm(summary, "Does this summarize a legal contract?")
    assert llm(summary, "Does this mention the contract duration?")
```

## Comparing Judge Models

Not sure which LLM to use as your assertion judge? Run the same tests against multiple models to find the best one for your use case:

```python
import pytest
from pytest_llm_assert import LLMAssert

MODELS = ["openai/gpt-5-mini", "anthropic/claude-sonnet-4-20250514", "ollama/llama3.1:8b"]

@pytest.fixture(params=MODELS)
def llm(request):
    return LLMAssert(model=request.param)

def test_validates_sql_equivalence(llm):
    """Test which models can judge SQL semantic equivalence."""
    sql = "SELECT u.name FROM users AS u WHERE u.age >= 22"
    assert llm(sql, "Is this equivalent to selecting names of users over 21?")
```

Output shows which judge models correctly evaluate your criterion:
```
test_validates_sql_equivalence[openai/gpt-5-mini] PASSED
test_validates_sql_equivalence[anthropic/claude-sonnet-4-20250514] PASSED  
test_validates_sql_equivalence[ollama/llama3.1:8b] FAILED
```

> **Note:** This tests which LLM makes a good *judge* for your assertions. To test AI agents themselves (e.g., "does my coding agent produce working code?"), see [pytest-aitest](https://github.com/sbroenne/pytest-aitest).

## Configuration

### Programmatic

```python
from pytest_llm_assert import LLMAssert

llm = LLMAssert(
    model="openai/gpt-5-mini",
    api_key="sk-...",           # Or use env var
    api_base="https://...",     # Custom endpoint
)
```

### CLI Options

```bash
pytest --llm-model=openai/gpt-5-mini
pytest --llm-api-key='${OPENAI_API_KEY}'  # Env var expansion
pytest --llm-api-base=http://localhost:8080
```

### Environment Variables

```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=openai/gpt-5-mini
```

## API Reference

### `LLMAssert(model, api_key=None, api_base=None, **kwargs)`

Create an LLM assertion helper.

- `model`: LiteLLM model string (e.g., `"openai/gpt-5-mini"`, `"azure/gpt-4o"`)
- `api_key`: Optional API key (or use environment variables)
- `api_base`: Optional custom endpoint
- `**kwargs`: Additional parameters passed to LiteLLM

### `llm(content, criterion) -> AssertionResult`

Evaluate if content meets the criterion.

- Returns `AssertionResult` which is truthy if criterion is met
- Access `.reasoning` for the LLM's explanation

## See Also

- **[Examples](examples/)** — Example pytest tests showing basic usage, model comparison, and fixture patterns
- **[pytest-aitest](https://github.com/sbroenne/pytest-aitest)** — Full framework for testing MCP servers, CLIs, and AI agents. Uses pytest-llm-assert for the judge.

## License

MIT
