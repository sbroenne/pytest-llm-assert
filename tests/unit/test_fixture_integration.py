"""Integration test for the llm_assert pytest fixture.

This test must run WITH the plugin enabled to test the actual fixture.
"""


def test_llm_assert_fixture_is_available(llm_assert) -> None:
    """The llm_assert fixture should be available when plugin is loaded."""
    from pytest_llm_assert import LLMAssert

    assert isinstance(llm_assert, LLMAssert)
    assert llm_assert.model == "openai/gpt-5-mini"  # Default
