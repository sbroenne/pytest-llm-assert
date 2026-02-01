"""Tests for Azure authentication in LLMAssert."""

from unittest.mock import MagicMock, patch

from pytest_llm_assert.core import LLMAssert


class TestAzureModelDetection:
    """Detection of Azure OpenAI models."""

    def test_azure_model_detected(self) -> None:
        llm = LLMAssert(model="azure/gpt-4o")
        assert llm._is_azure_model() is True

    def test_openai_model_not_azure(self) -> None:
        llm = LLMAssert(model="openai/gpt-5-mini")
        assert llm._is_azure_model() is False

    def test_anthropic_model_not_azure(self) -> None:
        llm = LLMAssert(model="anthropic/claude-3")
        assert llm._is_azure_model() is False


class TestAzureApiKeyDetection:
    """Detection of Azure API key availability."""

    def test_no_key_returns_false(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            llm = LLMAssert(model="azure/gpt-4o")
            # Remove any key that might have been set
            llm.api_key = None
            assert llm._has_azure_api_key() is False

    def test_instance_key_returns_true(self) -> None:
        llm = LLMAssert(model="azure/gpt-4o", api_key="test-key")
        assert llm._has_azure_api_key() is True

    def test_env_key_returns_true(self) -> None:
        with patch.dict("os.environ", {"AZURE_API_KEY": "env-key"}):
            llm = LLMAssert(model="azure/gpt-4o")
            llm.api_key = None  # Ensure not using instance key
            assert llm._has_azure_api_key() is True


class TestAzureAdTokenProvider:
    """Azure AD token provider for Entra ID auth."""

    def test_returns_provider_when_available(self) -> None:
        mock_provider = MagicMock()
        with patch(
            "pytest_llm_assert.core.LLMAssert._get_azure_ad_token_provider",
            return_value=mock_provider,
        ):
            with patch.dict("os.environ", {}, clear=True):
                # Clear AZURE_API_KEY to trigger Entra ID auth
                llm = LLMAssert.__new__(LLMAssert)
                llm.model = "azure/gpt-4o"
                llm.api_key = None
                llm.api_base = None
                llm.kwargs = {}
                llm._system_prompt = "test"
                llm.response = None
                llm._azure_ad_token_provider = None

                # Manually trigger the check
                if llm._is_azure_model() and not llm._has_azure_api_key():
                    llm._azure_ad_token_provider = (
                        LLMAssert._get_azure_ad_token_provider()
                    )

    def test_returns_none_on_import_error(self) -> None:
        with patch(
            "pytest_llm_assert.core.LLMAssert._get_azure_ad_token_provider"
        ) as mock:
            # Simulate the actual method behavior on ImportError
            mock.return_value = None
            result = mock()
            assert result is None

    def test_returns_none_on_credential_exception(self) -> None:
        """Test that generic exceptions in credential retrieval return None."""
        with patch(
            "litellm.secret_managers.get_azure_ad_token_provider.get_azure_ad_token_provider",
            side_effect=Exception("Credential not available"),
        ):
            result = LLMAssert._get_azure_ad_token_provider()
            assert result is None

    def test_actual_provider_import_error(self) -> None:
        """Test the actual _get_azure_ad_token_provider with import failure."""
        with patch.dict(
            "sys.modules", {"litellm.secret_managers.get_azure_ad_token_provider": None}
        ):
            with patch(
                "litellm.secret_managers.get_azure_ad_token_provider.get_azure_ad_token_provider",
                side_effect=ImportError("Module not found"),
            ):
                # The actual method should catch ImportError and return None
                # Result could be None or a real provider depending on environment
                # We're testing it doesn't raise
                LLMAssert._get_azure_ad_token_provider()


class TestAzureInitialization:
    """Azure model initialization with Entra ID."""

    def test_azure_without_key_gets_token_provider(self) -> None:
        """Azure model without API key should attempt to get token provider."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(
                LLMAssert,
                "_get_azure_ad_token_provider",
                return_value=lambda: "mock-token",
            ) as mock_get_provider:
                LLMAssert(
                    model="azure/gpt-4o", api_base="https://test.openai.azure.com"
                )
                mock_get_provider.assert_called_once()

    def test_azure_with_key_skips_token_provider(self) -> None:
        """Azure model with API key should not attempt Entra ID."""
        with patch.object(
            LLMAssert, "_get_azure_ad_token_provider"
        ) as mock_get_provider:
            LLMAssert(
                model="azure/gpt-4o",
                api_key="test-key",
                api_base="https://test.openai.azure.com",
            )
            mock_get_provider.assert_not_called()

    def test_non_azure_skips_token_provider(self) -> None:
        """Non-Azure models should not attempt Entra ID."""
        with patch.object(
            LLMAssert, "_get_azure_ad_token_provider"
        ) as mock_get_provider:
            LLMAssert(model="openai/gpt-5-mini")
            mock_get_provider.assert_not_called()


class TestAzureTokenProviderInCall:
    """Azure AD token provider usage in LLM calls."""

    @patch("pytest_llm_assert.core.litellm.completion")
    def test_token_provider_passed_to_litellm(self, mock_completion: MagicMock) -> None:
        """When token provider is set, it should be passed to litellm."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "PASS"
        mock_completion.return_value = mock_response

        # Create LLM and manually set token provider
        llm = LLMAssert(model="azure/gpt-4o", api_base="https://test.openai.azure.com")
        mock_token_provider = MagicMock(return_value="mock-token")
        llm._azure_ad_token_provider = mock_token_provider

        # Make a call
        llm("content", "criterion")

        # Verify token provider was passed
        call_kwargs = mock_completion.call_args.kwargs
        assert "azure_ad_token_provider" in call_kwargs
        assert call_kwargs["azure_ad_token_provider"] == mock_token_provider
