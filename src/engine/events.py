"""Event logging for game history."""

from __future__ import annotations

from datetime import UTC, datetime

from src.schemas import Event


class EventLog:
    """
    Manages game events for both runtime context and persistence.

    During gameplay, events are used to build player context (filtered public view).
    After game ends, the full event log is saved to JSON with private reasoning
    for entertainment value.
    """

    def __init__(self, game_id: str | None = None):
        """Initialize empty event log."""
        import uuid

        self.game_id = game_id or str(uuid.uuid4())
        self.events: list[Event] = []

    def add(
        self, event_type: str, data: dict, private_fields: list[str] | None = None
    ) -> Event:
        """
        Add an event to the log.

        Args:
            event_type: Type of event (phase_start, speech, vote, etc.)
            data: Event-specific data
            private_fields: Fields in data to filter for public view

        Returns:
            The created Event
        """
        event = Event(
            type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            data=data,
            private_fields=private_fields or [],
        )
        self.events.append(event)
        return event

    def get_public_view(self, since_index: int = 0) -> list[Event]:
        """
        Get events with private fields filtered out.

        Args:
            since_index: Start from this event index

        Returns:
            List of events with private data removed
        """
        public_events = []
        for event in self.events[since_index:]:
            if event.private_fields and set(event.private_fields) >= set(event.data.keys()):
                continue
            public_data = {
                k: v for k, v in event.data.items() if k not in event.private_fields
            }
            public_events.append(
                Event(
                    type=event.type,
                    timestamp=event.timestamp,
                    data=public_data,
                    private_fields=[],
                )
            )
        return public_events

    def get_full_view(self) -> list[Event]:
        """
        Get all events with private data included.

        Used for persistence and viewer experience.
        """
        return self.events.copy()

    def get_full_view_since(self, since_index: int = 0) -> list[Event]:
        """Get full events since a given index."""
        return self.events[since_index:]

    def get_events_since_timestamp(self, since_timestamp: str) -> list[Event]:
        """Get events after a given ISO8601 timestamp."""
        normalized = (
            since_timestamp[:-1] + "+00:00"
            if since_timestamp.endswith("Z")
            else since_timestamp
        )
        since_dt = datetime.fromisoformat(normalized)
        return [
            event
            for event in self.events
            if datetime.fromisoformat(event.timestamp) > since_dt
        ]

    def get_events_of_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.type == event_type]

    def get_last_event(self) -> Event | None:
        """Get the most recent event."""
        return self.events[-1] if self.events else None

    def get_all_events(self) -> list[dict]:
        """Get all events as dicts for serialization."""
        return [e.model_dump() for e in self.events]

    # =========================================================================
    # Convenience methods for common event types
    # =========================================================================

    def add_phase_start(self, phase: str, round_number: int) -> Event:
        """Log start of a new phase."""
        return self.add(
            "phase_start",
            {"phase": phase, "round_number": round_number},
        )

    def add_speech(
        self, speaker: str, text: str, nomination: str, reasoning: dict
    ) -> Event:
        """
        Log a player's speech.

        Args:
            speaker: Name of the speaking player
            text: The speech content
            nomination: Who they nominated
            reasoning: Private reasoning (filtered from public view)
        """
        return self.add(
            "speech",
            {
                "speaker": speaker,
                "text": text,
                "nomination": nomination,
                "reasoning": reasoning,
            },
            private_fields=["reasoning"],
        )

    def add_vote(
        self,
        votes: dict[str, str],
        outcome: str,
        eliminated: str | None,
        vote_details: dict[str, dict] | None = None,
        revote: dict[str, str] | None = None,
        revote_outcome: str | None = None,
        revote_details: dict[str, dict] | None = None,
    ) -> Event:
        """
        Log voting results.

        Args:
            votes: Dict of voter -> target or "skip"
            outcome: "eliminated", "no_elimination", or "revote"
            eliminated: Name of eliminated player if any
            vote_details: Full per-voter output (private)
            revote: Revote ballot if a revote occurred
            revote_outcome: Final outcome after revote
            revote_details: Full per-voter revote output (private)
        """
        data: dict[str, object] = {
            "votes": votes,
            "outcome": outcome,
            "eliminated": eliminated,
        }
        private_fields: list[str] = []

        if vote_details:
            data["vote_details"] = vote_details
            private_fields.append("vote_details")

        if revote is not None:
            data["revote"] = revote
        if revote_outcome is not None:
            data["revote_outcome"] = revote_outcome
        if revote_details:
            data["revote_details"] = revote_details
            private_fields.append("revote_details")

        return self.add("vote", data, private_fields=private_fields)

    def add_night_kill(self, target: str | None, reasoning: dict) -> Event:
        """
        Log Mafia's night kill.

        Args:
            target: Name of killed player, or None if no kill
            reasoning: Private reasoning (filtered from public view)
        """
        return self.add(
            "night_kill",
            {"target": target, "reasoning": reasoning},
            private_fields=["reasoning"],
        )

    def add_investigation(
        self, target: str, result: str, reasoning: dict
    ) -> Event:
        """
        Log Detective's investigation.

        All fields are private - only Detective knows results.

        Args:
            target: Who was investigated
            result: "Mafia" or "Not Mafia"
            reasoning: Detective's reasoning
        """
        return self.add(
            "investigation",
            {"target": target, "result": result, "reasoning": reasoning},
            private_fields=["target", "result", "reasoning"],
        )

    def add_last_words(self, speaker: str, text: str) -> Event:
        """Log eliminated player's last words."""
        return self.add(
            "last_words",
            {"speaker": speaker, "text": text},
        )

    def add_defense(self, speaker: str, text: str) -> Event:
        """Log defense speech during revote."""
        return self.add(
            "defense",
            {"speaker": speaker, "text": text},
        )

    def add_game_end(self, winner: str, final_roles: dict[str, str]) -> Event:
        """
        Log game end.

        Args:
            winner: "town" or "mafia"
            final_roles: Dict of player name -> role
        """
        return self.add(
            "game_end",
            {"winner": winner, "final_roles": final_roles},
        )
