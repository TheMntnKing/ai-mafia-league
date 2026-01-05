"""Tests for transcript management and context building."""

import pytest

from src.engine.context import ContextBuilder
from src.engine.transcript import TranscriptManager
from src.schemas import (
    ActionType,
    DefenseSpeech,
    GameState,
    PlayerMemory,
    Speech,
)


class TestTranscriptManager:
    @pytest.fixture
    def manager(self):
        return TranscriptManager()

    def test_add_speech(self, manager):
        """Can add speeches to current round."""
        manager.add_speech("Alice", "I think Bob is suspicious", "Bob")
        manager.add_speech("Bob", "I'm innocent!", "Alice")

        speeches = manager.get_current_speeches()
        assert len(speeches) == 2
        assert speeches[0].speaker == "Alice"
        assert speeches[1].nomination == "Alice"

    def test_finalize_round(self, manager):
        """Finalize round creates transcript and clears current speeches."""
        manager.add_speech("Alice", "Hello", "Bob")
        manager.add_speech("Bob", "Hi", "Alice")

        transcript = manager.finalize_round(
            round_number=1,
            night_kill=None,
            votes={"Alice": "Bob", "Bob": "skip"},
            vote_outcome="no_elimination",
        )

        assert transcript.round_number == 1
        assert len(transcript.speeches) == 2
        assert manager.get_current_speeches() == []
        assert len(manager.rounds) == 1
        assert transcript.last_words is None

    def test_finalize_round_stores_last_words(self, manager):
        """Finalize round stores day-elimination last words."""
        manager.add_speech("Alice", "Vote Bob", "Bob")

        transcript = manager.finalize_round(
            round_number=1,
            night_kill=None,
            votes={"Alice": "Bob"},
            vote_outcome="eliminated:Bob",
            last_words="I was town. Watch Alice.",
        )

        assert transcript.last_words == "I was town. Watch Alice."

    def test_live_round_includes_night_info(self, manager):
        """In-progress round includes night kill (no last words for night kills)."""
        manager.start_round(2, night_kill="Alice")
        manager.add_speech("Bob", "We lost Alice", "Charlie")

        transcript = manager.get_transcript_for_player(current_round=2)
        live = transcript[-1]

        assert live.round_number == 2
        assert live.night_kill == "Alice"
        assert live.last_words is None  # Night kills have no last words
        assert len(live.speeches) == 1

    def test_finalize_round_with_revote(self, manager):
        """Finalize round captures revote data."""
        manager.add_speech("Alice", "Vote Bob", "Bob")

        transcript = manager.finalize_round(
            round_number=2,
            night_kill="Charlie",
            votes={"Alice": "Bob", "Bob": "Alice"},
            vote_outcome="revote",
            last_words="Good luck, Town.",
            defense_speeches=[DefenseSpeech(speaker="Alice", text="I'm innocent")],
            revote={"Diana": "Bob"},
            revote_outcome="eliminated:Bob",
        )

        assert transcript.revote_outcome == "eliminated:Bob"
        assert transcript.defense_speeches is not None
        assert transcript.last_words == "Good luck, Town."

    def test_live_round_has_pending_vote_outcome(self, manager):
        """Live (in-progress) rounds have vote_outcome='pending'."""
        manager.start_round(1, night_kill=None)
        manager.add_speech("Alice", "Hello", "Bob")

        transcript = manager.get_transcript_for_player(current_round=1)
        live_round = transcript[-1]

        assert live_round.vote_outcome == "pending"


class TestTranscriptCompression:
    @pytest.fixture
    def manager(self):
        return TranscriptManager()

    def test_two_round_window(self, manager):
        """Transcripts older than 2 rounds are compressed."""
        # Add 3 rounds
        for i in range(1, 4):
            manager.add_speech(f"Player{i}", "Speech text", f"Player{i+1}")
            manager.finalize_round(
                round_number=i,
                night_kill=None if i == 1 else f"Player{i-1}",
                votes={f"Player{i}": "skip"},
                vote_outcome="no_elimination",
            )

        # Get transcript for round 3
        transcript = manager.get_transcript_for_player(current_round=3)

        # Round 1 should be compressed
        assert hasattr(transcript[0], "vote_result")  # CompressedRoundSummary
        # Rounds 2 and 3 should be full
        assert hasattr(transcript[1], "speeches")  # DayRoundTranscript
        assert hasattr(transcript[2], "speeches")  # DayRoundTranscript

    def test_compression_captures_deaths(self, manager):
        """Compression captures night and vote deaths."""
        manager.add_speech("Alice", "Vote Bob", "Bob")
        manager.finalize_round(
            round_number=1,
            night_kill="Charlie",
            votes={"Alice": "Bob"},
            vote_outcome="eliminated:Bob",
        )

        # Add rounds
        for i in range(2, 4):
            manager.add_speech("Diana", "Test", "Eve")
            manager.finalize_round(i, None, {}, "no_elimination")

        transcript = manager.get_transcript_for_player(current_round=3)
        compressed = transcript[0]

        assert compressed.night_death == "Charlie"
        assert compressed.vote_death == "Bob"


class TestContextBuilder:
    @pytest.fixture
    def builder(self):
        return ContextBuilder()

    @pytest.fixture
    def game_state(self):
        return GameState(
            phase="day_1",
            round_number=1,
            living_players=[
                "Alice",
                "Bob",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
                "Grace",
                "Hector",
                "Ivy",
                "Jules",
            ],
            dead_players=[],
            nominated_players=[],
        )

    @pytest.fixture
    def memory(self):
        return PlayerMemory(facts={}, beliefs={})

    def test_build_context_includes_all_sections(
        self, builder, sample_persona, game_state, memory
    ):
        """Context includes all required sections."""
        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert "[YOUR IDENTITY]" in context
        assert "[GAME RULES]" in context
        assert "[CURRENT STATE]" in context
        assert "[TRANSCRIPT]" in context
        assert "[YOUR MEMORY]" in context
        assert "[YOUR TASK: SPEAK]" in context

    def test_context_includes_persona_info(
        self, builder, sample_persona, game_state, memory
    ):
        """Context includes persona details."""
        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert sample_persona.identity.name in context
        assert sample_persona.identity.background in context
        assert sample_persona.play_style.voice in context

    def test_mafia_context_includes_partner(
        self, builder, sample_persona, game_state, memory
    ):
        """Mafia players see partner info."""
        context = builder.build_context(
            player_name="Alice",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
            extra={"partners": ["Bob", "Charlie"]},
        )

        assert "[MAFIA INFO]" in context
        assert "Your partners are: Bob, Charlie" in context

    def test_action_prompts_differ_by_type(
        self, builder, sample_persona, game_state, memory
    ):
        """Different action types get different prompts."""
        speak_context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        vote_context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.VOTE,
        )

        assert "[YOUR TASK: SPEAK]" in speak_context
        assert "[YOUR TASK: VOTE]" in vote_context
        assert "nomination" in speak_context.lower()
        assert "vote" in vote_context.lower()

    def test_night_kill_shows_valid_targets(
        self, builder, sample_persona, game_state, memory
    ):
        """Night kill prompt shows valid targets (excluding self)."""
        context = builder.build_context(
            player_name="Alice",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.NIGHT_KILL,
            extra={"partners": ["Bob", "Charlie"]},
        )

        assert "[YOUR TASK: MAFIA NIGHT KILL]" in context
        # Should list targets excluding Alice
        targets_line = context.split("Valid targets:")[1].split("\n")[0]
        assert "Alice" not in targets_line
        # Should list targets excluding partners
        assert "Bob" not in targets_line
        assert "Charlie" not in targets_line

    def test_vote_prompt_does_not_duplicate_skip(
        self, builder, sample_persona, game_state, memory
    ):
        """Vote prompt doesn't show duplicate skip when no nominations."""
        game_state.nominated_players = []

        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.VOTE,
        )

        assert "skip, skip" not in context

    def test_transcript_renders_full_rounds(self, builder, sample_persona, memory):
        """Full round transcripts show complete speeches."""
        from src.schemas import DayRoundTranscript

        transcript = [
            DayRoundTranscript(
                round_number=1,
                night_kill=None,
                last_words=None,
                speeches=[
                    Speech(speaker="Alice", text="Hello everyone", nomination="Bob"),
                    Speech(speaker="Bob", text="I'm innocent", nomination="Alice"),
                ],
                votes={"Alice": "Bob", "Bob": "Alice"},
                vote_outcome="no_elimination",
            )
        ]

        game_state = GameState(
            phase="day_2",
            round_number=2,
            living_players=["Alice", "Bob", "Charlie"],
            dead_players=[],
            nominated_players=[],
        )

        context = builder.build_context(
            player_name="Charlie",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=transcript,
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert "Day 1 (full)" in context
        assert 'Alice: "Hello everyone"' in context
        assert 'Bob: "I\'m innocent"' in context
        assert "Nominated: Bob" in context

    def test_transcript_renders_compressed_rounds(self, builder, sample_persona, memory):
        """Compressed rounds show summaries."""
        from src.schemas import CompressedRoundSummary

        transcript = [
            CompressedRoundSummary(
                round_number=1,
                night_death=None,
                vote_death="Bob",
                vote_result="eliminated:Bob",
                vote_line="Alice->Bob, Charlie->Bob",
                defense_note="Defense: yes (tie -> revote)",
            )
        ]

        game_state = GameState(
            phase="day_3",
            round_number=3,
            living_players=["Alice", "Charlie"],
            dead_players=["Bob"],
            nominated_players=[],
        )

        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=transcript,
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert "Day 1 (summary)" in context
        assert "Vote elimination: Bob" in context
        assert "Votes: Alice->Bob, Charlie->Bob" in context
        assert "Defense: yes (tie -> revote)" in context

    def test_memory_renders_to_json(self, builder, sample_persona, game_state):
        """Memory section shows facts and beliefs as JSON."""
        memory = PlayerMemory(
            facts={"speeches_heard": ["Alice spoke first"]},
            beliefs={"suspicions": {"Bob": "very suspicious"}},
        )

        context = builder.build_context(
            player_name="Charlie",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert "[YOUR MEMORY]" in context
        assert "speeches_heard" in context
        assert "very suspicious" in context

    def test_defense_context_section(self, builder, sample_persona, game_state, memory):
        """Defense context shows tied players, vote counts, and votes."""
        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.DEFENSE,
            extra={
                "defense_context": {
                    "tied_players": ["Alice", "Bob"],
                    "vote_counts": {"Alice": 2, "Bob": 2},
                    "votes": {"Charlie": "Alice", "Diana": "Bob"},
                }
            },
        )

        assert "[DEFENSE CONTEXT]" in context
        assert "Tied players: Alice, Bob" in context
        assert "Alice:2" in context
        assert "Bob:2" in context
        assert "Charlie->Alice" in context

    def test_detective_empty_results(self, builder, sample_persona, game_state, memory):
        """Detective with no results shows appropriate message."""
        context = builder.build_context(
            player_name="Alice",
            role="detective",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        assert "[YOUR MEMORY]" in context
        assert "Fact summary: None yet." in context

    def test_mafia_dead_partner(self, builder, sample_persona, game_state, memory):
        """Mafia context lists partners."""
        context = builder.build_context(
            player_name="Alice",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
            extra={"partners": ["Bob", "Charlie"]},
        )

        assert "[MAFIA INFO]" in context
        assert "Your partners are: Bob, Charlie" in context

    def test_investigation_prompt(self, builder, sample_persona, game_state, memory):
        """Investigation prompt shows valid targets excluding self."""
        context = builder.build_context(
            player_name="Alice",
            role="detective",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.INVESTIGATION,
        )

        assert "[YOUR TASK: DETECTIVE INVESTIGATION]" in context
        assert "Choose someone to investigate" in context
        # Should exclude self from targets
        targets_section = context.split("Valid targets:")[1].split("\n")[0]
        assert "Alice" not in targets_section

    def test_last_words_prompt(self, builder, sample_persona, game_state, memory):
        """Last words prompt shows appropriate instructions."""
        context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.LAST_WORDS,
        )

        assert "[YOUR TASK: LAST WORDS]" in context
        assert "eliminated from the game" in context
        assert "final statement" in context


class TestNightZeroPrompt:
    """Tests for Night Zero coordination prompt."""

    @pytest.fixture
    def builder(self):
        return ContextBuilder()

    @pytest.fixture
    def game_state(self):
        return GameState(
            phase="night_zero",
            round_number=0,
            living_players=[
                "Alice",
                "Bob",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
                "Grace",
                "Hector",
                "Ivy",
                "Jules",
            ],
            dead_players=[],
            nominated_players=[],
        )

    @pytest.fixture
    def memory(self):
        return PlayerMemory(facts={}, beliefs={})

    def test_night_zero_prompt_first_mafia(
        self, builder, sample_persona, game_state, memory
    ):
        """First Mafia gets Night Zero coordination prompt without partner strategy."""
        context = builder.build_context(
            player_name="Alice",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
            extra={"night_zero": True},
        )

        assert "[YOUR TASK: NIGHT ZERO COORDINATION]" in context
        assert "No kill tonight" in context
        assert "Share your initial strategy" in context
        assert "nomination" in context.lower()  # Tells LLM nomination is unused
        # Should NOT have partner's strategy section
        assert "Your partners shared their strategies" not in context

    def test_night_zero_prompt_second_mafia_sees_partner(
        self, builder, sample_persona, game_state, memory
    ):
        """Second Mafia sees partner's strategy in Night Zero prompt."""
        context = builder.build_context(
            player_name="Bob",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
            extra={
                "partners": ["Alice", "Charlie"],
                "night_zero": True,
                "partner_strategies": {
                    "Alice": "Let's use signal words and target quiet players"
                },
            },
        )

        assert "[YOUR TASK: NIGHT ZERO COORDINATION]" in context
        assert "Your partners shared their strategies" in context
        assert "Let's use signal words and target quiet players" in context
        assert "Now share YOUR strategy" in context

    def test_night_zero_flag_uses_different_prompt_than_speak(
        self, builder, sample_persona, game_state, memory
    ):
        """Night Zero flag causes different prompt than regular SPEAK."""
        # Regular SPEAK (day phase)
        day_state = GameState(
            phase="day_1",
            round_number=1,
            living_players=["Alice", "Bob", "Charlie"],
            dead_players=[],
            nominated_players=[],
        )
        regular_context = builder.build_context(
            player_name="Alice",
            role="town",
            persona=sample_persona,
            game_state=day_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
        )

        # Night Zero SPEAK
        night_zero_context = builder.build_context(
            player_name="Alice",
            role="mafia",
            persona=sample_persona,
            game_state=game_state,
            transcript=[],
            memory=memory,
            action_type=ActionType.SPEAK,
            extra={"partners": ["Bob", "Charlie"], "night_zero": True},
        )

        # Regular speak has [YOUR TASK: SPEAK], Night Zero has different
        assert "[YOUR TASK: SPEAK]" in regular_context
        assert "[YOUR TASK: NIGHT ZERO COORDINATION]" in night_zero_context
        assert "[YOUR TASK: SPEAK]" not in night_zero_context


class TestTranscriptFullMode:
    @pytest.fixture
    def manager(self):
        return TranscriptManager()

    def test_full_mode_returns_uncompressed(self, manager):
        """full=True returns all rounds uncompressed."""
        # Add 3 rounds
        for i in range(1, 4):
            manager.add_speech(f"Player{i}", "Speech text", f"Player{i+1}")
            manager.finalize_round(
                round_number=i,
                night_kill=None if i == 1 else f"Player{i-1}",
                votes={f"Player{i}": "skip"},
                vote_outcome="no_elimination",
            )

        # Get transcript with full=True
        transcript = manager.get_transcript_for_player(current_round=3, full=True)

        # All rounds should be DayRoundTranscript (not compressed)
        for item in transcript:
            assert hasattr(item, "speeches"), "Expected full transcript, got compressed"
