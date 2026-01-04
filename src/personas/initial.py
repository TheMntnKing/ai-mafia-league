"""Initial personas for AI Mafia games."""

from __future__ import annotations

from src.personas.bombardiro import create_persona as create_bombardiro
from src.personas.tralalero import create_persona as create_tralalero
from src.schemas import Persona


def get_personas() -> dict[str, Persona]:
    """
    Get the current persona roster for a game.

    Returns:
        Dict mapping player name to Persona
    """
    return {
        "Bombardiro Crocodilo": create_bombardiro(),
        "Tralalero Tralala": create_tralalero(),
    }
