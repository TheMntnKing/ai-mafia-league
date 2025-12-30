"""Tests for player agent and action handling."""

from unittest.mock import AsyncMock

import pytest

from src.players.actions import ActionHandler, ActionValidationError
from src.players.agent import PlayerAgent
from src.providers.base import InvalidResponseError, ProviderError, RetryExhausted
from src.schemas import ActionType, GameState, PlayerMemory
from tests.sgr_helpers import (
    make_investigation_response,
    make_night_kill_response,
    make_speak_response,
    make_vote_response,
)


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

    def test_validate_speaking_day1_skip_nomination(self, handler, game_state):
        """Day 1 allows nomination skip."""
        output = {"speech": "Let's gather info before naming someone.", "nomination": "skip"}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "skip"

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

    def test_validate_speaking_day2_skip_invalid(self, handler, game_state):
        """Day 2 should not allow skip nomination."""
        game_state.phase = "day_2"
        game_state.round_number = 2
        output = {"speech": "We should make a real nomination.", "nomination": "skip"}
        with pytest.raises(ActionValidationError, match="only allowed on Day 1"):
            handler.validate(output, ActionType.SPEAK, game_state)

    def test_validate_speaking_day1_skip_case_insensitive(self, handler, game_state):
        """Day 1 allows skip with any capitalization."""
        # Test "Skip" (capitalized)
        output = {"speech": "Let's gather info first.", "nomination": "Skip"}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "skip"  # Normalized to lowercase

        # Test "SKIP" (uppercase)
        output = {"speech": "Let's gather info first.", "nomination": "SKIP"}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "skip"

        # Test " skip " (with whitespace)
        output = {"speech": "Let's gather info first.", "nomination": " skip "}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "skip"

    def test_validate_speaking_nomination_case_insensitive(self, handler, game_state):
        """Nomination is case-insensitive and normalized to correct case."""
        output = {"speech": "I suspect this player.", "nomination": "bob"}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "Bob"  # Normalized to original case

        output = {"speech": "I suspect this player.", "nomination": "BOB"}
        result = handler.validate(output, ActionType.SPEAK, game_state)
        assert result["nomination"] == "Bob"

    def test_validate_speaking_day1_error_includes_skip(self, handler, game_state):
        """Day 1 error message includes 'skip' as valid option."""
        output = {"speech": "Testing invalid nomination.", "nomination": "InvalidPlayer"}
        with pytest.raises(ActionValidationError) as exc_info:
            handler.validate(output, ActionType.SPEAK, game_state)
        assert "skip" in str(exc_info.value)

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
            return_value=make_speak_response(
                observations="Day started.",
                suspicions="Bob seems slightly suspicious.",
                strategy="Stay cautious and gather information.",
                reasoning="No information yet.",
                speech="Hello everyone, let's discuss.",
                nomination="Bob",
            )
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
            return_value=make_speak_response(
                observations="No major changes since last turn.",
                suspicions="Bob is very suspicious because he avoided questions.",
                strategy="Find Mafia by pressing on evasive players.",
                reasoning="Bob deflected when challenged.",
                speech="I suspect Bob.",
                nomination="Bob",
            )
        )

        response = await agent.act(game_state, [], memory, ActionType.SPEAK)

        assert response.updated_memory.beliefs.get("suspicions") == (
            "Bob is very suspicious because he avoided questions."
        )
        assert response.updated_memory.beliefs.get("strategy") == (
            "Find Mafia by pressing on evasive players."
        )

    async def test_act_retries_on_invalid_output(
        self, agent, mock_provider, game_state, memory
    ):
        """Agent retries when output is invalid."""
        # First call returns invalid nomination, second is valid
        mock_provider.act = AsyncMock(
            side_effect=[
                make_speak_response(
                    speech="Hello",
                    nomination="DeadPlayer",  # Invalid
                    observations="No changes.",
                    suspicions="No strong suspicions.",
                    strategy="Stay safe.",
                    reasoning="test",
                ),
                make_speak_response(
                    speech="Hello again",
                    nomination="Bob",  # Valid
                    observations="No changes.",
                    suspicions="No strong suspicions.",
                    strategy="Stay safe.",
                    reasoning="test",
                ),
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
            return_value=make_speak_response(
                speech="Hello",
                nomination="InvalidPlayer",  # Always invalid
                observations="No changes.",
                suspicions="No strong suspicions.",
                strategy="Stay safe.",
                reasoning="test",
            )
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
                make_speak_response(
                    speech="Hello again",
                    nomination="Bob",
                    observations="No changes.",
                    suspicions="No strong suspicions.",
                    strategy="Stay safe.",
                    reasoning="test",
                ),
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
        """Vote action returns updated memory."""
        game_state = GameState(
            phase="day_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=["Bob"],
        )
        mock_provider.act = AsyncMock(
            return_value=make_vote_response(
                observations="Discussion complete.",
                suspicions="Bob seems most suspicious.",
                strategy="Vote to remove top suspect.",
                reasoning="Bob's answers were evasive.",
                vote="Bob",
            )
        )

        response = await agent.act(game_state, [], memory, ActionType.VOTE)
        assert response.updated_memory.beliefs["suspicions"] == "Bob seems most suspicious."
        assert response.updated_memory.beliefs["strategy"] == "Vote to remove top suspect."

    async def test_act_updates_memory_investigation(self, agent, mock_provider, memory):
        """Investigation action stores last_investigation in memory facts."""
        game_state = GameState(
            phase="night_1",
            round_number=1,
            living_players=["Alice", "Bob"],
            dead_players=[],
            nominated_players=[],
        )
        mock_provider.act = AsyncMock(
            return_value=make_investigation_response(
                observations="Night phase with limited info.",
                suspicions="Bob is a candidate.",
                strategy="Gather information for town.",
                reasoning="Investigate Bob to confirm suspicions.",
                target="Bob",
            )
        )

        response = await agent.act(game_state, [], memory, ActionType.INVESTIGATION)

        assert response.updated_memory.facts["last_investigation"] == {
            "target": "Bob",
            "reasoning": "Investigate Bob to confirm suspicions.",
        }

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
        mock_provider.act = AsyncMock(
            return_value=make_night_kill_response(
                observations="Night phase after a tense day.",
                suspicions="Charlie is influential.",
                strategy="Remove a strong town voice.",
                reasoning="Charlie could be leading town.",
                target="Charlie",
            )
        )

        response = await agent.act(game_state, [], memory, ActionType.NIGHT_KILL)

        assert response.updated_memory.facts["last_night_kill"] == {
            "target": "Charlie",
            "reasoning": "Charlie could be leading town.",
        }


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
