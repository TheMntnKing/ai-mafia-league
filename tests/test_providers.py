"""Tests for LLM providers."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.providers import (
    GoogleGenAIProvider,
    InvalidResponseError,
    RetryExhausted,
    retry_with_backoff,
)
from src.schemas import ActionType, SpeakingOutput
from tests.sgr_helpers import make_speak_response


class TestRetryDecorator:
    async def test_success_first_try(self):
        """Function succeeds on first attempt."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    async def test_success_after_retry(self):
        """Function succeeds after initial failure."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await eventually_succeeds()
        assert result == "success"
        assert call_count == 2

    async def test_exhausts_retries(self):
        """Raises RetryExhausted after max attempts."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryExhausted) as exc_info:
            await always_fails()

        assert call_count == 3
        assert "Failed after 3 attempts" in str(exc_info.value)

    async def test_only_catches_specified_exceptions(self):
        """Only retries on specified exception types."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("Different error")

        with pytest.raises(TypeError):
            await raises_type_error()

        # Should not retry because TypeError is not in exceptions
        assert call_count == 1


class TestGoogleGenAIProvider:
    @pytest.fixture
    def mock_genai_client(self):
        """Mock Google GenAI client."""
        with patch("src.providers.google.genai.Client") as mock:
            client = mock.return_value
            client.aio = MagicMock()
            client.aio.models.generate_content = AsyncMock()
            yield client

    @pytest.fixture
    def provider(self, mock_genai_client):
        """Provider with mocked client."""
        return GoogleGenAIProvider(api_key="test-key")

    @pytest.fixture
    def sample_response(self):
        """Sample JSON response from Gemini."""
        response = MagicMock()
        response.text = json.dumps(
            make_speak_response(
                observations="Day started.",
                suspicions="No strong suspicions yet.",
                strategy="Gather information.",
                reasoning="No information yet.",
                speech="Hello everyone, let's discuss.",
                nomination="Bob",
            )
        )
        return response

    async def test_act_returns_structured_output(
        self, provider, mock_genai_client, sample_response
    ):
        """Provider extracts structured data from response JSON."""
        mock_genai_client.aio.models.generate_content = AsyncMock(
            return_value=sample_response
        )

        result = await provider.act(
            action_type=ActionType.SPEAK,
            context="You are Alice playing Mafia.",
        )

        assert result["speech"] == "Hello everyone, let's discuss."
        assert result["nomination"] == "Bob"

    async def test_act_calls_api_correctly(
        self, provider, mock_genai_client, sample_response
    ):
        """Provider calls GenAI API with correct parameters."""
        mock_genai_client.aio.models.generate_content = AsyncMock(
            return_value=sample_response
        )

        await provider.act(
            action_type=ActionType.SPEAK,
            context="Test context",
        )

        mock_genai_client.aio.models.generate_content.assert_called_once()
        call_kwargs = mock_genai_client.aio.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-3-flash-preview"
        assert call_kwargs["contents"] == "Test context"
        assert call_kwargs["config"]["response_mime_type"] == "application/json"
        assert call_kwargs["config"]["response_json_schema"] == SpeakingOutput.model_json_schema()

    async def test_act_raises_on_empty_response(self, provider, mock_genai_client):
        """Provider raises InvalidResponseError if response is empty."""
        response = MagicMock()
        response.text = ""
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=response)

        with pytest.raises(InvalidResponseError):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )

    async def test_act_raises_on_invalid_schema(self, provider, mock_genai_client):
        """Provider raises InvalidResponseError for invalid schema."""
        response = MagicMock()
        response.text = json.dumps({"speech": "Hello"})
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=response)

        with pytest.raises(InvalidResponseError):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )

    async def test_records_usage_with_langfuse(
        self, provider, mock_genai_client, sample_response, monkeypatch
    ):
        """Langfuse receives usage details when available."""
        from src.providers import google as provider_module

        mock_langfuse = MagicMock()
        monkeypatch.setattr(provider_module, "LANGFUSE_AVAILABLE", True)
        monkeypatch.setattr(provider_module, "Langfuse", MagicMock(return_value=mock_langfuse))

        usage = MagicMock()
        usage.prompt_token_count = 12
        usage.candidates_token_count = 8
        sample_response.usage_metadata = usage
        mock_genai_client.aio.models.generate_content = AsyncMock(return_value=sample_response)

        await provider.act(
            action_type=ActionType.SPEAK,
            context="Test context",
        )

        mock_langfuse.update_current_generation.assert_called_once()
        call_kwargs = mock_langfuse.update_current_generation.call_args.kwargs
        assert call_kwargs["model"] == "gemini-3-flash-preview"
        assert call_kwargs["usage_details"]["total"] == 20

    async def test_act_retries_on_provider_error(
        self, provider, mock_genai_client, sample_response
    ):
        """Provider retries when API errors occur."""
        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=[Exception("Connection error."), sample_response]
        )

        result = await provider.act(
            action_type=ActionType.SPEAK,
            context="Test context",
        )

        assert result["speech"] == "Hello everyone, let's discuss."
        assert mock_genai_client.aio.models.generate_content.call_count == 2

    async def test_act_retries_exhausted(self, provider, mock_genai_client):
        """Provider raises RetryExhausted after repeated API errors."""
        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=[
                Exception("Connection error."),
                Exception("Connection error."),
                Exception("Connection error."),
            ]
        )

        with pytest.raises(RetryExhausted):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )
