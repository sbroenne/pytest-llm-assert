"""Example: Compare multiple LLM models using pytest parametrization.

Run with: pytest examples/test_compare_models.py -v

This shows how to run the same tests against multiple models to compare
their semantic understanding capabilities.

Output looks like:
    test_understands_sarcasm[azure] PASSED
    test_understands_sarcasm[vertex] PASSED
"""

import os

import pytest

from pytest_llm_assert import LLMAssert


def _get_azure_llm():
    """Create Azure OpenAI LLM if configured."""
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    if not endpoint:
        pytest.skip("AZURE_OPENAI_ENDPOINT not set")

    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    return LLMAssert(model=f"azure/{deployment}", api_base=endpoint, api_key=token)


def _get_vertex_llm():
    """Create Vertex AI LLM if configured."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID")
    location = (
        os.environ.get("GOOGLE_CLOUD_LOCATION")
        or os.environ.get("GCP_LOCATION")
        or "us-central1"
    )
    model = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash")
    if not project:
        pytest.skip("GCP_PROJECT_ID not set")

    return LLMAssert(
        model=f"vertex_ai/{model}", vertex_project=project, vertex_location=location
    )


@pytest.fixture(params=["azure", "vertex"])
def llm(request):
    """Parametrized fixture that runs tests against each configured provider."""
    if request.param == "azure":
        return _get_azure_llm()
    elif request.param == "vertex":
        return _get_vertex_llm()


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
