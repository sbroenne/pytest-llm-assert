# Comparing Judge Models

Not sure which LLM to use as your assertion judge? Different models have different strengths — some are better at code evaluation, others at natural language understanding.

## Example

See [`examples/test_compare_models.py`](../examples/test_compare_models.py) for a working example that compares Azure OpenAI and Vertex AI.

Run it with:
```bash
pytest examples/test_compare_models.py -v
```

## What to Look For

When comparing judge models, consider:

1. **Accuracy** — Does it correctly evaluate your criteria?
2. **Cost** — Check `llm.response.cost` after each test
3. **Speed** — Smaller/local models are faster
4. **Consistency** — Run the same test multiple times

## Note on Testing AI Agents

This tests which LLM makes a good *judge* for your assertions. To test AI agents themselves (e.g., "does my coding agent produce working code?"), see [pytest-aitest](https://github.com/sbroenne/pytest-aitest).
