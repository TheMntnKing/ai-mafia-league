"""Async SQLite database wrapper."""

from __future__ import annotations

import uuid
from pathlib import Path

import aiosqlite

from src.schemas import Persona


class Database:
    """Async SQLite wrapper for personas and games."""

    def __init__(self, db_path: str = "data/mafia.db"):
        self.db_path = Path(db_path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open database connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def initialize_schema(self, schema_path: str = "docs/database.sql") -> None:
        """Initialize database schema from SQL file."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        schema = schema_file.read_text()
        await self._connection.executescript(schema)
        await self._connection.commit()

    # =========================================================================
    # Persona CRUD
    # =========================================================================

    async def create_persona(self, persona: Persona) -> str:
        """Create a new persona and return its ID."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        # Enforce unique persona names
        cursor = await self._connection.execute(
            "SELECT 1 FROM personas WHERE name = ?",
            (persona.identity.name,),
        )
        if await cursor.fetchone():
            raise ValueError(f"Persona name already exists: {persona.identity.name}")

        persona_id = uuid.uuid4().hex
        definition = persona.model_dump_json()

        await self._connection.execute(
            "INSERT INTO personas (id, name, definition) VALUES (?, ?, ?)",
            (persona_id, persona.identity.name, definition),
        )
        await self._connection.commit()
        return persona_id

    async def get_persona(self, persona_id: str) -> Persona | None:
        """Get a persona by ID."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        cursor = await self._connection.execute(
            "SELECT definition FROM personas WHERE id = ?",
            (persona_id,),
        )
        row = await cursor.fetchone()
        if row:
            return Persona.model_validate_json(row["definition"])
        return None

    async def get_persona_by_name(self, name: str) -> Persona | None:
        """Get a persona by name."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        cursor = await self._connection.execute(
            "SELECT definition FROM personas WHERE name = ?",
            (name,),
        )
        row = await cursor.fetchone()
        if row:
            return Persona.model_validate_json(row["definition"])
        return None

    async def list_personas(self) -> list[Persona]:
        """List all personas."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        cursor = await self._connection.execute("SELECT definition FROM personas")
        rows = await cursor.fetchall()
        return [Persona.model_validate_json(row["definition"]) for row in rows]

    async def update_persona_stats(
        self, persona_id: str, games_played_delta: int = 0, wins_delta: int = 0
    ) -> None:
        """Update persona game statistics."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        await self._connection.execute(
            """
            UPDATE personas
            SET games_played = games_played + ?, wins = wins + ?
            WHERE id = ?
            """,
            (games_played_delta, wins_delta, persona_id),
        )
        await self._connection.commit()

    # =========================================================================
    # Game Records
    # =========================================================================

    async def record_game(
        self,
        game_id: str,
        winner: str,
        rounds: int,
        log_file: str,
        tournament_id: str | None = None,
    ) -> None:
        """Record a completed game."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        await self._connection.execute(
            """
            INSERT INTO games (id, tournament_id, timestamp, winner, rounds, log_file)
            VALUES (?, ?, datetime('now'), ?, ?, ?)
            """,
            (game_id, tournament_id, winner, rounds, log_file),
        )
        await self._connection.commit()

    async def record_game_player(
        self, game_id: str, persona_id: str, role: str, outcome: str
    ) -> None:
        """Record a player's participation in a game."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        await self._connection.execute(
            """
            INSERT INTO game_players (game_id, persona_id, role, outcome)
            VALUES (?, ?, ?, ?)
            """,
            (game_id, persona_id, role, outcome),
        )
        await self._connection.commit()

    async def list_games(self, limit: int | None = None) -> list[dict]:
        """List game records, optionally limited to most recent."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        query = "SELECT * FROM games"
        params: tuple = ()
        if limit is not None:
            query += " ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)

        cursor = await self._connection.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_game(
        self,
        game_id: str,
        winner: str | None = None,
        rounds: int | None = None,
        log_file: str | None = None,
        tournament_id: str | None = None,
    ) -> None:
        """Update a game record."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        updates: dict[str, object] = {}
        if winner is not None:
            updates["winner"] = winner
        if rounds is not None:
            updates["rounds"] = rounds
        if log_file is not None:
            updates["log_file"] = log_file
        if tournament_id is not None:
            updates["tournament_id"] = tournament_id

        if not updates:
            raise ValueError("No fields provided to update")

        set_clause = ", ".join(f"{field} = ?" for field in updates)
        values = [*updates.values(), game_id]
        await self._connection.execute(
            f"UPDATE games SET {set_clause} WHERE id = ?",
            values,
        )
        await self._connection.commit()

    async def delete_game(self, game_id: str) -> None:
        """Delete a game record and its participants."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        await self._connection.execute(
            "DELETE FROM game_players WHERE game_id = ?",
            (game_id,),
        )
        await self._connection.execute(
            "DELETE FROM games WHERE id = ?",
            (game_id,),
        )
        await self._connection.commit()

    async def get_game(self, game_id: str) -> dict | None:
        """Get a game record by ID."""
        if not self._connection:
            raise RuntimeError("Database not connected")

        cursor = await self._connection.execute(
            "SELECT * FROM games WHERE id = ?",
            (game_id,),
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
