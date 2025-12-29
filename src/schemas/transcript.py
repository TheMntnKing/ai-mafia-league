"""Transcript schemas for game history."""

from __future__ import annotations

from pydantic import BaseModel


class Speech(BaseModel):
    """Single speech in discussion."""

    speaker: str
    text: str
    nomination: str


class DefenseSpeech(BaseModel):
    """Defense speech during revote (no nomination)."""

    speaker: str
    text: str


class DayRoundTranscript(BaseModel):
    """
    Full detail transcript for a day round.

    A "round" = one Day phase, includes preceding night's outcome.
    Round 1 = Day 1 (no night kill), Round 2 = Day 2 (includes Night 1 kill), etc.

    Note: last_words is only populated for DAY eliminations (vote outcomes).
    Night kills are silent - victims have no last words. The last_words field
    will be None when night_kill is set.
    """

    round_number: int
    night_kill: str | None  # Who died preceding night (silent - no last words)
    last_words: str | None  # Last words from DAY elimination only (None for night kills)
    speeches: list[Speech]
    votes: dict[str, str]  # player -> target or "skip"
    # "eliminated:{name}", "no_elimination", "revote", or "pending" (in-progress)
    vote_outcome: str
    defense_speeches: list[DefenseSpeech] | None = None  # If revote
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
