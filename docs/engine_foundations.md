# Engine Foundations (Phases 1-9)

Single reference for how the engine works today. This consolidates Phases 1-7 by subsystem
so an LLM can understand how pieces fit together without hopping between task files.
Viewer + log schema upgrades live in Phase 8 and beyond.

**Phase 9 (in progress):** 10 players (3 Mafia + Doctor), decomposed night events,
and prompt/context upgrades are implemented. Remaining tasks: tests, sample log,
viewer parser sync (see `tasks/phase9.md`).

**Phase 9 preload docs:** `tasks/phase9.md`, `tasks/phase8.md`, `docs/02_game_rules.md`,
`docs/05_context_management.md`.

## Current Scope (As Built)
- Player count: 10 (3 Mafia, 1 Detective, 1 Doctor, 5 Town).
- Night Zero: Mafia coordination only (no kill).
- Day/Night loop with plurality voting and optional revote.
- Night kills are silent (no last words).
- Storage is JSON logs (schema v1.3).
- Persona roster: defined in `src/personas/initial.py` (10 total).

## Phase 9 Delta Summary (Implemented)
- Player count: 10 (3 Mafia, 1 Detective, 1 Doctor, 5 Town).
- New action: `DOCTOR_PROTECT`.
- Night events split: `mafia_discussion`, `mafia_vote`, `doctor_protection`,
  `night_resolution` (remove bundled `night_kill`).
- Mafia coordination: 3-way, majority rules with lowest-seat tie-break.
- Log schema bump: v1.3 (see `tasks/phase8.md`).

## Engine Invariants
- LLMs are stateless; the engine owns and persists `PlayerMemory`.
- One LLM call per action (Schema-Guided Reasoning).
- Speakers are called sequentially so later speakers hear earlier speeches.
- Transcript window: current + previous rounds full; older rounds compressed.
- Public/private separation: private reasoning never appears in player context.

## Core Components (How They Fit)
- **GameRunner** orchestrates a full game and writes the final JSON log.
- **GameStateManager** owns rules, roles, nominations, votes, and win checks.
- **Phases** execute Night Zero, Day, and Night logic.
- **TranscriptManager** maintains a 2-round window plus compressed history.
- **ContextBuilder** builds the prompt string for each action.
- **PlayerAgent** calls the LLM provider, validates output, and updates beliefs.
- **Provider** executes a structured LLM call with retries and schema validation.
- **EventLog** captures events for replay and persistence (not used to build prompts).

## Schemas and Contracts
Core models live in `src/schemas/`:
- `ActionType`: `SPEAK`, `VOTE`, `NIGHT_KILL`, `INVESTIGATION`, `DOCTOR_PROTECT`,
  `LAST_WORDS`, `DEFENSE`.
- `GameState`: phase, round, living/dead, nominations.
- `PlayerMemory`: `facts` + `beliefs` (engine persists; agent updates beliefs).
- `PlayerResponse`: action output + updated memory.
- `Event`: type + timestamp + data + private_fields.

SGR output schema (Phase 7 simplification):
```
BaseThinking: observations, suspicions, strategy, reasoning
SpeakingOutput: BaseThinking + speech + nomination
VotingOutput: BaseThinking + vote
NightKillOutput: BaseThinking + message + target
InvestigationOutput: BaseThinking + target
DoctorProtectOutput: BaseThinking + target
LastWordsOutput: reasoning + text
DefenseOutput: reasoning + text
```

## Provider Layer
Location: `src/providers/`
- `PlayerProvider` protocol: `act(action_type, context) -> dict`.
- `retry_with_backoff`: exponential backoff, max 3 attempts.
- `GoogleGenAIProvider`:
  - Uses `response_json_schema` with Pydantic schema per action.
  - Validates output and raises `InvalidResponseError` on schema mismatch.
  - Retries on provider-level errors raised during API calls.

## Game State and Rules (Engine)
Location: `src/engine/state.py`
- Roles: 3 Mafia, 1 Detective, 1 Doctor, 5 Town (randomized each game).
- Seats randomized and used for speaking order rotation.
- Speaking order advances by seat each day; dead seats are skipped.
- Nominations are tracked (unique list).
- Votes must target nominated players or `skip`.
- Role claims are unverified; bluffs are allowed. Do not invent public events.
- Win conditions:
  - Town wins when Mafia count reaches 0.
  - Mafia wins when Mafia >= Town-aligned players.
  - If Doctor is dead and parity is unavoidable after the next night kill,
    the game ends immediately after that day elimination.

## Event Log and JSON Logs
Location: `src/engine/events.py`, `src/storage/json_logs.py`
- EventLog stores events and filters `private_fields` for public view.
- EventLog is not used for player context; transcript + memory are.
- Event types: `phase_start`, `speech`, `vote_round`, `elimination`,
  `mafia_discussion`, `mafia_vote`, `doctor_protection`, `night_resolution`,
  `investigation`, `last_words`, `defense`, `game_end`, `night_zero_strategy`.
- JSON logs schema v1.3 (GameLogWriter). GameRunner adds:
  - `metadata` (seed, model, player_count)
  - `transcript` (full transcript dump)
  - `result` (rounds, eliminations, final living)

## Transcript and Context
Location: `src/engine/transcript.py`, `src/engine/context.py`
- 2-round window: current + previous full detail, older rounds compressed.
- Compression keeps factual outcomes only (vote line + defense marker).
- Last words are included only for day eliminations.
- ContextBuilder sections:
  - Identity + persona play style + role tactics
  - Mafia info (partners list)
  - Mafia coordination context (Night Zero + Night rounds)
  - Role playbook (role-specific tips)
  - Rules summary
  - Current state (phase, round, living/dead, nominations)
  - Speaking order context (SPEAK/DEFENSE)
  - Defense context (tied players, vote counts)
  - Transcript window
  - Memory (fact summary + beliefs)
  - Action-specific task prompt
- Prompt templates live in `src/engine/prompts.py`.

## Player Agent and Validation
Location: `src/players/agent.py`, `src/players/actions.py`
- `ActionHandler` validates outputs and supplies defaults after retries.
- `PlayerAgent` is stateless; engine passes memory each call.
- Agent updates beliefs; engine writes factual night histories.
- Retry flow:
  - Invalid outputs → up to 3 retries with feedback.
  - Provider errors → fallback to defaults.
- Night Zero uses `SPEAK` but skips nomination validation via a flag.

## Mafia Coordination (3 Mafia)
Location: `src/engine/phases.py`
```
Round 1: Each Mafia proposes target + message.
         If 2/3+ agree (including skip), execute.
Round 2: If split, each sees Round 1 proposals.
         If 2/3+ agree, execute; else lowest-seat Mafia decides.
```
Single Mafia alive chooses directly.

## Game Loop (High Level)
1. Initialization: assign roles, create agents/memories.
2. Night Zero: Mafia coordination (no kill).
3. Day 1: speeches → nominations → votes → optional revote → last words (if eliminated).
4. Night: Mafia coordination → Doctor protects → Detective investigates →
   night resolution → apply kill.
5. Repeat Day/Night until win condition.
6. Persist JSON log with full events and transcript.

## Testing Map (Phases 1-7)
- `tests/test_providers.py`: provider retries, schema, observability.
- `tests/test_state.py`: role distribution, transitions, speaking order, event log.
- `tests/test_context.py`: transcript window, compression, context sections.
- `tests/test_player.py`: validation, defaults, retry behavior.
- `tests/test_game.py`: full game orchestration, voting, log schema fields.

## Phase Timeline (Compressed)
- **Phase 1**: Core schemas, config, project scaffolding.
- **Phase 2**: Provider protocol + Anthropic tool_use.
- **Phase 3**: Game state manager + EventLog + JSON logs.
- **Phase 4**: Transcript window + ContextBuilder.
- **Phase 5**: PlayerAgent + validation + stateless memory flow.
- **Phase 6**: Game loop, phases, voting, Night Zero.
- **Phase 7**: SGR simplification, prompt abstraction, mafia coordination tweaks.
