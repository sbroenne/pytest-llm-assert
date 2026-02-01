"""Tests for LLMResponse dataclass."""

from pytest_llm_assert.core import LLMResponse


class TestLLMResponse:
    """LLMResponse should store response metadata from LLM calls."""

    def test_defaults_to_none(self) -> None:
        response = LLMResponse()
        assert response.model is None
        assert response.prompt_tokens is None
        assert response.completion_tokens is None
        assert response.total_tokens is None
        assert response.cost is None
        assert response.response_id is None
        assert response.created is None

    def test_stores_all_fields(self) -> None:
        response = LLMResponse(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost=0.001,
            response_id="chatcmpl-123",
            created=1234567890,
        )
        assert response.model == "gpt-4"
        assert response.prompt_tokens == 100
        assert response.completion_tokens == 50
        assert response.total_tokens == 150
        assert response.cost == 0.001
        assert response.response_id == "chatcmpl-123"
        assert response.created == 1234567890
