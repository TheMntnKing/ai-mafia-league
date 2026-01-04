"""Anthropic Claude provider implementation."""

from __future__ import annotations

from typing import Any

import anthropic
from anthropic import APIConnectionError, APIError, AsyncAnthropic
from pydantic import ValidationError

from src.providers.base import InvalidResponseError, ProviderError, retry_with_backoff
from src.schemas import (
    ActionType,
    DefenseOutput,
    DoctorProtectOutput,
    InvestigationOutput,
    LastWordsOutput,
    NightKillOutput,
    SpeakingOutput,
    VotingOutput,
)

# Try to import langfuse, but make it optional
try:
    from langfuse import Langfuse, observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    Langfuse = None  # type: ignore[assignment]
    LANGFUSE_AVAILABLE = False

    def observe(name: str | None = None, **kwargs: Any) -> Any:  # noqa: ARG001
        """No-op decorator when langfuse is not available."""

        def decorator(func: Any) -> Any:
            return func

        return decorator


# Map ActionType to output schema class
ACTION_SCHEMA_MAP: dict[ActionType, type] = {
    ActionType.SPEAK: SpeakingOutput,
    ActionType.VOTE: VotingOutput,
    ActionType.NIGHT_KILL: NightKillOutput,
    ActionType.INVESTIGATION: InvestigationOutput,
    ActionType.DOCTOR_PROTECT: DoctorProtectOutput,
    ActionType.LAST_WORDS: LastWordsOutput,
    ActionType.DEFENSE: DefenseOutput,
}

_MODEL_PRICING_PER_MILLION: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
}


class AnthropicProvider:
    """
    Anthropic Claude provider using tool_use for structured output.

    Uses function calling (tool_use) to get reliable structured responses.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
        max_tokens: int = 2048,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name to use
            max_tokens: Maximum tokens in response
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def _build_tool_for_action(self, action_type: ActionType) -> dict:
        """
        Build Anthropic tool definition from action type.

        Args:
            action_type: The type of action

        Returns:
            Tool definition dict for Anthropic API
        """
        schema_class = ACTION_SCHEMA_MAP[action_type]
        json_schema = schema_class.model_json_schema()

        # Remove $defs if present (Anthropic doesn't need it for simple schemas)
        json_schema.pop("$defs", None)

        return {
            "name": action_type.value,
            "description": f"Output for {action_type.value} action in Mafia game",
            "input_schema": json_schema,
        }

    @observe(name="llm_call", as_type="generation")
    @retry_with_backoff(
        max_attempts=3,
        base_delay=1.0,
        exceptions=(APIError, APIConnectionError),
    )
    async def act(
        self,
        action_type: ActionType,
        context: str,
    ) -> dict:
        """
        Execute a player action via Claude.

        Args:
            action_type: Type of action (determines output schema)
            context: Full assembled context/prompt string from ContextBuilder

        Returns:
            Raw structured output dict from Claude
        """
        tool = self._build_tool_for_action(action_type)

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=context,
                messages=[{"role": "user", "content": "Execute your action using the tool."}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool["name"]},
            )
        except anthropic.BadRequestError as e:
            raise ProviderError(f"Bad request to Anthropic API: {e}") from e

        # Extract tool use result
        tool_use_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_use_block = block
                break

        if tool_use_block is None:
            raise InvalidResponseError("No tool_use block in response")

        schema_class = ACTION_SCHEMA_MAP[action_type]
        try:
            parsed = schema_class.model_validate(tool_use_block.input)
        except ValidationError as e:
            raise InvalidResponseError(f"Invalid response schema: {e}") from e

        self._record_usage(response)
        return parsed.model_dump()

    def _record_usage(self, response: Any) -> None:
        if not LANGFUSE_AVAILABLE:
            return

        usage = getattr(response, "usage", None)
        if not usage:
            return

        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        if input_tokens is None and output_tokens is None:
            return

        input_tokens = int(input_tokens or 0)
        output_tokens = int(output_tokens or 0)
        total_tokens = input_tokens + output_tokens

        usage_details = {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens,
        }

        cost_details = self._estimate_cost(input_tokens, output_tokens)

        Langfuse().update_current_generation(
            model=self.model,
            usage_details=usage_details,
            cost_details=cost_details,
        )

    def _estimate_cost(
        self, input_tokens: int, output_tokens: int
    ) -> dict[str, float] | None:
        pricing = _MODEL_PRICING_PER_MILLION.get(self.model)
        if not pricing:
            return None

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        return {
            "input": input_cost,
            "output": output_cost,
            "total": total_cost,
        }
