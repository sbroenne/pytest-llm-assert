"""Example conftest.py for using pytest-llm-assert in your test suite.

Copy this file to your tests/ directory as conftest.py and customize as needed.

Usage:
    # Run with default model
    pytest tests/

    # Run with specific model
    pytest tests/ --llm-model=anthropic/claude-sonnet-4-20250514

    # Compare multiple models
    pytest tests/ -k "test_my_feature"  # with parametrized fixture
"""

import os

import pytest

from pytest_llm_assert import LLMAssert


# Option 1: Simple fixture using CLI options (recommended)
# The plugin already provides `llm_assert` fixture, but you can customize:
@pytest.fixture
def llm(request):
    """LLM assertion helper with CLI configuration.

    Uses --llm-model, --llm-api-key, --llm-api-base from CLI.
    """
    return LLMAssert(
        model=request.config.getoption("--llm-model", "openai/gpt-5-mini"),
        api_key=request.config.getoption("--llm-api-key"),
        api_base=request.config.getoption("--llm-api-base"),
    )


# Option 2: Parametrized fixture for comparing models
MODELS_TO_TEST = [
    "openai/gpt-5-mini",
    # "anthropic/claude-sonnet-4-20250514",
    # "ollama/llama3",
]


@pytest.fixture(params=MODELS_TO_TEST)
def llm_multi(request):
    """Parametrized fixture that runs tests against multiple models.

    Test output will show which model(s) passed/failed:
        test_example[openai/gpt-5-mini] PASSED
        test_example[anthropic/claude-sonnet-4-20250514] FAILED
    """
    return LLMAssert(model=request.param)


# Option 3: Azure with Entra ID authentication
@pytest.fixture
def llm_azure():
    """LLM assertion helper for Azure OpenAI with Entra ID.

    Requires:
        pip install pytest-llm-assert[azure]
        export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
    """
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        pytest.skip("AZURE_OPENAI_ENDPOINT not set")

    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    return LLMAssert(
        model="azure/gpt-5-mini",  # Your deployment name
        api_base=endpoint,
        api_key=token,
    )


# Option 4: Google Vertex AI
@pytest.fixture
def llm_vertex():
    """LLM assertion helper for Google Vertex AI.

    Requires:
        gcloud auth application-default login
        export GCP_PROJECT_ID=your-project-id  # or GOOGLE_CLOUD_PROJECT
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID")
    location = (
        os.environ.get("GOOGLE_CLOUD_LOCATION")
        or os.environ.get("GCP_LOCATION")
        or "us-central1"
    )

    if not project:
        pytest.skip("GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT not set")

    return LLMAssert(
        model="vertex_ai/gemini-2.0-flash",
        vertex_project=project,
        vertex_location=location,
    )


# Example test using the fixtures
class TestExampleUsage:
    """Example tests demonstrating fixture usage."""

    def test_greeting_is_friendly(self, llm):
        response = "Hello! Welcome to our service. How can I help you today?"
        assert llm(response, "Is this a friendly and welcoming greeting?")

    def test_error_message_is_helpful(self, llm):
        error = "Invalid email format. Please enter an email like user@example.com"
        assert llm(error, "Does this error message explain what went wrong?")
        assert llm(error, "Does this error message suggest how to fix the issue?")

    def test_response_is_clear(self, llm):
        response = (
            "To reset your password: "
            "1) Go to Settings 2) Click Security 3) Select 'Reset Password'"
        )
        assert llm(response, "Is this response clear and actionable?")
