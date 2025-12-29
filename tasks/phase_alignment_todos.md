# Phase Alignment To-Dos (1-5)

This document captures non-blocking follow-ups discovered while reviewing
Phases 1-5 against the tasks and specs. These are future hardening tasks,
not current blockers.

Severity levels:
- Medium: risk in non-local usage or misconfiguration
- Low: spec clarity or optional test coverage

## Phase 1: Project Foundation

1) Database schema loading is repo-relative
- Severity: Medium
- Where: `src/storage/database.py:33-44`
- Current behavior: `Database.initialize_schema()` loads `docs/database.sql`
  via a path relative to the repo.
- Risk: packaging or running from a different working directory without
  the docs folder will fail.
- Suggested fix: ship `docs/database.sql` as package data and load it via
  `importlib.resources`, or make the schema path configurable via `Settings`
  and pass it explicitly from the app.
- Optional test: add a minimal config/env test to validate settings loading.

## Phase 2: Provider Layer

1) Langfuse is "optional" but not guarded
- Severity: Medium
- Where: `src/providers/anthropic.py:22-185`, `pyproject.toml:7-13`
- Current behavior: `langfuse` is a required dependency and calls to
  `Langfuse().update_current_generation()` are not guarded by key presence.
- Risk: missing keys or Langfuse misconfiguration can raise at runtime,
  despite "graceful fallback" being promised in specs.
- Suggested fix: only send usage to Langfuse when keys are configured,
  and/or wrap the call in try/except. If you want Langfuse to be optional,
  move it behind an extra.

2) Retry coverage for `APIError`
- Severity: Low
- Where: `tests/test_providers.py:184-217`
- Current tests cover `APIConnectionError`, but not `APIError`.
- Suggested fix: add a test that confirms retry behavior for `APIError`.

## Phase 3: Game State and Events

1) Nomination de-duplication vs rules
- Severity: Low
- Where: `src/engine/state.py:255-263`, `docs/02_game_rules.md:63-67`
- Current behavior: nominations are de-duplicated in `GameStateManager`.
- Docs state: a player can be nominated multiple times.
- Impact: de-duplication does not affect vote eligibility but removes
  any chance to log or show nomination frequency.
- Suggested fix: decide whether duplicates matter; if yes, store counts
  or allow duplicates; if no, update docs to clarify de-duplication.

## Phase 4: Transcript and Context

1) Last words now stored in transcripts
- Severity: Low
- Where: `src/engine/transcript.py:177-216`, `src/engine/phases.py:176-273`
- Fix implemented: day-elimination last words are stored in transcripts and
  passed through `finalize_round()`.
- Optional test: add an explicit context rendering test to assert last words
  appear in `[TRANSCRIPT]` when present.

## Phase 5: Player Agent

1) Night Zero validation bypass (informational)
- Severity: Low
- Where: `src/players/actions.py:26-77`, `src/engine/phases.py:52-96`
- Implementation skips nomination validation for Night Zero `SPEAK` actions.
- This matches engine behavior but is not explicitly documented in Phase 5.
- Suggested fix: add a short note in Phase 5 docs or tests if desired.

## Phase 6: Game Loop

1) Game log persona_id uses persona name
- Severity: Medium
- Where: `src/engine/game.py:227-234`
- Current behavior: `persona_id` in the log uses `persona.identity.name`.
- Risk: if you later persist personas in SQLite (with UUID IDs), logs won’t
  match database IDs.
- Suggested fix: add stable persona IDs to persona definitions or pass
  persona IDs into `GameConfig` and use those in logs.

2) Placeholder personas vs spec
- Severity: Low
- Where: `src/personas/initial.py:1-245`
- Current behavior: personas are short and labeled as placeholders.
- Spec: target 250–400 words per persona with richer detail.
- Suggested fix: replace placeholders when ready; defer for now if
  not needed for core engine testing.
