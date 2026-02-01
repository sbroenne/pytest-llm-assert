"""Tests for LLM response parsing."""

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import LLMAssert


class TestJsonParsing:
    """JSON response parsing from LLM."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_parses_json_pass(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '{"result": "PASS", "reasoning": "Looks good"}'
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is True
        assert result.reasoning == "Looks good"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_parses_json_fail(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '{"result": "FAIL", "reasoning": "Does not meet criterion"}'
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is False
        assert result.reasoning == "Does not meet criterion"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_parses_json_in_markdown_block(self, mock_completion: MagicMock) -> None:
        """LLMs sometimes wrap JSON in markdown code blocks."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '```json\n{"result": "PASS", "reasoning": "Valid"}\n```'
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is True
        assert result.reasoning == "Valid"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_parses_json_in_plain_markdown_block(
        self, mock_completion: MagicMock
    ) -> None:
        """Handle markdown blocks without json language specifier."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = '```\n{"result": "PASS", "reasoning": "OK"}\n```'
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is True


class TestFallbackParsing:
    """Fallback line-based parsing when JSON fails."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_fallback_pass_variations(self, mock_completion: MagicMock) -> None:
        """Various pass indicators should be recognized."""
        pass_indicators = ["PASS", "YES", "TRUE", "PASSED", "pass", "yes", "true"]

        for indicator in pass_indicators:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = f"{indicator}\nReasoning here"
            mock_completion.return_value = mock_response

            llm = LLMAssert(model="test/model")
            result = llm("content", "criterion")

            assert result.passed is True, f"Failed for indicator: {indicator}"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_fallback_fail(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "FAIL\nDoes not match"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is False
        assert result.reasoning == "Does not match"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_fallback_no_newline(self, mock_completion: MagicMock) -> None:
        """Single line response should use whole response as reasoning."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "UNKNOWN_RESPONSE"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("content", "criterion")

        assert result.passed is False  # Not a recognized pass indicator
        assert result.reasoning == "UNKNOWN_RESPONSE"


class TestResponseMetadata:
    """LLM response metadata capture."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_captures_usage_stats(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_response.model = "gpt-4"
        mock_response.id = "chatcmpl-123"
        mock_response.created = 1234567890
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        mock_response._hidden_params = {"response_cost": 0.002}
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        llm("content", "criterion")

        assert llm.response is not None
        assert llm.response.model == "gpt-4"
        assert llm.response.response_id == "chatcmpl-123"
        assert llm.response.created == 1234567890
        assert llm.response.prompt_tokens == 100
        assert llm.response.completion_tokens == 50
        assert llm.response.total_tokens == 150
        assert llm.response.cost == 0.002

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_handles_missing_usage(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_response.model = "test-model"
        mock_response.id = None
        mock_response.created = None
        mock_response.usage = None
        # No _hidden_params
        del mock_response._hidden_params
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        llm("content", "criterion")

        assert llm.response is not None
        assert llm.response.prompt_tokens is None
        assert llm.response.cost is None

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_handles_no_hidden_params(self, mock_completion: MagicMock) -> None:
        """Handle responses without _hidden_params attribute."""
        mock_response = MagicMock(spec=["choices", "model", "id", "created", "usage"])
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_response.model = "test"
        mock_response.id = None
        mock_response.created = None
        mock_response.usage = None
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        llm("content", "criterion")

        assert llm.response.cost is None
