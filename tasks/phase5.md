# Phase 5: Player Agent

**Goal:** LLM-powered player that reasons and acts, with stateless design and robust error handling.

## Deliverables

### Action Handler (`src/players/actions.py`)
- `ActionHandler` class for validation and defaults
- `ActionValidationError` exception for invalid outputs
- Validation rules:

| Action | Validation |
|--------|------------|
| SPEAK | Nomination must be living player; speech ≥ 10 chars |
| VOTE | Must be nominated player or "skip" |
| NIGHT_KILL | Must be living non-Mafia player or "skip" |
| INVESTIGATION | Must be living non-self player |
| LAST_WORDS | No constraints |
| DEFENSE | No constraints |

- Default actions after retry exhaustion:

| Action | Default Behavior |
|--------|------------------|
| SPEAK | Generic speech + random valid nomination |
| VOTE | "skip" |
| NIGHT_KILL | Random non-Mafia target (or "skip" if none) |
| INVESTIGATION | Random non-self target |
| LAST_WORDS | "Good luck to the remaining players." |
| DEFENSE | "I am not Mafia. Please reconsider." |

### Player Agent (`src/players/agent.py`)
- `PlayerAgent` class implementing stateless design
- Constructor: `name`, `persona`, `role`, `seat`, `provider: PlayerProvider`, `partner`
- **Stateless**: Engine owns `PlayerMemory`, passes it each call, agent returns updated memory
- Main method: `act(game_state, transcript, memory, action_type, action_context) -> PlayerResponse`
- Retry logic: up to 3 attempts for invalid outputs, with error feedback in context
- Fallback: defaults applied after validation failures OR provider errors
- Catches: `InvalidResponseError`, `ActionValidationError`, `ProviderError`, `RetryExhausted`
- Memory updates extracted from SGR output: suspicions, patterns, current_goal, last action
- Role-specific context:
  - Mafia: partner name from constructor
  - Detective: investigation results from engine-passed memory (`memory.facts["investigation_results"]`)
  - Town: no extra context
- Langfuse observability: `@observe` decorator on `act()` method

### Package Exports (`src/players/__init__.py`)
- Exports: `PlayerAgent`, `ActionHandler`, `ActionValidationError`

### Tests (`tests/test_player.py`)

| Test Class | Coverage |
|------------|----------|
| TestActionHandler | SPEAK/VOTE/NIGHT_KILL/INVESTIGATION validation (valid, invalid, edge cases) |
| TestActionHandler | Mafia target exclusion, self-investigation rejection |
| TestActionHandler | Default actions for all types, Mafia-only skip edge case |
| TestPlayerAgent | Returns PlayerResponse, updates memory from SGR |
| TestPlayerAgent | Retries on invalid output, uses default after max retries |
| TestPlayerAgent | Retries on InvalidResponseError, falls back on ProviderError/RetryExhausted |
| TestPlayerAgent | Memory updates for VOTE, INVESTIGATION, NIGHT_KILL |
| TestPlayerAgentRoles | Mafia has partner, Detective reads results from memory, Town has no extra |
| TestPlayerAgentRoles | `_get_mafia_names()` returns correct lists by role |

## Files Created/Modified
```
src/players/__init__.py
src/players/actions.py
src/players/agent.py
tests/test_player.py
```

## Design Notes

### Stateless Agent Contract
- Agent has NO instance state for game data (no `self.investigation_results`)
- Engine owns all `PlayerMemory` instances in `memories: dict[str, PlayerMemory]`
- Engine passes memory to agent, agent returns `PlayerResponse.updated_memory`
- Engine persists updated memory for next call
- Detective investigation results stored in `memory.facts["investigation_results"]` by engine (`phases.py`)

### Provider-Agnostic Design
- `PlayerAgent` typed against `PlayerProvider` protocol (not `AnthropicProvider`)
- Any provider implementing `act(action_type, context) -> dict` works
- Provider errors caught and handled gracefully with defaults

### Two-Layer Retry Architecture
```
Agent Layer (invalid outputs)          Provider Layer (API failures)
├── Catches: ActionValidationError     ├── Retries: APIError, timeout
├── Catches: InvalidResponseError      ├── Raises: RetryExhausted (after 3)
├── Retries: 3 attempts with feedback  └── Raises: ProviderError
├── Catches: ProviderError, RetryExhausted
└── Fallback: Default action
```

### Validation Context
- `validate()` accepts `player_name` and `mafia_names` for role-aware validation
- NIGHT_KILL: rejects targets in `mafia_names` (self + partner)
- INVESTIGATION: rejects target == `player_name` (self)
- `get_default()` also accepts these for consistent exclusion

### Deviation from Original Spec
- Added minimum speech length (10 chars) as sanity check to prevent empty speeches
- This may cause extra retries but ensures meaningful output
