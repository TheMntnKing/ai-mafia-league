"""Integration tests for game loop."""

from unittest.mock import AsyncMock

import pytest

from src.engine.game import GameConfig, GameRunner
from src.engine.voting import VoteResolver
from src.personas.initial import get_personas
from src.schemas import PlayerMemory
from tests.sgr_helpers import (
    make_defense_response,
    make_doctor_protect_response,
    make_investigation_response,
    make_last_words_response,
    make_night_kill_response,
    make_speak_response,
    make_vote_response,
)


class TestVoteResolver:
    @pytest.fixture
    def resolver(self):
        return VoteResolver()

    def test_plurality_eliminates(self, resolver):
        """Clear plurality eliminates the target."""
        votes = {
            "Alice": "Bob",
            "Bob": "Charlie",
            "Charlie": "Bob",
            "Diana": "Bob",
            "Eve": "Bob",
        }
        result = resolver.resolve(votes, 5)
        assert result.outcome == "eliminated"
        assert result.eliminated == "Bob"

    def test_tie_with_skip_single_player_triggers_revote(self, resolver):
        """Skip tied with a single player triggers revote."""
        votes = {
            "Alice": "Bob",
            "Bob": "Bob",
            "Charlie": "Diana",
            "Diana": "skip",
            "Eve": "skip",
        }
        # Bob has 2 votes, Diana has 1, skip has 2 -> tie at top with skip + 1 player
        result = resolver.resolve(votes, 5)
        assert result.outcome == "revote"
        assert result.tied_players == ["Bob"]

    def test_plurality_eliminates_without_skip_tie(self, resolver):
        """Plurality eliminates when skip is not tied for top."""
        votes = {
            "Alice": "Bob",
            "Bob": "Bob",
            "Charlie": "Diana",
            "Diana": "skip",
            "Eve": "Bob",
        }
        # Bob has 3 votes, skip has 1, Diana has 1
        result = resolver.resolve(votes, 5)
        assert result.outcome == "eliminated"
        assert result.eliminated == "Bob"

    def test_tie_triggers_revote(self, resolver):
        """Tie at top triggers revote."""
        votes = {
            "Alice": "Bob",
            "Bob": "Charlie",
            "Charlie": "Bob",
            "Diana": "Charlie",
        }
        result = resolver.resolve(votes, 4)
        assert result.outcome == "revote"
        assert set(result.tied_players) == {"Bob", "Charlie"}

    def test_all_skip_no_elimination(self, resolver):
        """All skips means no elimination."""
        votes = {
            "Alice": "skip",
            "Bob": "skip",
            "Charlie": "skip",
        }
        result = resolver.resolve(votes, 3)
        assert result.outcome == "no_elimination"

    def test_revote_plurality_eliminates(self, resolver):
        """Revote plurality eliminates."""
        votes = {
            "Alice": "Bob",
            "Bob": "skip",
            "Charlie": "Bob",
            "Diana": "Bob",
        }
        result = resolver.resolve_revote(votes, 4, ["Bob", "Charlie"])
        assert result.outcome == "eliminated"
        assert result.eliminated == "Bob"

    def test_revote_tie_no_elimination(self, resolver):
        """Revote tie means no elimination (no further revotes)."""
        votes = {
            "Alice": "Bob",
            "Bob": "Charlie",
            "Charlie": "Bob",
            "Diana": "Charlie",
        }
        result = resolver.resolve_revote(votes, 4, ["Bob", "Charlie"])
        assert result.outcome == "no_elimination"

    def test_revote_skip_wins_no_elimination(self, resolver):
        """Revote skip plurality means no elimination."""
        votes = {
            "Alice": "skip",
            "Bob": "Bob",
            "Charlie": "skip",
            "Diana": "Charlie",
        }
        result = resolver.resolve_revote(votes, 4, ["Bob", "Charlie"])
        assert result.outcome == "no_elimination"

    def test_skip_wins_plurality_no_elimination(self, resolver):
        """Skip wins plurality means no elimination."""
        votes = {
            "Alice": "skip",
            "Bob": "skip",
            "Charlie": "skip",
            "Diana": "Bob",
            "Eve": "Charlie",
        }
        result = resolver.resolve(votes, 5)
        assert result.outcome == "no_elimination"

    def test_skip_ties_multiple_players_no_elimination(self, resolver):
        """Skip tied with multiple players means no elimination."""
        votes = {
            "Alice": "skip",
            "Bob": "Bob",
            "Charlie": "Charlie",
            "Diana": "skip",
        }
        result = resolver.resolve(votes, 4)
        assert result.outcome == "no_elimination"


class TestGameRunner:
    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider that returns valid actions."""
        provider = AsyncMock()
        return provider

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def game_config(self, personas, mock_provider):
        return GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

    def test_game_runner_creates_agents(self, game_config):
        """GameRunner creates agents for all players."""
        runner = GameRunner(game_config)

        assert len(runner.agents) == 10
        for name in game_config.player_names:
            assert name in runner.agents
            assert runner.agents[name].name == name

    def test_game_runner_assigns_roles(self, game_config):
        """GameRunner assigns correct role distribution."""
        runner = GameRunner(game_config)

        roles = [runner.state.get_player_role(name) for name in game_config.player_names]

        assert roles.count("mafia") == 3
        assert roles.count("doctor") == 1
        assert roles.count("detective") == 1
        assert roles.count("town") == 5

    def test_game_runner_initializes_memories(self, game_config):
        """GameRunner initializes empty memories for all players."""
        runner = GameRunner(game_config)

        assert len(runner.memories) == 10
        for name in game_config.player_names:
            assert name in runner.memories
            assert isinstance(runner.memories[name], PlayerMemory)

    async def test_game_runner_runs_to_completion(self, game_config, mock_provider):
        """GameRunner completes a game with mocked provider."""
        runner = GameRunner(game_config)

        def get_living():
            return runner.state.get_living_players()

        def make_response(action_type: str):
            """Generate a response based on action type and current game state."""
            if action_type == "speak":
                living = get_living()
                nomination = living[0] if living else "skip"
                return make_speak_response(
                    speech="I've been observing carefully and have some thoughts.",
                    nomination=nomination,
                )
            if action_type == "vote":
                nominations = runner.state.nominations
                target = nominations[0] if nominations else "skip"
                return make_vote_response(vote=target, reasoning="Based on behavior.")
            if action_type == "night_kill":
                living = get_living()
                non_mafia = [
                    name
                    for name in living
                    if runner.state.get_player_role(name) != "mafia"
                ]
                target = non_mafia[0] if non_mafia else "skip"
                return make_night_kill_response(
                    target=target,
                    reasoning="Strategic target.",
                )
            if action_type == "doctor_protect":
                living = get_living()
                target = living[0] if living else game_config.player_names[0]
                return make_doctor_protect_response(target=target, reasoning="Safe protect.")
            if action_type == "investigation":
                living = get_living()
                target = living[1] if len(living) > 1 else living[0]
                return make_investigation_response(
                    target=target,
                    reasoning="Most suspicious.",
                )
            if action_type in ("last_words", "defense"):
                if action_type == "last_words":
                    return make_last_words_response(
                        reasoning="Offer a final note to help town.",
                        text="I did my best for the town.",
                    )
                return make_defense_response(
                    reasoning="Offer a final note to help town.",
                    text="I did my best for the town.",
                )
            return make_speak_response()

        async def mock_act(*args, **kwargs):
            # New signature: act(action_type, context)
            action_type = kwargs.get("action_type") or args[0]
            return make_response(action_type.value)

        mock_provider.act = mock_act

        # Run with a timeout to prevent infinite loops
        import asyncio

        try:
            result = await asyncio.wait_for(runner.run(), timeout=30.0)
        except TimeoutError:
            pytest.fail("Game did not complete within timeout")

        assert result.winner in ("town", "mafia")
        assert result.rounds > 0
        assert len(result.final_living) > 0

    def test_mafia_agents_have_partners(self, game_config):
        """Mafia agents are assigned their partners."""
        runner = GameRunner(game_config)

        mafia_agents = [a for a in runner.agents.values() if a.role == "mafia"]
        assert len(mafia_agents) == 3

        mafia_names = [a.name for a in mafia_agents]
        for agent in mafia_agents:
            assert len(agent.partners) == 2
            assert agent.name not in agent.partners
            assert set(agent.partners) == (set(mafia_names) - {agent.name})


class TestGameIntegration:
    """Higher-level integration tests."""

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    @pytest.fixture
    def personas(self):
        return get_personas()

    async def test_town_wins_when_mafia_eliminated(self, personas, mock_provider):
        """Town wins when all Mafia are eliminated."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Find mafia players
        mafia_names = [
            name for name in config.player_names
            if runner.state.get_player_role(name) == "mafia"
        ]

        # Mock provider to always vote for first mafia until eliminated
        current_target_idx = [0]

        async def mock_act(*args, **kwargs):
            # New signature: act(action_type, context)
            action_type = kwargs.get("action_type") or args[0]
            action_name = action_type.value

            if action_name == "speak":
                target = mafia_names[current_target_idx[0]]
                is_dead = not runner.state.is_alive(target)
                if is_dead and current_target_idx[0] < len(mafia_names) - 1:
                    current_target_idx[0] += 1
                    target = mafia_names[current_target_idx[0]]
                return make_speak_response(
                    observations="Discussion ongoing.",
                    suspicions="Mafia targets identified.",
                    strategy="Eliminate Mafia systematically.",
                    reasoning="Strategic.",
                    speech=f"I suspect {target} is Mafia based on their behavior.",
                    nomination=target,
                )
            elif action_name == "vote":
                target = mafia_names[current_target_idx[0]]
                is_dead = not runner.state.is_alive(target)
                if is_dead and current_target_idx[0] < len(mafia_names) - 1:
                    current_target_idx[0] += 1
                    target = mafia_names[current_target_idx[0]]
                return make_vote_response(
                    observations="Discussion ongoing.",
                    suspicions="Mafia targets identified.",
                    strategy="Eliminate Mafia systematically.",
                    reasoning="Strategic.",
                    vote=target,
                )
            elif action_name == "night_kill":
                # Mafia kills random town
                living = runner.state.get_living_players()
                town = [p for p in living if runner.state.get_player_role(p) == "town"]
                target = town[0] if town else "skip"
                return make_night_kill_response(
                    observations="Discussion ongoing.",
                    suspicions="Mafia targets identified.",
                    strategy="Eliminate Mafia systematically.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_name == "doctor_protect":
                living = runner.state.get_living_players()
                target = living[0] if living else "skip"
                return make_doctor_protect_response(
                    observations="Discussion ongoing.",
                    suspicions="Mafia targets identified.",
                    strategy="Protect key town voices.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_name == "investigation":
                return make_investigation_response(
                    observations="Discussion ongoing.",
                    suspicions="Mafia targets identified.",
                    strategy="Eliminate Mafia systematically.",
                    reasoning="Strategic.",
                    target=mafia_names[0],
                )
            elif action_name in ("last_words", "defense"):
                if action_name == "last_words":
                    return make_last_words_response(
                        reasoning="Leave a final note.",
                        text="Final words.",
                    )
                return make_defense_response(
                    reasoning="Leave a final note.",
                    text="Final words.",
                )
            return make_speak_response()

        mock_provider.act = mock_act

        import asyncio

        try:
            result = await asyncio.wait_for(runner.run(), timeout=60.0)
        except TimeoutError:
            pytest.fail("Game did not complete within timeout")

        assert result.winner == "town"

    async def test_mafia_wins_when_majority(self, personas, mock_provider):
        """Mafia wins when they equal or outnumber Town-aligned players."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Find town players (including detective and doctor)
        town_names = [
            name for name in config.player_names
            if runner.state.get_player_role(name) in ("town", "detective", "doctor")
        ]

        # Mock provider to always vote for town until Mafia wins
        current_target_idx = [0]

        async def mock_act(*args, **kwargs):
            action_type = kwargs.get("action_type") or args[0]
            action_name = action_type.value

            if action_name == "speak":
                # Find next living town member
                target = town_names[current_target_idx[0]]
                while not runner.state.is_alive(target):
                    current_target_idx[0] = (current_target_idx[0] + 1) % len(town_names)
                    target = town_names[current_target_idx[0]]
                return make_speak_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate town to secure majority.",
                    reasoning="Strategic.",
                    speech=f"I think {target} is suspicious.",
                    nomination=target,
                )
            elif action_name == "vote":
                target = town_names[current_target_idx[0]]
                while not runner.state.is_alive(target):
                    current_target_idx[0] = (current_target_idx[0] + 1) % len(town_names)
                    target = town_names[current_target_idx[0]]
                return make_vote_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate town to secure majority.",
                    reasoning="Strategic.",
                    vote=target,
                )
            elif action_name == "night_kill":
                living = runner.state.get_living_players()
                town = [
                    p
                    for p in living
                    if runner.state.get_player_role(p) in ("town", "detective", "doctor")
                ]
                target = town[0] if town else "skip"
                return make_night_kill_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate town to secure majority.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_name == "doctor_protect":
                living = runner.state.get_living_players()
                target = living[0] if living else "skip"
                return make_doctor_protect_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Protect key town voices.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_name == "investigation":
                living = runner.state.get_living_players()
                return make_investigation_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate town to secure majority.",
                    reasoning="Strategic.",
                    target=living[0],
                )
            elif action_name in ("last_words", "defense"):
                if action_name == "last_words":
                    return make_last_words_response(
                        reasoning="Leave a final note.",
                        text="Final words.",
                    )
                return make_defense_response(
                    reasoning="Leave a final note.",
                    text="Final words.",
                )
            return make_speak_response()

        mock_provider.act = mock_act

        import asyncio

        try:
            result = await asyncio.wait_for(runner.run(), timeout=60.0)
        except TimeoutError:
            pytest.fail("Game did not complete within timeout")

        assert result.winner == "mafia"


class TestSpeakingOrder:
    """Tests for speaking order rotation."""

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    def test_speaking_order_advances_by_seat(self, personas, mock_provider):
        """Speaking order starting position advances by 1 seat each day."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Get initial speaking order for day 1
        runner.state.advance_phase()  # setup -> night_zero
        runner.state.advance_phase()  # night_zero -> day_1
        order_day1 = runner.state.get_speaking_order()
        first_speaker_day1 = order_day1[0]

        # Advance to day 2
        runner.state.advance_phase()  # day_1 -> night_1
        runner.state.advance_phase()  # night_1 -> day_2
        order_day2 = runner.state.get_speaking_order()
        first_speaker_day2 = order_day2[0]

        # First speaker should be different (rotation advanced)
        assert first_speaker_day1 != first_speaker_day2

        # The rotation should follow seat order
        seat_day1 = runner.state.get_player_seat(first_speaker_day1)
        seat_day2 = runner.state.get_player_seat(first_speaker_day2)
        # Day 2 should start at the next living seat after (day1_seat + 1) % 10.
        expected_start_seat = (seat_day1 + 1) % 10
        next_living_seat = None
        for offset in range(10):
            seat = (expected_start_seat + offset) % 10
            if any(p.seat == seat and p.alive for p in runner.state.players.values()):
                next_living_seat = seat
                break

        assert seat_day2 == next_living_seat

    def test_dead_players_skipped_in_speaking_order(self, personas, mock_provider):
        """Dead players are not included in speaking order."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Advance to day phase
        runner.state.advance_phase()  # setup -> night_zero
        runner.state.advance_phase()  # night_zero -> day_1

        # Kill a player
        victim = config.player_names[0]
        runner.state.kill_player(victim)

        # Get speaking order
        order = runner.state.get_speaking_order()

        assert victim not in order
        assert len(order) == 9  # 10 - 1 dead


class TestNightZeroCoordination:
    """Tests for Night Zero Mafia coordination."""

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    async def test_night_zero_stores_strategies_in_memory(self, personas, mock_provider):
        """Night Zero stores all Mafia strategies in their memories."""
        from src.engine.events import EventLog
        from src.engine.phases import NightZeroPhase

        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Find mafia agents
        mafia_agents = [a for a in runner.agents.values() if a.role == "mafia"]
        mafia_names = [a.name for a in mafia_agents]

        # Mock provider to return distinct strategies by call order.
        call_count = [0]

        async def mock_act(_action_type, _context_string):
            call_count[0] += 1
            if call_count[0] == 1:
                return make_speak_response(
                    observations="Night zero coordination.",
                    suspicions="No suspicions yet.",
                    strategy="Coordinate signals and cover.",
                    reasoning="Planning.",
                    speech="I suggest we use signal words and target quiet players.",
                    nomination="Bob",
                )
            if call_count[0] == 2:
                return make_speak_response(
                    observations="Night zero coordination.",
                    suspicions="No suspicions yet.",
                    strategy="Coordinate signals and cover.",
                    reasoning="Planning.",
                    speech="I want a subtle push on confident Town voices.",
                    nomination="Alice",
                )
            return make_speak_response(
                observations="Night zero coordination.",
                suspicions="No suspicions yet.",
                strategy="Coordinate signals and cover.",
                reasoning="Planning.",
                speech="Let's keep our tells consistent and avoid overreach.",
                nomination="Charlie",
            )

        mock_provider.act = mock_act

        # Run night zero
        phase = NightZeroPhase()
        event_log = EventLog()

        memories = await phase.run(
            runner.agents,
            runner.state,
            event_log,
            runner.memories,
        )

        # Night Zero strategies are logged and fully private.
        events = event_log.get_events_of_type("night_zero_strategy")
        assert len(events) == 3
        public_types = {event.type for event in event_log.get_public_view()}
        assert "night_zero_strategy" not in public_types

        # All Mafia should have strategies stored
        for mafia_name in mafia_names:
            assert "night_zero_strategies" in memories[mafia_name].facts
            strategies = memories[mafia_name].facts["night_zero_strategies"]
            assert len(strategies) == 3
            assert all(name in strategies for name in mafia_names)
            assert set(strategies.values()) == {
                "I suggest we use signal words and target quiet players.",
                "I want a subtle push on confident Town voices.",
                "Let's keep our tells consistent and avoid overreach.",
            }

    async def test_second_mafia_sees_first_strategy(self, personas, mock_provider):
        """Second Mafia in speaking order sees first Mafia's strategy."""
        from src.engine.events import EventLog
        from src.engine.phases import NightZeroPhase

        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Track context strings for each call
        context_strings = []

        async def mock_act(_action_type, context_string):
            context_strings.append(context_string)

            return make_speak_response(
                observations="Night zero coordination.",
                suspicions="No suspicions yet.",
                strategy="Coordinate signals and cover.",
                reasoning="Planning.",
                speech="My strategy is to target Alice",
                nomination="Alice",
            )

        mock_provider.act = mock_act

        phase = NightZeroPhase()
        event_log = EventLog()

        await phase.run(
            runner.agents,
            runner.state,
            event_log,
            runner.memories,
        )

        assert len(context_strings) == 3
        # First Mafia's context should NOT contain partner strategies
        assert "[PARTNER STRATEGIES]" not in context_strings[0]

        # Later Mafia should see partner strategies
        assert "[PARTNER STRATEGIES]" in context_strings[1]
        assert "[PARTNER STRATEGIES]" in context_strings[2]
        assert "My strategy is to target Alice" in context_strings[1]
        assert "My strategy is to target Alice" in context_strings[2]


class TestLogSchema:
    """Tests for game log schema compliance."""

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    def test_log_schema_has_required_fields(self, personas, mock_provider):
        """Game log data includes all required fields per Phase 3 spec."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        names = list(personas.keys())
        # Simulate some eliminations
        runner.eliminations = [
            {"round": 1, "phase": "day", "player": names[0], "role": "town"},
            {"round": 1, "phase": "night", "player": names[1], "role": "mafia"},
        ]
        runner.state.kill_player(names[0])
        runner.state.kill_player(names[1])

        log_data = runner._build_log_data("town")

        # Check required fields
        assert "schema_version" in log_data
        assert "game_id" in log_data
        assert "timestamp_start" in log_data
        assert "timestamp_end" in log_data
        assert "winner" in log_data
        assert "players" in log_data
        assert "events" in log_data

        # Check timestamp format (ISO8601)
        assert "T" in log_data["timestamp_start"]
        assert "T" in log_data["timestamp_end"]

    def test_player_outcomes_calculated_correctly(self, personas, mock_provider):
        """Player outcomes are correctly calculated from eliminations."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)

        # Get player names
        names = list(personas.keys())

        # Alice eliminated by vote (day), Bob killed at night, rest survived
        runner.eliminations = [
            {"round": 1, "phase": "day", "player": names[0], "role": "town"},
            {"round": 1, "phase": "night", "player": names[1], "role": "mafia"},
        ]
        runner.state.kill_player(names[0])
        runner.state.kill_player(names[1])

        log_data = runner._build_log_data("town")

        # Find player entries
        player_outcomes = {p["name"]: p["outcome"] for p in log_data["players"]}

        # Check outcomes
        assert player_outcomes[names[0]] == "eliminated"  # Day vote
        assert player_outcomes[names[1]] == "killed"  # Night kill
        for name in names[2:]:
            assert player_outcomes[name] == "survived"

    def test_player_entries_have_required_fields(self, personas, mock_provider):
        """Each player entry has all required fields."""
        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)
        log_data = runner._build_log_data("town")

        for player in log_data["players"]:
            assert "seat" in player
            assert "persona_id" in player
            assert "name" in player
            assert "role" in player
            assert "outcome" in player


class TestMafiaCoordination:
    """Tests for Mafia night kill coordination."""

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    async def test_round1_agreement_skips_round2(self, personas, mock_provider):
        """When all Mafia agree in Round 1, Round 2 is skipped."""
        from src.engine.events import EventLog
        from src.engine.phases import NightPhase
        from src.engine.transcript import TranscriptManager

        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)
        runner.state.advance_phase()  # setup -> night_zero
        runner.state.advance_phase()  # night_zero -> day_1
        runner.state.advance_phase()  # day_1 -> night_1

        mafia_call_count = [0]
        round1_contexts = []
        non_mafia = [
            name
            for name in runner.state.get_living_players()
            if runner.state.get_player_role(name) != "mafia"
        ]
        agreed_target = non_mafia[0] if non_mafia else "skip"

        async def mock_act(action_type, _context_string):
            if action_type.value == "night_kill":
                mafia_call_count[0] += 1
                # All Mafia agree on same target
                round1_contexts.append(_context_string)
                return make_night_kill_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target=agreed_target,
                )
            elif action_type.value == "doctor_protect":
                return make_doctor_protect_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Protect key town voices.",
                    reasoning="Strategic.",
                    target=agreed_target,
                )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target=agreed_target,
                )
            return make_speak_response()

        mock_provider.act = mock_act

        phase = NightPhase()
        event_log = EventLog()
        transcript = TranscriptManager()

        await phase.run(
            runner.agents,
            runner.state,
            transcript,
            event_log,
            runner.memories,
        )

        # Should have 3 Mafia calls (Round 1 only)
        assert mafia_call_count[0] == 3
        assert len(round1_contexts) == 3
        assert "[COORDINATION ROUND 1]" in round1_contexts[1]
        assert "[COORDINATION ROUND 1]" in round1_contexts[2]
        assert "Prior proposals" in round1_contexts[1]
        assert "Prior messages" in round1_contexts[1]

    async def test_round2_on_disagreement(self, personas, mock_provider):
        """Round 2 occurs when Mafia disagree in Round 1."""
        from src.engine.events import EventLog
        from src.engine.phases import NightPhase
        from src.engine.transcript import TranscriptManager

        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)
        runner.state.advance_phase()  # setup -> night_zero
        runner.state.advance_phase()  # night_zero -> day_1
        runner.state.advance_phase()  # day_1 -> night_1

        mafia_call_count = [0]
        round2_context_strings = []
        round1_context_strings = []
        non_mafia = [
            name
            for name in runner.state.get_living_players()
            if runner.state.get_player_role(name) != "mafia"
        ]
        r1_targets = non_mafia[:3]
        r2_target = non_mafia[0] if non_mafia else "skip"

        async def mock_act(action_type, context_string):
            if action_type.value == "night_kill":
                mafia_call_count[0] += 1
                # Check if this is Round 2 by looking for COORDINATION ROUND 2 in context
                is_round2 = "[COORDINATION ROUND 2]" in context_string
                if not is_round2:
                    round1_context_strings.append(context_string)
                if is_round2:
                    round2_context_strings.append(context_string)
                    # In Round 2, all agree on the same target
                    return make_night_kill_response(
                        observations="Night phase begins.",
                        suspicions="Town targets identified.",
                        strategy="Eliminate a key town voice.",
                        reasoning="Strategic.",
                        target=r2_target,
                    )
                else:
                    # Round 1: disagree - each Mafia picks a different target
                    r1_index = (mafia_call_count[0] - 1) % 3
                    target = r1_targets[r1_index] if r1_targets else "skip"
                    return make_night_kill_response(
                        observations="Night phase begins.",
                        suspicions="Town targets identified.",
                        strategy="Eliminate a key town voice.",
                        reasoning="Strategic.",
                        target=target,
                    )
            elif action_type.value == "doctor_protect":
                target = non_mafia[0] if non_mafia else "skip"
                return make_doctor_protect_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Protect key town voices.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target=r2_target,
                )
            return make_speak_response()

        mock_provider.act = mock_act

        phase = NightPhase()
        event_log = EventLog()
        transcript = TranscriptManager()

        await phase.run(
            runner.agents,
            runner.state,
            transcript,
            event_log,
            runner.memories,
        )

        # Should have 6 Mafia calls (3 R1 + 3 R2)
        assert mafia_call_count[0] == 6

        # Round 2 should have occurred with partner proposals visible
        assert len(round2_context_strings) == 3
        for ctx in round2_context_strings:
            # Context should contain info about Round 1 proposals
            assert "Round 1 proposals" in ctx
            assert "Round 1 messages" in ctx
        # Later Mafia should see prior proposals in Round 1
        assert len(round1_context_strings) == 3
        assert "[COORDINATION ROUND 1]" in round1_context_strings[1]
        assert "[COORDINATION ROUND 1]" in round1_context_strings[2]

    async def test_first_mafia_decides_on_continued_disagreement(self, personas, mock_provider):
        """First Mafia (by seat) decides if still disagree after Round 2."""
        from src.engine.events import EventLog
        from src.engine.phases import NightPhase
        from src.engine.transcript import TranscriptManager

        config = GameConfig(
            player_names=list(personas.keys()),
            personas=personas,
            provider=mock_provider,
            seed=42,
        )

        runner = GameRunner(config)
        runner.state.advance_phase()
        runner.state.advance_phase()
        runner.state.advance_phase()

        mafia_call_count = [0]
        non_mafia = [
            name
            for name in runner.state.get_living_players()
            if runner.state.get_player_role(name) != "mafia"
        ]
        targets = non_mafia[:3]
        if len(targets) < 3:
            targets = (targets + ["skip", "skip", "skip"])[:3]

        async def mock_act(action_type, _context_string):
            if action_type.value == "night_kill":
                mafia_call_count[0] += 1
                r1_index = (mafia_call_count[0] - 1) % 3
                target = targets[r1_index]
                return make_night_kill_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_type.value == "doctor_protect":
                target = non_mafia[0] if non_mafia else "skip"
                return make_doctor_protect_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Protect key town voices.",
                    reasoning="Strategic.",
                    target=target,
                )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target=targets[0],
                )
            return make_speak_response()

        mock_provider.act = mock_act

        phase = NightPhase()
        event_log = EventLog()
        transcript = TranscriptManager()

        await phase.run(
            runner.agents,
            runner.state,
            transcript,
            event_log,
            runner.memories,
        )

        mafia_votes = event_log.get_events_of_type("mafia_vote")
        assert mafia_votes
        final_vote = mafia_votes[-1]
        mafia_agents = sorted(
            [a for a in runner.agents.values() if a.role == "mafia"],
            key=lambda a: a.seat,
        )
        expected_decider = mafia_agents[0].name

        # First mafia's R2 choice should be used as tiebreaker
        assert final_vote.data.get("coordination_round") == 2
        assert final_vote.data.get("decided_by") == expected_decider
        assert final_vote.data.get("final_target") == targets[0]
