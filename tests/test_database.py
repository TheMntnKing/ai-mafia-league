"""Tests for database operations."""

import sqlite3

import pytest

from src.storage.database import Database


class TestDatabase:
    async def test_connect_and_close(self, tmp_path):
        """Database can connect and close."""
        db = Database(str(tmp_path / "test.db"))
        await db.connect()
        assert db._connection is not None
        await db.close()
        assert db._connection is None

    async def test_initialize_schema(self, test_db):
        """Database schema initializes correctly."""
        # Schema should create tables - verify by querying
        cursor = await test_db._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()
        table_names = [t["name"] for t in tables]
        assert "personas" in table_names
        assert "games" in table_names
        assert "game_players" in table_names
        assert "tournaments" in table_names
        assert "persona_memories" in table_names

    async def test_initialize_schema_with_changed_cwd(self, tmp_path, monkeypatch):
        """Schema initializes even when cwd differs from repo root."""
        db = Database(str(tmp_path / "test.db"))
        await db.connect()
        monkeypatch.chdir(tmp_path)
        await db.initialize_schema()
        cursor = await db._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()
        table_names = [t["name"] for t in tables]
        assert "personas" in table_names
        await db.close()

    async def test_initialize_schema_missing_file(self, tmp_path):
        """Missing schema file raises an error."""
        db = Database(str(tmp_path / "test.db"))
        await db.connect()
        with pytest.raises(FileNotFoundError):
            await db.initialize_schema(schema_path=str(tmp_path / "missing.sql"))
        await db.close()


class TestPersonaCRUD:
    async def test_create_persona(self, test_db, sample_persona):
        """Can create a persona and get its ID."""
        persona_id = await test_db.create_persona(sample_persona)
        assert persona_id is not None
        assert len(persona_id) == 32  # UUID hex string

    async def test_get_persona(self, test_db, sample_persona):
        """Can retrieve a persona by ID."""
        persona_id = await test_db.create_persona(sample_persona)
        retrieved = await test_db.get_persona(persona_id)
        assert retrieved is not None
        assert retrieved.identity.name == sample_persona.identity.name

    async def test_get_persona_not_found(self, test_db):
        """Returns None for non-existent persona."""
        result = await test_db.get_persona("nonexistent")
        assert result is None

    async def test_get_persona_by_name(self, test_db, sample_persona):
        """Can retrieve a persona by name."""
        await test_db.create_persona(sample_persona)
        retrieved = await test_db.get_persona_by_name("Test Player")
        assert retrieved is not None
        assert retrieved.identity.name == "Test Player"

    async def test_get_persona_id_by_name(self, test_db, sample_persona):
        """Can retrieve a persona's database ID by name."""
        persona_id = await test_db.create_persona(sample_persona)
        retrieved_id = await test_db.get_persona_id_by_name("Test Player")
        assert retrieved_id == persona_id

    async def test_duplicate_persona_name(self, test_db, sample_persona):
        """Creating a persona with duplicate name raises error."""
        await test_db.create_persona(sample_persona)
        with pytest.raises(ValueError):
            await test_db.create_persona(sample_persona)

    async def test_list_personas(self, test_db, seven_personas):
        """Can list all personas."""
        for persona in seven_personas:
            await test_db.create_persona(persona)

        all_personas = await test_db.list_personas()
        assert len(all_personas) == 7

    async def test_update_persona_stats(self, test_db, sample_persona):
        """Can update persona statistics."""
        persona_id = await test_db.create_persona(sample_persona)
        await test_db.update_persona_stats(persona_id, games_played_delta=1, wins_delta=1)

        # Verify update
        cursor = await test_db._connection.execute(
            "SELECT games_played, wins FROM personas WHERE id = ?",
            (persona_id,),
        )
        row = await cursor.fetchone()
        assert row["games_played"] == 1
        assert row["wins"] == 1


class TestGameRecords:
    async def test_record_game(self, test_db, sample_persona):
        """Can record a completed game."""
        await test_db.create_persona(sample_persona)  # Create persona for later tests

        await test_db.record_game(
            game_id="test_game_1",
            winner="town",
            rounds=5,
            log_file="logs/test_game_1.json",
        )

        game = await test_db.get_game("test_game_1")
        assert game is not None
        assert game["winner"] == "town"
        assert game["rounds"] == 5

    async def test_record_game_player(self, test_db, sample_persona):
        """Can record player participation."""
        persona_id = await test_db.create_persona(sample_persona)

        await test_db.record_game(
            game_id="test_game_2",
            winner="town",
            rounds=4,
            log_file="logs/test_game_2.json",
        )

        await test_db.record_game_player(
            game_id="test_game_2",
            persona_id=persona_id,
            role="detective",
            outcome="survived",
        )

        # Verify
        cursor = await test_db._connection.execute(
            "SELECT * FROM game_players WHERE game_id = ?",
            ("test_game_2",),
        )
        row = await cursor.fetchone()
        assert row["role"] == "detective"
        assert row["outcome"] == "survived"

    async def test_record_game_player_requires_game(self, test_db, sample_persona):
        """Foreign keys prevent orphaned game_players records."""
        persona_id = await test_db.create_persona(sample_persona)

        with pytest.raises(sqlite3.IntegrityError):
            await test_db.record_game_player(
                game_id="missing_game",
                persona_id=persona_id,
                role="town",
                outcome="survived",
            )

    async def test_list_games(self, test_db):
        """Can list recorded games."""
        await test_db.record_game(
            game_id="list_game_1",
            winner="town",
            rounds=3,
            log_file="logs/list_game_1.json",
        )
        await test_db.record_game(
            game_id="list_game_2",
            winner="mafia",
            rounds=4,
            log_file="logs/list_game_2.json",
        )

        games = await test_db.list_games()
        game_ids = {game["id"] for game in games}
        assert {"list_game_1", "list_game_2"} <= game_ids

    async def test_list_games_limit(self, test_db):
        """Can limit game listing."""
        await test_db.record_game(
            game_id="limit_game_1",
            winner="town",
            rounds=2,
            log_file="logs/limit_game_1.json",
        )
        await test_db.record_game(
            game_id="limit_game_2",
            winner="mafia",
            rounds=2,
            log_file="logs/limit_game_2.json",
        )

        games = await test_db.list_games(limit=1)
        assert len(games) == 1

    async def test_update_game(self, test_db):
        """Can update a game record."""
        await test_db.record_game(
            game_id="update_game_1",
            winner="town",
            rounds=5,
            log_file="logs/update_game_1.json",
        )

        await test_db._connection.execute(
            "INSERT INTO tournaments (id, name, status) VALUES (?, ?, ?)",
            ("tourney_1", "Test Tourney", "active"),
        )
        await test_db._connection.commit()

        await test_db.update_game(
            "update_game_1",
            winner="mafia",
            rounds=6,
            log_file="logs/update_game_1_v2.json",
            tournament_id="tourney_1",
        )

        game = await test_db.get_game("update_game_1")
        assert game["winner"] == "mafia"
        assert game["rounds"] == 6
        assert game["log_file"] == "logs/update_game_1_v2.json"
        assert game["tournament_id"] == "tourney_1"

    async def test_update_game_no_fields(self, test_db):
        """Update requires at least one field."""
        await test_db.record_game(
            game_id="update_game_2",
            winner="town",
            rounds=2,
            log_file="logs/update_game_2.json",
        )

        with pytest.raises(ValueError):
            await test_db.update_game("update_game_2")

    async def test_delete_game(self, test_db, sample_persona):
        """Can delete a game and its participants."""
        persona_id = await test_db.create_persona(sample_persona)
        await test_db.record_game(
            game_id="delete_game_1",
            winner="town",
            rounds=1,
            log_file="logs/delete_game_1.json",
        )
        await test_db.record_game_player(
            game_id="delete_game_1",
            persona_id=persona_id,
            role="town",
            outcome="survived",
        )

        await test_db.delete_game("delete_game_1")

        game = await test_db.get_game("delete_game_1")
        assert game is None

        cursor = await test_db._connection.execute(
            "SELECT * FROM game_players WHERE game_id = ?",
            ("delete_game_1",),
        )
        rows = await cursor.fetchall()
        assert rows == []
