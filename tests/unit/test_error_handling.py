"""Tests for error handling scenarios."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pytest_llm_assert.core import EvaluationResult, LLMAssert


class TestAPIErrors:
    """API errors should propagate to caller."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_rate_limit_propagates(self, mock_run_sync: MagicMock) -> None:
        mock_run_sync.side_effect = Exception("API rate limit exceeded")

        llm = LLMAssert(model="openai:test-model", api_key="test-key")

        with pytest.raises(Exception, match="API rate limit exceeded"):
            llm("Content", "criterion")

    @patch("pydantic_ai.Agent.run_sync")
    def test_network_error_propagates(self, mock_run_sync: MagicMock) -> None:
        mock_run_sync.side_effect = ConnectionError("Failed to connect")

        llm = LLMAssert(model="openai:test-model", api_key="test-key")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            llm("Content", "criterion")

    @patch("pydantic_ai.Agent.run_sync")
    def test_timeout_propagates(self, mock_run_sync: MagicMock) -> None:
        mock_run_sync.side_effect = TimeoutError("Request timed out")

        llm = LLMAssert(model="openai:test-model", api_key="test-key")

        with pytest.raises(TimeoutError, match="Request timed out"):
            llm("Content", "criterion")


class TestResponseValidation:
    """Validation of LLM response structure."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_invalid_result_field_raises(self, mock_run_sync: MagicMock) -> None:
        """Invalid result field should raise validation error."""
        # Simulate pydantic validation error
        mock_run_sync.side_effect = ValueError("Invalid result value")

        llm = LLMAssert(model="openai:test-model", api_key="test-key")

        with pytest.raises(ValueError):
            llm("Content", "criterion")

    @patch("pydantic_ai.Agent.run_sync")
    def test_missing_reasoning_field_raises(self, mock_run_sync: MagicMock) -> None:
        """Missing reasoning field should raise validation error."""
        mock_run_sync.side_effect = ValueError("Missing required field: reasoning")

        llm = LLMAssert(model="openai:test-model", api_key="test-key")

        with pytest.raises(ValueError):
            llm("Content", "criterion")

    @patch("pydantic_ai.Agent.run_sync")
    def test_valid_response_format(self, mock_run_sync: MagicMock) -> None:
        """Valid EvaluationResult should be parsed correctly."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="PASS", reasoning="Content meets criteria"
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("Content", "criterion")

        assert result.passed is True
        assert result.reasoning == "Content meets criteria"
