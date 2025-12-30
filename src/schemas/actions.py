"""
Schema-Guided Reasoning (SGR) output schemas for player actions.

Field order matters: earlier fields become context for later fields.
Flow: observe → analyze → strategize → decide → output
"""

from __future__ import annotations

from pydantic import BaseModel


class BaseThinking(BaseModel):
    """Common reasoning fields for all actions."""

    observations: str
    suspicions: str
    strategy: str
    reasoning: str


class SpeakingOutput(BaseThinking):
    """Day phase: speaking turn."""

    speech: str
    nomination: str


class VotingOutput(BaseThinking):
    """Day phase: voting."""

    vote: str  # player name or "skip"


class NightKillOutput(BaseThinking):
    """Night phase: Mafia kill target."""

    message: str
    target: str  # player name or "skip"


class InvestigationOutput(BaseThinking):
    """Night phase: Detective investigation."""

    target: str  # player name


class LastWordsOutput(BaseModel):
    """Eliminated player's final statement."""

    reasoning: str
    text: str


class DefenseOutput(BaseModel):
    """Revote: defense speech."""

    reasoning: str
    text: str
