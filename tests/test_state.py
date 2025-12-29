"""Tests for game state management."""

import pytest

from src.engine.events import EventLog
from src.engine.state import GameStateManager
from src.storage.json_logs import GameLogWriter, PlayerEntry


class TestGameStateManager:
    @pytest.fixture
    def player_names(self):
        return ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]

    @pytest.fixture
    def manager(self, player_names):
        return GameStateManager(player_names, seed=42)

    def test_requires_seven_players(self):
        """Game requires exactly 7 players."""
        with pytest.raises(ValueError, match="exactly 7 players"):
            GameStateManager(["Alice", "Bob", "Charlie"])

        with pytest.raises(ValueError, match="exactly 7 players"):
            GameStateManager(["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])

    def test_role_distribution(self, manager):
        """7 players get correct role distribution: 2 Mafia, 1 Detective, 4 Town."""
        roles = [p.role for p in manager.players.values()]
        assert roles.count("mafia") == 2
        assert roles.count("detective") == 1
        assert roles.count("town") == 4

    def test_all_players_start_alive(self, manager):
        """All players start alive."""
        for player in manager.players.values():
            assert player.alive is True

    def test_seeding_produces_reproducible_results(self, player_names):
        """Same seed produces same role assignments."""
        manager1 = GameStateManager(player_names, seed=123)
        manager2 = GameStateManager(player_names, seed=123)

        for name in player_names:
            assert manager1.players[name].role == manager2.players[name].role
            assert manager1.players[name].seat == manager2.players[name].seat

    def test_add_nomination_rejects_unknown_player(self, manager):
        """Nominating an unknown player should raise."""
        with pytest.raises(ValueError, match="Unknown player"):
            manager.add_nomination("Zoe")

    def test_add_nomination_rejects_dead_player(self, manager):
        """Nominating a dead player should raise."""
        manager.kill_player("Alice")
        with pytest.raises(ValueError, match="dead"):
            manager.add_nomination("Alice")

    def test_record_vote_rejects_unknown_voter(self, manager):
        """Votes from unknown players should raise."""
        manager.add_nomination("Bob")
        with pytest.raises(ValueError, match="Unknown voter"):
            manager.record_vote("Zoe", "Bob")

    def test_record_vote_rejects_dead_voter(self, manager):
        """Votes from dead players should raise."""
        manager.add_nomination("Bob")
        manager.kill_player("Alice")
        with pytest.raises(ValueError, match="dead voter"):
            manager.record_vote("Alice", "Bob")

    def test_record_vote_rejects_non_nominated_target(self, manager):
        """Votes must target a nominated player or skip."""
        manager.add_nomination("Bob")
        with pytest.raises(ValueError, match="not nominated"):
            manager.record_vote("Alice", "Charlie")

    def test_record_vote_rejects_unknown_target(self, manager):
        """Votes cannot target unknown players."""
        manager.add_nomination("Bob")
        with pytest.raises(ValueError, match="Unknown vote target"):
            manager.record_vote("Alice", "Zoe")

    def test_record_vote_rejects_dead_target(self, manager):
        """Votes cannot target dead players."""
        manager.add_nomination("Bob")
        manager.kill_player("Bob")
        with pytest.raises(ValueError, match="dead player"):
            manager.record_vote("Alice", "Bob")

    def test_record_vote_allows_skip(self, manager):
        """Skip is always a valid vote."""
        manager.add_nomination("Bob")
        manager.record_vote("Alice", "skip")
        assert manager.votes["Alice"] == "skip"


class TestPhaseTransitions:
    @pytest.fixture
    def manager(self):
        return GameStateManager(
            ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
            seed=42,
        )

    def test_initial_phase_is_setup(self, manager):
        """Game starts in setup phase."""
        assert manager.phase == "setup"
        assert manager.round_number == 0

    def test_setup_to_night_zero(self, manager):
        """Setup transitions to night_zero."""
        manager.advance_phase()
        assert manager.phase == "night_zero"

    def test_night_zero_to_day_one(self, manager):
        """Night zero transitions to day 1."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        assert manager.phase == "day_1"
        assert manager.round_number == 1

    def test_day_to_night_transition(self, manager):
        """Day N transitions to night N."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        manager.advance_phase()  # -> night_1
        assert manager.phase == "night_1"

    def test_night_to_day_transition(self, manager):
        """Night N transitions to day N+1."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        manager.advance_phase()  # -> night_1
        manager.advance_phase()  # -> day_2
        assert manager.phase == "day_2"
        assert manager.round_number == 2

    def test_nominations_cleared_on_new_day(self, manager):
        """Nominations are cleared when entering a new day phase."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        manager.add_nomination("Alice")
        assert len(manager.nominations) == 1

        manager.advance_phase()  # -> night_1
        manager.advance_phase()  # -> day_2
        assert manager.nominations == []

    def test_nominations_cleared_on_night(self, manager):
        """Nominations are cleared when entering a night phase."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        manager.add_nomination("Alice")
        assert len(manager.nominations) == 1

        manager.advance_phase()  # -> night_1
        assert manager.nominations == []


class TestWinConditions:
    @pytest.fixture
    def manager(self):
        return GameStateManager(
            ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
            seed=42,
        )

    def test_no_winner_at_start(self, manager):
        """No winner when game starts."""
        assert manager.check_win_condition() is None

    def test_town_wins_when_mafia_eliminated(self, manager):
        """Town wins when both Mafia are dead."""
        mafia_players = manager.get_players_by_role("mafia")
        for name in mafia_players:
            manager.kill_player(name)

        assert manager.check_win_condition() == "town"

    def test_mafia_wins_when_equals_town(self, manager):
        """Mafia wins when Mafia count >= Town-aligned count."""
        # Start: 2 Mafia, 5 Town-aligned (1 Detective + 4 Town)
        # Kill 3 Town-aligned: 2 Mafia vs 2 Town-aligned -> Mafia wins

        town_aligned = [
            name
            for name, info in manager.players.items()
            if info.role in ("town", "detective")
        ]

        # Kill 3 town-aligned to get to 2v2
        for name in town_aligned[:3]:
            manager.kill_player(name)

        assert manager.check_win_condition() == "mafia"

    def test_game_continues_with_mafia_minority(self, manager):
        """Game continues while Mafia is in minority."""
        # Kill 1 town-aligned: 2 Mafia vs 4 Town-aligned
        town_player = next(
            name for name, info in manager.players.items() if info.role == "town"
        )
        manager.kill_player(town_player)

        assert manager.check_win_condition() is None

    def test_mafia_wins_with_majority(self, manager):
        """Mafia wins when they outnumber Town."""
        # Kill 4 town-aligned: 2 Mafia vs 1 Town-aligned -> Mafia wins
        town_aligned = [
            name
            for name, info in manager.players.items()
            if info.role in ("town", "detective")
        ]

        for name in town_aligned[:4]:
            manager.kill_player(name)

        assert manager.check_win_condition() == "mafia"


class TestSpeakingOrder:
    @pytest.fixture
    def manager(self):
        return GameStateManager(
            ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
            seed=42,
        )

    def test_all_living_players_speak(self, manager):
        """All living players are in speaking order."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1

        order = manager.get_speaking_order()
        living = [p.name for p in manager.players.values() if p.alive]

        assert len(order) == len(living)
        assert set(order) == set(living)

    def test_speaking_order_rotates_by_day(self, manager):
        """First speaker changes each day."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1
        order_day1 = manager.get_speaking_order()

        manager.advance_phase()  # -> night_1
        manager.advance_phase()  # -> day_2
        order_day2 = manager.get_speaking_order()

        # First speaker should be different
        assert order_day1[0] != order_day2[0]

    def test_dead_players_skipped(self, manager):
        """Dead players are not in speaking order."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1

        # Kill first player in the order
        order_before = manager.get_speaking_order()
        first_speaker = order_before[0]
        manager.kill_player(first_speaker)

        order_after = manager.get_speaking_order()
        assert first_speaker not in order_after
        assert len(order_after) == 6


class TestMafiaPartner:
    @pytest.fixture
    def manager(self):
        return GameStateManager(
            ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
            seed=42,
        )

    def test_mafia_knows_partner(self, manager):
        """Mafia player can get their partner's name."""
        mafia_players = manager.get_players_by_role("mafia")
        assert len(mafia_players) == 2

        partner_of_first = manager.get_mafia_partner(mafia_players[0])
        partner_of_second = manager.get_mafia_partner(mafia_players[1])

        assert partner_of_first == mafia_players[1]
        assert partner_of_second == mafia_players[0]

    def test_non_mafia_has_no_partner(self, manager):
        """Non-Mafia players return None for partner."""
        town_player = next(
            name for name, info in manager.players.items() if info.role == "town"
        )
        detective = next(
            name for name, info in manager.players.items() if info.role == "detective"
        )

        assert manager.get_mafia_partner(town_player) is None
        assert manager.get_mafia_partner(detective) is None


class TestPublicState:
    @pytest.fixture
    def manager(self):
        return GameStateManager(
            ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
            seed=42,
        )

    def test_public_state_has_all_fields(self, manager):
        """Public state contains all required fields."""
        manager.advance_phase()  # -> night_zero
        manager.advance_phase()  # -> day_1

        state = manager.get_public_state()
        assert state.phase == "day_1"
        assert state.round_number == 1
        assert len(state.living_players) == 7
        assert state.dead_players == []
        assert state.nominated_players == []

    def test_public_state_reflects_deaths(self, manager):
        """Public state shows dead players without roles."""
        manager.advance_phase()
        manager.advance_phase()

        # Kill a player
        manager.kill_player("Alice")
        state = manager.get_public_state()

        assert "Alice" not in state.living_players
        assert "Alice" in state.dead_players

    def test_public_state_shows_nominations(self, manager):
        """Public state includes current nominations."""
        manager.advance_phase()
        manager.advance_phase()

        manager.add_nomination("Bob")
        manager.add_nomination("Charlie")

        state = manager.get_public_state()
        assert "Bob" in state.nominated_players
        assert "Charlie" in state.nominated_players


class TestEventLog:
    def test_add_event(self):
        """Can add events to log."""
        log = EventLog()
        event = log.add("speech", {"speaker": "Alice", "text": "Hello"})

        assert event.type == "speech"
        assert event.data["speaker"] == "Alice"
        assert len(log.events) == 1

    def test_public_view_filters_private_fields(self):
        """Public view removes private fields."""
        log = EventLog()
        log.add(
            "speech",
            {"speaker": "Alice", "text": "Hello", "reasoning": "secret"},
            private_fields=["reasoning"],
        )

        public = log.get_public_view()
        assert "reasoning" not in public[0].data
        assert "speaker" in public[0].data

    def test_full_view_includes_private_fields(self):
        """Full view includes all data."""
        log = EventLog()
        log.add(
            "speech",
            {"speaker": "Alice", "text": "Hello", "reasoning": "secret"},
            private_fields=["reasoning"],
        )

        full = log.get_full_view()
        assert "reasoning" in full[0].data

    def test_full_view_since_index(self):
        """Full view since index returns only newer events."""
        log = EventLog()
        log.add("phase_start", {"phase": "day_1", "round_number": 1})
        second = log.add("speech", {"speaker": "Alice", "text": "Hello"})

        events = log.get_full_view_since(1)
        assert len(events) == 1
        assert events[0] == second

    def test_events_since_timestamp(self):
        """Timestamp filter returns only later events."""
        log = EventLog()
        first = log.add("phase_start", {"phase": "day_1", "round_number": 1})
        second = log.add("speech", {"speaker": "Alice", "text": "Hello"})

        first.timestamp = "2024-01-01T00:00:00+00:00"
        second.timestamp = "2024-01-01T00:00:10+00:00"

        events = log.get_events_since_timestamp("2024-01-01T00:00:00Z")
        assert events == [second]

    def test_convenience_methods(self):
        """Convenience methods create correct event types."""
        log = EventLog()

        log.add_phase_start("day_1", 1)
        log.add_speech("Alice", "Hello", "Bob", {"thought": "hmm"})
        log.add_vote({"Alice": "Bob"}, "eliminated", "Bob")
        log.add_last_words("Bob", "Goodbye")
        log.add_game_end("town", {"Alice": "town", "Bob": "mafia"})

        assert log.events[0].type == "phase_start"
        assert log.events[1].type == "speech"
        assert log.events[2].type == "vote"
        assert log.events[3].type == "last_words"
        assert log.events[4].type == "game_end"

    def test_investigation_fully_private(self):
        """Investigation events have all fields private."""
        log = EventLog()
        event = log.add_investigation("Alice", "Mafia", {"thought": "suspicious"})

        assert "target" in event.private_fields
        assert "result" in event.private_fields
        assert "reasoning" in event.private_fields

        public = log.get_public_view()
        assert public == []  # Fully private events should be hidden


class TestGameLogWriter:
    def test_write_and_read(self, tmp_path):
        """Can write and read game logs."""
        writer = GameLogWriter(str(tmp_path))

        players = [
            PlayerEntry(0, "p1", "Alice", "town", "survived"),
            PlayerEntry(1, "p2", "Bob", "mafia", "eliminated"),
        ]

        log = EventLog()
        log.add_phase_start("day_1", 1)

        filepath = writer.write(
            game_id="test123",
            timestamp_start="2024-01-01T00:00:00Z",
            timestamp_end="2024-01-01T01:00:00Z",
            winner="town",
            players=players,
            events=log.get_full_view(),
        )

        assert filepath.exists()

        # Read back
        data = writer.read("test123")
        assert data is not None
        assert data["schema_version"] == "1.0"
        assert data["winner"] == "town"
        assert len(data["players"]) == 2
        assert len(data["events"]) == 1

    def test_list_games(self, tmp_path):
        """Can list all game IDs."""
        writer = GameLogWriter(str(tmp_path))
        log = EventLog()

        writer.write("game1", "t1", "t2", "town", [], log.get_full_view())
        writer.write("game2", "t1", "t2", "mafia", [], log.get_full_view())

        games = writer.list_games()
        assert "game1" in games
        assert "game2" in games

    async def test_write_game_log(self, tmp_path):
        """Async write_game_log writes to disk."""
        writer = GameLogWriter(str(tmp_path))
        log_data = {"game_id": "async123", "schema_version": "1.0"}

        path = await writer.write_game_log(log_data)
        assert (tmp_path / "game_async123.json").exists()
        assert path.endswith("game_async123.json")

        data = writer.read("async123")
        assert data is not None
        assert data["game_id"] == "async123"

    def test_read_nonexistent(self, tmp_path):
        """Reading nonexistent game returns None."""
        writer = GameLogWriter(str(tmp_path))
        assert writer.read("nonexistent") is None
