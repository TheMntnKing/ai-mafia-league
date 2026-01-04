"""Initial personas for AI Mafia games."""

from __future__ import annotations

from src.personas.ballerina_cappuccina import create_persona as create_ballerina_cappuccina
from src.personas.cappuccino_assassino import create_persona as create_cappuccino_assassino
from src.personas.gigachad import create_persona as create_gigachad
from src.personas.machiavelli import create_persona as create_machiavelli
from src.personas.patapim import create_persona as create_patapim
from src.personas.sherlock_holmes import create_persona as create_sherlock_holmes
from src.personas.sun_tzu import create_persona as create_sun_tzu
from src.personas.tralalero import create_persona as create_tralalero
from src.personas.tung_tung_tung_sahur import (
    create_persona as create_tung_tung_tung_sahur,
)
from src.personas.yagami_light import create_persona as create_yagami_light
from src.schemas import Persona


def get_personas() -> dict[str, Persona]:
    """
    Get the current persona roster for a game.

    Returns:
        Dict mapping player name to Persona
    """
    return {
        "Ballerina Cappuccina": create_ballerina_cappuccina(),
        "Cappuccino Assassino": create_cappuccino_assassino(),
        "Gigachad": create_gigachad(),
        "Machiavelli": create_machiavelli(),
        "Brr Brr Patapim": create_patapim(),
        "Sherlock Holmes": create_sherlock_holmes(),
        "Sun Tzu": create_sun_tzu(),
        "Tralalero Tralala": create_tralalero(),
        "Tung Tung Tung Sahur": create_tung_tung_tung_sahur(),
        "Yagami Light": create_yagami_light(),
    }
