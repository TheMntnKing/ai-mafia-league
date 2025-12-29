"""Tests for LLM providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from anthropic import APIConnectionError

from src.providers import (
    AnthropicProvider,
    InvalidResponseError,
    RetryExhausted,
    retry_with_backoff,
)
from src.schemas import ActionType


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


class TestAnthropicProvider:
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client."""
        with patch("src.providers.anthropic.AsyncAnthropic") as mock:
            yield mock.return_value

    @pytest.fixture
    def provider(self, mock_anthropic_client):
        """Provider with mocked client."""
        return AnthropicProvider(api_key="test-key")

    @pytest.fixture
    def sample_tool_response(self):
        """Sample tool use response from Claude."""
        tool_use = MagicMock()
        tool_use.type = "tool_use"
        tool_use.input = {
            "new_events": ["Day started"],
            "notable_changes": [],
            "suspicion_updates": {},
            "pattern_notes": [],
            "current_goal": "survive",
            "reasoning": "No information yet",
            "information_to_share": [],
            "information_to_hide": [],
            "speech": "Hello everyone, let's discuss.",
            "nomination": "Bob",
        }

        response = MagicMock()
        response.content = [tool_use]
        return response

    async def test_act_returns_tool_output(
        self, provider, mock_anthropic_client, sample_tool_response
    ):
        """Provider extracts structured data from tool_use response."""
        mock_anthropic_client.messages.create = AsyncMock(return_value=sample_tool_response)

        result = await provider.act(
            action_type=ActionType.SPEAK,
            context="You are Alice playing Mafia.",
        )

        assert result["speech"] == "Hello everyone, let's discuss."
        assert result["nomination"] == "Bob"

    async def test_act_calls_api_correctly(
        self, provider, mock_anthropic_client, sample_tool_response
    ):
        """Provider calls Anthropic API with correct parameters."""
        mock_anthropic_client.messages.create = AsyncMock(return_value=sample_tool_response)

        await provider.act(
            action_type=ActionType.SPEAK,
            context="Test context",
        )

        # Verify API was called
        mock_anthropic_client.messages.create.assert_called_once()

        # Check call arguments
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["system"] == "Test context"
        assert len(call_kwargs["tools"]) == 1
        assert call_kwargs["tools"][0]["name"] == "speak"

    async def test_act_raises_on_missing_tool_use(self, provider, mock_anthropic_client):
        """Provider raises InvalidResponseError if no tool_use in response."""
        # Response without tool_use block
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "I refuse to use tools"

        response = MagicMock()
        response.content = [text_block]
        mock_anthropic_client.messages.create = AsyncMock(return_value=response)

        with pytest.raises(InvalidResponseError):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )

    async def test_act_raises_on_invalid_schema(self, provider, mock_anthropic_client):
        """Provider raises InvalidResponseError for invalid schema."""
        tool_use = MagicMock()
        tool_use.type = "tool_use"
        tool_use.input = {"speech": "Hello"}  # Missing required fields

        response = MagicMock()
        response.content = [tool_use]
        mock_anthropic_client.messages.create = AsyncMock(return_value=response)

        with pytest.raises(InvalidResponseError):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )

    async def test_act_retries_on_api_error(
        self, provider, mock_anthropic_client, sample_tool_response
    ):
        """Provider retries when API errors occur."""
        request = httpx.Request("POST", "https://example.com")
        error = APIConnectionError(message="Connection error.", request=request)

        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=[error, sample_tool_response]
        )

        result = await provider.act(
            action_type=ActionType.SPEAK,
            context="Test context",
        )

        assert result["speech"] == "Hello everyone, let's discuss."
        assert mock_anthropic_client.messages.create.call_count == 2

    async def test_act_retries_exhausted(self, provider, mock_anthropic_client):
        """Provider raises RetryExhausted after repeated API errors."""
        request = httpx.Request("POST", "https://example.com")
        error = APIConnectionError(message="Connection error.", request=request)

        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=[error, error, error]
        )

        with pytest.raises(RetryExhausted):
            await provider.act(
                action_type=ActionType.SPEAK,
                context="Test context",
            )

    def test_build_tool_for_action(self, provider):
        """Provider builds correct tool schema for each action type."""
        tool = provider._build_tool_for_action(ActionType.SPEAK)

        assert tool["name"] == "speak"
        assert "description" in tool
        assert "input_schema" in tool

        # Check schema has expected fields
        schema = tool["input_schema"]
        assert "properties" in schema
        assert "speech" in schema["properties"]
        assert "nomination" in schema["properties"]

    def test_build_tool_for_vote(self, provider):
        """Provider builds correct tool schema for voting."""
        tool = provider._build_tool_for_action(ActionType.VOTE)

        assert tool["name"] == "vote"
        schema = tool["input_schema"]
        assert "vote" in schema["properties"]
        assert "vote_reasoning" in schema["properties"]

    def test_build_tool_for_last_words(self, provider):
        """Provider builds correct tool schema for last words (simple)."""
        tool = provider._build_tool_for_action(ActionType.LAST_WORDS)

        assert tool["name"] == "last_words"
        schema = tool["input_schema"]
        assert "text" in schema["properties"]
        # LastWordsOutput is simpler, doesn't have reasoning fields
        assert "reasoning" not in schema["properties"]
