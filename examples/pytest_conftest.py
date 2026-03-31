"""Example conftest.py for using pytest-llm-assert in your test suite.

Copy this file to your tests/ directory as conftest.py and customize as needed.

Usage:
    # Run with default model
    pytest tests/

    # Run with specific model
    pytest tests/ --llm-model=anthropic:claude-3-5-sonnet-latest

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

    Uses --llm-model and --llm-api-key from CLI.
    """
    return LLMAssert(
        model=request.config.getoption("--llm-model", "openai:gpt-4o-mini"),
        api_key=request.config.getoption("--llm-api-key"),
    )


# Option 2: Parametrized fixture for comparing models
MODELS_TO_TEST = [
    "openai:gpt-4o-mini",
    # "anthropic:claude-3-5-sonnet-latest",
    # "gemini:gemini-2.0-flash",
]


@pytest.fixture(params=MODELS_TO_TEST)
def llm_multi(request):
    """Parametrized fixture that runs tests against multiple models.

    Test output will show which model(s) passed/failed:
        test_example[openai:gpt-4o-mini] PASSED
        test_example[anthropic:claude-3-5-sonnet-latest] FAILED
    """
    return LLMAssert(model=request.param)


# Option 3: Azure with Entra ID authentication
@pytest.fixture
def llm_azure():
    """LLM assertion helper for Azure OpenAI with Entra ID.

    Requires:
        export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
        az login
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        pytest.skip("AZURE_OPENAI_ENDPOINT not set")

    return LLMAssert(model="azure:gpt-4o")


# Option 4: Google Gemini
@pytest.fixture
def llm_gemini():
    """LLM assertion helper for Google Gemini.

    Requires:
        export GEMINI_API_KEY=your-api-key
        # or use Google Cloud credentials
        gcloud auth application-default login
    """
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    ):
        pytest.skip("GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS not set")

    return LLMAssert(model="gemini:gemini-2.0-flash")


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
