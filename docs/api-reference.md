# API Reference

## LLMAssert

The main class for creating LLM-powered assertions.

### Constructor

```python
LLMAssert(model, api_key=None, api_base=None, **kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | `str` | LiteLLM model string (e.g., `"openai/gpt-5-mini"`, `"azure/gpt-4o"`) |
| `api_key` | `str` | Optional API key (or use environment variables) |
| `api_base` | `str` | Optional custom endpoint |
| `**kwargs` | | Additional parameters passed to LiteLLM |

**Example:**

```python
from pytest_llm_assert import LLMAssert

llm = LLMAssert(
    model="openai/gpt-5-mini",
    api_key="sk-...",
    temperature=0,
)
```

### `__call__(content, criterion)`

Evaluate if content meets a criterion.

```python
result = llm(content, criterion)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | `str` | The content to evaluate |
| `criterion` | `str` | Natural language criterion to check |

**Returns:** `AssertionResult` — truthy if criterion is met, falsy otherwise.

**Example:**

```python
result = llm("SELECT * FROM users", "Is this a valid SQL query?")
assert result  # Passes if criterion is met
```

### `system_prompt` Property

Get or set the system prompt used for evaluations.

```python
# Get current prompt
current = llm.system_prompt

# Set custom prompt
llm.system_prompt = "Your custom evaluation prompt..."
```

**Example:**

```python
llm = LLMAssert(model="openai/gpt-5-mini")

# Override with domain-specific prompt
llm.system_prompt = """You are a strict code reviewer.
Evaluate if the code meets the criterion.
Respond in JSON: {"result": "PASS" or "FAIL", "reasoning": "..."}"""
```

### `response` Property

Access details from the most recent LLM call. Returns `None` if no calls have been made.

**Type:** `LLMResponse | None`

## AssertionResult

Returned by `llm()` calls. Truthy when the criterion is met.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `result` | `bool` | `True` if criterion was met |
| `reasoning` | `str` | The LLM's explanation for its decision |

**Example:**

```python
result = llm("Hello world", "Is this a greeting?")

if result:
    print("Passed!")
else:
    print(f"Failed: {result.reasoning}")
```

## LLMResponse

Details about the LLM API call. Accessed via `llm.response` after making a call.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `str \| None` | Model that was used |
| `prompt_tokens` | `int \| None` | Number of input tokens |
| `completion_tokens` | `int \| None` | Number of output tokens |
| `total_tokens` | `int \| None` | Total tokens used |
| `cost` | `float \| None` | Cost in USD (if available from provider) |
| `response_time` | `float \| None` | Response time in seconds |

**Example:**

```python
result = llm("content", "criterion")
assert result

# Inspect the response
print(f"Cost: ${llm.response.cost:.6f}")
print(f"Tokens: {llm.response.total_tokens}")
print(f"Model: {llm.response.model}")
print(f"Time: {llm.response.response_time:.2f}s")
```

### Cost Tracking Across Tests

```python
class TestSuite:
    total_cost = 0
    
    def test_one(self, llm):
        assert llm("...", "...")
        TestSuite.total_cost += llm.response.cost or 0
    
    def test_two(self, llm):
        assert llm("...", "...")
        TestSuite.total_cost += llm.response.cost or 0
    
    @classmethod
    def teardown_class(cls):
        print(f"\nTotal cost: ${cls.total_cost:.4f}")
```
