"""Transcript schemas for game history."""

from __future__ import annotations

from pydantic import BaseModel


class Speech(BaseModel):
    """Single speech in discussion."""

    speaker: str
    text: str
    nomination: str


class DayRoundTranscript(BaseModel):
    """
    Full detail transcript for a day round.

    A "round" = one Day phase, includes preceding night's outcome.
    Round 1 = Day 1 (no night kill), Round 2 = Day 2 (includes Night 1 kill), etc.
    """

    round_number: int
    night_kill: str | None  # Who died preceding night, or None
    last_words: str | None  # Killed player's last words
    speeches: list[Speech]
    votes: dict[str, str]  # player -> target or "skip"
    vote_outcome: str  # "eliminated:{name}", "no_elimination", "revote"
    defense_speeches: list[Speech] | None = None  # If revote
    revote: dict[str, str] | None = None
    revote_outcome: str | None = None


class CompressedRoundSummary(BaseModel):
    """Compressed summary for older rounds (2+ rounds ago)."""

    round_number: int
    night_death: str | None
    vote_death: str | None
    accusations: list[str]
    vote_result: str
    claims: list[str]


# Type alias for transcript (mix of full and compressed rounds)
Transcript = list[DayRoundTranscript | CompressedRoundSummary]
