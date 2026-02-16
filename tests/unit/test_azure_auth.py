"""Tests for Azure model support in LLMAssert.

With Pydantic AI, Azure authentication is handled automatically via
environment variables (AZURE_OPENAI_ENDPOINT, OPENAI_API_KEY, etc.)
and Entra ID credentials.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import EvaluationResult, LLMAssert


class TestAzureModelNaming:
    """Azure model naming with pydantic-ai format."""

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_azure_model_format(self, mock_agent_init: MagicMock) -> None:
        """Azure models should use 'azure:' prefix."""
        llm = LLMAssert(model="azure:gpt-4o", api_key="test-key")
        assert llm.model_name == "azure:gpt-4o"

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_openai_model_format(self, mock_agent_init: MagicMock) -> None:
        """OpenAI models should use 'openai:' prefix."""
        llm = LLMAssert(model="openai:gpt-4o-mini", api_key="test-key")
        assert llm.model_name == "openai:gpt-4o-mini"

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_anthropic_model_format(self, mock_agent_init: MagicMock) -> None:
        """Anthropic models should use 'anthropic:' prefix."""
        llm = LLMAssert(model="anthropic:claude-3-sonnet", api_key="test-key")
        assert llm.model_name == "anthropic:claude-3-sonnet"


class TestAzureEnvironmentVariables:
    """Azure requires specific environment variables."""

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_azure_api_key_from_env(self, mock_agent_init: MagicMock) -> None:
        """API key can be set via environment or constructor."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            llm = LLMAssert(model="azure:gpt-4o", api_key="test-key")
            # API key is stored in the instance
            assert llm.api_key == "test-key"

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_azure_api_key_from_constructor(self, mock_agent_init: MagicMock) -> None:
        """API key can be passed to constructor."""
        llm = LLMAssert(model="azure:gpt-4o", api_key="test-key")
        assert llm.api_key == "test-key"

    @patch("pydantic_ai.Agent.__init__", return_value=None)
    def test_azure_endpoint_via_env(self, mock_agent_init: MagicMock) -> None:
        """Azure endpoint should be set via AZURE_OPENAI_ENDPOINT."""
        with patch.dict(
            "os.environ", {"AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com"}
        ):
            # Constructor should not fail with proper env setup
            llm = LLMAssert(model="azure:gpt-4o", api_key="test-key")
            assert llm.model_name == "azure:gpt-4o"


class TestAzureCallWithCredentials:
    """Azure model calls with credentials."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_azure_call_with_api_key(self, mock_run_sync: MagicMock) -> None:
        """Azure model should work with API key."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="PASS", reasoning="Content passed evaluation"
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "azure:gpt-4o"
        mock_run_sync.return_value = mock_result

        with patch("pydantic_ai.Agent.__init__", return_value=None):
            llm = LLMAssert(model="azure:gpt-4o", api_key="test-key")
            llm._agent = MagicMock()
            llm._agent.run_sync = mock_run_sync
            result = llm("Test content", "Is this valid?")

            assert result.passed is True

    @patch("pydantic_ai.Agent.run_sync")
    def test_azure_call_with_entra_id(self, mock_run_sync: MagicMock) -> None:
        """Azure model can work with Entra ID (no API key)."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="PASS", reasoning="Content passed evaluation"
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "azure:gpt-4o"
        mock_run_sync.return_value = mock_result

        with patch("pydantic_ai.Agent.__init__", return_value=None):
            llm = LLMAssert(model="azure:gpt-4o")
            llm._agent = MagicMock()
            llm._agent.run_sync = mock_run_sync
            result = llm("Test content", "Is this valid?")
            assert result.passed is True
