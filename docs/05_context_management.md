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
- Game rules summary
- Current phase and round number
- Living/dead player lists

**Accumulated context:**
- Memory and beliefs from previous turns
 - Transcript window (current + previous rounds full, older rounds compressed)

**Turn-specific prompt:**
- Required action (speak, vote, night action, last words)
- Constraints (nominated players, etc.)

**LLM output contract:** Providers return a raw action output dict that matches the action-specific schema. The PlayerAgent validates it and wraps it into `PlayerResponse` with updated memory.

## Event Format

Events are structured facts, not narrative.
EventLog exists for replay/persistence; player context uses transcript + memory.
Only **public** information is reflected in player context via the transcript; private fields
never appear in LLM prompts.

| Event | Fields |
|-------|--------|
| Speech | speaker, text, nomination |
| Vote | votes (dict), outcome, eliminated |
| Night kill | target (or null) |
| Last words | speaker, text (day elimination only) |
| Investigation (Detective only) | target, result (Mafia/Not Mafia) |

Investigation events are private and never appear in the public event stream. Only the
Detective receives investigation results via their memory/context.

## Context by Game Phase

### Night Zero

| Role | Receives |
|------|----------|
| Mafia | Role, partner identity, strategy prompt |
| Detective | Nothing (not called) |
| Town | Nothing (not called) |

**Mafia Coordination (single round):**
- Each Mafia called independently
- Prompt: "You are Mafia. Your partner is [X]. Discuss strategy: signals to use during day discussion, cover stories, initial suspicion targets to push. No kill tonight."
- Each returns: strategy notes
- Engine shares both responses with both Mafia players (stored in their memory for subsequent nights)

### Day One

**Speakers (called in order):** Fixed context + all speeches from this round so far (earlier speakers) + note that no night kill occurred + prompt to speak and nominate

**Voting (after all speeches):** Fixed context + full transcript of all speeches this round + list of nominated players + prompt to vote

### Subsequent Nights

#### Mafia Coordination (2-round protocol)

**Round 1:**
- Each Mafia receives: fixed context, memory, partner identity
- Prompt: "Propose kill target. If both name same player, kill occurs. Round 1 of 2."
- Each Mafia returns: target or "skip"

**Engine resolves Round 1:**
- Same target → execute kill, skip Round 2
- Both "skip" → no kill, skip Round 2
- Different targets → proceed to Round 2

**Round 2 (only if disagreement):**
- Each Mafia receives: fixed context + partner's Round 1 proposal
- Prompt: "Partner proposed [X]. You proposed [Y]. Final round. No agreement = first Mafia by seat decides."
- Each Mafia returns: final target

**Engine resolves Round 2:**
- Both agree → use agreed target
- Still disagree → first Mafia (lower seat number) decides

**Single Mafia alive:** Direct choice, no coordination needed.

#### Detective

- Receives: fixed context, memory, previous results
- Prompt: choose investigation target
- After: receives result

### Subsequent Days

**Order of events:**
1. **Night kill announced** - no last words (night kills are silent)
2. **Discussion** - each speaker called in order
3. **Voting** - all players vote simultaneously
4. **Revote** (if tie) - tied players defend, then revote

**Speakers (called in order):** Fixed context + memory + death announcement + all speeches from this round so far (in-progress) + prompt to speak and nominate

**Tied players (if revote):** Fixed context + context of the tie + prompt for defense speech

**Voting:** Fixed context + full transcript including the current round's speeches + nominated players (or tied players for revote) + prompt to vote

## Transcript Management

Fixed 2-round window for full detail:

| Which Rounds | Detail Level | Rationale |
|--------------|--------------|-----------|
| Current round | Full speeches verbatim | Need exact words to catch contradictions |
| Previous round | Full speeches verbatim | Track momentum, position shifts |
| All older rounds | Compressed summary only | Players should have processed into beliefs already |

**Compressed summary includes:** deaths, major accusations, vote outcomes, role claims.
No hard cap on the number of extracted accusations or claims.

See `src/schemas/transcript.py` for `DayRoundTranscript` and `CompressedRoundSummary`.

## Memory Format

Memory stored by engine and passed back each call includes both **facts** and **beliefs**, matching the `PlayerMemory` schema.

**Factual memory:**
- Key events witnessed
- Claims made by each player
- Votes cast by each player
- Deaths (night kills have no last words; day eliminations do)

**Processed beliefs:**
- Suspicion level for each living player (with reasoning)
- Perceived relationships (alliances, conflicts)
- Behavioral pattern notes

Memory is structured so engine can store between calls. Players return updated memory with each action.

## Information Barriers

Players DON'T receive:
- Other players' private reasoning
- Other players' memory or beliefs
- Dead players' roles (until game end)
- Mafia discussion (for non-Mafia)
- Investigation results (for non-Detective)

## Hallucination Prevention

Every call injects fresh ground truth:
- Exact living/dead player lists
- Player's own role
- Mafia partner identity (Mafia only)
- Detective investigation results (Detective only)

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
Day 1: No elimination. Player 2 accused Player 5.
Night 1: Player 3 killed.
Day 2: Player 5 eliminated (4-2-1). Claimed Town in last words.

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
