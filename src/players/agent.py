"""LLM-powered player agent."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.context import ContextBuilder
from src.players.actions import ActionHandler, ActionValidationError
from src.providers.base import InvalidResponseError, ProviderError, RetryExhausted
from src.schemas import ActionType, Event, GameState, PlayerMemory, PlayerResponse, Transcript

if TYPE_CHECKING:
    from src.providers.base import PlayerProvider
    from src.schemas import Persona

# Try to import langfuse, but make it optional
try:
    from langfuse.decorators import observe

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

    def observe(name: str | None = None):  # noqa: ARG001
        """No-op decorator when langfuse is not available."""

        def decorator(func):
            return func

        return decorator


class PlayerAgent:
    """
    LLM-powered player agent.

    Stateless design: engine owns PlayerMemory and passes it each call.
    Agent builds context, gets LLM response, validates, and updates memory.
    """

    def __init__(
        self,
        name: str,
        persona: Persona,
        role: str,
        seat: int,
        provider: PlayerProvider,
        partner: str | None = None,
    ):
        """
        Initialize player agent.

        Args:
            name: Player's name
            persona: Player's persona definition
            role: Player's role (mafia, detective, town)
            seat: Player's seat number (0-6)
            provider: LLM provider for making calls
            partner: Mafia partner's name (if role is mafia)
        """
        self.name = name
        self.persona = persona
        self.role = role
        self.seat = seat
        self.provider = provider
        self.partner = partner

        # Internal helpers
        self.context_builder = ContextBuilder()
        self.action_handler = ActionHandler()

    @observe(name="player_act")
    async def act(
        self,
        game_state: GameState,
        transcript: Transcript,
        memory: PlayerMemory,
        action_type: ActionType,
        recent_events: list[Event] | None = None,
        action_context: dict | None = None,
    ) -> PlayerResponse:
        """
        Execute action and return response with updated memory.

        Args:
            game_state: Current game state
            transcript: Game transcript history
            memory: Player's current memory state
            action_type: Type of action to take
            recent_events: Public events since the player's last turn
            action_context: Action-specific context (e.g., defense info)

        Returns:
            PlayerResponse with output and updated memory
        """
        # Build role-specific extra context
        extra = self._get_role_extra(memory)
        if action_context:
            extra = {**extra, **action_context}

        # Build context string
        context = self.context_builder.build_context(
            player_name=self.name,
            role=self.role,
            persona=self.persona,
            game_state=game_state,
            transcript=transcript,
            memory=memory,
            action_type=action_type,
            extra=extra or None,
            recent_events=recent_events,
        )

        # Get valid output with retries and fallback
        output = await self._get_valid_output(
            game_state, action_type, context, action_context=action_context
        )

        # Update memory from SGR output
        updated_memory = self._update_memory(memory, output, action_type)

        return PlayerResponse(output=output, updated_memory=updated_memory)

    def _get_role_extra(self, memory: PlayerMemory) -> dict:
        """Get role-specific extra context from engine-owned memory."""
        if self.role == "mafia" and self.partner:
            return {"partner": self.partner}
        if self.role == "detective":
            results = memory.facts.get("investigation_results", [])
            if results is None:
                results = []
            return {"results": results}
        return {}

    async def _get_valid_output(
        self,
        game_state: GameState,
        action_type: ActionType,
        context: str,
        max_retries: int = 3,
        action_context: dict | None = None,
    ) -> dict:
        """
        Get valid output with retries and fallback to default.

        Args:
            game_state: Current game state (for validation)
            action_type: Type of action
            context: Context string for LLM
            max_retries: Maximum retry attempts
            action_context: Action-specific context (for validation flags like night_zero)

        Returns:
            Valid output dict
        """
        # Build mafia_names for validation (Mafia players only)
        mafia_names = self._get_mafia_names()

        # Extract night_zero flag for validation
        night_zero = (action_context or {}).get("night_zero", False)

        last_error: str | None = None

        for attempt in range(max_retries):
            try:
                # Add error feedback if retrying
                current_context = context
                if last_error:
                    current_context += (
                        f"\n\n[ERROR] Your previous response was invalid: {last_error}. "
                        "Please try again and ensure your output is valid."
                    )

                # Get LLM response
                raw_output = await self.provider.act(action_type, current_context)

                # Validate output with player context
                validated = self.action_handler.validate(
                    raw_output,
                    action_type,
                    game_state,
                    player_name=self.name,
                    mafia_names=mafia_names,
                    night_zero=night_zero,
                )
                return validated

            except (InvalidResponseError, ActionValidationError) as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    continue
            except (ProviderError, RetryExhausted):
                # Provider-level failure after retries exhausted, fall back to default
                break

        # All retries failed or provider error, return default
        return self.action_handler.get_default(
            action_type, game_state, self.name, mafia_names=mafia_names
        )

    def _get_mafia_names(self) -> list[str] | None:
        """Get list of all Mafia player names (for validation)."""
        if self.role == "mafia":
            names = [self.name]
            if self.partner:
                names.append(self.partner)
            return names
        return None

    def _update_memory(
        self, memory: PlayerMemory, output: dict, action_type: ActionType
    ) -> PlayerMemory:
        """
        Extract beliefs/facts from SGR output and update memory.

        Args:
            memory: Current memory state
            output: LLM output containing reasoning
            action_type: Type of action taken

        Returns:
            Updated PlayerMemory
        """
        new_facts = dict(memory.facts)
        new_beliefs = dict(memory.beliefs)

        # Extract SGR analysis fields
        if "suspicions" in output:
            new_beliefs["suspicions"] = output["suspicions"]

        if "strategy" in output:
            new_beliefs["strategy"] = output["strategy"]

        # Record the action taken
        action_key = f"last_{action_type.value}"
        if action_type == ActionType.SPEAK:
            new_facts[action_key] = {
                "speech": output.get("speech", ""),
                "nomination": output.get("nomination", ""),
            }
        elif action_type == ActionType.VOTE:
            new_facts[action_key] = output.get("vote", "skip")
        elif action_type == ActionType.NIGHT_KILL:
            new_facts[action_key] = output.get("target", "skip")
        elif action_type == ActionType.INVESTIGATION:
            new_facts[action_key] = output.get("target", "")

        return PlayerMemory(facts=new_facts, beliefs=new_beliefs)
