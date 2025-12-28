-- AI Mafia Agent League - Database Schema
-- SQLite with JSON1 extension. JSON fields stored as TEXT, query via json_extract().

-- Persona bank
CREATE TABLE personas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    traits TEXT,      -- JSON
    play_style TEXT,  -- JSON
    games_played INTEGER DEFAULT 0,
    win_rate REAL
);

-- Game records
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    timestamp DATETIME,
    winner TEXT,      -- 'town' or 'mafia'
    rounds INTEGER,
    log_file TEXT     -- path to JSON log
);

-- Game participants
CREATE TABLE game_players (
    game_id TEXT REFERENCES games(id),
    persona_id TEXT REFERENCES personas(id),
    role TEXT,        -- 'mafia', 'detective', 'town'
    outcome TEXT,     -- 'survived', 'eliminated', 'killed'
    PRIMARY KEY (game_id, persona_id)
);

-- Tournament data (future)
CREATE TABLE tournaments (
    id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    standings TEXT    -- JSON
);

-- Cross-game memory for tournaments (future)
CREATE TABLE persona_memories (
    persona_id TEXT REFERENCES personas(id),
    opponent_id TEXT REFERENCES personas(id),
    observations TEXT,  -- JSON
    PRIMARY KEY (persona_id, opponent_id)
);
