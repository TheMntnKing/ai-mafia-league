# Phase 6: Game Loop

**Goal:** Complete game orchestration - FIRST MILESTONE. A runnable game from start to finish.

**Status:** ✅ IMPLEMENTED (all tests passing)

## Deliverables

### Vote Resolver (`src/engine/voting.py`) ✅
- `VoteResult` dataclass with outcome, eliminated, tied_players, vote_counts
- `VoteResolver` class for vote resolution logic
- `resolve(votes, living_count)` method:
  - Majority (>50% of living) → eliminated
  - Tie at top (no majority) → revote with tied players
  - No majority, no tie → no elimination
- `resolve_revote(votes, living_count, tied_players)` method:
  - Majority → eliminated
  - Still no majority → no elimination (no further revotes)

### Phases (`src/engine/phases.py`) ✅

#### NightZeroPhase
- Single round Mafia coordination (no kill)
- **Sequential execution** (sorted by seat):
  1. First Mafia speaks (receives partner identity)
  2. Second Mafia speaks (receives partner identity + first Mafia's strategy via `partner_strategy` in action_context)
- Both strategies stored in both Mafia's `memory.facts["night_zero_strategies"]`
- No Detective action, no Town action

#### DayPhase ✅
- `run()` returns `(eliminated_player | None, updated_memories)`
- Flow:
  1. Start round with night kill info (no last words - night kills are silent)
  2. Discussion: call speakers in order, collect speeches + nominations
  3. Voting: collect votes from all living players
  4. Resolve vote:
     - Majority → eliminate, collect last words, kill player
     - Tie → run revote (defenses, revote, resolve)
     - No majority → no elimination
  5. Finalize transcript with vote outcome

#### NightPhase ✅
- `run()` returns `(killed_player | None, updated_memories)`
- **No last words collected for night kills**
- Mafia coordination (up to 2 rounds):
  - Round 1: Each Mafia proposes target (sorted by seat)
  - If agree → execute kill, skip Round 2
  - If both skip → no kill, skip Round 2
  - If disagree → Round 2 with `partner_proposal` and `my_r1_proposal` in action_context
  - Round 2: Each sees partner's R1 proposal, submits final choice
  - If still disagree → first Mafia (by seat) decides
  - Single Mafia alive → direct choice, no coordination
- Detective investigation:
  - Choose target (non-self)
  - Receive result (Mafia / Not Mafia)
  - Store result in `memory.facts["investigation_results"]`

### Game Runner (`src/engine/game.py`) ✅
- `GameConfig` dataclass: player_names, personas, provider, output_dir, seed
- `GameResult` dataclass: winner, rounds, log_path, final_living, eliminations
- `GameRunner` class:
  - Initialize: create agents, assign roles, set up state and memories
  - Mafia agents get partner reference
  - Main loop:
    1. Night Zero (Mafia coordination)
    2. Day 1 (no death announcement)
    3. Loop: Night → Day until win condition
  - Win condition checked after each phase
  - `_finalize_game()`: add game_end event, write JSON log
  - `_build_log_data()`: schema version, players, events, transcript, result
- `run_game()` convenience function

### Initial Personas (`src/personas/initial.py`) ✅
- `get_personas()` returns dict of 7 personas
- Each persona follows `Persona` schema:
  - Identity: name, background, core_traits (3-5 role-neutral)
  - Voice and behavior: speech_style, reasoning_style, accusation_style, defense_style, trust_disposition, risk_tolerance, signature_phrases, quirks
  - Role guidance: brief (1-2 sentences) for town/mafia/detective
- Target 250-400 words per persona
- Diverse and entertaining personalities

### Run Script (`src/engine/run.py`) ✅
- CLI entry point: `python -m src.engine.run`
- Arguments: --seed, --output, --model
- Loads personas from `src/personas/initial.py`
- Creates AnthropicProvider with settings
- Runs game, displays result with Rich

### Context Builder Enhancement (`src/engine/context.py`) ✅
- Added `_build_mafia_coordination_section()` to render coordination context:
  - `[PARTNER'S STRATEGY]` section for NightZero (second Mafia sees first's strategy)
  - `[COORDINATION ROUND 2]` section for Night kill disagreement resolution
- Added `_build_night_zero_prompt()` for dedicated NightZero task prompt:
  - `[YOUR TASK: NIGHT ZERO COORDINATION]` instead of generic SPEAK prompt
  - First Mafia: strategy sharing instructions
  - Second Mafia: shows partner's strategy, asks for response
  - Tells LLM that nomination field is unused during Night Zero

### Tests (`tests/test_game.py`) ✅

| Test Class | Tests |
|------------|-------|
| TestVoteResolver | `test_majority_eliminates`, `test_plurality_without_majority`, `test_tie_triggers_revote`, `test_all_skip_no_elimination`, `test_revote_majority_eliminates`, `test_revote_tie_no_elimination` |
| TestGameRunner | `test_creates_agents`, `test_assigns_roles`, `test_initializes_memories`, `test_mafia_agents_have_partners`, `test_runs_to_completion` |
| TestGameIntegration | `test_town_wins_when_both_mafia_eliminated`, `test_mafia_wins_when_majority` |
| TestSpeakingOrder | `test_speaking_order_advances_by_seat`, `test_dead_players_skipped_in_speaking_order` |
| TestNightZeroCoordination | `test_night_zero_stores_strategies_in_memory`, `test_second_mafia_sees_first_strategy` |
| TestLogSchema | `test_log_schema_has_required_fields`, `test_player_outcomes_calculated_correctly`, `test_player_entries_have_required_fields` |
| TestMafiaCoordination | `test_round1_agreement_skips_round2`, `test_round2_on_disagreement`, `test_first_mafia_decides_on_continued_disagreement` |

### Additional Tests (`tests/test_context.py`, `tests/test_player.py`) ✅
| Test Class | Tests |
|------------|-------|
| TestNightZeroPrompt | `test_night_zero_prompt_first_mafia`, `test_night_zero_prompt_second_mafia_sees_partner`, `test_night_zero_flag_uses_different_prompt_than_speak` |
| TestActionHandler | `test_validate_speaking_skips_nomination_for_night_zero`, `test_validate_speaking_validates_nomination_without_night_zero` |

**Total: 190 tests passing** (includes tests from all test files)

## Files Created/Modified
```
src/engine/__init__.py (add exports)
src/engine/voting.py
src/engine/phases.py
src/engine/game.py (includes log schema with timestamps + player outcomes)
src/engine/run.py
src/engine/context.py (coordination section + NightZero prompt)
src/players/actions.py (night_zero validation skip)
src/players/agent.py (pass night_zero flag to validation)
src/personas/__init__.py
src/personas/initial.py
tests/test_game.py (includes TestLogSchema)
tests/test_context.py (includes TestNightZeroPrompt)
tests/test_player.py (includes night_zero validation tests)
```

## Design Notes

### Last Words Policy
- **Night kills**: No last words (silent kills, victim doesn't know it's coming)
- **Day eliminations**: Last words collected before player is killed
- Strategic implication: Detective eliminated by vote can reveal results; killed at night cannot

### NightZero Strategy Sharing
- Sequential execution: first Mafia (by seat) speaks, second sees first's strategy
- Second Mafia receives `partner_strategy` in action_context
- ContextBuilder renders this as `[PARTNER'S STRATEGY]` section
- Both strategies stored in `memory.facts["night_zero_strategies"]` dict

### Mafia Coordination Protocol
```
Round 1:
  Both propose (by seat order) → Same target? Execute. Both skip? No kill. Else Round 2.

Round 2 (disagreement only):
  Both receive partner_proposal and my_r1_proposal in action_context
  ContextBuilder renders as [COORDINATION ROUND 2] section
  Both agree? Execute. Else first Mafia (by seat) decides.
```

### Context Builder Flow
- `action_context` dict passed from phases to `PlayerAgent.act()`
- Agent merges into `extra` dict and calls `ContextBuilder.build_context()`
- ContextBuilder has dedicated methods for coordination context:
  - `_build_mafia_coordination_section()` renders partner_strategy, partner_proposal, my_r1_proposal
- Final context string passed to `provider.act(action_type, context_string)`

### Event Cursors
- Each player has an event cursor tracking last-seen event index
- `_get_recent_events()` returns public events since cursor, advances cursor
- Ensures players only see events since their last action

### Memory Ownership
- Engine owns all `PlayerMemory` instances in `memories: dict[str, PlayerMemory]`
- Phases update memories in place and return the dict
- Detective investigation results stored by engine in `memory.facts["investigation_results"]`

## Deviations from Original Spec
- **Night kill last words removed**: Simplifies flow, adds strategic asymmetry
- **NightZero uses SPEAK action type**: Pragmatic choice, works with existing schema (with dedicated prompt)
- **NightZero sequential (not simultaneous)**: Second Mafia sees first's strategy before responding

## Post-Implementation Fixes

### NightZero Prompt Enhancement
- Added dedicated `[YOUR TASK: NIGHT ZERO COORDINATION]` prompt instead of generic SPEAK
- First Mafia receives strategy coordination instructions
- Second Mafia sees partner's strategy before responding
- Prompt explicitly tells LLM that nomination field is unused

### Validation Skip for NightZero
- Added `night_zero` parameter to `ActionHandler.validate()`
- When `night_zero=True`, nomination validation is skipped (nomination meaningless during Mafia coordination)
- Speech length validation still applies
- `PlayerAgent._get_valid_output()` extracts flag from `action_context` and passes to validator

### Log Schema Alignment (Phase 3 Compliance)
- Added `timestamp_start` (captured in `GameRunner.__init__`)
- Added `timestamp_end` (captured in `_finalize_game`)
- Added `winner` at top level of log
- Added `outcome` field per player: "survived", "eliminated" (day vote), or "killed" (night)
- Renamed `persona_name` to `persona_id`
- Kept extra fields (metadata, transcript, result) for enrichment
