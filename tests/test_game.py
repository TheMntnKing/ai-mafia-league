"""Integration tests for game loop."""

from unittest.mock import AsyncMock

import pytest

from src.engine.game import GameConfig, GameRunner
from src.engine.voting import VoteResolver
from src.personas.initial import get_personas
from src.schemas import PlayerMemory
from tests.sgr_helpers import (
    make_defense_response,
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

    def test_majority_eliminates(self, resolver):
        """Clear majority eliminates the target."""
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

    def test_plurality_without_majority(self, resolver):
        """Plurality without majority and no tie doesn't eliminate."""
        votes = {
            "Alice": "Bob",
            "Bob": "Bob",
            "Charlie": "Diana",
            "Diana": "skip",
            "Eve": "skip",
        }
        # Bob has 2 votes, Diana has 1 - not a tie, but not majority (3 needed)
        result = resolver.resolve(votes, 5)
        assert result.outcome == "no_elimination"

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

    def test_revote_majority_eliminates(self, resolver):
        """Revote with majority eliminates."""
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

        assert len(runner.agents) == 7
        for name in game_config.player_names:
            assert name in runner.agents
            assert runner.agents[name].name == name

    def test_game_runner_assigns_roles(self, game_config):
        """GameRunner assigns correct role distribution."""
        runner = GameRunner(game_config)

        roles = [runner.state.get_player_role(name) for name in game_config.player_names]

        assert roles.count("mafia") == 2
        assert roles.count("detective") == 1
        assert roles.count("town") == 4

    def test_game_runner_initializes_memories(self, game_config):
        """GameRunner initializes empty memories for all players."""
        runner = GameRunner(game_config)

        assert len(runner.memories) == 7
        for name in game_config.player_names:
            assert name in runner.memories
            assert isinstance(runner.memories[name], PlayerMemory)

    async def test_game_runner_runs_to_completion(self, game_config, mock_provider):
        """GameRunner completes a game with mocked provider."""

        # Track calls to determine game phase
        call_count = [0]
        eliminated = set()

        def make_response(action_type):
            """Generate a response based on action type and game state."""
            call_count[0] += 1

            if action_type == "speak":
                # Nominate someone who isn't eliminated
                living = [n for n in game_config.player_names if n not in eliminated]
                nomination = living[1] if len(living) > 1 else living[0]
                return make_speak_response(
                    speech="I've been observing carefully and have some thoughts.",
                    nomination=nomination,
                )
            elif action_type == "vote":
                living = [n for n in game_config.player_names if n not in eliminated]
                target = living[1] if len(living) > 1 else "skip"
                return make_vote_response(vote=target, reasoning="Based on behavior.")
            elif action_type == "night_kill":
                living = [n for n in game_config.player_names if n not in eliminated]
                # Pick a non-mafia target
                target = living[2] if len(living) > 2 else living[0]
                return make_night_kill_response(target=target, reasoning="Strategic target.")
            elif action_type == "investigation":
                living = [n for n in game_config.player_names if n not in eliminated]
                return make_investigation_response(
                    target=living[1],
                    reasoning="Most suspicious.",
                )
            elif action_type in ("last_words", "defense"):
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

        runner = GameRunner(game_config)

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
        """Mafia agents are assigned their partner."""
        runner = GameRunner(game_config)

        mafia_agents = [a for a in runner.agents.values() if a.role == "mafia"]
        assert len(mafia_agents) == 2

        # Each mafia should have the other as partner
        m1, m2 = mafia_agents
        assert m1.partner == m2.name
        assert m2.partner == m1.name


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

        # Find town players (including detective)
        town_names = [
            name for name in config.player_names
            if runner.state.get_player_role(name) in ("town", "detective")
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
                    if runner.state.get_player_role(p) in ("town", "detective")
                ]
                target = town[0] if town else "skip"
                return make_night_kill_response(
                    observations="Discussion ongoing.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate town to secure majority.",
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
        # Day 2 should start at the next living seat after (day1_seat + 1) % 7.
        expected_start_seat = (seat_day1 + 1) % 7
        next_living_seat = None
        for offset in range(7):
            seat = (expected_start_seat + offset) % 7
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
        assert len(order) == 6  # 7 - 1 dead


class TestNightZeroCoordination:
    """Tests for Night Zero Mafia coordination."""

    @pytest.fixture
    def personas(self):
        return get_personas()

    @pytest.fixture
    def mock_provider(self):
        return AsyncMock()

    async def test_night_zero_stores_strategies_in_memory(self, personas, mock_provider):
        """Night Zero stores both Mafia strategies in their memories."""
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
            return make_speak_response(
                observations="Night zero coordination.",
                suspicions="No suspicions yet.",
                strategy="Coordinate signals and cover.",
                reasoning="Planning.",
                speech="I agree with partner. Let's target the detective.",
                nomination="Alice",
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
        assert len(events) == 2
        public_types = {event.type for event in event_log.get_public_view()}
        assert "night_zero_strategy" not in public_types

        # Both Mafia should have strategies stored
        for mafia_name in mafia_names:
            assert "night_zero_strategies" in memories[mafia_name].facts
            strategies = memories[mafia_name].facts["night_zero_strategies"]
            assert len(strategies) == 2
            assert all(name in strategies for name in mafia_names)
            assert set(strategies.values()) == {
                "I suggest we use signal words and target quiet players.",
                "I agree with partner. Let's target the detective.",
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

        # First Mafia's context should NOT contain partner's strategy section
        assert "[PARTNER'S STRATEGY]" not in context_strings[0]

        # Second Mafia's context SHOULD contain partner's strategy
        # The context builder wraps it in a PARTNER'S STRATEGY section
        assert "[PARTNER'S STRATEGY]" in context_strings[1]
        assert "My strategy is to target Alice" in context_strings[1]


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

        # Simulate some eliminations
        runner.eliminations = [
            {"round": 1, "phase": "day", "player": "Alice", "role": "town"},
            {"round": 1, "phase": "night", "player": "Bob", "role": "mafia"},
        ]
        runner.state.kill_player("Alice")
        runner.state.kill_player("Bob")

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
        """When both Mafia agree in Round 1, Round 2 is skipped."""
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

        call_count = [0]
        round1_contexts = []

        async def mock_act(action_type, _context_string):
            call_count[0] += 1

            if action_type.value == "night_kill":
                # Both agree on same target
                round1_contexts.append(_context_string)
                return make_night_kill_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target="Alice",
                )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target="Bob",
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

        # Should have 2 Mafia calls (Round 1 only) + 1 Detective = 3
        # If Round 2 happened, would be 4 Mafia + 1 Detective = 5
        assert call_count[0] == 3
        assert len(round1_contexts) == 2
        assert "[COORDINATION ROUND 1]" in round1_contexts[1]
        assert "Partner's message" in round1_contexts[1]

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

        async def mock_act(action_type, context_string):
            if action_type.value == "night_kill":
                mafia_call_count[0] += 1
                # Check if this is Round 2 by looking for COORDINATION ROUND 2 in context
                is_round2 = "[COORDINATION ROUND 2]" in context_string
                if not is_round2:
                    round1_context_strings.append(context_string)
                if is_round2:
                    round2_context_strings.append(context_string)
                    # In Round 2, both agree on Alice
                    return make_night_kill_response(
                        observations="Night phase begins.",
                        suspicions="Town targets identified.",
                        strategy="Eliminate a key town voice.",
                        reasoning="Strategic.",
                        target="Alice",
                    )
                else:
                    # Round 1: disagree - first says Alice, second says Bob
                    if mafia_call_count[0] == 1:
                        return make_night_kill_response(
                            observations="Night phase begins.",
                            suspicions="Town targets identified.",
                            strategy="Eliminate a key town voice.",
                            reasoning="Strategic.",
                            target="Alice",
                        )
                    return make_night_kill_response(
                        observations="Night phase begins.",
                        suspicions="Town targets identified.",
                        strategy="Eliminate a key town voice.",
                        reasoning="Strategic.",
                        target="Bob",
                    )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target="Charlie",
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

        # Should have 4 Mafia calls (2 R1 + 2 R2)
        assert mafia_call_count[0] == 4

        # Round 2 should have occurred with partner proposals visible
        assert len(round2_context_strings) == 2
        for ctx in round2_context_strings:
            # Context should contain info about partner's R1 proposal
            assert "Partner's Round 1 proposal" in ctx
            assert "Partner's Round 1 message" in ctx
        # Second Mafia should see partner proposal in Round 1
        assert len(round1_context_strings) == 2
        assert "[COORDINATION ROUND 1]" in round1_context_strings[1]

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

        # Track Mafia calls to alternate between first and second Mafia
        # Order: First(R1), Second(R1), First(R2), Second(R2)
        mafia_call_count = [0]

        async def mock_act(action_type, _context_string):
            if action_type.value == "night_kill":
                mafia_call_count[0] += 1
                # First Mafia always says Alice (calls 1, 3)
                # Second Mafia always says Bob (calls 2, 4)
                if mafia_call_count[0] % 2 == 1:
                    return make_night_kill_response(
                        observations="Night phase begins.",
                        suspicions="Town targets identified.",
                        strategy="Eliminate a key town voice.",
                        reasoning="Strategic.",
                        target="Alice",
                    )
                return make_night_kill_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target="Bob",
                )
            elif action_type.value == "investigation":
                return make_investigation_response(
                    observations="Night phase begins.",
                    suspicions="Town targets identified.",
                    strategy="Eliminate a key town voice.",
                    reasoning="Strategic.",
                    target="Charlie",
                )
            return make_speak_response()

        mock_provider.act = mock_act

        phase = NightPhase()
        event_log = EventLog()
        transcript = TranscriptManager()

        kill_target, _ = await phase.run(
            runner.agents,
            runner.state,
            transcript,
            event_log,
            runner.memories,
        )

        # First mafia's R2 choice (Alice) should be used as tiebreaker
        assert kill_target == "Alice"
