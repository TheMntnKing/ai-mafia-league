# Phase 3: Game State & Event System

**Goal:** Core game state management and event logging.

## Deliverables

### Game State Manager (`src/engine/state.py`)
- `GameStateManager` class with seeded randomization
- Initializes 7 players: randomized seats (0-6), roles (2 Mafia, 1 Detective, 4 Town)
- Tracks: phase, round_number, living/dead players, nominations, votes
- Phase transitions: setup → night_zero → day_1 → night_1 → day_2 → ...
- Clears nominations on phase change (day or night)
- Win conditions: Town wins when Mafia=0, Mafia wins when Mafia >= Town-aligned
- Speaking order: rotates by day, skips dead players
- Validation: rejects invalid nominations (unknown/dead) and votes (unknown/dead voter/target, non-nominated target, allows skip)
- Helpers: `get_mafia_partner()`, `get_player_role()`, `get_living_players()`, `get_players_by_role()`, `get_public_state()`

### Event Log (`src/engine/events.py`)
- `EventLog` class managing game events
- Public/private field filtering for player context vs viewer experience
- Fully private events (all fields private) excluded from public view
- Incremental access: `get_public_view(since_index)`, `get_full_view_since(index)`, `get_events_since_timestamp()`
- Convenience methods for all event types:

| Method | Private Fields |
|--------|----------------|
| `add_phase_start` | none |
| `add_speech` | reasoning |
| `add_vote` | none |
| `add_night_kill` | reasoning |
| `add_investigation` | target, result, reasoning (all) |
| `add_last_words` | none |
| `add_defense` | none |
| `add_game_end` | none |

### JSON Game Logs (`src/storage/json_logs.py`)
- `GameLogWriter` class
- Schema version 1.0 format
- Writes to `logs/game_{id}.json`
- Includes player entries (seat, persona_id, name, role, outcome) and full event history
- Sync `write()` and async `write_game_log()` methods
- Read/list helpers for log inspection

### Tests (`tests/test_state.py`)
| Test Class | Coverage |
|------------|----------|
| TestGameStateManager | Role distribution, player validation, nomination/vote validation |
| TestPhaseTransitions | All transitions, nomination clearing on day/night |
| TestWinConditions | Town win, Mafia win (equality/majority), game continues |
| TestSpeakingOrder | All living speak, rotation by day, dead skipped |
| TestMafiaPartner | Partner lookup, non-Mafia returns None |
| TestPublicState | All fields present, reflects deaths/nominations |
| TestEventLog | Add events, public/private filtering, since methods, convenience methods, investigation hiding |
| TestGameLogWriter | Write/read, list games, async write |

## Files Created
```
src/engine/__init__.py
src/engine/state.py
src/engine/events.py
src/storage/json_logs.py
tests/test_state.py
```
