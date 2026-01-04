# Phase 9: 10-Player Expansion + Night Event Decomposition

**Goal:** Move engine to 10 players (3 Mafia + Doctor) and split night events for replay.

**Status:** IN PROGRESS (9.1–9.4 complete, 9.5 started)  
**Prerequisites:** Phase 1-8 complete

---

## Changes (what + where)

### 9.1 Schema + State
**Status:** ✅ implemented in code (tests pending in 9.7)
- `src/schemas/core.py`: add `ActionType.DOCTOR_PROTECT` ✅
- `src/schemas/actions.py`: add `DoctorProtectOutput(BaseThinking)` ✅
- `src/schemas/persona.py`: add `doctor` to `RoleGuidance` (optional field) ✅
- `src/engine/state.py`: require 10 players; roles = 3 Mafia + Doctor + Detective + 5 Town; speaking order uses player count (use `% player_count`, no hardcoded 7); add `get_mafia_partners()` ✅
- `src/engine/state.py` or `src/engine/game.py`: improve win-condition evaluation to handle “forced parity after night” when no Doctor is alive (end immediately after a mislynch if the next night kill is guaranteed to reach parity) ✅
- `src/engine/game.py`: pass Mafia partners list into agents (not single partner) ✅
- Use `partners: list[str]` (all other Mafia) as the standard key in `action_context` ✅
- Flow: `game.py` builds partners list -> `agent.py` stores -> `context.py` reads for role/coordination sections ✅
- `src/engine/run.py`: expect 10 personas (remove 7-persona guard) ✅
- `src/providers/anthropic.py`: add `DoctorProtectOutput` to `ACTION_SCHEMA_MAP` ✅
- `src/players/actions.py`: validate `DOCTOR_PROTECT` (living target, allow self); add default action ✅
- `src/players/agent.py`: store partners list; use for validation + context ✅
- `src/engine/context.py`: add `ActionType.DOCTOR_PROTECT` handling in `_build_action_prompt` ✅

### 9.2 Log Schema + Event Decomposition
**Status:** ✅ implemented in engine (doctor event emitted in 9.3)
- `src/engine/events.py`: add
  - `add_mafia_discussion()` ✅
  - `add_mafia_vote()` ✅
  - `add_doctor_protection()` ✅
  - `add_night_resolution()` ✅
- Remove `night_kill` event usage entirely in night flow (use `mafia_discussion` + `mafia_vote` + `night_resolution`) ✅
- `src/storage/json_logs.py`: bump `schema_version` to `1.3` ✅
- `tasks/phase8.md`: update stage/event registry for new types ✅
- `docs/replay_vision.md`: confirm night flow uses discrete events (no monolithic `night_kill`) ✅

Event types (stable shapes):
- `mafia_discussion`: `speaker`, `target`, `message`, `reasoning`, `coordination_round` (all private)
- `mafia_vote`: `votes`, `final_target`, `decided_by`, `coordination_round` (all private)
- `doctor_protection`: `protector`, `protected`, `reasoning` (all private)
- `investigation`: unchanged (private)
- `night_resolution`: `intended_kill`, `protected`, `actual_kill` (only `actual_kill` public)

### 9.3 Night Flow + 3-Mafia Coordination
**Status:** ✅ implemented in code (tests pending in 9.7)
- `src/engine/phases.py`:
  - Night Zero: sequential strategies for all living Mafia (not hardcoded to 2)
  - Night Phase: proposals per Mafia (round 1), majority rules; if split -> round 2 -> tie-break by lowest seat
  - Emit `mafia_discussion` per proposal and `mafia_vote` after decision
  - Run Doctor protection, Investigation, then `night_resolution`
  - Apply kill only after `night_resolution`
  - Store all Mafia strategies in memory (Night Zero)
  - Append Mafia kill history (target + outcome) after `night_resolution` (no cap)
  - Append Doctor protection history (target + reasoning) after `doctor_protection` (no cap)
  - Detective history unified in engine: `investigation_results` + `investigation_history` + `last_investigation`
  - Pass `game_over` flag into last-words context when an elimination ends the game

Rules:
- Round 1: 3/3 or 2/3 agreement executes (skip counts as a target)
- Round 2: 2/3+ agreement executes; otherwise lowest-seat Mafia decides

### 9.4 Context + Prompt Optimization (review + tune)
- `src/engine/context.py`: add speaking-order awareness for SPEAK/DEFENSE (include order, who has spoken, who still speaks, and round framing like “speaker #X of Y”); avoid accusing “silent” players who haven’t had a turn yet ✅
- `src/engine/phases.py`: pass speaking-order context into `action_context` for SPEAK/DEFENSE ✅
- `src/engine/prompts.py`: tighten prompts to be phase-aware (Night Zero = no deaths, Day 1 = low info), emphasize strategic play (ask questions, avoid overconfident claims) ✅
- `src/engine/prompts.py`: update `RULES_SUMMARY` for 10-player roster + Doctor ✅
- `src/engine/prompts.py`: add `DOCTOR_PROTECT_PROMPT_TEMPLATE` + `build_doctor_protect_prompt()` ✅
- `src/engine/prompts.py`: update last-words guidance to allow endgame trash talk/analysis when `game_over=true` ✅
- `src/engine/context.py`: update `_build_role_specific_section` to display list of partners (not single) ✅
- `src/engine/context.py`: update `_build_mafia_coordination_section` to accept/display multiple partner proposals + messages ✅
- `src/engine/prompts.py`: update Night Zero prompt wording for multiple partners ✅
- `src/engine/context.py`: remove duplicate investigation results block; summarize facts once in memory ✅
- `src/engine/transcript.py`: drop heuristic accusations/claims from compressed summaries (keep factual outcomes only) ✅

### 9.5 Strategy Guidance + Context Signals (added scope)
- `src/engine/prompts.py`: add role playbooks (short, advisory guidance for Town/Mafia/Detective/Doctor) ✅
- Scope: 5-7 short bullets per role; phrased as “consider/aim,” not hard rules ✅
- `src/engine/prompts.py`: add `SGR_FIELD_GUIDE` with clear per-field intent (observations/suspicions/strategy/reasoning vs public text) ✅
- Call out audience: `message` is Mafia-only; `speech/text` are public ✅
- `src/schemas/actions.py`: add `Field(description=...)` hints for SGR fields so tool schemas include guidance ✅
- Keep descriptions short; mirror `SGR_FIELD_GUIDE` wording ✅
- `src/engine/transcript.py`: add deterministic vote line in compressed summaries (final votes only) ✅
- `src/engine/transcript.py`: include a compact “defense occurred” marker when revote/defense happened ✅
- `src/schemas/transcript.py`: remove `accusations`/`claims` from `CompressedRoundSummary` (schema break) ✅
- Deferred to avoid redundancy: context pattern hints (conflict pairs/vote blocs) and a win-condition reminder line

### 9.6 Personas + Roster ✅
- Remove generic personas (keep `Tralalero Tralala`; Bombardiro removed) ✅
- Add 9 new unique personas ✅
- `src/personas/initial.py`: include 10 total (1 existing + 9 new) ✅
- Add doctor role tactics where desired (`RoleTactics.doctor` is optional) ✅

### 9.7 Tests + Sample Log + Viewer Sync
- `tests/test_state.py`: 10-player distribution + speaking order
- `tests/test_game.py`: agent count, roles, win condition edges
- `tests/test_player.py`: doctor validation/defaults
- `tests/test_providers.py`: schema map includes doctor
- Add tests for 3-Mafia coordination + doctor protection outcomes
- `tests/sgr_helpers.py`: add `make_doctor_protect_response()`
- `tests/test_context.py`: update for speaking-order block; compression no longer extracts accusations/claims
- Generate one 10-player log to validate event stream
- Viewer parser: handle `mafia_discussion`, `mafia_vote`, `doctor_protection`, `night_resolution`

---

## Clarifications

- `mafia_vote` does not require `coordination_round` unless replay needs explicit “round 2” labeling.
- Replace bundled `night_kill` with `mafia_discussion` + `mafia_vote` + `night_resolution` (keep `night_kill` only if needed for backward compatibility).
- Night flow order (omniscient):
  1) `mafia_discussion` per Mafia proposal
  2) `mafia_vote` final decision
  3) `doctor_protection`
  4) `investigation`
  5) `night_resolution` + apply kill (if any)
