"""Tests for pytest-llm-assert."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pytest_llm_assert.core import AssertionResult, LLMAssert


class TestAssertionResult:
    """Tests for AssertionResult dataclass."""

    def test_bool_pass(self) -> None:
        result = AssertionResult(
            passed=True,
            criterion="Is greeting",
            reasoning="Contains hello",
            content_preview="Hello...",
        )
        assert result
        assert bool(result) is True

    def test_bool_fail(self) -> None:
        result = AssertionResult(
            passed=False,
            criterion="Is greeting",
            reasoning="No greeting found",
            content_preview="Goodbye...",
        )
        assert not result
        assert bool(result) is False

    def test_repr_pass(self) -> None:
        result = AssertionResult(
            passed=True,
            criterion="Is professional",
            reasoning="Uses formal language",
            content_preview="Dear Sir...",
        )
        repr_str = repr(result)
        assert "PASS" in repr_str
        assert "Is professional" in repr_str
        assert "Uses formal language" in repr_str

    def test_repr_fail(self) -> None:
        result = AssertionResult(
            passed=False,
            criterion="Is professional",
            reasoning="Too casual",
            content_preview="Hey dude...",
        )
        repr_str = repr(result)
        assert "FAIL" in repr_str


class TestLLMAssert:
    """Tests for LLMAssert class."""

    def test_env_expansion(self) -> None:
        with patch.dict("os.environ", {"TEST_KEY": "secret123"}):
            expanded = LLMAssert._expand_env("Bearer ${TEST_KEY}")
            assert expanded == "Bearer secret123"

    def test_env_expansion_missing(self) -> None:
        expanded = LLMAssert._expand_env("${NONEXISTENT_VAR}")
        assert expanded == "${NONEXISTENT_VAR}"

    def test_truncate_short(self) -> None:
        text = "Short text"
        assert LLMAssert._truncate(text) == text

    def test_truncate_long(self) -> None:
        text = "A" * 150
        truncated = LLMAssert._truncate(text, max_len=100)
        assert len(truncated) == 100
        assert truncated.endswith("...")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_call_pass(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS\nThe content is a greeting."
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Hello world", "Is this a greeting?")

        assert result.passed is True
        assert result.criterion == "Is this a greeting?"
        assert "greeting" in result.reasoning.lower()

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_call_fail(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "FAIL\nNot a greeting."
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Goodbye", "Is this a greeting?")

        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_call_with_empty_response(self, mock_completion: MagicMock) -> None:
        """Handle LLM returning empty/None content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        # Should not crash, treats as fail
        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_call_with_no_newline(self, mock_completion: MagicMock) -> None:
        """Handle response with just PASS/FAIL and no reasoning."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        assert result.passed is True
        # Reasoning contains the raw response when no separate reasoning provided
        assert "PASS" in result.reasoning or result.reasoning == ""


class TestPlugin:
    """Tests for pytest plugin integration."""

    def test_plugin_registered(self) -> None:
        """Test that the plugin entry point is correctly configured."""
        from pytest_llm_assert import plugin

        # Plugin should have the required pytest hooks
        assert hasattr(plugin, "pytest_addoption")
        assert hasattr(plugin, "llm_assert")
        assert callable(plugin.pytest_addoption)

    def test_llm_assert_class_importable(self) -> None:
        """Test that LLMAssert can be imported from package root."""
        from pytest_llm_assert import LLMAssert

        assert LLMAssert is not None
        assert callable(LLMAssert)


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_api_error_propagates(self, mock_completion: MagicMock) -> None:
        """API errors should propagate to caller."""
        mock_completion.side_effect = Exception("API rate limit exceeded")

        llm = LLMAssert(model="test/model")

        with pytest.raises(Exception, match="API rate limit exceeded"):
            llm("Content", "criterion")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_network_error_propagates(self, mock_completion: MagicMock) -> None:
        """Network errors should propagate to caller."""
        mock_completion.side_effect = ConnectionError("Failed to connect")

        llm = LLMAssert(model="test/model")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            llm("Content", "criterion")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_timeout_error_propagates(self, mock_completion: MagicMock) -> None:
        """Timeout errors should propagate to caller."""
        mock_completion.side_effect = TimeoutError("Request timed out")

        llm = LLMAssert(model="test/model")

        with pytest.raises(TimeoutError, match="Request timed out"):
            llm("Content", "criterion")

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_malformed_response_handling(self, mock_completion: MagicMock) -> None:
        """Malformed responses should be handled gracefully."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Completely unexpected format
        mock_response.choices[0].message.content = "@@#$%INVALID"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        # Should not crash, treats as fail since it doesn't start with PASS
        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_empty_choices_handling(self, mock_completion: MagicMock) -> None:
        """Empty choices array should raise an appropriate error."""
        mock_response = MagicMock()
        mock_response.choices = []
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")

        with pytest.raises(IndexError):
            llm("Content", "criterion")
