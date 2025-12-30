"""Tests for schema definitions."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    ActionType,
    CompressedRoundSummary,
    DayRoundTranscript,
    DefenseOutput,
    DefenseSpeech,
    Event,
    GameState,
    InvestigationOutput,
    LastWordsOutput,
    NightKillOutput,
    PersonaIdentity,
    PlayerResponse,
    SpeakingOutput,
    Speech,
    VotingOutput,
)


class TestActionType:
    def test_action_types_exist(self):
        """All expected action types are defined."""
        assert ActionType.SPEAK == "speak"
        assert ActionType.VOTE == "vote"
        assert ActionType.DEFENSE == "defense"
        assert ActionType.LAST_WORDS == "last_words"
        assert ActionType.NIGHT_KILL == "night_kill"
        assert ActionType.INVESTIGATION == "investigation"


class TestGameState:
    def test_create_game_state(self, sample_game_state):
        """GameState can be created with valid data."""
        assert sample_game_state.phase == "day_1"
        assert sample_game_state.round_number == 1
        assert len(sample_game_state.living_players) == 7

    def test_game_state_validation(self):
        """GameState validates required fields."""
        with pytest.raises(ValidationError):
            GameState()  # Missing required fields


class TestPlayerMemory:
    def test_create_memory(self, sample_memory):
        """PlayerMemory stores facts and beliefs."""
        assert "round_1_speeches" in sample_memory.facts
        assert "suspicions" in sample_memory.beliefs

    def test_empty_memory(self, empty_memory):
        """Empty memory is valid."""
        assert empty_memory.facts == {}
        assert empty_memory.beliefs == {}


class TestPlayerResponse:
    def test_create_response(self, sample_memory):
        """PlayerResponse contains output and updated memory."""
        response = PlayerResponse(
            output={"speech": "Hello", "nomination": "Bob"},
            updated_memory=sample_memory,
        )
        assert response.output["speech"] == "Hello"
        assert response.updated_memory == sample_memory


class TestEvent:
    def test_create_event(self):
        """Event can be created with type, timestamp, and data."""
        event = Event(
            type="speech",
            timestamp="2024-01-01T00:00:00Z",
            data={"speaker": "Alice", "text": "Hello"},
        )
        assert event.type == "speech"
        assert event.private_fields == []

    def test_event_with_private_fields(self):
        """Event can specify private fields."""
        event = Event(
            type="speech",
            timestamp="2024-01-01T00:00:00Z",
            data={"speaker": "Alice", "text": "Hello", "reasoning": "secret"},
            private_fields=["reasoning"],
        )
        assert event.private_fields == ["reasoning"]


class TestPersona:
    def test_create_persona(self, sample_persona):
        """Persona can be created with identity and behavior."""
        assert sample_persona.identity.name == "Test Player"
        assert len(sample_persona.identity.core_traits) == 3

    def test_persona_requires_min_traits(self):
        """Persona identity requires at least 3 core traits."""
        with pytest.raises(ValidationError):
            PersonaIdentity(
                name="Test",
                background="Test background",
                core_traits=["one", "two"],  # Only 2 traits
            )

    def test_persona_max_traits(self):
        """Persona identity allows up to 5 core traits."""
        identity = PersonaIdentity(
            name="Test",
            background="Test background",
            core_traits=["one", "two", "three", "four", "five"],
        )
        assert len(identity.core_traits) == 5

    def test_persona_too_many_traits(self):
        """Persona identity rejects more than 5 traits."""
        with pytest.raises(ValidationError):
            PersonaIdentity(
                name="Test",
                background="Test background",
                core_traits=["one", "two", "three", "four", "five", "six"],
            )

    def test_persona_with_role_guidance(self, sample_persona):
        """Persona can include role guidance."""
        assert sample_persona.role_guidance is not None
        assert sample_persona.role_guidance.town
        assert sample_persona.role_guidance.mafia
        assert sample_persona.role_guidance.detective


class TestTranscript:
    def test_create_speech(self):
        """Speech model captures speaker, text, and nomination."""
        speech = Speech(speaker="Alice", text="I suspect Bob", nomination="Bob")
        assert speech.speaker == "Alice"
        assert speech.nomination == "Bob"

    def test_create_day_transcript(self):
        """DayRoundTranscript captures a full day's events."""
        transcript = DayRoundTranscript(
            round_number=1,
            night_kill=None,
            last_words=None,
            speeches=[Speech(speaker="Alice", text="Hello", nomination="Bob")],
            votes={"Alice": "Bob", "Bob": "skip"},
            vote_outcome="no_elimination",
            defense_speeches=[DefenseSpeech(speaker="Bob", text="I'm innocent")],
        )
        assert transcript.round_number == 1
        assert len(transcript.speeches) == 1

    def test_create_compressed_summary(self):
        """CompressedRoundSummary captures key events."""
        summary = CompressedRoundSummary(
            round_number=1,
            night_death=None,
            vote_death="Charlie",
            accusations=["Alice accused Charlie"],
            vote_result="eliminated:Charlie",
            claims=[],
        )
        assert summary.vote_death == "Charlie"


class TestSGROutputs:
    def test_speaking_output(self):
        """SpeakingOutput captures full reasoning chain."""
        output = SpeakingOutput(
            observations="Day 1 started with no night kill.",
            suspicions="Bob is slightly suspicious.",
            strategy="Stay cautious and gather information.",
            reasoning="No strong reads yet.",
            speech="Hello everyone, let's discuss.",
            nomination="Bob",
        )
        assert output.speech == "Hello everyone, let's discuss."
        assert output.nomination == "Bob"

    def test_voting_output(self):
        """VotingOutput captures vote with reasoning."""
        output = VotingOutput(
            observations="Discussion complete; Bob seemed nervous.",
            suspicions="Bob is highly suspicious and avoided questions.",
            strategy="Eliminate the top suspect.",
            reasoning="Bob's deflection indicates guilt.",
            vote="Bob",
        )
        assert output.vote == "Bob"

    def test_night_kill_output(self):
        """NightKillOutput captures target selection."""
        output = NightKillOutput(
            observations="Night 1 after a tense Day 1.",
            suspicions="Alice is dangerous and influential.",
            strategy="Reduce town leadership.",
            reasoning="Eliminate the strongest town voice.",
            target="Alice",
        )
        assert output.target == "Alice"

    def test_investigation_output(self):
        """InvestigationOutput captures investigation target."""
        output = InvestigationOutput(
            observations="Night 1 with unclear alignments.",
            suspicions="Bob is evasive.",
            strategy="Gather info to find Mafia.",
            reasoning="Bob was evasive and needs checking.",
            target="Bob",
        )
        assert output.target == "Bob"

    def test_last_words_output(self):
        """LastWordsOutput captures final statement."""
        output = LastWordsOutput(
            reasoning="Warn town about my strongest suspicion.",
            text="I was town. Watch Alice.",
        )
        assert "town" in output.text

    def test_defense_output(self):
        """DefenseOutput captures defense statement."""
        output = DefenseOutput(
            reasoning="Refute the case and point to voting record.",
            text="I'm not mafia. Check my votes.",
        )
        assert "votes" in output.text
