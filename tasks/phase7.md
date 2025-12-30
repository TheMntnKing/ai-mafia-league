# Phase 7: Quality, Observability, and Replay

**Goal:** Improve coordination logic, simplify context/data flow, abstract prompts, and enhance replay UX.

---

## Completed

### Pre-Phase 7 Bug Fixes ✅

| Bug | Fix |
|-----|-----|
| Phase transition off-by-one | Move `advance_phase()` before each phase |
| Day 1 skip nomination rejected | Case-insensitive validation, show "skip" in targets |
| Circular import | Remove game exports from `engine/__init__.py` |
| JSON log vote details | Already working |

### 1. Sequential Mafia Coordination ✅

**Problem:** R1 proposals were blind - both Mafia submitted independently.

**Solution:** Sequential R1 with message passing:
```
R1: First Mafia proposes (message + target)
    Second Mafia sees first's message + proposal, responds
R2: If disagree, both see each other's R1 message + proposal
    Still disagree → first Mafia decides
```

**Files modified:**
- `src/schemas/actions.py` - Added `message: str` to `NightKillOutput`
- `src/engine/phases.py` - Sequential R1, pass `partner_message` in action_context
- `src/engine/context.py` - Render partner's message in coordination sections, prompt asks for message
- `src/players/actions.py` - Default `message` value

### 3. SGR Schema Simplification ✅

**Problem:** 6 verbose reasoning fields, action-specific naming unnecessary.

**Solution:** 4 universal fields:
```python
class BaseThinking(BaseModel):
    observations: str  # What happened
    suspicions: str    # Who I suspect and why
    strategy: str      # My plan
    reasoning: str     # Why THIS action (universal, replaces vote_reasoning/target_reasoning)

class NightKillOutput(BaseThinking):
    message: str  # Message to partner
    target: str

class LastWordsOutput(BaseModel):  # Doesn't inherit BaseThinking
    reasoning: str
    text: str

class DefenseOutput(BaseModel):
    reasoning: str
    text: str
```

**Files modified:**
- `src/schemas/actions.py` - Simplified schema
- `src/players/agent.py` - Extract `suspicions`, `strategy` to beliefs
- `src/players/actions.py` - Updated defaults
- `src/engine/context.py` - Updated prompts
- `tests/sgr_helpers.py` - New helper builders with Pydantic validation

### 2. Context Simplification ✅

**Problem:** `[RECENT EVENTS]` section is redundant with transcript.

**Solution:** Remove `_build_recent_events_section()` entirely and drop `recent_events` plumbing. Remove redundant memory facts (`last_speak`, `last_vote`).

**Files modified:**
- `src/engine/context.py` - Remove `[RECENT EVENTS]` section
- `src/engine/phases.py` - Remove `recent_events` and event cursor usage
- `src/players/agent.py` - Remove `recent_events`, stop storing `last_speak`/`last_vote`
- `src/engine/game.py` - Remove `event_cursors`
- `tests/test_context.py` - Remove recent_events tests
- `tests/test_player.py` - Adjust memory assertions
- `tests/test_game.py` - Update phase signatures in tests

### 4. Prompt Abstraction ✅

**Problem:** Prompts embedded in `ContextBuilder._build_action_prompt()` make tuning difficult.

**Solution:** Extract to `src/engine/prompts.py` with constants + template builders.

**Files modified:**
- `src/engine/prompts.py` - New prompt templates/builders
- `src/engine/context.py` - Import and use prompts

### 6. Persona Modularization ✅

**Problem:** All personas lived in a single file, making it harder to add or swap personas.

**Solution:** Split each persona into its own module and update the initial roster.

**Files modified:**
- `src/personas/*.py` - One file per persona with `create_persona()`
- `src/personas/initial.py` - Updated to import individual personas

**Notes:**
- Roster now includes `Bombardiro Crocodilo` and `Tralalero Tralala` (7 total)

---
## Remaining

### 5. Replay Viewer Enhancement

**Current:** Basic HTML viewer with event filtering.

**Target:**
- Phase-by-phase navigation
- Show private reasoning → then public speech
- Player focus mode
- Side-by-side private vs public

**File:** `scripts/replay_viewer.html`

---

## Implementation Order

1. ~~Sequential R1 Coordination~~ ✅
2. ~~Context Simplification~~ ✅
3. ~~SGR Schema Simplification~~ ✅
4. ~~Prompt Abstraction~~ ✅
5. Replay Viewer

---

## Testing

**Done:**
- `tests/sgr_helpers.py` - Schema-validated mock builders
- Updated mocked provider outputs in tests to use helpers
- Removed recent_events tests and updated affected tests

---

## Future Considerations

### 3+ Mafia Support

The current coordination logic in `src/engine/phases.py` assumes exactly 2 Mafia:
- `NightZeroPhase`: First/second sequential pattern
- `NightPhase._run_mafia_coordination()`: R1→R2 protocol designed for pairs

**To support 3+ Mafia** (e.g., 10-player games), would need:
- Round-robin proposals or Mafia voting
- Designated leader who decides after hearing all
- Significant refactor of coordination logic

**Current scope:** 7 players, 2 Mafia. Expansion deferred until needed.

### Dynamic Role Counts

Adding new roles (Doctor, Jester, etc.) would require:
- New action types in `src/schemas/`
- New phase methods or hooks
- Role-specific context sections

Not planned for Phase 7.

---

## Open Questions

1. ~~SGR field names~~ **Resolved:** `observations`, `suspicions`, `strategy`, `reasoning`
2. ~~Prompt format~~ **Resolved:** constants + template builders
3. **Replay viewer:** Standalone HTML or need server for file listing?
