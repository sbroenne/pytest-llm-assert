"""Tests for LLM response parsing.

With pydantic-ai, responses are structured using Pydantic models,
so JSON parsing is handled automatically.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import EvaluationResult, LLMAssert


class TestStructuredResponseParsing:
    """Pydantic-ai provides structured responses as EvaluationResult."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_parses_pass_result(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="Looks good")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("content", "criterion")

        assert result.passed is True
        assert result.reasoning == "Looks good"

    @patch("pydantic_ai.Agent.run_sync")
    def test_parses_fail_result(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="FAIL", reasoning="Does not meet criterion"
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("content", "criterion")

        assert result.passed is False
        assert result.reasoning == "Does not meet criterion"

    @patch("pydantic_ai.Agent.run_sync")
    def test_case_insensitive_pass(self, mock_run_sync: MagicMock) -> None:
        """PASS result should be case-insensitive."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="pass", reasoning="Valid")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("content", "criterion")

        assert result.passed is True

    @patch("pydantic_ai.Agent.run_sync")
    def test_case_insensitive_fail(self, mock_run_sync: MagicMock) -> None:
        """FAIL result should be case-insensitive."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="fail", reasoning="Invalid")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("content", "criterion")

        assert result.passed is False


class TestResponseMetadata:
    """LLM response metadata capture from pydantic-ai."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_captures_usage_stats(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="OK")
        mock_usage = MagicMock()
        mock_usage.request_tokens = 100
        mock_usage.response_tokens = 50
        mock_usage.total_tokens = 150
        mock_result.usage.return_value = mock_usage
        mock_result.model_name = "gpt-4o-mini"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:gpt-4o-mini", api_key="test-key")
        llm("content", "criterion")

        assert llm.response is not None
        assert llm.response.model == "gpt-4o-mini"
        assert llm.response.prompt_tokens == 100
        assert llm.response.completion_tokens == 50
        assert llm.response.total_tokens == 150

    @patch("pydantic_ai.Agent.run_sync")
    def test_handles_missing_usage(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="OK")
        mock_result.usage.return_value = None
        mock_result.model_name = "test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        llm("content", "criterion")

        assert llm.response is not None
        assert llm.response.prompt_tokens is None
        assert llm.response.completion_tokens is None
        assert llm.response.total_tokens is None

    @patch("pydantic_ai.Agent.run_sync")
    def test_handles_no_cost_info(self, mock_run_sync: MagicMock) -> None:
        """Pydantic AI doesn't provide cost info, so it should be None."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="OK")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        llm("content", "criterion")

        assert llm.response is not None
        assert llm.response.cost is None
