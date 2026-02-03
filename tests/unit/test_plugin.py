"""Tests for pytest plugin integration."""

from unittest.mock import MagicMock

from pytest_llm_assert import AssertionResult, LLMAssert, LLMResponse, plugin


class TestPluginHooks:
    """Plugin entry point configuration."""

    def test_has_required_hooks(self) -> None:
        """Plugin should have required pytest hooks."""
        assert hasattr(plugin, "pytest_addoption")
        assert hasattr(plugin, "llm_assert")
        assert callable(plugin.pytest_addoption)

    def test_pytest_addoption_adds_options(self) -> None:
        """pytest_addoption should register CLI options."""
        mock_parser = MagicMock()
        mock_group = MagicMock()
        mock_parser.getgroup.return_value = mock_group

        plugin.pytest_addoption(mock_parser)

        # Verify group was created
        mock_parser.getgroup.assert_called_once_with(
            "llm-assert", "LLM-powered assertions"
        )

        # Verify all options were added
        assert mock_group.addoption.call_count == 3

        # Check option names
        calls = mock_group.addoption.call_args_list
        option_names = [call[0][0] for call in calls]
        assert "--llm-model" in option_names
        assert "--llm-api-key" in option_names
        assert "--llm-api-base" in option_names


class TestLlmAssertFixture:
    """Tests for the llm_assert fixture."""

    def test_fixture_creates_llm_assert(self, pytestconfig) -> None:
        """Fixture should create an LLMAssert instance."""
        # Use pytestconfig to access the real config
        mock_request = MagicMock()
        mock_request.config = pytestconfig

        # The fixture function (unwrapped) expects a request object
        # We can't easily test the decorated fixture, so test the logic
        model = pytestconfig.getoption("--llm-model", default="openai/gpt-5-mini")
        api_key = pytestconfig.getoption("--llm-api-key", default=None)
        api_base = pytestconfig.getoption("--llm-api-base", default=None)

        result = LLMAssert(model=model, api_key=api_key, api_base=api_base)

        assert isinstance(result, LLMAssert)
        assert result.model == "openai/gpt-5-mini"  # Default value


class TestPackageExports:
    """Package-level imports."""

    def test_llm_assert_importable(self) -> None:
        """LLMAssert can be imported from package root."""
        assert LLMAssert is not None
        assert callable(LLMAssert)

    def test_assertion_result_importable(self) -> None:
        """AssertionResult can be imported from package root."""
        assert AssertionResult is not None

    def test_llm_response_importable(self) -> None:
        """LLMResponse can be imported from package root."""
        assert LLMResponse is not None

    def test_version_available(self) -> None:
        """Package version should be accessible."""
        from pytest_llm_assert import __version__

        assert __version__ == "0.1.0"

    def test_all_exports(self) -> None:
        """__all__ should list expected exports."""
        from pytest_llm_assert import __all__ as exports

        assert set(exports) == {
            "LLMAssert",
            "AssertionResult",
            "LLMResponse",
        }
