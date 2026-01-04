# Phase 4: Context Builder

**Goal:** Transcript management and context assembly for player LLM calls.

## Deliverables

### Transcript Manager (`src/engine/transcript.py`)
- `TranscriptManager` class for game history with 2-round window
- Current + previous round: full detail (`DayRoundTranscript`)
- Older rounds: compressed summaries (`CompressedRoundSummary`)
- `start_round(round_number, night_kill)`: Set night kill context before discussion (no last words for night kills - they are silent)
- `add_speech()`: Add speech to current round
- `finalize_round()`: Complete round with votes, defense speeches, revote data (last words only for day eliminations)
- `get_transcript_for_player()`: Returns windowed transcript (`full=True` for uncompressed)
- Compression keeps factual outcomes only: deaths, final vote result, final vote line, defense marker

### Context Builder (`src/engine/context.py`)
- `ContextBuilder` class assembling full context strings for LLM calls
- Sections assembled:

| Section | Content |
|---------|---------|
| `[YOUR IDENTITY]` | Name, role, persona details, role-specific guidance |
| `[GAME RULES]` | Rules summary (roles, game flow, constraints) |
| `[CURRENT STATE]` | Phase, round, living/dead players, nominations |
| `[MAFIA INFO]` | Partner list (Mafia only) |
| `[ROLE PLAYBOOK]` | Advisory tactics per role |
| `[DEFENSE CONTEXT]` | Tied players, vote counts (Defense only) |
| `[TRANSCRIPT]` | Game history (full or compressed) |
| `[YOUR MEMORY]` | Facts and beliefs as JSON |
| `[YOUR TASK: *]` | Action-specific prompt with valid targets |

- Action prompts for: SPEAK, VOTE, NIGHT_KILL, INVESTIGATION, DOCTOR_PROTECT, LAST_WORDS, DEFENSE
- Night kill targets exclude all Mafia (self + partners)
- Nomination rule only in SPEAK prompt

### Tests (`tests/test_context.py`)
| Test Class | Coverage |
|------------|----------|
| TestTranscriptManager | Add speech, finalize round, live round with night info, revote data, pending vote_outcome |
| TestTranscriptCompression | 2-round window, death capture, vote line/defense marker |
| TestContextBuilder | All sections, persona info, Mafia partners, action prompts, transcript rendering, memory JSON |
| TestTranscriptFullMode | `full=True` returns uncompressed |

Additional coverage:
- Defense context with tied_players, vote_counts, votes
- Detective with empty results
- Mafia with dead partner
- INVESTIGATION and LAST_WORDS prompts

## Files Created
```
src/engine/transcript.py
src/engine/context.py
tests/test_context.py
```

## Design Notes
- `vote_outcome` allows "pending" for in-progress rounds (spec updated)
- Compression keeps factual outcomes only (no heuristic accusations/claims)
- ContextBuilder trusts caller (engine) to pass correct `extra` data
- **Deviation:** Spec says VOTE requires full transcript, but ContextBuilder doesn't enforce this. Engine must pass `full=True` transcript for VOTE actions.

### Last Words Policy (updated in Phase 6)
- **Night kills**: No last words (silent kills - victim doesn't know it's coming)
- **Day eliminations**: Last words collected before player is killed
- `start_round()` only receives `night_kill` parameter, no last_words
- `finalize_round()` stores `last_words=None` for night kills in transcript
- Strategic implication: Detective eliminated by vote can reveal results; killed at night cannot

### Mafia Coordination Context (added in Phase 6)
- ContextBuilder extended with `_build_mafia_coordination_section()` method
- Renders `[PARTNER STRATEGIES]` section for NightZero (Mafia see prior strategies)
- Renders coordination sections for Round 1 and Round 2 proposals/messages
- Keys in `extra` dict: `partner_strategies`, `prior_proposals`, `prior_messages`, `r1_proposals`, `r1_messages`
