"""Tests for AssertionResult dataclass."""

from pytest_llm_assert.core import AssertionResult


class TestBooleanBehavior:
    """AssertionResult should be truthy when passed, falsy when failed."""

    def test_passed_is_truthy(self) -> None:
        result = AssertionResult(
            passed=True,
            criterion="Is greeting",
            reasoning="Contains hello",
            content_preview="Hello...",
        )
        assert result
        assert bool(result) is True

    def test_failed_is_falsy(self) -> None:
        result = AssertionResult(
            passed=False,
            criterion="Is greeting",
            reasoning="No greeting found",
            content_preview="Goodbye...",
        )
        assert not result
        assert bool(result) is False


class TestRepr:
    """AssertionResult repr should be informative for pytest output."""

    def test_pass_shows_criterion_and_reasoning(self) -> None:
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

    def test_fail_shows_status(self) -> None:
        result = AssertionResult(
            passed=False,
            criterion="Is professional",
            reasoning="Too casual",
            content_preview="Hey dude...",
        )
        repr_str = repr(result)
        assert "FAIL" in repr_str
