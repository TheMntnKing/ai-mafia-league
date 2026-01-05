"""Pytest fixtures for AI Mafia Agent League tests."""

import pytest

from src.schemas import (
    GameState,
    Persona,
    PersonaIdentity,
    PlayerMemory,
    PlayStyle,
    RoleTactics,
)
@pytest.fixture
def sample_game_state() -> GameState:
    """Sample game state for testing."""
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
def sample_game_state_mid_game() -> GameState:
    """Mid-game state with some deaths."""
    return GameState(
        phase="day_3",
        round_number=3,
        living_players=["Alice", "Charlie", "Diana", "Eve", "Grace", "Hector", "Ivy"],
        dead_players=["Bob", "Frank", "Jules"],
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
        play_style=PlayStyle(
            voice="Direct and methodical, with a calm and factual tone.",
            approach=(
                "Leans on evidence, builds cases carefully, and defends with clear rebuttals. "
                "Conservative with risk and slow to accuse without support."
            ),
            signature_phrases=["Let's examine the facts"],
            signature_moves=["Summarizes voting patterns before speaking"],
        ),
        tactics=RoleTactics(
            town=[
                "Gather information before nominating.",
                "Test claims with follow-up questions.",
            ],
            mafia=[
                "Use credibility to steer suspicion elsewhere.",
                "Avoid over-explaining when pressured.",
            ],
            detective=[
                "Investigate the least consistent players first.",
                "Reveal only when it flips a vote.",
            ],
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
            "strategy": "find the Mafia",
        },
    )


@pytest.fixture
def empty_memory() -> PlayerMemory:
    """Empty player memory for start of game."""
    return PlayerMemory(facts={}, beliefs={})


@pytest.fixture
def seven_personas() -> list[Persona]:
    """Ten distinct personas for a full game."""
    names = [
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
    ]
    traits_list = [
        ["analytical", "cautious", "patient"],
        ["aggressive", "confident", "blunt"],
        ["diplomatic", "observant", "calm"],
        ["emotional", "loyal", "reactive"],
        ["strategic", "calculating", "quiet"],
        ["charismatic", "persuasive", "bold"],
        ["skeptical", "independent", "direct"],
        ["methodical", "reserved", "precise"],
        ["curious", "empathetic", "steady"],
        ["blunt", "decisive", "pragmatic"],
    ]
    styles = [
        ("Methodical", "logical"),
        ("Direct", "intuitive"),
        ("Diplomatic", "pattern-based"),
        ("Emotional", "reactive"),
        ("Strategic", "calculating"),
        ("Charismatic", "persuasive"),
        ("Skeptical", "contrarian"),
        ("Reserved", "careful"),
        ("Empathetic", "observant"),
        ("Blunt", "decisive"),
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
                play_style=PlayStyle(
                    voice=f"{styles[i][0]} and clear",
                    approach=(
                        f"{styles[i][1]} analysis with balanced risk; accuses carefully "
                        "and defends with calm denials."
                    ),
                ),
                tactics=RoleTactics(
                    town=["Ask pointed questions", "Build cases before voting"],
                    mafia=["Blend in with the group", "Avoid leading early"],
                    detective=["Investigate quiet players", "Reveal with leverage"],
                ),
            )
        )
    return personas
