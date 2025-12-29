"""JSON game log persistence."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from src.schemas import Event


@dataclass
class PlayerEntry:
    """Player information for game log."""

    seat: int
    persona_id: str
    name: str
    role: str  # "mafia", "detective", "town"
    outcome: str  # "survived", "eliminated", "killed"


class GameLogWriter:
    """
    Writes complete game logs to JSON files.

    Format follows schema version 1.0 from docs/schemas.py.
    Includes full event history with private reasoning for viewers.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize log writer.

        Args:
            log_dir: Directory for game logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        game_id: str,
        timestamp_start: str,
        timestamp_end: str,
        winner: str,
        players: list[PlayerEntry],
        events: list[Event],
    ) -> Path:
        """
        Write complete game log to JSON file.

        Args:
            game_id: Unique game identifier
            timestamp_start: ISO8601 game start time
            timestamp_end: ISO8601 game end time
            winner: "town" or "mafia"
            players: List of player entries with roles and outcomes
            events: Full event log (including private data)

        Returns:
            Path to the written log file
        """
        log_data = {
            "schema_version": self.SCHEMA_VERSION,
            "game_id": game_id,
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "winner": winner,
            "players": [
                {
                    "seat": p.seat,
                    "persona_id": p.persona_id,
                    "name": p.name,
                    "role": p.role,
                    "outcome": p.outcome,
                }
                for p in players
            ],
            "events": [e.model_dump() for e in events],
        }

        filepath = self.log_dir / f"game_{game_id}.json"
        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2)

        return filepath

    def read(self, game_id: str) -> dict | None:
        """
        Read a game log by ID.

        Args:
            game_id: Game identifier

        Returns:
            Game log dict or None if not found
        """
        filepath = self.log_dir / f"game_{game_id}.json"
        if not filepath.exists():
            return None

        with open(filepath) as f:
            return json.load(f)

    def list_games(self) -> list[str]:
        """List all game IDs in the log directory."""
        game_files = self.log_dir.glob("game_*.json")
        return [f.stem.replace("game_", "") for f in game_files]

    async def write_game_log(self, log_data: dict) -> str:
        """
        Write pre-built game log data to JSON file.

        This is a convenience method for when the log is already built.

        Args:
            log_data: Complete log data dict with game_id

        Returns:
            Path to the written log file as string
        """
        game_id = log_data.get("game_id", "unknown")
        filepath = self.log_dir / f"game_{game_id}.json"

        def _write() -> None:
            with open(filepath, "w") as f:
                json.dump(log_data, f, indent=2)

        await asyncio.to_thread(_write)
        return str(filepath)
