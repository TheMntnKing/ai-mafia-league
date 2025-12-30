"""Action validation and default handlers."""

from __future__ import annotations

import random

from src.schemas import ActionType, GameState


class ActionValidationError(Exception):
    """Output validation failed."""

    pass


class ActionHandler:
    """Validates action outputs and provides defaults."""

    def validate(
        self,
        output: dict,
        action_type: ActionType,
        game_state: GameState,
        player_name: str | None = None,
        mafia_names: list[str] | None = None,
        night_zero: bool = False,
    ) -> dict:
        """
        Validate output against game rules.

        Args:
            output: Raw output from LLM
            action_type: Type of action
            game_state: Current game state
            player_name: Name of the acting player (for self-exclusion checks)
            mafia_names: List of all Mafia player names (for Mafia exclusion checks)
            night_zero: If True, skip nomination validation (Night Zero coordination)

        Returns:
            Validated output dict

        Raises:
            ActionValidationError: If output is invalid
        """
        if action_type == ActionType.SPEAK:
            return self._validate_speaking(output, game_state, night_zero=night_zero)
        elif action_type == ActionType.VOTE:
            return self._validate_voting(output, game_state)
        elif action_type == ActionType.NIGHT_KILL:
            return self._validate_night_kill(output, game_state, mafia_names)
        elif action_type == ActionType.INVESTIGATION:
            return self._validate_investigation(output, game_state, player_name)
        else:
            # LAST_WORDS and DEFENSE have no validation constraints
            return output

    def _validate_speaking(
        self, output: dict, state: GameState, night_zero: bool = False
    ) -> dict:
        """Validate speaking action.

        Args:
            output: Raw output dict
            state: Current game state
            night_zero: If True, skip nomination validation (Night Zero uses SPEAK
                but nomination is meaningless during Mafia coordination)
        """
        speech = output.get("speech", "")
        if not speech or len(speech.strip()) < 10:
            raise ActionValidationError("Speech is too short or empty")

        # Only validate nomination during day phases, not Night Zero
        if not night_zero:
            # Normalize nomination (case-insensitive, strip whitespace)
            nomination = output.get("nomination", "").strip().lower()

            # Check if skip is allowed (Day 1 only)
            is_day_one = state.phase == "day_1" or (
                state.phase.startswith("day") and state.round_number == 1
            )
            if nomination == "skip":
                if is_day_one:
                    # Normalize the output to lowercase "skip"
                    output["nomination"] = "skip"
                    return output
                else:
                    raise ActionValidationError(
                        "Nomination 'skip' is only allowed on Day 1."
                    )

            # Check against living players (case-insensitive)
            living_lower = {p.lower(): p for p in state.living_players}
            if nomination in living_lower:
                # Normalize to correct case
                output["nomination"] = living_lower[nomination]
                return output

            # Build helpful error message
            valid_options = list(state.living_players)
            if is_day_one:
                valid_options.append("skip")
            raise ActionValidationError(
                f"Invalid nomination '{output.get('nomination', '')}'. "
                f"Must be one of: {valid_options}"
            )

        return output

    def _validate_voting(self, output: dict, state: GameState) -> dict:
        """Vote must be nominated player or 'skip'."""
        vote = output.get("vote", "")
        valid_votes = list(state.nominated_players) + ["skip"]

        if vote not in valid_votes:
            raise ActionValidationError(
                f"Invalid vote '{vote}'. Must be one of: {valid_votes}"
            )
        return output

    def _validate_night_kill(
        self, output: dict, state: GameState, mafia_names: list[str] | None
    ) -> dict:
        """Target must be living non-Mafia player or 'skip'."""
        target = output.get("target", "")
        if target == "skip":
            return output
        if target not in state.living_players:
            raise ActionValidationError(
                f"Invalid target '{target}'. Must be a living player or 'skip'."
            )
        if mafia_names and target in mafia_names:
            raise ActionValidationError(
                f"Invalid target '{target}'. Cannot target Mafia members."
            )
        return output

    def _validate_investigation(
        self, output: dict, state: GameState, player_name: str | None
    ) -> dict:
        """Target must be living non-self player."""
        target = output.get("target", "")
        if target not in state.living_players:
            raise ActionValidationError(
                f"Invalid target '{target}'. Must be a living player."
            )
        if player_name and target == player_name:
            raise ActionValidationError("Cannot investigate yourself.")
        return output

    def get_default(
        self,
        action_type: ActionType,
        game_state: GameState,
        player_name: str,
        mafia_names: list[str] | None = None,
    ) -> dict:
        """
        Return safe default action after validation failures.

        Args:
            action_type: Type of action
            game_state: Current game state
            player_name: Name of the acting player
            mafia_names: List of all Mafia player names (for NIGHT_KILL exclusion)

        Returns:
            Default output dict for the action type
        """
        # Filter out self from valid targets
        valid_targets = [p for p in game_state.living_players if p != player_name]
        if not valid_targets:
            valid_targets = game_state.living_players

        # For NIGHT_KILL, also exclude all Mafia members
        kill_targets = valid_targets
        if mafia_names:
            kill_targets = [p for p in valid_targets if p not in mafia_names]
            if not kill_targets:
                kill_targets = ["skip"]  # No valid targets, must skip

        defaults = {
            ActionType.SPEAK: {
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {},
                "pattern_notes": [],
                "current_goal": "survive",
                "reasoning": "Unable to process situation clearly.",
                "information_to_share": [],
                "information_to_hide": [],
                "speech": "I need more time to think about this situation. "
                "Let's hear from everyone before making judgments.",
                "nomination": random.choice(valid_targets),
            },
            ActionType.VOTE: {
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {},
                "pattern_notes": [],
                "current_goal": "avoid mistakes",
                "reasoning": "Not confident enough to vote.",
                "vote_reasoning": "Choosing to skip due to uncertainty.",
                "vote": "skip",
            },
            ActionType.NIGHT_KILL: {
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {},
                "pattern_notes": [],
                "current_goal": "eliminate threats",
                "reasoning": "Random selection due to uncertainty.",
                "target_reasoning": "No clear target identified.",
                "target": random.choice(kill_targets),
            },
            ActionType.INVESTIGATION: {
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {},
                "pattern_notes": [],
                "current_goal": "find Mafia",
                "reasoning": "Random selection.",
                "target_reasoning": "No strong lead, investigating randomly.",
                "target": random.choice(valid_targets),
            },
            ActionType.LAST_WORDS: {"text": "Good luck to the remaining players."},
            ActionType.DEFENSE: {"text": "I am not Mafia. Please reconsider."},
        }

        return defaults[action_type]
