# Running Integration Tests

Integration tests verify that pytest-llm-assert works correctly with real LLM API calls. These tests are **not run by default** in CI because they require API credentials and incur costs.

## Prerequisites

You need API credentials for at least one LLM provider:

### OpenAI (Recommended for testing)
```bash
export OPENAI_API_KEY=sk-...
```

### Azure OpenAI
```bash
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# Then authenticate:
az login
```

### Google Gemini
```bash
export GEMINI_API_KEY=...
# OR use Google Cloud credentials:
gcloud auth application-default login
```

## Running Tests Locally

### Run all integration tests (requires credentials)
```bash
pytest tests/integration/ -v -m integration
```

### Run with a specific provider
The default fixture uses OpenAI. To test other providers, modify the `llm` fixture in `tests/integration/test_llm_integration.py`:

```python
# Change from:
@pytest.fixture(params=["openai"])

# To test multiple providers:
@pytest.fixture(params=["openai", "azure", "gemini"])
```

### Skip integration tests
Integration tests are marked with `@pytest.mark.integration`, so you can exclude them:
```bash
pytest -m "not integration"
```

## CI/CD Integration

Integration tests are **disabled by default** in CI to avoid:
- API costs on every PR
- Required secrets in forks
- Flaky test failures due to API rate limits

### Enable in CI (Repository Settings)

To enable integration tests in GitHub Actions:

1. Add secrets to your repository:
   - Go to Settings → Secrets and variables → Actions
   - Add `OPENAI_API_KEY` with your API key

2. Enable the integration test job:
   - Go to Settings → Variables → Actions
   - Add variable `RUN_INTEGRATION_TESTS` with value `true`

The integration tests will now run on every push/PR.

### Manual/Scheduled Testing

For production repositories, consider:
- Running integration tests on a schedule (nightly/weekly)
- Running them only on main branch
- Running them manually via workflow_dispatch

Example workflow for scheduled tests:
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:  # Allow manual trigger
```

## Test Structure

Integration tests are organized in `tests/integration/test_llm_integration.py`:

- **TestBasicAssertions**: Basic pass/fail scenarios
- **TestSemanticVariations**: Different ways to express the same meaning
- **TestSQLSemanticEquivalence**: SQL query validation
- **TestSemanticUnderstanding**: Complex semantic reasoning

Each test class runs against the configured provider(s).

## Cost Considerations

Integration tests make real API calls:
- **OpenAI gpt-4o-mini**: ~$0.01-0.02 per full test run (8 tests)
- Tests use small prompts to minimize costs
- No retry logic to avoid duplicate charges

For development, consider:
- Running only specific tests: `pytest tests/integration/test_llm_integration.py::TestBasicAssertions -v`
- Using cheaper models (gpt-4o-mini vs gpt-4)
- Mocking for most development (unit tests)

## Troubleshooting

### Tests are skipped
If you see "SKIPPED: OPENAI_API_KEY not set", ensure:
- Environment variable is exported in your shell
- Variable name matches exactly (case-sensitive)
- Key has sufficient permissions/credits

### API errors
- Check your API key is valid and has credits
- Verify network connectivity
- Check rate limits if tests fail intermittently

### Provider-specific issues
- **Azure**: Ensure `AZURE_OPENAI_ENDPOINT` is set and you're authenticated (`az login`)
- **Gemini**: Ensure `GEMINI_API_KEY` or Google Cloud credentials are available
