"""Tests for LLMAssert class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import LLMAssert


class TestEnvExpansion:
    """Environment variable expansion in API keys."""

    def test_expands_env_variable(self) -> None:
        with patch.dict("os.environ", {"TEST_KEY": "secret123"}):
            expanded = LLMAssert._expand_env("Bearer ${TEST_KEY}")
            assert expanded == "Bearer secret123"

    def test_missing_var_unchanged(self) -> None:
        expanded = LLMAssert._expand_env("${NONEXISTENT_VAR}")
        assert expanded == "${NONEXISTENT_VAR}"

    def test_multiple_vars(self) -> None:
        with patch.dict("os.environ", {"A": "first", "B": "second"}):
            expanded = LLMAssert._expand_env("${A}-${B}")
            assert expanded == "first-second"


class TestTruncation:
    """Content preview truncation."""

    def test_short_text_unchanged(self) -> None:
        text = "Short text"
        assert LLMAssert._truncate(text) == text

    def test_long_text_truncated(self) -> None:
        text = "A" * 150
        truncated = LLMAssert._truncate(text, max_len=100)
        assert len(truncated) == 100
        assert truncated.endswith("...")

    def test_exact_length_unchanged(self) -> None:
        text = "A" * 100
        assert LLMAssert._truncate(text, max_len=100) == text


class TestSystemPrompt:
    """System prompt getter and setter."""

    def test_default_prompt_loaded(self) -> None:
        llm = LLMAssert(model="test/model")
        assert "assertion evaluator" in llm.system_prompt.lower()
        assert "JSON" in llm.system_prompt

    def test_custom_prompt_setter(self) -> None:
        llm = LLMAssert(model="test/model")
        custom = "You are a custom evaluator."
        llm.system_prompt = custom
        assert llm.system_prompt == custom

    def test_prompt_used_in_messages(self) -> None:
        """Custom prompt should be used in LLM call."""
        with patch("pytest_llm_assert.core.litellm.completion") as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "PASS"
            mock_completion.return_value = mock_response

            llm = LLMAssert(model="test/model")
            llm.system_prompt = "CUSTOM_PROMPT_MARKER"
            llm("content", "criterion")

            call_args = mock_completion.call_args
            messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
            system_msg = messages[0]
            assert system_msg["content"] == "CUSTOM_PROMPT_MARKER"


class TestInitialization:
    """LLMAssert initialization."""

    def test_default_model(self) -> None:
        llm = LLMAssert()
        assert llm.model == "openai/gpt-5-mini"

    def test_custom_model(self) -> None:
        llm = LLMAssert(model="anthropic/claude-3")
        assert llm.model == "anthropic/claude-3"

    def test_api_key_expansion(self) -> None:
        with patch.dict("os.environ", {"MY_KEY": "secret"}):
            llm = LLMAssert(model="test", api_key="${MY_KEY}")
            assert llm.api_key == "secret"

    def test_kwargs_stored(self) -> None:
        llm = LLMAssert(model="test", temperature=0.5, max_tokens=100)
        assert llm.kwargs == {"temperature": 0.5, "max_tokens": 100}

    def test_response_initially_none(self) -> None:
        llm = LLMAssert(model="test")
        assert llm.response is None


class TestLLMCall:
    """LLM call behavior with mocked responses."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_pass_result(self, mock_completion: MagicMock) -> None:
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
    def test_fail_result(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "FAIL\nNot a greeting."
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Goodbye", "Is this a greeting?")

        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_empty_content_is_fail(self, mock_completion: MagicMock) -> None:
        """Handle LLM returning empty/None content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        assert result.passed is False

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_no_reasoning_ok(self, mock_completion: MagicMock) -> None:
        """Handle response with just PASS/FAIL and no reasoning."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Content", "criterion")

        assert result.passed is True

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_kwargs_passed_to_litellm(self, mock_completion: MagicMock) -> None:
        """Additional kwargs should be passed to litellm.completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model", temperature=0, max_tokens=50)
        llm("content", "criterion")

        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs.get("temperature") == 0
        assert call_kwargs.get("max_tokens") == 50

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_content_preview_in_result(self, mock_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        result = llm("Hello world", "criterion")

        assert result.content_preview == "Hello world"

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_long_content_truncated_in_preview(
        self, mock_completion: MagicMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        llm = LLMAssert(model="test/model")
        long_content = "X" * 200
        result = llm(long_content, "criterion")

        assert len(result.content_preview) == 100
        assert result.content_preview.endswith("...")
