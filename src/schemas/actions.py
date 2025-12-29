"""
Schema-Guided Reasoning (SGR) output schemas for player actions.

Field order matters: earlier fields become context for later fields.
Flow: observe → analyze → strategize → decide → output
"""

from __future__ import annotations

from pydantic import BaseModel


class BaseThinking(BaseModel):
    """Common reasoning fields for all actions."""

    # Observation
    new_events: list[str]
    notable_changes: list[str]

    # Analysis
    suspicion_updates: dict[str, str]  # player -> assessment
    pattern_notes: list[str]

    # Strategy
    current_goal: str
    reasoning: str


class SpeakingOutput(BaseThinking):
    """Day phase: speaking turn."""

    information_to_share: list[str]
    information_to_hide: list[str]
    speech: str
    nomination: str


class VotingOutput(BaseThinking):
    """Day phase: voting."""

    vote_reasoning: str
    vote: str  # player name or "skip"


class NightKillOutput(BaseThinking):
    """Night phase: Mafia kill target."""

    target_reasoning: str
    target: str  # player name or "skip"


class InvestigationOutput(BaseThinking):
    """Night phase: Detective investigation."""

    target_reasoning: str
    target: str  # player name


class LastWordsOutput(BaseModel):
    """Eliminated player's final statement."""

    text: str


class DefenseOutput(BaseModel):
    """Revote: defense speech."""

    text: str
