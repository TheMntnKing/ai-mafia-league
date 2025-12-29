# Phase 4: Context Builder

**Goal:** Transcript management and context assembly for player LLM calls.

## Deliverables

### Transcript Manager (`src/engine/transcript.py`)
- `TranscriptManager` class for game history with 2-round window
- Current + previous round: full detail (`DayRoundTranscript`)
- Older rounds: compressed summaries (`CompressedRoundSummary`)
- `start_round()`: Set night kill and last words context before discussion
- `add_speech()`: Add speech to current round
- `finalize_round()`: Complete round with votes, defense speeches, revote data
- `get_transcript_for_player()`: Returns windowed transcript (`full=True` for uncompressed)
- Compression extracts: accusations (keyword heuristics), role claims, deaths (no hard caps)

### Context Builder (`src/engine/context.py`)
- `ContextBuilder` class assembling full context strings for LLM calls
- Sections assembled:

| Section | Content |
|---------|---------|
| `[YOUR IDENTITY]` | Name, role, persona details, role-specific guidance |
| `[GAME RULES]` | Rules summary (roles, game flow, constraints) |
| `[CURRENT STATE]` | Phase, round, living/dead players, nominations |
| `[MAFIA INFO]` | Partner name and alive status (Mafia only) |
| `[INVESTIGATION RESULTS]` | Investigation history (Detective only) |
| `[RECENT EVENTS]` | Public events since last turn (private_fields filtered) |
| `[DEFENSE CONTEXT]` | Tied players, vote counts (Defense only) |
| `[TRANSCRIPT]` | Game history (full or compressed) |
| `[YOUR MEMORY]` | Facts and beliefs as JSON |
| `[YOUR TASK: *]` | Action-specific prompt with valid targets |

- Action prompts for: SPEAK, VOTE, NIGHT_KILL, INVESTIGATION, LAST_WORDS, DEFENSE
- Night kill targets exclude all Mafia (self + partner)
- Nomination rule only in SPEAK prompt

### Tests (`tests/test_context.py`)
| Test Class | Coverage |
|------------|----------|
| TestTranscriptManager | Add speech, finalize round, live round with night info, revote data, pending vote_outcome |
| TestTranscriptCompression | 2-round window, accusations extraction, claims extraction, death capture |
| TestContextBuilder | All sections, persona info, Mafia partner, Detective results, action prompts, recent events, transcript rendering, memory JSON |
| TestTranscriptFullMode | `full=True` returns uncompressed |

Additional coverage:
- Defense context with tied_players, vote_counts, votes
- Detective with empty results
- Mafia with dead partner
- INVESTIGATION and LAST_WORDS prompts
- Recent events private_fields filtering

## Files Created
```
src/engine/transcript.py
src/engine/context.py
tests/test_context.py
```

## Design Notes
- `vote_outcome` allows "pending" for in-progress rounds (spec updated)
- Compression uses simple keyword heuristics (intentionally basic, can improve later)
- Compression does not cap the number of extracted accusations/claims
- ContextBuilder trusts caller (engine) to pass correct `extra` data
- Recent events defensively filter `private_fields` to prevent accidental leaks
- **Deviation:** Spec says VOTE requires full transcript, but ContextBuilder doesn't enforce this. Engine must pass `full=True` transcript for VOTE actions.
