# Context Management

What information players receive, when, and in what format.

## Core Principle

Engine provides ground truth facts. Players build interpretations.

| Engine Provides | Players Build |
|-----------------|---------------|
| Speeches, votes, deaths | Suspicions, trust levels |
| Game state (alive/dead, phase) | Relationship maps |
| Player's role and private knowledge | Pattern recognition |

## What Players Receive Each Call

**Fixed context (every call):**
- Role and private knowledge
- Persona description
- Role playbook (role-specific strategy tips)
- Game rules summary
- Current phase and round number
- Living/dead player lists

**Accumulated context:**
- Memory and beliefs from previous turns
- Transcript window (current + previous rounds full, older rounds compressed)

**Turn-specific prompt:**
- Required action (speak, vote, night action, last words)
- Constraints (nominated players, etc.)
- SGR field guide that clarifies how to fill observations/suspicions/strategy/reasoning
- For last words, a `game_over` hint may be passed when the elimination ends the game

**LLM output contract:** Providers return a raw action output dict that matches the action-specific schema. The PlayerAgent validates it and wraps it into `PlayerResponse` with updated memory.

## Event Format

Events are structured facts, not narrative.
EventLog exists for replay/persistence; player context uses transcript + memory.
Only **public** information is reflected in player context via the transcript; private fields
never appear in LLM prompts.

| Event | Fields |
|-------|--------|
| Speech | speaker, text, nomination |
| Vote round | votes (dict), outcome, round |
| Elimination | eliminated |
| Last words | speaker, text (day elimination only) |
| Investigation (Detective only) | target, result (Mafia/Not Mafia) |
| Mafia discussion | speaker, target, message, reasoning, coordination_round (private) |
| Mafia vote | votes, final_target, decided_by, coordination_round (private) |
| Doctor protection | protector, protected, reasoning (private) |
| Night resolution | intended_kill, protected, actual_kill |

Investigation, Mafia coordination, and Doctor protection events are private and never
appear in public player context. Only the relevant role receives those details via
their memory/context.

For `night_resolution`, only `actual_kill` is public; `intended_kill` and `protected`
are private fields.

## Context by Game Phase

### Night Zero

| Role | Receives |
|------|----------|
| Mafia | Role, partner identities, strategy prompt |
| Detective | Nothing (not called) |
| Doctor | Nothing (not called) |
| Town | Nothing (not called) |

**Mafia Coordination (single round):**
- Mafia are called sequentially (seat order) so later Mafia see earlier strategies
- Prompt: "You are Mafia. Your partners are [X, Y]. Discuss strategy: signals to use during day discussion, cover stories, initial suspicion targets to push. No kill tonight."
- Each returns: strategy notes
- Engine shares all responses with all Mafia players (stored in their memory for subsequent nights)

### Day One

**Speakers (called in order):** Fixed context + all speeches from this round so far (earlier speakers) + note that no night kill occurred + prompt to speak and nominate

**Voting (after all speeches):** Fixed context + full transcript of all speeches this round + list of nominated players + prompt to vote

### Subsequent Nights

#### Mafia Coordination (2-round protocol)

**Round 1:**
- Mafia are called sequentially; later Mafia receive prior proposals + messages
- Each Mafia receives: fixed context, memory, partner identities
- Prompt: "Propose kill target. If 2/3+ agree, kill occurs. Round 1 of 2."
- Each Mafia returns: target or "skip" + message to partners

**Engine resolves Round 1:**
- 2/3+ agreement → execute kill, skip Round 2
- All different → proceed to Round 2
Note: "skip" counts as a target for agreement.

**Round 2 (only if disagreement):**
- Each Mafia receives: fixed context + all Round 1 proposals + messages
- Prompt: "Round 2. Try to reach consensus. No agreement = lowest-seat Mafia decides."
- Each Mafia returns: final target

**Engine resolves Round 2:**
- 2/3+ agreement → use agreed target
- Still split → lowest-seat Mafia decides

**Single Mafia alive:** Direct choice, no coordination needed.

#### Doctor

- Receives: fixed context, memory, previous protections (history; no success flag)
- Prompt: choose a protection target (may self-protect)
- Doctor is not told whether protection succeeded; they can infer only from public outcomes

#### Detective

- Receives: fixed context, memory, previous results + investigation history
- Prompt: choose investigation target
- After: receives result

### Subsequent Days

**Order of events:**
1. **Night kill announced** - no last words (night kills are silent)
2. **Discussion** - each speaker called in order
3. **Voting** - all players vote simultaneously
4. **Revote** (if tie) - tied players defend, then revote

**Speakers (called in order):** Fixed context + memory + speaking-order context + death announcement + all speeches from this round so far (in-progress) + prompt to speak and nominate

**Tied players (if revote):** Fixed context + context of the tie + speaking-order context + prompt for defense speech

**Voting:** Fixed context + full transcript including the current round's speeches + nominated players (or tied players for revote) + prompt to vote

## Transcript Management

Fixed 2-round window for full detail:

| Which Rounds | Detail Level | Rationale |
|--------------|--------------|-----------|
| Current round | Full speeches verbatim | Need exact words to catch contradictions |
| Previous round | Full speeches verbatim | Track momentum, position shifts |
| All older rounds | Compressed summary only | Players should have processed into beliefs already |

**Full transcript shape (current):**
- `round_number`
- `night_kill` (None for Day 1)
- `speeches` (speaker, text, nomination)
- `votes` (voter -> target/skip) + `vote_outcome`
- `defense_speeches`, `revote`, `revote_outcome` (only if revote)
- `last_words` (day eliminations only)

**Compressed summary shape (current):**
- `round_number`, `night_death`, `vote_death`, `vote_result`
- `vote_line` (deterministic vote line), `defense_note` (revote/defense marker)

See `src/schemas/transcript.py` for `DayRoundTranscript` and `CompressedRoundSummary`.

## Memory Format

Memory stored by engine and passed back each call includes both **facts** and **beliefs**, matching the `PlayerMemory` schema.

**Factual memory (engine-owned):**
- Mafia kill history (target + outcome)
- Doctor protection history (target + reasoning; no success flag)
- Detective investigation results/history (target + result; history includes reasoning)
- Latest night action snapshots (`last_*`) for the role

**Processed beliefs:**
- Suspicion level for each living player (with reasoning)
- Perceived relationships (alliances, conflicts)
- Behavioral pattern notes

Memory is structured so engine can store between calls. Players return updated beliefs with each action; the engine augments factual memory as needed.

## Information Barriers

Players DON'T receive:
- Other players' private reasoning
- Other players' memory or beliefs
- Dead players' roles (until game end)
- Mafia discussion (for non-Mafia)
- Investigation results (for non-Detective)
- Doctor protection details (for non-Doctor)

## Hallucination Prevention

Every call injects fresh ground truth:
- Exact living/dead player lists
- Player's own role
- Mafia partner identities (Mafia only)
- Mafia kill history (Mafia only)
- Detective investigation results (Detective only)
- Doctor protection history (Doctor only, no success flag)

Format: structured data, explicit lists, current state separated from history.

## Example Context

```
[ROLE AND IDENTITY]
You are Player 4. Your role is Town.
Your persona: [description]

[GAME STATE]
Round: Day 3
Living: Player 1, Player 2, Player 4, Player 7
Dead: Player 3 (night 1), Player 5 (voted day 2), Player 6 (night 2)

[PREVIOUS ROUNDS SUMMARY]
Day 1: No elimination.
Night 1: Player 3 killed.
Day 2: Player 5 eliminated (4-2-1).

[CURRENT ROUND]
Night 2: Player 6 killed.

Discussion so far:
- Player 1: [speech] Nominated Player 2.
- Player 2: [speech] Nominated Player 7.

[YOUR MEMORY AND BELIEFS]
[stored from previous turns]

[YOUR TASK]
Speak and nominate one player.
```
