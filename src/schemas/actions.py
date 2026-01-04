"""
Schema-Guided Reasoning (SGR) output schemas for player actions.

Field order matters: earlier fields become context for later fields.
Flow: observe → analyze → strategize → decide → output
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BaseThinking(BaseModel):
    """Common reasoning fields for all actions."""

    observations: str = Field(
        description="Public facts from this phase only (no speculation)."
    )
    suspicions: str = Field(
        description="Persistent suspicions/leans with brief reasons (update, do not reset)."
    )
    strategy: str = Field(
        description="Ongoing plan/tactics for upcoming actions (update, do not reset)."
    )
    reasoning: str = Field(
        description=(
            "Internal monologue tying observations to strategy (not a speech rewrite)."
        )
    )


class SpeakingOutput(BaseThinking):
    """Day phase: speaking turn."""

    speech: str = Field(description="Public day speech in persona voice.")
    nomination: str = Field(
        description="Nominated player name (or 'skip' on Day 1)."
    )


class VotingOutput(BaseThinking):
    """Day phase: voting."""

    vote: str = Field(description="Vote target (nominated player name or 'skip').")


class NightKillOutput(BaseThinking):
    """Night phase: Mafia kill target."""

    message: str = Field(
        description="Private Mafia-only message to partners (not public speech)."
    )
    target: str = Field(description="Kill target player name or 'skip'.")


class InvestigationOutput(BaseThinking):
    """Night phase: Detective investigation."""

    target: str = Field(description="Investigation target player name.")


class DoctorProtectOutput(BaseThinking):
    """Night phase: Doctor protection."""

    target: str = Field(description="Protection target player name (can be self).")


class LastWordsOutput(BaseModel):
    """Eliminated player's final statement."""

    reasoning: str = Field(
        description="Private final monologue (not public speech)."
    )
    text: str = Field(description="Final public message.")


class DefenseOutput(BaseModel):
    """Revote: defense speech."""

    reasoning: str = Field(
        description="Private defense monologue (not public speech)."
    )
    text: str = Field(description="Defense speech delivered publicly.")
