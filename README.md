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

## Installation

```bash
pip install pytest-llm-assert
```

## Setup

This library uses [LiteLLM](https://docs.litellm.ai/) under the hood, giving you access to **100+ LLM providers** with a unified API.

### 1. Choose a Provider

| Provider | Model String | Best For |
|----------|--------------|----------|
| **OpenAI** | `openai/gpt-5-mini` | Fast, cheap, good default |
| **Azure OpenAI** | `azure/your-deployment` | Enterprise, compliance |
| **Google Vertex AI** | `vertex_ai/gemini-2.0-flash` | Google Cloud users |
| **Anthropic** | `anthropic/claude-sonnet-4-20250514` | Strong reasoning |
| **Ollama** | `ollama/llama3.1:8b` | Local, free, private |

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for all providers.

### 2. Set Your API Key

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Azure OpenAI (API key)
export AZURE_API_KEY=...
export AZURE_API_BASE=https://your-resource.openai.azure.com

# Azure OpenAI (Entra ID / Azure AD) - no key needed!
pip install pytest-llm-assert[azure]
export AZURE_API_BASE=https://your-resource.openai.azure.com
# Uses DefaultAzureCredential (az login, managed identity, etc.)

# Google Vertex AI - uses Application Default Credentials
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1  # optional, defaults to us-central1

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Ollama (no key needed - runs locally)
```

### 3. Use It

```python
from pytest_llm_assert import LLMAssert

# Uses OPENAI_API_KEY from environment
llm = LLMAssert(model="openai/gpt-5-mini")

# Or pass key explicitly
llm = LLMAssert(model="openai/gpt-5-mini", api_key="sk-...")

# Azure with Entra ID
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
token = credential.get_token("https://cognitiveservices.azure.com/.default").token
llm = LLMAssert(model="azure/gpt-5-mini", api_base="https://your-resource.openai.azure.com", api_key=token)
```

## Quick Start

```python
from pytest_llm_assert import LLMAssert

# Configure once
llm = LLMAssert(model="openai/gpt-5-mini", api_key="...")

# Semantic assertions - returns True/False
assert llm(result.message, "Does this indicate the operation succeeded?")
assert llm(error.description, "Does this explain what went wrong?")
assert not llm(response.status, "Does this indicate a failure?")
```

## Why This Works

The LLM evaluates your criterion against the content and returns a judgment. It understands:

- **Synonyms**: "success", "succeeded", "worked", "completed" all mean the same thing
- **Semantics**: Two SQL queries can be equivalent even with different syntax
- **Context**: "The operation failed successfully" is actually a failure
- **Intent**: Generated code can be correct even if it's not identical to a reference

## Real Examples

### Testing Error Messages

```python
def test_validation_error_is_helpful(llm):
    """Error messages should explain the problem clearly."""
    try:
        validate_config({"port": "not-a-number"})
    except ValidationError as e:
        assert llm(str(e), "Does this explain that port must be a number?")
        assert llm(str(e), "Does this indicate which field failed validation?")
```

### Testing Generated SQL

```python
def test_query_builder_generates_valid_sql(llm):
    """Query builder should produce semantically correct SQL."""
    query = build_query(table="users", filters={"age": ">21"}, select=["name"])
    
    # Don't check exact string - check semantic correctness
    assert llm(query, "Is this a valid SELECT query that returns names of users over 21?")
    assert llm(query, "Does this query use parameterized values or escape inputs properly?")
```

### Testing Function Return Values

```python
def test_parser_extracts_metadata(llm):
    """Parser should extract meaningful metadata from documents."""
    result = parse_document("path/to/contract.pdf")
    
    assert llm(result["summary"], "Does this summarize a legal contract?")
    assert llm(result["summary"], "Is this summary comprehensive?")
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

## Supported Providers

See [Setup](#setup) for common providers. Full list at [LiteLLM docs](https://docs.litellm.ai/docs/providers).

## API Reference

### `LLMAssert(content, criterion) -> AssertionResult`

Evaluate if content meets the criterion.

- Returns `AssertionResult` which is truthy if criterion is met
- Access `.reasoning` for the LLM's explanation

## See Also

- **[Examples](examples/)** — Example pytest tests showing basic usage, model comparison, and fixture patterns
- **[pytest-aitest](https://github.com/sbroenne/pytest-aitest)** — Full framework for testing MCP servers, CLIs, and AI agents. Uses pytest-llm-assert for the judge.

## License

MIT
