-- AI Mafia Agent League - Database Schema
-- SQLite with JSON1 extension. JSON fields stored as TEXT, query via json_extract().

-- Persona bank
CREATE TABLE personas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    definition TEXT NOT NULL,  -- Full Persona JSON (identity, voice_and_behavior, role_guidance, relationships)
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0
);

-- Game records
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    tournament_id TEXT REFERENCES tournaments(id),  -- NULL for standalone games
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
    status TEXT,       -- 'pending', 'active', 'completed'
    roster TEXT,       -- JSON array of persona_ids (fixed for tournament)
    games_total INTEGER,
    standings TEXT     -- JSON (persona scores, wins, etc.)
);

-- Cross-game memory for tournaments (future)
-- Each persona maintains memories of opponents, scoped to tournament
CREATE TABLE persona_memories (
    tournament_id TEXT REFERENCES tournaments(id),
    persona_id TEXT REFERENCES personas(id),
    opponent_id TEXT REFERENCES personas(id),
    memory TEXT,  -- Free-form text in persona's voice (~100-200 words)
    games_together INTEGER DEFAULT 0,
    last_updated DATETIME,
    PRIMARY KEY (tournament_id, persona_id, opponent_id)
);
