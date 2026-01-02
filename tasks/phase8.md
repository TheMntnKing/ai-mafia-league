# Phase 8: Replayable Logs + CLI Progress

**Goal:** Make the game replayable phase-by-phase in two modes: public (town view) and
omniscient (all roles + private reasoning). Achieve this with a log schema upgrade
and lightweight CLI progress.

**Status:** ✅ COMPLETE

---

## Scope

- Log schema v1.2 (state snapshots + phase metadata)
- Night Zero logging
- CLI progress updates

---

## Log Schema v1.2

Required fields:
```javascript
log.schema_version
log.game_id
log.timestamp_start
log.timestamp_end
log.winner
log.players           // [{seat, persona_id, name, role, outcome}]
log.events            // [{type, timestamp, data, private_fields}]

event.type            // "speech", "vote_round", "elimination", "night_kill", etc.
event.timestamp       // ISO8601
event.data.phase      // "day_1", "night_1", etc.
event.data.round_number
event.data.stage
event.data.state_public    // {phase, round_number, living, dead, nominated}
event.private_fields // list of data keys hidden in public mode
event.data.reasoning // present in omniscient view when not filtered
```

Notes:
- `state_before`/`state_after` live inside `event.data` for roster-changing events.
- Private reasoning is in `event.data.reasoning` and listed in `event.private_fields`.
- `vote_round` includes `data.round`, `data.outcome`, and `data.votes`.
- `vote_round.data.outcome`: `"eliminated"`, `"no_elimination"`, or `"tie"` (round 1 only).
- `elimination` includes `data.eliminated`.

**Stage mapping (expected):**
- `phase_start` → `stage: "phase_start"`
- `speech` → `stage: "discussion"`
- `vote_round` → `stage: "vote"` (data includes `round: 1 | 2`)
- `defense` → `stage: "defense"`
- `elimination` → `stage: "elimination"`
- `night_kill` → `stage: "night_kill"`
- `investigation` → `stage: "investigation"`
- `last_words` → `stage: "last_words"`
- `night_zero_strategy` → `stage: "night_zero"`
- `game_end` → `stage: "game_end"`

**Night Zero:**
- New event type `night_zero_strategy`
- Data fields: `speaker`, `text`, `reasoning`
- **Fully private** (all fields, including phase metadata, are in `private_fields`)

**Private/omniscient view:**
- Roles are static and read from top-level `players`.
- No per-event role duplication required (avoid log bloat).

**Investigation events:**
- Remain fully private (target/result/reasoning hidden in public view).
- Phase/round/state metadata can be included but remain private if needed.

**Reasoning payloads (viewer mapping):**
Use `thought` for internal monologue TTS (plays before spoken line) and `subtitle` for the
spoken line. Many events have no subtitle.

| event.type | thought source | subtitle source | notes |
|-----------|----------------|-----------------|-------|
| `speech` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `SpeakingOutput`. |
| `defense` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `DefenseOutput`. |
| `last_words` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `LastWordsOutput`. |
| `night_zero_strategy` | `data.reasoning.reasoning` | `data.text` | `data.reasoning` is full `SpeakingOutput` (night_zero context). |
| `vote_round` | `data.vote_details[<voter>].reasoning` | none | Per-voter `VotingOutput`. Use selectively. |
| `night_kill` | see notes | `proposal_details*[*].message` (optional) | Reasoning is a coordination bundle. |
| `investigation` | `data.reasoning.reasoning` | none | `data.reasoning` is full `InvestigationOutput`. |
| `elimination` | none | none | Use UI + day announcement, not log text. |

**Night kill bundle details:**
- Round 1: `reasoning.proposals` + `reasoning.proposal_details`
- Round 2: `reasoning.proposals_r1`, `reasoning.proposals_r2`,
  `reasoning.proposal_details_r1`, `reasoning.proposal_details_r2`, optional `decided_by`
- Each entry in `proposal_details*` is a full `NightKillOutput` (includes `message` and
  `reasoning`). Viewer must parse these; do not assume `data.text` exists.

Viewer should handle `vote_round` + `elimination` events (schema v1.2).

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
5. ~~Bump `schema_version` to "1.2" in log output (`src/engine/game.py`).~~ ✅
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
