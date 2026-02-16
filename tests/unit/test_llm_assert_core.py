"""Tests for LLMAssert class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import EvaluationResult, LLMAssert


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
        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        assert "assertion evaluator" in llm.system_prompt.lower()
        assert "JSON" in llm.system_prompt

    def test_custom_prompt_setter(self) -> None:
        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        custom = "You are a custom evaluator."
        llm.system_prompt = custom
        assert llm.system_prompt == custom

    @patch("pydantic_ai.Agent.run_sync")
    def test_prompt_used_in_agent(self, mock_run_sync: MagicMock) -> None:
        """Custom prompt should be used in agent."""
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="Test")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        custom_prompt = "CUSTOM_PROMPT_MARKER"
        llm.system_prompt = custom_prompt
        llm("content", "criterion")

        # Verify the agent was recreated with the custom prompt
        assert llm._system_prompt == custom_prompt


class TestInitialization:
    """LLMAssert initialization."""

    def test_default_model(self) -> None:
        llm = LLMAssert()
        assert llm.model_name == "openai:gpt-4o-mini"

    def test_custom_model(self) -> None:
        llm = LLMAssert(model="anthropic:claude-3-sonnet")
        assert llm.model_name == "anthropic:claude-3-sonnet"

    def test_api_key_expansion(self) -> None:
        with patch.dict("os.environ", {"MY_KEY": "secret"}):
            llm = LLMAssert(model="openai:test", api_key="${MY_KEY}")
            assert llm.api_key == "secret"

    def test_kwargs_stored(self) -> None:
        llm = LLMAssert(
            model="openai:test", api_key="key", temperature=0.5, max_tokens=100
        )
        assert llm.kwargs == {"temperature": 0.5, "max_tokens": 100}

    def test_response_initially_none(self) -> None:
        llm = LLMAssert(model="openai:test", api_key="key")
        assert llm.response is None


class TestLLMCall:
    """LLM call behavior with mocked responses."""

    @patch("pydantic_ai.Agent.run_sync")
    def test_pass_result(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="PASS", reasoning="The content is a greeting."
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("Hello world", "Is this a greeting?")

        assert result.passed is True
        assert result.criterion == "Is this a greeting?"
        assert "greeting" in result.reasoning.lower()

    @patch("pydantic_ai.Agent.run_sync")
    def test_fail_result(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(
            result="FAIL", reasoning="Not a greeting."
        )
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("Goodbye", "Is this a greeting?")

        assert result.passed is False

    @patch("pydantic_ai.Agent.run_sync")
    def test_content_preview_in_result(self, mock_run_sync: MagicMock) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="OK")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        result = llm("Hello world", "criterion")

        assert result.content_preview == "Hello world"

    @patch("pydantic_ai.Agent.run_sync")
    def test_long_content_truncated_in_preview(
        self, mock_run_sync: MagicMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.output = EvaluationResult(result="PASS", reasoning="OK")
        mock_result.usage.return_value = MagicMock(
            request_tokens=10, response_tokens=5, total_tokens=15
        )
        mock_result.model_name = "openai:test-model"
        mock_run_sync.return_value = mock_result

        llm = LLMAssert(model="openai:test-model", api_key="test-key")
        long_content = "X" * 200
        result = llm(long_content, "criterion")

        assert len(result.content_preview) == 100
        assert result.content_preview.endswith("...")
