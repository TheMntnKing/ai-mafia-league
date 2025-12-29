"""Pytest fixtures for AI Mafia Agent League tests."""

import pytest

from src.schemas import (
    GameState,
    Persona,
    PersonaIdentity,
    PlayerMemory,
    RoleGuidance,
    VoiceAndBehavior,
)
from src.storage.database import Database


@pytest.fixture
async def test_db(tmp_path):
    """Temporary database for testing."""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.connect()
    await db.initialize_schema()
    yield db
    await db.close()


@pytest.fixture
def sample_game_state() -> GameState:
    """Sample game state for testing."""
    return GameState(
        phase="day_1",
        round_number=1,
        living_players=["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"],
        dead_players=[],
        nominated_players=[],
    )


@pytest.fixture
def sample_game_state_mid_game() -> GameState:
    """Mid-game state with some deaths."""
    return GameState(
        phase="day_3",
        round_number=3,
        living_players=["Alice", "Charlie", "Diana", "Eve", "Grace"],
        dead_players=["Bob", "Frank"],
        nominated_players=["Alice", "Diana"],
    )


@pytest.fixture
def sample_persona() -> Persona:
    """Sample persona for testing."""
    return Persona(
        identity=PersonaIdentity(
            name="Test Player",
            background="A test persona created for unit testing purposes.",
            core_traits=["analytical", "cautious", "verbose"],
        ),
        voice_and_behavior=VoiceAndBehavior(
            speech_style="Direct and methodical",
            reasoning_style="Logical deduction based on evidence",
            accusation_style="Evidence-based, builds cases carefully",
            defense_style="Calm and factual rebuttals",
            trust_disposition="neutral",
            risk_tolerance="conservative",
            signature_phrases=["Let's examine the facts"],
            quirks=["Often pauses before speaking"],
        ),
        role_guidance=RoleGuidance(
            town="Focus on gathering information and finding inconsistencies.",
            mafia="Use analytical reputation as cover for misdirection.",
            detective="Methodically investigate suspicious players.",
        ),
    )


@pytest.fixture
def sample_memory() -> PlayerMemory:
    """Sample player memory for testing."""
    return PlayerMemory(
        facts={
            "round_1_speeches": ["Alice accused Bob", "Charlie defended Bob"],
            "votes": {"round_1": {"Alice": "Bob", "Bob": "skip"}},
        },
        beliefs={
            "suspicions": {"Bob": "slightly suspicious", "Charlie": "trustworthy"},
            "current_goal": "find the Mafia",
        },
    )


@pytest.fixture
def empty_memory() -> PlayerMemory:
    """Empty player memory for start of game."""
    return PlayerMemory(facts={}, beliefs={})


@pytest.fixture
def seven_personas() -> list[Persona]:
    """Seven distinct personas for a full game."""
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    traits_list = [
        ["analytical", "cautious", "patient"],
        ["aggressive", "confident", "blunt"],
        ["diplomatic", "observant", "calm"],
        ["emotional", "loyal", "reactive"],
        ["strategic", "calculating", "quiet"],
        ["charismatic", "persuasive", "bold"],
        ["skeptical", "independent", "direct"],
    ]
    styles = [
        ("Methodical", "logical"),
        ("Direct", "intuitive"),
        ("Diplomatic", "pattern-based"),
        ("Emotional", "reactive"),
        ("Strategic", "calculating"),
        ("Charismatic", "persuasive"),
        ("Skeptical", "contrarian"),
    ]

    personas = []
    for i, name in enumerate(names):
        personas.append(
            Persona(
                identity=PersonaIdentity(
                    name=name,
                    background=f"{name} is player {i + 1} in the game.",
                    core_traits=traits_list[i],
                ),
                voice_and_behavior=VoiceAndBehavior(
                    speech_style=f"{styles[i][0]} and clear",
                    reasoning_style=f"{styles[i][1]} analysis",
                    accusation_style="Evidence-based",
                    defense_style="Calm denial",
                    trust_disposition="neutral",
                    risk_tolerance="moderate",
                ),
            )
        )
    return personas
