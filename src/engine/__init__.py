"""Game engine: loop, rules, state management."""

from src.engine.events import EventLog
from src.engine.game import GameConfig, GameResult, GameRunner, run_game
from src.engine.phases import DayPhase, NightPhase, NightZeroPhase
from src.engine.state import GameStateManager
from src.engine.transcript import TranscriptManager
from src.engine.voting import VoteResolver, VoteResult

__all__ = [
    "EventLog",
    "GameConfig",
    "GameResult",
    "GameRunner",
    "run_game",
    "DayPhase",
    "NightPhase",
    "NightZeroPhase",
    "GameStateManager",
    "TranscriptManager",
    "VoteResolver",
    "VoteResult",
]
