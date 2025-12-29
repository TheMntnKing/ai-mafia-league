"""Schema definitions for AI Mafia Agent League."""

from src.schemas.actions import (
    BaseThinking,
    DefenseOutput,
    InvestigationOutput,
    LastWordsOutput,
    NightKillOutput,
    SpeakingOutput,
    VotingOutput,
)
from src.schemas.core import (
    ActionType,
    Event,
    GameState,
    PlayerMemory,
    PlayerResponse,
)
from src.schemas.persona import (
    Persona,
    PersonaIdentity,
    RoleGuidance,
    VoiceAndBehavior,
)
from src.schemas.transcript import (
    CompressedRoundSummary,
    DayRoundTranscript,
    Speech,
    Transcript,
)

__all__ = [
    # Core
    "ActionType",
    "Event",
    "GameState",
    "PlayerMemory",
    "PlayerResponse",
    # Actions
    "BaseThinking",
    "DefenseOutput",
    "InvestigationOutput",
    "LastWordsOutput",
    "NightKillOutput",
    "SpeakingOutput",
    "VotingOutput",
    # Transcript
    "CompressedRoundSummary",
    "DayRoundTranscript",
    "Speech",
    "Transcript",
    # Persona
    "Persona",
    "PersonaIdentity",
    "RoleGuidance",
    "VoiceAndBehavior",
]
