"""pytest plugin providing LLM-powered assertion fixtures."""

from __future__ import annotations

import pytest

from pytest_llm_assert.core import LLMAssert


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add pytest CLI options for LLM assertions."""
    group = parser.getgroup("llm-assert", "LLM-powered assertions")
    group.addoption(
        "--llm-model",
        default="openai/gpt-5-mini",
        help="Default LiteLLM model for assertions (default: openai/gpt-5-mini)",
    )
    group.addoption(
        "--llm-api-key",
        default=None,
        help="API key for LLM provider (supports ${ENV_VAR} expansion)",
    )
    group.addoption(
        "--llm-api-base",
        default=None,
        help="Custom API base URL for LLM provider",
    )


@pytest.fixture
def llm_assert(request: pytest.FixtureRequest) -> LLMAssert:
    """Fixture providing an LLMAssert instance configured via CLI options.

    Example:
        def test_greeting(llm_assert):
            response = "Hello! How can I help you today?"
            assert llm_assert(response, "Is this a friendly greeting?")
    """
    return LLMAssert(
        model=request.config.getoption("--llm-model"),
        api_key=request.config.getoption("--llm-api-key"),
        api_base=request.config.getoption("--llm-api-base"),
    )
