"""Base provider classes, protocols, and utilities."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.schemas import ActionType


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class RetryExhausted(ProviderError):
    """All retry attempts failed."""

    pass


class RetryExhaustedError(RetryExhausted):
    """All retry attempts failed (legacy name)."""

    pass


class InvalidResponseError(ProviderError):
    """LLM returned invalid/unparseable response."""

    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each attempt)
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)
            raise RetryExhausted(
                f"Failed after {max_attempts} attempts: {last_error}"
            ) from last_error

        return wrapper

    return decorator


class PlayerProvider(Protocol):
    """
    Protocol for LLM providers.

    Providers handle communication with LLM APIs and return validated structured output.
    The PlayerAgent handles context building and higher-level validation.
    """

    async def act(
        self,
        action_type: ActionType,
        context: str,
    ) -> dict:
        """
        Execute a player action via LLM.

        Args:
            action_type: Type of action (determines output schema)
            context: Full assembled context/prompt string from ContextBuilder

        Returns:
            Validated structured output dict from LLM
        """
        ...
