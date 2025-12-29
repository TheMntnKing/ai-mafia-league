"""Transcript management with 2-round window compression."""

from __future__ import annotations

from src.schemas import (
    CompressedRoundSummary,
    DayRoundTranscript,
    DefenseSpeech,
    Speech,
    Transcript,
)


class TranscriptManager:
    """
    Manages game transcript with 2-round window.

    - Current and previous round: full detail
    - Older rounds: compressed summaries
    """

    def __init__(self):
        """Initialize empty transcript manager."""
        self.rounds: list[DayRoundTranscript] = []
        self.current_speeches: list[Speech] = []
        self.current_round_number: int | None = None
        self.current_night_kill: str | None = None
        self.current_last_words: str | None = None

    def start_round(
        self,
        round_number: int,
        night_kill: str | None,
    ) -> None:
        """
        Set current round context before discussion starts.

        Args:
            round_number: The current day round number
            night_kill: Who died the preceding night (None for day 1)
        """
        self.current_round_number = round_number
        self.current_night_kill = night_kill
        self.current_last_words = None  # Night kills have no last words

    def add_speech(self, speaker: str, text: str, nomination: str) -> None:
        """
        Add a speech to the current round.

        Args:
            speaker: Name of the speaking player
            text: Speech content
            nomination: Who they nominated
        """
        self.current_speeches.append(
            Speech(speaker=speaker, text=text, nomination=nomination)
        )

    def get_current_speeches(self) -> list[Speech]:
        """Get speeches from current (in-progress) round."""
        return self.current_speeches.copy()

    def get_transcript_for_player(
        self, current_round: int, full: bool = False
    ) -> Transcript:
        """
        Get transcript with 2-round window.

        - Current and previous round: full detail
        - Older rounds: compressed summaries

        Args:
            current_round: The current round number
            full: If True, return full transcripts for all rounds

        Returns:
            List of full transcripts and compressed summaries
        """
        result: Transcript = []

        if full:
            result.extend(self.rounds)
        else:
            for round_transcript in self.rounds:
                if round_transcript.round_number >= current_round - 1:
                    # Full detail for current and previous round
                    result.append(round_transcript)
                else:
                    # Compress older rounds
                    result.append(self._compress_round(round_transcript))

        if self._has_current_round():
            result.append(self._build_live_round(current_round))

        return result

    def _compress_round(
        self, round_t: DayRoundTranscript
    ) -> CompressedRoundSummary:
        """
        Extract key information from old round.

        Uses simple heuristics (keyword matching) to identify:
        - Major accusations
        - Role claims

        Args:
            round_t: Full round transcript to compress

        Returns:
            Compressed summary
        """
        accusations = []
        claims = []

        for speech in round_t.speeches:
            text_lower = speech.text.lower()

            # Simple heuristic: look for accusation patterns
            accusation_keywords = ["mafia", "suspect", "suspicious", "vote out", "eliminate"]
            if any(kw in text_lower for kw in accusation_keywords):
                accusations.append(f"{speech.speaker} accused {speech.nomination}")

            # Simple heuristic: look for role claims
            claim_keywords = ["i am", "i'm the", "detective", "investigated", "town"]
            if any(kw in text_lower for kw in claim_keywords):
                # Check if they're claiming a role
                if "detective" in text_lower or "investigated" in text_lower:
                    claims.append(f"{speech.speaker} claimed Detective")
                elif "town" in text_lower and ("i am" in text_lower or "i'm" in text_lower):
                    claims.append(f"{speech.speaker} claimed Town")

        # Determine vote death
        vote_death = None
        if round_t.vote_outcome.startswith("eliminated:"):
            vote_death = round_t.vote_outcome.split(":")[1]
        elif round_t.revote_outcome and round_t.revote_outcome.startswith("eliminated:"):
            vote_death = round_t.revote_outcome.split(":")[1]

        return CompressedRoundSummary(
            round_number=round_t.round_number,
            night_death=round_t.night_kill,
            vote_death=vote_death,
            accusations=accusations,
            vote_result=round_t.revote_outcome or round_t.vote_outcome,
            claims=claims,
        )

    def _has_current_round(self) -> bool:
        """Return True if a current round is in progress."""
        return self.current_round_number is not None

    def _build_live_round(self, fallback_round: int) -> DayRoundTranscript:
        """Build an in-progress round transcript."""
        round_number = self.current_round_number or fallback_round
        return DayRoundTranscript(
            round_number=round_number,
            night_kill=self.current_night_kill,
            last_words=self.current_last_words,
            speeches=self.current_speeches.copy(),
            votes={},
            vote_outcome="pending",
        )

    def clear(self) -> None:
        """Clear all transcript data."""
        self.rounds = []
        self.current_speeches = []
        self.current_round_number = None
        self.current_night_kill = None
        self.current_last_words = None

    def get_full_transcript(self) -> list[dict]:
        """Get all rounds as dicts for serialization."""
        return [r.model_dump() for r in self.rounds]

    def finalize_round(
        self,
        round_number: int,
        night_kill: str | None,
        votes: dict[str, str],
        vote_outcome: str,
        last_words: str | None = None,
        defense_speeches: list[DefenseSpeech] | None = None,
        revote: dict[str, str] | None = None,
        revote_outcome: str | None = None,
    ) -> DayRoundTranscript:
        """
        Complete current round and start new one.

        Args:
            round_number: The round being finalized
            night_kill: Who died the preceding night (None for day 1)
            votes: Dict of voter -> target or "skip"
            vote_outcome: "eliminated:{name}", "no_elimination", or "revote"
            last_words: Last words for day elimination (None for night kills or no elim)
            defense_speeches: Defense speeches if revote occurred
            revote: Revote results if applicable
            revote_outcome: Final outcome after revote

        Returns:
            The completed DayRoundTranscript
        """
        transcript = DayRoundTranscript(
            round_number=round_number,
            night_kill=night_kill,
            last_words=last_words,
            speeches=self.current_speeches.copy(),
            votes=votes,
            vote_outcome=vote_outcome,
            defense_speeches=defense_speeches,
            revote=revote,
            revote_outcome=revote_outcome,
        )
        self.rounds.append(transcript)
        self.current_speeches = []
        self.current_round_number = None
        self.current_night_kill = None
        self.current_last_words = None
        return transcript
