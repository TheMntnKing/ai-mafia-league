"""Initial personas for AI Mafia games."""

from __future__ import annotations

from src.personas.alice import create_persona as create_alice
from src.personas.bob import create_persona as create_bob
from src.personas.bombardiro import create_persona as create_bombardiro
from src.personas.charlie import create_persona as create_charlie
from src.personas.diana import create_persona as create_diana
from src.personas.eve import create_persona as create_eve
from src.personas.tralalero import create_persona as create_tralalero
from src.schemas import Persona


def get_personas() -> dict[str, Persona]:
    """
    Get the 7 player personas for a game.

    Returns:
        Dict mapping player name to Persona
    """
    return {
        "Alice": create_alice(),
        "Bob": create_bob(),
        "Charlie": create_charlie(),
        "Diana": create_diana(),
        "Eve": create_eve(),
        "Bombardiro Crocodilo": create_bombardiro(),
        "Tralalero Tralala": create_tralalero(),
    }
