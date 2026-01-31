"""Integration tests for pytest-llm-assert with real LLM calls.

These tests verify that LLM-powered assertions work correctly with actual models.
Supports multiple providers: Azure OpenAI (Entra ID) and Google Vertex AI.

Run with: pytest -m integration -v
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_llm_assert import LLMAssert


# Load .env from workspace root (search upward)
def _find_env_file() -> Path | None:
    path = Path(__file__).resolve()
    for parent in path.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None


if env_file := _find_env_file():
    from dotenv import load_dotenv

    load_dotenv(env_file)

pytestmark = pytest.mark.integration


# =============================================================================
# Provider Configuration (from environment)
# =============================================================================

# Azure deployment name (default: gpt-5-mini - fast and cheap)
AZURE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

# Google Vertex AI model (default: gemini-2.0-flash - fast and capable)
VERTEX_MODEL = os.environ.get("VERTEX_MODEL", "gemini-2.0-flash")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def azure_llm_factory():
    """Factory to create LLMAssert for Azure OpenAI.
    
    Uses Entra ID authentication automatically (via DefaultAzureCredential).
    Requires: AZURE_OPENAI_ENDPOINT environment variable.
    Auth: az login or managed identity - no API key needed.
    """
    from pytest_llm_assert import LLMAssert

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]  # Fail if not set

    def create(deployment: str) -> LLMAssert:
        # Entra ID auth is automatic when no api_key is provided
        return LLMAssert(
            model=f"azure/{deployment}",
            api_base=endpoint,
        )

    return create


@pytest.fixture
def vertex_llm_factory():
    """Factory to create LLMAssert for Google Vertex AI.
    
    Uses Application Default Credentials via LiteLLM.
    Requires: GOOGLE_CLOUD_PROJECT, VERTEXAI_PROJECT, or GCP_PROJECT_ID environment variable.
    Auth: gcloud auth application-default login.
    """
    from pytest_llm_assert import LLMAssert

    project = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("VERTEXAI_PROJECT")
        or os.environ["GCP_PROJECT_ID"]  # Fail if none set
    )

    def create(model: str) -> LLMAssert:
        return LLMAssert(model=f"vertex_ai/{model}")

    return create


# Combined fixture for running same tests across providers
@pytest.fixture(params=["azure", "vertex"])
def llm(request, azure_llm_factory, vertex_llm_factory):
    """LLM instance that cycles through available providers."""
    if request.param == "azure":
        return azure_llm_factory(AZURE_DEPLOYMENT)
    elif request.param == "vertex":
        return vertex_llm_factory(VERTEX_MODEL)


class TestBasicAssertions:
    """Test basic pass/fail assertions."""

    def test_success_message_passes(self, llm):
        """A success message should be recognized."""
        result = llm(
            "Operation completed successfully. 3 records updated.",
            "Does this indicate the operation succeeded?",
        )
        assert result

    def test_error_message_detected(self, llm):
        """An error message should fail a success check."""
        result = llm(
            "Error: Connection refused. Unable to reach database.",
            "Does this indicate success?",
        )
        assert not result


class TestSemanticVariations:
    """Test the core value: handling variations that string matching can't.

    This is WHY you use pytest-llm-assert instead of regular assertions.
    """

    def test_success_message_variations(self, llm):
        """Different ways to indicate success should all pass."""
        success_messages = [
            "Operation completed successfully",
            "Done. 5 items processed.",
            "Build succeeded with 0 errors",
            "All tests passed",
            "Request fulfilled",
            "Task finished without errors",
        ]
        for msg in success_messages:
            result = llm(msg, "Does this indicate the operation succeeded?")
            assert result, f"Failed to recognize success: {msg}"

    def test_error_message_variations(self, llm):
        """Different ways to indicate failure should all be detected.

        Allow minor LLM inconsistency - require 5/6 to pass (AI can be flaky).
        """
        error_messages = [
            "Error: file not found",
            "Failed to connect to database",
            "Build failed with 3 errors",
            "Exception: NullPointerException",
            "Unable to process request",
            "FATAL: Out of memory",
        ]
        passed_count = 0
        for msg in error_messages:
            result = llm(msg, "Does this indicate an error or failure?")
            if result:
                passed_count += 1

        # Allow 1 flaky failure - LLMs can be inconsistent
        min_required = len(error_messages) - 1
        assert passed_count >= min_required, (
            f"Only {passed_count}/{len(error_messages)} error messages recognized "
            f"(need at least {min_required})"
        )


class TestSQLSemanticEquivalence:
    """Test SQL validation - the README hero example."""

    def test_valid_sql_variations(self, llm):
        """Different valid SQL for the same intent should all pass."""
        valid_queries = [
            "SELECT name FROM users WHERE age > 21",
            "SELECT name FROM users WHERE age >= 22",
            "select NAME from USERS where AGE > 21",  # Case insensitive
            "SELECT u.name FROM users u WHERE u.age > 21",  # With alias
            "SELECT name FROM users WHERE age > 21 ORDER BY name",  # With ORDER BY
        ]
        for sql in valid_queries:
            result = llm(
                sql,
                "Is this a valid SQL query that selects user names filtered by age?",
            )
            assert result, f"Failed to validate: {sql}"

    def test_invalid_sql_detected(self, llm):
        """Invalid or wrong SQL should fail."""
        invalid_queries = [
            "SELEC name FROM users",  # Typo
            "SELECT name WHERE age > 21",  # Missing FROM
            "DELETE FROM users",  # Wrong operation
        ]
        for sql in invalid_queries:
            result = llm(sql, "Is this a valid SELECT query for user names?")
            assert not result, f"Should have rejected: {sql}"


class TestSemanticUnderstanding:
    """Test that LLM understands semantic meaning, not just keywords."""

    def test_understands_equivalent_logic(self, llm):
        """LLM should recognize logically equivalent code."""
        code = "if not (x > 0 and y > 0): return False"
        result = llm(
            code, "Does this code return False when either x or y is not positive?"
        )
        assert result

    def test_detects_potential_bug(self, llm):
        """LLM should detect a potential off-by-one error."""
        code = "for i in range(len(items)): print(items[i+1])"
        result = llm(code, "Does this code have a potential index out of bounds error?")
        assert result
