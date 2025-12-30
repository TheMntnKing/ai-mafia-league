"""Game engine: loop, rules, state management."""

from src.engine.events import EventLog
from src.engine.state import GameStateManager
from src.engine.transcript import TranscriptManager
from src.engine.voting import VoteResolver, VoteResult

# Note: GameConfig, GameResult, GameRunner, run_game are NOT imported here
# to avoid circular imports with src.players.agent.
# Import them directly from src.engine.game when needed.
# Phases are also kept out for the same reason.

__all__ = [
    "EventLog",
    "GameStateManager",
    "TranscriptManager",
    "VoteResolver",
    "VoteResult",
]
