"""Core LLM assertion implementation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

import litellm

if TYPE_CHECKING:
    from typing import Any


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
        >>> llm = LLMAssert(model="openai/gpt-5-mini")
        >>> assert llm("Hello world", "Is this a greeting?")

    For Azure OpenAI with Entra ID, just use `az login` - no API key needed:
        >>> llm = LLMAssert(model="azure/gpt-4o", api_base="https://your-resource.openai.azure.com")
    """

    def __init__(
        self,
        model: str = "openai/gpt-5-mini",
        api_key: str | None = None,
        api_base: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM assertion helper.

        Args:
            model: LiteLLM model string (e.g., "openai/gpt-5-mini", "azure/gpt-4o")
            api_key: API key (supports ${ENV_VAR} expansion).
                For Azure, leave empty to use Entra ID.
            api_base: Custom API base URL (required for Azure)
            **kwargs: Additional parameters passed to LiteLLM
        """
        self.model = model
        self.api_key = self._expand_env(api_key) if api_key else None
        self.api_base = api_base
        self.kwargs = kwargs
        self._azure_ad_token_provider: Callable[[], str] | None = None
        self._system_prompt: str = (
            "You are an assertion evaluator. "
            "Evaluate if the given content meets the specified criterion.\n\n"
            "Respond in JSON format:\n"
            '{"result": "PASS" or "FAIL", "reasoning": "brief explanation"}'
        )
        self.response: LLMResponse | None = None

        # Auto-configure Azure Entra ID when no API key is provided
        if self._is_azure_model() and not self._has_azure_api_key():
            self._azure_ad_token_provider = self._get_azure_ad_token_provider()

    def _is_azure_model(self) -> bool:
        """Check if the model is an Azure OpenAI model."""
        return self.model.startswith("azure/")

    def _has_azure_api_key(self) -> bool:
        """Check if an Azure API key is available."""
        return bool(self.api_key or os.environ.get("AZURE_API_KEY"))

    @staticmethod
    def _get_azure_ad_token_provider() -> Callable[[], str] | None:
        """Get Azure AD token provider for Entra ID authentication.

        Uses LiteLLM's built-in helper which leverages DefaultAzureCredential:
        - Azure CLI credentials (az login)
        - Managed Identity
        - Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, ...)
        - Visual Studio Code credentials
        """
        try:
            from litellm.secret_managers.get_azure_ad_token_provider import (
                get_azure_ad_token_provider,
            )

            return get_azure_ad_token_provider()
        except ImportError:
            # azure-identity not installed
            return None
        except Exception:
            # Credential not available
            return None

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

    def _call_llm(self, messages: list[dict[str, str]]) -> str:
        """Call the LLM and return response content. Updates self.response."""
        kwargs = {**self.kwargs}

        # Use Azure AD token provider if configured (Entra ID auth)
        if self._azure_ad_token_provider is not None:
            kwargs["azure_ad_token_provider"] = self._azure_ad_token_provider

        response = litellm.completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            api_base=self.api_base,
            **kwargs,
        )
        content = response.choices[0].message.content or ""  # type: ignore[union-attr]

        # Store response details on instance
        self.response = LLMResponse(
            model=getattr(response, "model", None),
            response_id=getattr(response, "id", None),
            created=getattr(response, "created", None),
        )

        # Extract usage info
        usage = getattr(response, "usage", None)
        if usage:
            self.response.prompt_tokens = getattr(usage, "prompt_tokens", None)
            self.response.completion_tokens = getattr(usage, "completion_tokens", None)
            self.response.total_tokens = getattr(usage, "total_tokens", None)

        # Extract cost from hidden params (litellm calculates this)
        if hasattr(response, "_hidden_params"):
            self.response.cost = response._hidden_params.get("response_cost")

        return content

    def __call__(self, content: str, criterion: str) -> AssertionResult:
        """Evaluate if content meets the given criterion.

        Args:
            content: The text to evaluate
            criterion: Plain English criterion (e.g., "Is this professional?")

        Returns:
            AssertionResult that is truthy if criterion is met
        """
        messages = [
            {
                "role": "system",
                "content": self._system_prompt,
            },
            {
                "role": "user",
                "content": f"Criterion: {criterion}\n\nContent:\n{content}",
            },
        ]

        response_text = self._call_llm(messages)

        # Parse JSON response
        try:
            # Handle potential markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            passed = data.get("result", "").upper() == "PASS"
            reasoning = data.get("reasoning", "")
        except (json.JSONDecodeError, AttributeError):
            # Fallback to line-based parsing
            lines = response_text.strip().split("\n", 1)
            first_line = lines[0].strip().upper()
            passed = first_line in ("PASS", "YES", "TRUE", "PASSED")
            reasoning = lines[1].strip() if len(lines) > 1 else response_text

        return AssertionResult(
            passed=passed,
            criterion=criterion,
            reasoning=reasoning,
            content_preview=self._truncate(content),
        )
