# Examples

Example pytest tests demonstrating pytest-llm-assert usage.

## Prerequisites

```bash
pip install pytest-llm-assert
export OPENAI_API_KEY=sk-...  # Or configure another provider
```

## Examples

### [test_basic.py](test_basic.py)

Core usage patterns - semantic variations, SQL validation, scoring:

```bash
pytest examples/test_basic.py -v
```

### [test_compare_models.py](test_compare_models.py)

Compare multiple LLM providers on the same tests:

```bash
pytest examples/test_compare_models.py -v
```

Output shows which models pass/fail each test:
```
test_understands_sarcasm[openai/gpt-5-mini] PASSED
test_understands_sarcasm[anthropic/claude-sonnet-4-20250514] FAILED
```

### [pytest_conftest.py](pytest_conftest.py)

Example `conftest.py` showing different fixture patterns:

- **Simple fixture**: Uses CLI options
- **Parametrized fixture**: Tests against multiple models
- **Azure fixture**: Entra ID authentication
- **Vertex fixture**: Google Cloud authentication

Copy to your `tests/conftest.py` and customize:

```bash
cp examples/pytest_conftest.py tests/conftest.py
pytest tests/
```

## CLI Options

The plugin provides pytest CLI options:

```bash
# Specify model
pytest tests/ --llm-model=openai/gpt-5-mini

# Custom API key (with env var expansion)
pytest tests/ --llm-api-key='${OPENAI_API_KEY}'

# Custom endpoint
pytest tests/ --llm-api-base=http://localhost:8080
```
