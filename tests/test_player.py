"""Tests for player agent and action handling."""

from unittest.mock import AsyncMock

import pytest

from src.players.actions import ActionHandler, ActionValidationError
from src.players.agent import PlayerAgent
from src.providers.base import InvalidResponseError, ProviderError, RetryExhausted
from src.schemas import ActionType, GameState, PlayerMemory


class TestActionHandler:
    @pytest.fixture
    def handler(self):
        return ActionHandler()

    @pytest.fixture
    def game_state(self):
        return GameState(
            phase="day_1",
            round_number=1,
            living_players=["Alice", "Bob", "Charlie", "Diana"],
            dead_players=[],
            nominated_players=["Bob", "Charlie"],
        )

    def test_validate_speaking_valid(self, handler, game_state):
        """Valid speaking output passes validation."""
        output = {
            "speech": "I think we should discuss this carefully.",
            "nomination": "Bob",
        }
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "Bob"

    def test_validate_speaking_invalid_nomination(self, handler, game_state):
        """Invalid nomination raises error."""
        output = {"speech": "Test speech", "nomination": "DeadPlayer"}
        with pytest.raises(ActionValidationError, match="Invalid nomination"):
            handler.validate(output, ActionType.SPEAK, game_state)

    def test_validate_speaking_empty_speech(self, handler, game_state):
        """Empty speech raises error."""
        output = {"speech": "", "nomination": "Bob"}
        with pytest.raises(ActionValidationError, match="too short"):
            handler.validate(output, ActionType.SPEAK, game_state)

    def test_validate_speaking_skips_nomination_for_night_zero(self, handler, game_state):
        """Night Zero flag skips nomination validation."""
        # Invalid nomination that would normally fail
        output = {"speech": "My strategy is to target quiet players.", "nomination": ""}
        # Without night_zero, this would raise ActionValidationError
        result = handler.validate(
            output, ActionType.SPEAK, game_state, night_zero=True
        )
        assert result["speech"] == "My strategy is to target quiet players."

    def test_validate_speaking_validates_nomination_without_night_zero(self, handler, game_state):
        """Without night_zero, nomination is still validated."""
        output = {"speech": "This is a valid speech.", "nomination": "InvalidPlayer"}
        with pytest.raises(ActionValidationError, match="Invalid nomination"):
            handler.validate(output, ActionType.SPEAK, game_state, night_zero=False)

    def test_validate_voting_valid(self, handler, game_state):
        """Valid vote passes validation."""
        output = {"vote": "Bob"}
        result = handler.validate(output, ActionType.VOTE, game_state)
        assert result["vote"] == "Bob"

    def test_validate_voting_skip(self, handler, game_state):
        """Skip vote is valid."""
        output = {"vote": "skip"}
        result = handler.validate(output, ActionType.VOTE, game_state)
        assert result["vote"] == "skip"

    def test_validate_voting_invalid(self, handler, game_state):
        """Vote for non-nominated player raises error."""
        output = {"vote": "Alice"}  # Alice not nominated
        with pytest.raises(ActionValidationError, match="Invalid vote"):
            handler.validate(output, ActionType.VOTE, game_state)

    def test_validate_night_kill_valid(self, handler, game_state):
        """Valid kill target passes validation."""
        output = {"target": "Bob"}
        result = handler.validate(output, ActionType.NIGHT_KILL, game_state)
        assert result["target"] == "Bob"

    def test_validate_night_kill_skip(self, handler, game_state):
        """Skip kill is valid."""
        output = {"target": "skip"}
        result = handler.validate(output, ActionType.NIGHT_KILL, game_state)
        assert result["target"] == "skip"

    def test_validate_investigation_valid(self, handler, game_state):
        """Valid investigation target passes validation."""
        output = {"target": "Charlie"}
        result = handler.validate(output, ActionType.INVESTIGATION, game_state)
        assert result["target"] == "Charlie"

    def test_validate_investigation_invalid(self, handler, game_state):
        """Dead player as target raises error."""
        game_state.dead_players = ["DeadPlayer"]
        output = {"target": "DeadPlayer"}
        with pytest.raises(ActionValidationError, match="Invalid target"):
            handler.validate(output, ActionType.INVESTIGATION, game_state)

    def test_validate_night_kill_rejects_mafia_partner(self, handler, game_state):
        """Cannot target Mafia partner."""
        output = {"target": "Bob"}
        with pytest.raises(ActionValidationError, match="Cannot target Mafia"):
            handler.validate(
                output,
                ActionType.NIGHT_KILL,
                game_state,
                mafia_names=["Alice", "Bob"],
            )

    def test_validate_night_kill_rejects_self(self, handler, game_state):
        """Cannot target self (Mafia)."""
        output = {"target": "Alice"}
        with pytest.raises(ActionValidationError, match="Cannot target Mafia"):
            handler.validate(
                output,
                ActionType.NIGHT_KILL,
                game_state,
                mafia_names=["Alice", "Bob"],
            )

    def test_validate_investigation_rejects_self(self, handler, game_state):
        """Cannot investigate self."""
        output = {"target": "Alice"}
        with pytest.raises(ActionValidationError, match="Cannot investigate yourself"):
            handler.validate(
                output,
                ActionType.INVESTIGATION,
                game_state,
                player_name="Alice",
            )

    def test_get_default_speak(self, handler, game_state):
        """Default speaking output is valid."""
        default = handler.get_default(ActionType.SPEAK, game_state, "Alice")
        assert "speech" in default
        assert default["nomination"] in game_state.living_players
        assert default["nomination"] != "Alice"  # Not self

    def test_get_default_vote(self, handler, game_state):
        """Default vote is skip."""
        default = handler.get_default(ActionType.VOTE, game_state, "Alice")
        assert default["vote"] == "skip"

    def test_get_default_night_kill(self, handler, game_state):
        """Default night kill selects a target."""
        default = handler.get_default(ActionType.NIGHT_KILL, game_state, "Alice")
        assert default["target"] in game_state.living_players or default["target"] == "skip"

    def test_get_default_night_kill_excludes_mafia(self, handler, game_state):
        """Default kill target excludes all Mafia."""
        mafia_names = ["Alice", "Bob"]
        for _ in range(10):  # Random, so try multiple times
            default = handler.get_default(
                ActionType.NIGHT_KILL, game_state, "Alice", mafia_names=mafia_names
            )
            assert default["target"] not in mafia_names

    def test_get_default_night_kill_all_mafia(self, handler):
        """Default kill skips when only Mafia are available."""
        game_state = GameState(
            phase="night_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=[],
        )
        default = handler.get_default(
            ActionType.NIGHT_KILL,
            game_state,
            "Alice",
            mafia_names=["Alice", "Bob"],
        )
        assert default["target"] == "skip"

    def test_get_default_last_words(self, handler, game_state):
        """Default last words has text."""
        default = handler.get_default(ActionType.LAST_WORDS, game_state, "Alice")
        assert "text" in default
        assert len(default["text"]) > 0

    def test_get_default_investigation(self, handler):
        """Default investigation excludes self and targets a living player."""
        game_state = GameState(
            phase="night_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=[],
        )
        default = handler.get_default(ActionType.INVESTIGATION, game_state, "Alice")
        assert default["target"] == "Bob"


class TestPlayerAgent:
    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        return provider

    @pytest.fixture
    def agent(self, mock_provider, sample_persona):
        return PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="town",
            seat=0,
            provider=mock_provider,
        )

    @pytest.fixture
    def game_state(self):
        return GameState(
            phase="day_1",
            round_number=1,
            living_players=["Alice", "Bob", "Charlie", "Diana"],
            dead_players=[],
            nominated_players=[],
        )

    @pytest.fixture
    def memory(self):
        return PlayerMemory(facts={}, beliefs={})

    async def test_act_returns_response(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent returns PlayerResponse with output and updated memory."""
        mock_provider.act = AsyncMock(
            return_value={
                "new_events": ["Day started"],
                "notable_changes": [],
                "suspicion_updates": {"Bob": "slightly suspicious"},
                "pattern_notes": [],
                "current_goal": "survive",
                "reasoning": "No information yet",
                "information_to_share": [],
                "information_to_hide": [],
                "speech": "Hello everyone, let's discuss.",
                "nomination": "Bob",
            }
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        assert response.output["speech"] == "Hello everyone, let's discuss."
        assert response.output["nomination"] == "Bob"
        assert response.updated_memory is not None

    async def test_act_updates_memory(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent extracts beliefs from SGR output."""
        mock_provider.act = AsyncMock(
            return_value={
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {"Bob": "very suspicious"},
                "pattern_notes": ["Bob avoided questions"],
                "current_goal": "find Mafia",
                "reasoning": "Bob deflected",
                "information_to_share": [],
                "information_to_hide": [],
                "speech": "I suspect Bob.",
                "nomination": "Bob",
            }
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        assert response.updated_memory.beliefs.get("suspicions") == {"Bob": "very suspicious"}
        assert "Bob avoided questions" in response.updated_memory.beliefs.get("patterns", [])

    async def test_act_retries_on_invalid_output(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent retries when output is invalid."""
        # First call returns invalid nomination, second is valid
        mock_provider.act = AsyncMock(
            side_effect=[
                {
                    "speech": "Hello",
                    "nomination": "DeadPlayer",  # Invalid
                    "new_events": [],
                    "notable_changes": [],
                    "suspicion_updates": {},
                    "pattern_notes": [],
                    "current_goal": "survive",
                    "reasoning": "test",
                    "information_to_share": [],
                    "information_to_hide": [],
                },
                {
                    "speech": "Hello again",
                    "nomination": "Bob",  # Valid
                    "new_events": [],
                    "notable_changes": [],
                    "suspicion_updates": {},
                    "pattern_notes": [],
                    "current_goal": "survive",
                    "reasoning": "test",
                    "information_to_share": [],
                    "information_to_hide": [],
                },
            ]
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        assert mock_provider.act.call_count == 2
        assert response.output["nomination"] == "Bob"

    async def test_act_uses_default_after_max_retries(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent uses default action after exhausting retries."""
        # All calls return invalid output
        mock_provider.act = AsyncMock(
            return_value={
                "speech": "Hello",
                "nomination": "InvalidPlayer",  # Always invalid
                "new_events": [],
                "notable_changes": [],
                "suspicion_updates": {},
                "pattern_notes": [],
                "current_goal": "survive",
                "reasoning": "test",
                "information_to_share": [],
                "information_to_hide": [],
            }
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        # Should have tried 3 times then used default
        assert mock_provider.act.call_count == 3
        # Default should be valid
        assert response.output["nomination"] in game_state.living_players

    async def test_act_retries_on_provider_error(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent retries when provider raises InvalidResponseError."""
        mock_provider.act = AsyncMock(
            side_effect=[
                InvalidResponseError("bad response"),
                {
                    "speech": "Hello again",
                    "nomination": "Bob",
                    "new_events": [],
                    "notable_changes": [],
                    "suspicion_updates": {},
                    "pattern_notes": [],
                    "current_goal": "survive",
                    "reasoning": "test",
                    "information_to_share": [],
                    "information_to_hide": [],
                },
            ]
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        assert mock_provider.act.call_count == 2
        assert response.output["nomination"] == "Bob"

    async def test_act_falls_back_on_retry_exhausted(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent falls back to default when provider exhausts retries."""
        mock_provider.act = AsyncMock(side_effect=RetryExhausted("API failed after 3 retries"))

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        # Should use default action, not crash
        assert mock_provider.act.call_count == 1
        assert response.output["nomination"] in game_state.living_players

    async def test_act_falls_back_on_provider_error(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent falls back to default when provider raises ProviderError."""
        mock_provider.act = AsyncMock(side_effect=ProviderError("Connection failed"))

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        # Should use default action, not crash
        assert mock_provider.act.call_count == 1
        assert response.output["nomination"] in game_state.living_players

    async def test_act_updates_memory_vote(self, agent, mock_provider, memory):
        """Vote action stores last_vote in memory facts."""
        game_state = GameState(
            phase="day_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=["Bob"],
        )
        mock_provider.act = AsyncMock(return_value={"vote": "Bob"})

        response = await agent.act(game_state, [], memory, ActionType.VOTE)

        assert response.updated_memory.facts["last_vote"] == "Bob"

    async def test_act_updates_memory_investigation(self, agent, mock_provider, memory):
        """Investigation action stores last_investigation in memory facts."""
        game_state = GameState(
            phase="night_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=[],
        )
        mock_provider.act = AsyncMock(return_value={"target": "Bob"})

        response = await agent.act(game_state, [], memory, ActionType.INVESTIGATION)

        assert response.updated_memory.facts["last_investigation"] == "Bob"

    async def test_act_updates_memory_night_kill(self, mock_provider, sample_persona, memory):
        """Night kill action stores last_night_kill in memory facts."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="mafia",
            seat=0,
            provider=mock_provider,
            partner="Bob",
        )
        game_state = GameState(
            phase="night_1",
            round_number=1,
            living_players=["Alice", "Bob", "Charlie"],
            dead_players=[],
            nominated_players=[],
        )
        mock_provider.act = AsyncMock(return_value={"target": "Charlie"})

        response = await agent.act(game_state, [], memory, ActionType.NIGHT_KILL)

        assert response.updated_memory.facts["last_night_kill"] == "Charlie"


class TestPlayerAgentRoles:
    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        return provider

    def test_mafia_agent_has_partner(self, mock_provider, sample_persona):
        """Mafia agent tracks partner."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="mafia",
            seat=0,
            provider=mock_provider,
            partner="Bob",
        )

        assert agent.partner == "Bob"
        memory = PlayerMemory(facts={}, beliefs={})
        extra = agent._get_role_extra(memory)
        assert extra["partner"] == "Bob"

    def test_detective_tracks_investigation_results(self, mock_provider, sample_persona):
        """Detective agent tracks investigation results."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="detective",
            seat=0,
            provider=mock_provider,
        )

        memory = PlayerMemory(
            facts={
                "investigation_results": [
                    {"target": "Bob", "result": "Not Mafia"},
                    {"target": "Charlie", "result": "Mafia"},
                ]
            },
            beliefs={},
        )

        extra = agent._get_role_extra(memory)
        assert len(extra["results"]) == 2
        assert extra["results"][0]["target"] == "Bob"
        assert extra["results"][1]["result"] == "Mafia"

    def test_town_agent_has_no_extra(self, mock_provider, sample_persona):
        """Town agent has no special extra context."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="town",
            seat=0,
            provider=mock_provider,
        )

        memory = PlayerMemory(facts={}, beliefs={})
        extra = agent._get_role_extra(memory)
        assert extra == {}

    def test_mafia_agent_get_mafia_names(self, mock_provider, sample_persona):
        """Mafia agent returns list of all Mafia names."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="mafia",
            seat=0,
            provider=mock_provider,
            partner="Bob",
        )

        mafia_names = agent._get_mafia_names()
        assert mafia_names == ["Alice", "Bob"]

    def test_town_agent_get_mafia_names_returns_none(self, mock_provider, sample_persona):
        """Non-Mafia agent returns None for mafia_names."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="town",
            seat=0,
            provider=mock_provider,
        )

        mafia_names = agent._get_mafia_names()
        assert mafia_names is None

    def test_detective_agent_get_mafia_names_returns_none(self, mock_provider, sample_persona):
        """Detective agent returns None for mafia_names."""
        agent = PlayerAgent(
            name="Alice",
            persona=sample_persona,
            role="detective",
            seat=0,
            provider=mock_provider,
        )

        mafia_names = agent._get_mafia_names()
        assert mafia_names is None
