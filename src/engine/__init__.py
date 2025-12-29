"""Game engine: loop, rules, state management."""

from src.engine.events import EventLog
from src.engine.state import GameStateManager
from src.engine.transcript import TranscriptManager
from src.engine.voting import VoteResolver, VoteResult

# Note: GameConfig, GameResult, GameRunner, run_game are imported from src.engine.game
# directly to avoid circular imports with src.players.agent.
# Phases are also kept out to avoid the same issue.

__all__ = [
    "EventLog",
    "GameStateManager",
    "TranscriptManager",
    "VoteResolver",
    "VoteResult",
]
