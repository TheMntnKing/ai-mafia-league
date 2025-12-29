# Implementation Plan

Phased approach to build the AI Mafia Agent League MVP.

## Decisions

- **First milestone:** Phases 1-6 (full working game loop)
- **Provider strategy:** Anthropic only (Claude Haiku 4.5), add others later
- **Testing:** Test as we go - each phase includes tests
- **Observability:** Langfuse from the start

---

## Phase 1: Project Foundation

**Goal:** Establish project structure, dependencies, and core data models

### Tasks

1.1. Create `pyproject.toml` with project metadata and dependencies:
- Core: anthropic, pydantic, aiosqlite, langfuse, rich
- Dev: pytest, pytest-asyncio, ruff

1.2. Create directory structure:
```
/src
├── __init__.py
├── /schemas
├── /providers
├── /engine
├── /players
├── /personas
└── /storage
/tests
/data
/logs
```

1.3. Split `docs/schemas.py` into `src/schemas/` modules:
- `core.py` - GameState, PlayerMemory, Event, ActionType
- `actions.py` - SGR output schemas (SpeakingOutput, VotingOutput, etc.)
- `transcript.py` - DayRoundTranscript, CompressedRoundSummary, Speech
- `persona.py` - Persona, PersonaIdentity, VoiceAndBehavior, RoleGuidance

1.4. Create `src/storage/database.py`:
- Async SQLite wrapper using aiosqlite
- Initialize from `docs/database.sql` schema
- Basic CRUD for personas and games tables

1.5. Create `src/config.py`:
- Environment variable loading (API keys)
- Model configuration defaults

1.6. Set up pytest in `tests/conftest.py`:
- Async test fixtures
- Temporary database fixture

### Deliverables
- `pip install -e ".[dev]"` works
- `pytest` runs (even with no tests yet)
- `ruff check .` passes

---

## Phase 2: LLM Provider Layer

**Goal:** Anthropic provider with structured output and observability

### Tasks

2.1. Create `src/providers/base.py`:
- `PlayerProvider` protocol (from docs/schemas.py), e.g. `act(action_type, context)`
- Base exception classes (ProviderError, RetryExhausted)
- Retry decorator with exponential backoff (max 3 attempts)

2.2. Create `src/providers/anthropic.py`:
- `AnthropicProvider` implementing `PlayerProvider`
- Claude Haiku 4.5 with tool_use for structured output
- Langfuse `@observe` decorator on API calls
- Parse structured response into action-specific schema based on `action_type`

2.3. Create `tests/test_providers.py`:
- Mock anthropic client responses
- Test retry logic (success after failure)
- Test structured output parsing
- Test error handling

### Deliverables
- Can instantiate provider and make (mocked) calls
- Langfuse traces appear in dashboard
- All provider tests pass

---

## Phase 3: Game State & Event System

**Goal:** Core game state management and event logging

### Tasks

3.1. Create `src/engine/state.py`:
- `GameStateManager` class
- Initialize with 7 players:
  - Randomize seating order (seat 0-6)
  - Assign roles randomly (2 Mafia, 1 Detective, 4 Town)
- Track: phase, round_number, living_players, dead_players, nominations
- Phase transitions: night_zero → day_1 → night_1 → day_2 → ...
- Win condition checks:
  - Town wins: both Mafia dead
  - Mafia wins: Mafia count >= Town-aligned count

3.2. Create `src/engine/events.py`:
- `EventLog` class managing list of `Event`
- Add events: phase_start, speech, vote, night_kill, investigation, last_words, defense, game_end
- Filter events for public view (remove private_fields)
- Get events since timestamp/index

3.3. Create `src/storage/json_logs.py`:
- `GameLogWriter` class
- Schema version 1.0 format (per docs/schemas.py)
- Write complete game to `logs/game_{id}.json`
- Include player entries with roles and outcomes

3.4. Create `tests/test_state.py`:
- Test role assignment (2 Mafia, 1 Detective, 4 Town)
- Test phase transitions
- Test win conditions (various scenarios)
- Test player death updates

### Deliverables
- GameStateManager correctly tracks game progression
- Events logged with proper public/private filtering
- JSON logs written in correct format

---

## Phase 4: Context Builder

**Goal:** Build player context from game state and history

### Tasks

4.1. Create `src/engine/transcript.py`:
- `TranscriptManager` class
- Store `DayRoundTranscript` for each completed day
- Compress old rounds to `CompressedRoundSummary`:
  - Keep: round_number, night_death, vote_death, vote_result
  - Extract: major accusations, role claims
- Window: full detail for current + previous round, compressed for older

4.2. Create `src/engine/context.py`:
- `ContextBuilder` class
- Build fixed context: role, persona description, rules summary, game state
- Build accumulated context: memory, beliefs, events since last turn
- **Use public-filtered event stream only** (no private reasoning from other players)
- Build action-specific prompts (string) for each ActionType:
  - SPEAK: transcript so far, prompt to speak and nominate
  - VOTE: full transcript, nominated players, prompt to vote
  - NIGHT_KILL: partner info, prompt for target
  - INVESTIGATION: previous results, prompt for target
  - LAST_WORDS: full memory, prompt for final statement
  - DEFENSE: accusation context, prompt for defense

4.3. Create prompt templates:
- System prompt with rules summary
- Role-specific instructions (Mafia partner info, Detective results)
- Action-specific instructions

4.4. Create `tests/test_context.py`:
- Test transcript compression
- Test context assembly for each action type
- Test 2-round window (old rounds compressed)
- Test role-specific context (Mafia sees partner, Detective sees results)

### Deliverables
- Context correctly assembled for any game state
- Transcripts compressed after 2 rounds
- Prompt templates for all action types

---

## Phase 5: Player Agent

**Goal:** LLM-powered player that reasons and acts

### Tasks

5.1. Create `src/players/agent.py`:
- `PlayerAgent` class
- Constructor: provider, persona, role, seat, partner (if Mafia)
- **Stateless**: engine owns and passes PlayerMemory each call
- Main method: `async def act(game_state, transcript, memory, action_type) -> PlayerResponse`
- Returns PlayerResponse containing output + updated_memory (engine persists)

5.2. Create `src/players/actions.py`:
- Action handlers for each ActionType
- Parse provider response into correct schema
- Validate outputs:
  - SPEAK: nomination must be living player
  - VOTE: must be nominated player or "skip"
  - NIGHT_KILL: must be living non-Mafia or "skip"
  - INVESTIGATION: must be living non-self player
- Handle invalid actions: retry up to 3 times, then apply default

5.3. Implement default actions (fallback after retries):
- SPEAK: random valid nomination, generic speech
- VOTE: skip
- NIGHT_KILL: random valid target
- INVESTIGATION: random valid target

5.4. Create `tests/test_player.py`:
- Mock provider responses
- Test action parsing and validation
- Test memory updates
- Test invalid action handling and defaults
- Test role-specific behavior

### Deliverables
- PlayerAgent can execute all action types
- Invalid actions handled gracefully
- Memory persists between turns

---

## Phase 6: Game Loop

**Goal:** Complete game orchestration — FIRST MILESTONE

### Tasks

6.1. Create `src/engine/voting.py`:
- `VoteResolver` class
- Collect votes from all players
- Determine outcome:
  - Majority reached: return eliminated player
  - Tie for most (no majority): return tied players for revote
  - No majority, no tie: return no elimination
- Handle revote: same logic with tied players + skip

6.2. Create `src/engine/phases.py`:
- `NightZeroPhase`: Mafia coordination (single round, share strategies)
- `DayPhase`:
  - Announce death (if any), collect last words
  - Run discussion: call speakers in order, collect speeches + nominations
  - Run voting: collect votes, resolve
  - Run revote if needed: defenses, revote, resolve
- `NightPhase`:
  - Mafia coordination (2-round protocol)
  - Detective investigation
  - Record kill (if any)

6.3. Create `src/engine/game.py`:
- `GameRunner` class
- Initialize: create players, assign roles, set up state
- Main loop:
  - Night Zero
  - Day 1 (no death)
  - Loop: Night → Day until win condition
- Speaking order rotation: advances by 1 seat each day
- End game: announce winner, reveal roles, write log

6.4. Create `src/personas/initial.py`:
- 7 hardcoded personas following `Persona` schema from [04_player_agent.md](04_player_agent.md):
  - Identity: name, background, core_traits (3-5 role-neutral)
  - Voice and behavior: speech_style, reasoning_style, accusation_style, defense_style, trust_disposition, risk_tolerance, signature_phrases, quirks
  - Role guidance: brief (1-2 sentences each) contextualization for town/mafia/detective
  - Relationships: optional fixed lore with other personas
- Personas should be diverse and entertaining, not just effective
- Target 250-400 words per persona

6.5. Create simple runner script `src/engine/run.py`:
- Parse arguments: output path
- Load personas
- Create provider
- Run game
- Save log

6.6. Create `tests/test_game.py`:
- Integration test with mocked provider
- Test full game to completion
- Test various end conditions
- Test speaking order rotation
- Test Mafia coordination protocol

### Deliverables
- `python -m src.engine.run` executes a complete game
- Game log saved to `logs/`
- All game rules enforced correctly

---

## Post-MVP Phases

### Phase 7: Personas & Community
- Persona data model with SQLite persistence
- Expand roster to 10+ personas with diverse entertainment styles
- Basic stats (games played, wins) for viewer interest - not competitive ranking
- Community persona submission format and guidelines

### Phase 8: CLI & Polish
- Rich console output during game
- Configuration file support
- Game replay viewer
- Better error messages

### Future
- Additional providers (Gemini, OpenAI-compatible)
- Narrator system
- Tournament mode
- Evaluation framework

---

## File Map

```
/src
├── __init__.py
├── config.py                    # Phase 1
├── /schemas
│   ├── __init__.py              # Phase 1
│   ├── core.py                  # Phase 1
│   ├── actions.py               # Phase 1
│   ├── transcript.py            # Phase 1
│   └── persona.py               # Phase 1
├── /providers
│   ├── __init__.py              # Phase 2
│   ├── base.py                  # Phase 2
│   └── anthropic.py             # Phase 2
├── /engine
│   ├── __init__.py              # Phase 3
│   ├── state.py                 # Phase 3
│   ├── events.py                # Phase 3
│   ├── transcript.py            # Phase 4
│   ├── context.py               # Phase 4
│   ├── voting.py                # Phase 6
│   ├── phases.py                # Phase 6
│   ├── game.py                  # Phase 6
│   └── run.py                   # Phase 6
├── /players
│   ├── __init__.py              # Phase 5
│   ├── agent.py                 # Phase 5
│   └── actions.py               # Phase 5
├── /personas
│   ├── __init__.py              # Phase 6
│   └── initial.py               # Phase 6
└── /storage
    ├── __init__.py              # Phase 1
    ├── database.py              # Phase 1
    └── json_logs.py             # Phase 3

/tests
├── conftest.py                  # Phase 1
├── test_providers.py            # Phase 2
├── test_state.py                # Phase 3
├── test_context.py              # Phase 4
├── test_player.py               # Phase 5
└── test_game.py                 # Phase 6
```
