"""Example pytest tests demonstrating pytest-llm-assert.

Run with: pytest examples/test_basic.py -v

This shows the core value: semantic matching handles variations
that traditional string assertions fail on.
"""

import pytest

from pytest_llm_assert import LLMAssert


@pytest.fixture
def llm():
    """LLM assertion helper - configure via environment or override here."""
    import os

    model = os.environ.get("LLM_MODEL", "openai/gpt-5-mini")
    return LLMAssert(model=model)


class TestSemanticVariations:
    """The hero use case: handling variations that string matching can't."""

    def test_success_message_variations(self, llm):
        """LLM handles success variations that string matching can't."""
        success_messages = [
            "Operation completed successfully",
            "Success!",
            "Done ✓",
            "The task finished without errors",
        ]
        for msg in success_messages:
            assert llm(msg, "Does this indicate the operation succeeded?"), (
                f"Failed: {msg}"
            )

    def test_error_message_variations(self, llm):
        """Different error phrasings should all be recognized."""
        error_messages = [
            "Error: file not found",
            "Failed to connect",
            "Something went wrong",
            "❌ Operation failed",
        ]
        for msg in error_messages:
            assert llm(msg, "Does this indicate an error or failure?"), f"Failed: {msg}"


class TestSQLValidation:
    """SQL validation - the README hero example."""

    def test_valid_sql_variations(self, llm):
        """Different valid SQL for same intent should all pass."""
        valid_queries = [
            "SELECT name FROM users WHERE age > 21",
            "select NAME from USERS where AGE > 21",  # Case insensitive
            "SELECT u.name FROM users u WHERE u.age > 21",  # With alias
        ]
        for sql in valid_queries:
            assert llm(
                sql,
                "Is this a valid SQL query that selects user names filtered by age?",
            )

    def test_invalid_sql_rejected(self, llm):
        """Invalid SQL should fail."""
        assert not llm("SELEC name FROM users", "Is this a valid SELECT query?")
