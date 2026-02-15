"""Core LLM assertion implementation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName, Model

# Load default system prompt from file
_PROMPTS_DIR = Path(__file__).parent / "prompts"
_DEFAULT_SYSTEM_PROMPT = (_PROMPTS_DIR / "system_prompt.md").read_text().strip()

if TYPE_CHECKING:
    from typing import Any


class EvaluationResult(BaseModel):
    """Structured output from LLM evaluation."""

    result: str  # "PASS" or "FAIL"
    reasoning: str


@dataclass(slots=True)
class LLMResponse:
    """Response details from the last LLM call.

    Access via `llm.response` after making an assertion call.
    """

    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None
    response_id: str | None = None
    created: int | None = None


@dataclass(slots=True)
class AssertionResult:
    """Result of an LLM assertion with rich repr for pytest."""

    passed: bool
    criterion: str
    reasoning: str
    content_preview: str

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"LLMAssert({status}: {self.criterion!r})\n"
            f"  Content: {self.content_preview!r}\n"
            f"  Reasoning: {self.reasoning}"
        )


class LLMAssert:
    """LLM-powered assertions for semantic evaluation.

    Example:
        >>> llm = LLMAssert(model="openai:gpt-4o-mini")
        >>> assert llm("Hello world", "Is this a greeting?")

    For Azure OpenAI with Entra ID authentication via environment variables:
        >>> # Set AZURE_OPENAI_ENDPOINT and authenticate via az login
        >>> llm = LLMAssert(model="azure:gpt-4o")
    """

    def __init__(
        self,
        model: str | KnownModelName | Model = "openai:gpt-4o-mini",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM assertion helper.

        Args:
            model: Pydantic AI model string (e.g., "openai:gpt-4o-mini", "azure:gpt-4o")
                or a Model instance
            api_key: API key (supports ${ENV_VAR} expansion). Optional for Azure Entra ID.
            **kwargs: Additional parameters passed to Pydantic AI Agent
        """
        self.model_name = model if isinstance(model, str) else None
        self.api_key = self._expand_env(api_key) if api_key else None
        self.kwargs = kwargs
        self._system_prompt: str = _DEFAULT_SYSTEM_PROMPT
        self.response: LLMResponse | None = None

        # Set up environment variables for API key if provided
        if self.api_key:
            if isinstance(model, str):
                if model.startswith("openai:") or model.startswith("azure:"):
                    os.environ.setdefault("OPENAI_API_KEY", self.api_key)
                elif model.startswith("anthropic:"):
                    os.environ.setdefault("ANTHROPIC_API_KEY", self.api_key)

        # Create the agent with structured output
        self._agent = Agent(
            model,
            result_type=EvaluationResult,
            system_prompt=self._system_prompt,
        )

    @property
    def system_prompt(self) -> str:
        """Get the system prompt used for LLM assertions."""
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        """Set a custom system prompt for LLM assertions.

        The prompt should instruct the LLM to evaluate content against a criterion
        and respond in JSON format with 'result' (PASS/FAIL) and 'reasoning' keys.
        """
        self._system_prompt = value
        # Recreate agent with new system prompt
        self._agent = Agent(
            self.model_name or self._agent.model,
            result_type=EvaluationResult,
            system_prompt=self._system_prompt,
        )

    @staticmethod
    def _expand_env(value: str) -> str:
        """Expand ${VAR} patterns in string."""
        pattern = r"\$\{([^}]+)\}"
        return re.sub(pattern, lambda m: os.environ.get(m.group(1), m.group(0)), value)

    @staticmethod
    def _truncate(text: str, max_len: int = 100) -> str:
        """Truncate text for display."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def __call__(self, content: str, criterion: str) -> AssertionResult:
        """Evaluate if content meets the given criterion.

        Args:
            content: The text to evaluate
            criterion: Plain English criterion (e.g., "Is this professional?")

        Returns:
            AssertionResult that is truthy if criterion is met
        """
        user_message = f"Criterion: {criterion}\n\nContent:\n{content}"

        # Run the agent synchronously
        result = self._agent.run_sync(user_message)

        # Extract usage info from the result
        usage = result.usage()
        self.response = LLMResponse(
            model=result.model_name(),
            prompt_tokens=usage.request_tokens if usage else None,
            completion_tokens=usage.response_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            cost=None,  # Pydantic AI doesn't provide cost info directly
        )

        # Extract pass/fail and reasoning from structured output
        evaluation = result.data
        passed = evaluation.result.upper() == "PASS"

        return AssertionResult(
            passed=passed,
            criterion=criterion,
            reasoning=evaluation.reasoning,
            content_preview=self._truncate(content),
        )
