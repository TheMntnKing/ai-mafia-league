# Phase 8: Replayable Logs + CLI Progress

**Goal:** Make the game replayable phase-by-phase in two modes: public (town view) and
omniscient (all roles + private reasoning). Achieve this with a log schema upgrade
and lightweight CLI progress.

**Status:** ✅ COMPLETE

---

## Scope

- Log schema v1.1 (state snapshots + phase metadata)
- Night Zero logging
- CLI progress updates

---

## Log Schema v1.1

**Top-level:**
- `schema_version`: "1.1"
- `players`: unchanged (static roster with roles)
- `events`: enriched with phase metadata and state snapshots

**Event data (standard fields for all event types, always present):**
- `phase`: e.g., "night_zero", "day_1", "night_1"
- `round_number`: integer (0 for night_zero)
- `stage`: e.g., "night_zero", "discussion", "vote", "defense", "revote",
  "night_kill", "investigation", "last_words", "game_end"
- `state_public`:
  - `phase`
  - `round_number`
  - `living`: list of player names
  - `dead`: list of player names
  - `nominated`: list of player names

**Stage mapping (expected):**
- `phase_start` → `stage: "phase_start"`
- `speech` → `stage: "discussion"`
- `vote` → `stage: "vote"`
- `defense` → `stage: "defense"`
- `revote` remains inside the `vote` event (no separate event type)
- `night_kill` → `stage: "night_kill"`
- `investigation` → `stage: "investigation"`
- `last_words` → `stage: "last_words"`
- `night_zero_strategy` → `stage: "night_zero"`
- `game_end` → `stage: "game_end"`

**State transitions (for events that change roster):**
- `state_before`
- `state_after`

**Night Zero:**
- New event type `night_zero_strategy`
- Data fields: `speaker`, `text`, `reasoning`
- **Fully private** (speaker/text/reasoning all in `private_fields`)

**Private/omniscient view:**
- Roles are static and read from top-level `players`.
- No per-event role duplication required (avoid log bloat).

**Investigation events:**
- Remain fully private (target/result/reasoning hidden in public view).
- Phase/round/state metadata can be included but remain private if needed.

**Context alignment:**
- Event log changes are for replay/visibility only.
- Player prompts still use `GameState`, transcript, and memory (no event log dependency).

---

## CLI Progress

- Emit progress on `phase_start`, `night_kill`, `vote` outcome, and eliminations.
- Keep output concise for long runs.

---

## Implementation Tasks

1. ~~Add a public state snapshot helper in `src/engine/state.py`.~~ ✅
2. ~~Extend `src/engine/events.py` convenience methods to accept phase/round/stage/state.~~ ✅
3. ~~Log Night Zero strategies in `src/engine/phases.py`.~~ ✅
4. ~~Attach phase/round/stage + `state_public` to all events in phases.~~ ✅
5. ~~Bump `schema_version` to "1.1" in log output (`src/engine/game.py`).~~ ✅
6. ~~Add CLI progress reporting hook in `src/engine/run.py` (based on event stream).~~ ✅
7. ~~Update `.gitignore` to exclude `viewer/node_modules/` and `viewer/dist/`.~~ ✅
8. ~~Remove `scripts/pretty_log.py` (viewer replaces CLI log formatting).~~ ✅
9. ~~Update tests for event shape and Night Zero logging.~~ ✅

---

## Notes

- **Simplicity choice:** include `state_public` on every event to avoid replay
  state reconstruction in the viewer.
- **Role visibility:** use top-level `players` for omniscient mode to keep logs small.
- **Night-kill snapshots:** `state_after` is computed from intended kill target
  (correct under current rules; when Doctor/blocks exist, emit night_kill after
  resolution using the resolved target).
