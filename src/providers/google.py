"""Google GenAI provider implementation."""

from __future__ import annotations

import asyncio
from typing import Any

from google import genai
from google.genai import types
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

# Gemini pricing per million tokens (as of Jan 2025)
_MODEL_PRICING_PER_MILLION: dict[str, dict[str, float]] = {
    "gemini-3-flash-preview": {"input": 0.50, "output": 3.00}
}

ACTION_SCHEMA_MAP: dict[ActionType, type] = {
    ActionType.SPEAK: SpeakingOutput,
    ActionType.VOTE: VotingOutput,
    ActionType.NIGHT_KILL: NightKillOutput,
    ActionType.INVESTIGATION: InvestigationOutput,
    ActionType.DOCTOR_PROTECT: DoctorProtectOutput,
    ActionType.LAST_WORDS: LastWordsOutput,
    ActionType.DEFENSE: DefenseOutput,
}


class GoogleGenAIProvider:
    """Google GenAI provider using response_json_schema for structured output."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash-preview",
    ) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def _generate_content(self, *, contents: str, config: dict[str, Any]) -> Any:
        async_client = getattr(self.client, "aio", None)
        if async_client and hasattr(async_client.models, "generate_content"):
            return await async_client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        return await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=contents,
            config=config,
        )

    @retry_with_backoff(max_attempts=3, base_delay=1.0, exceptions=(ProviderError,))
    async def _request(self, *, contents: str, config: dict[str, Any]) -> Any:
        try:
            return await self._generate_content(contents=contents, config=config)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"GenAI request failed: {e}") from e

    @observe(name="llm_call", as_type="generation")
    async def act(
        self,
        action_type: ActionType,
        context: str,
    ) -> dict:
        """
        Execute a player action via Gemini.

        Args:
            action_type: Type of action (determines output schema)
            context: Full assembled context/prompt string from ContextBuilder

        Returns:
            Raw structured output dict from Gemini
        """
        schema_class = ACTION_SCHEMA_MAP[action_type]
        json_schema = schema_class.model_json_schema()

        config = {
            "response_mime_type": "application/json",
            "response_json_schema": json_schema,
            "thinking_config": types.ThinkingConfig(thinking_level="HIGH"),
        }

        response = await self._request(contents=context, config=config)

        response_text = getattr(response, "text", None)
        if not response_text:
            raise InvalidResponseError("Empty response from GenAI")

        try:
            parsed = schema_class.model_validate_json(response_text)
        except ValidationError as e:
            raise InvalidResponseError(f"Invalid response schema: {e}") from e

        self._record_usage(response)
        return parsed.model_dump()

    def _record_usage(self, response: Any) -> None:
        if not LANGFUSE_AVAILABLE:
            return

        usage = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
        if not usage:
            return

        # Google uses different field names than Anthropic
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        if input_tokens is None and output_tokens is None:
            input_tokens = getattr(usage, "input_tokens", None)
            output_tokens = getattr(usage, "output_tokens", None)

        if output_tokens is None and total_tokens is not None and input_tokens is not None:
            output_tokens = total_tokens - input_tokens

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
