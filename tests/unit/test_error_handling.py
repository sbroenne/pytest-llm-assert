"""Tests for error handling scenarios."""

from unittest.mock import MagicMock, patch

import pytest

from pytest_llm_assert.core import LLMAssert


class TestAPIErrors:
    """API errors should propagate to caller."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_rate_limit_propagates(self, mock_completion: MagicMock) -> None:
        mock_completion.side_effect = Exception("API rate limit exceeded")

        llm = LLMAssert(model="test/model")

        with pytest.raises(Exception, match="API rate limit exceeded"):
            llm("Content", "criterion")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_network_error_propagates(self, mock_completion: MagicMock) -> None:
        mock_completion.side_effect = ConnectionError("Failed to connect")

        llm = LLMAssert(model="test/model")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            llm("Content", "criterion")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_timeout_propagates(self, mock_completion: MagicMock) -> None:
        mock_completion.side_effect = TimeoutError("Request timed out")

        llm = LLMAssert(model="test/model")

        with pytest.raises(TimeoutError, match="Request timed out"):
            llm("Content", "criterion")


class TestMalformedResponses:
    """Graceful handling of unexpected LLM responses."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_invalid_format_is_fail(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "@@#$%INVALID"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        # Doesn't start with PASS, so fails
        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_empty_choices_raises(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = []
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")

        with pytest.raises(IndexError):
            llm("Content", "criterion")
