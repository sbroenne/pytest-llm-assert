"""Example: Compare multiple LLM models using pytest parametrization.

Run with: pytest examples/test_compare_models.py -v

This shows how to run the same tests against multiple models to compare
their semantic understanding capabilities.

Output looks like:
    test_understands_sarcasm[openai] PASSED
    test_understands_sarcasm[anthropic] PASSED
"""

import os

import pytest

from pytest_llm_assert import LLMAssert


def _get_openai_llm():
    """Create OpenAI LLM if API key is set."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    return LLMAssert(model="openai:gpt-4o-mini")


def _get_anthropic_llm():
    """Create Anthropic LLM if API key is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    return LLMAssert(model="anthropic:claude-3-5-sonnet-latest")


def _get_azure_llm():
    """Create Azure OpenAI LLM if configured."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        pytest.skip("AZURE_OPENAI_ENDPOINT not set")
    return LLMAssert(model="azure:gpt-4o")


@pytest.fixture(params=["openai", "anthropic", "azure"])
def llm(request):
    """Parametrized fixture that runs tests against each configured provider."""
    if request.param == "openai":
        return _get_openai_llm()
    elif request.param == "anthropic":
        return _get_anthropic_llm()
    elif request.param == "azure":
        return _get_azure_llm()
    else:
        msg = f"Unknown provider: {request.param}"
        raise ValueError(msg)


class TestModelComparison:
    """Run the same semantic tests across multiple models."""

    def test_understands_sarcasm(self, llm):
        """Can the model detect sarcasm?"""
        sarcastic = "Oh great, another meeting that could have been an email."
        assert llm(sarcastic, "Does this express frustration or sarcasm?")

    def test_detects_contradiction(self, llm):
        """Can the model detect logical contradictions?"""
        text = "All birds can fly. Penguins are birds. Penguins cannot fly."
        assert llm(text, "Does this contain a logical contradiction?")

    def test_recognizes_success_variations(self, llm):
        """Can the model recognize different success phrasings?"""
        messages = ["Done!", "Success", "Completed ✓", "It worked"]
        for msg in messages:
            assert llm(msg, "Does this indicate success?"), f"Model failed on: {msg}"
