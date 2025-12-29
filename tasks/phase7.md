# Phase 7: Quality, Observability, and Replay

**Goal:** Improve coordination logic, prompt quality, log visibility, and replay UX.

## Deliverables

### Mafia Coordination (Night Phase)
**Problem:** Round 1 proposals are blind, so Mafia do not actually coordinate.
**Fix:** Make Round 1 sequential:
- First Mafia proposes a target.
- Second Mafia sees the first proposal and responds.
- If they disagree, go to Round 2 with both seeing the Round 1 proposals.
- If still disagreement, first Mafia decides (by seat order).
**Notes:** This preserves two-round resolution while making coordination real.
**Tests:** Update night coordination tests to validate sequential R1 behavior.

### Prompt Tuning
**Problem:** Day 1 nominators often get voted out even when explanations are thin.
**Fix (prompt-level first):**
- Maintain 80-120 word target for SPEAK (already updated).
- Require explicit nomination rationale (especially Day 1 / first speaker).
- Encourage "soft nominations" (not hard accusations) early in Day 1.
**Optional schema change:** Add `nomination_reasoning` to `SpeakingOutput` for stronger enforcement.

### Prompt Abstraction
**Problem:** Prompts are embedded in `ContextBuilder`, making tuning harder.
**Fix:** Move prompts to a separate module or config file:
- Option A: `src/engine/prompts.py` with constants/templates.
- Option B: `prompts.json` or `prompts.yaml` loaded at runtime.
**Notes:** Keep Night Zero prompt and action prompts together for consistency.

### Log Visibility
**Problem:** Private reasoning can be hard to inspect without custom filters.
**Fix:**
- Ensure night kill reasoning is captured in JSON logs (proposal details + reasoning).
- Optional: add private Night Zero strategy events.
- Add a per-player context dump option (debug mode).

### Replay Viewer
- Build a minimal web viewer to list games and replay transcripts/events
- Allow toggling between public and private views
- Support filtering by event type (speech, vote, night_kill, investigation, etc.)

### Testing
- Add multi-run smoke test utility (run N games with fixed seeds)
- Capture summary stats (winner, rounds, failures)

## Files (Planned)
```
tasks/phase7.md
src/engine/phases.py
src/engine/context.py (optional)
src/storage/json_logs.py (optional)
scripts/pretty_log.py (optional)
tests/test_game.py (updates)
```
