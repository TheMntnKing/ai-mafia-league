# Player Agent

How player agents work internally.

## Overview

A player agent is an LLM-powered entity that plays Mafia. It receives game information, maintains its own understanding, reasons about what to do, and produces actions.

All players share the same structural design but differ only by persona, which includes their reasoning style.

## Player Components

| Component | Description |
|-----------|-------------|
| **Identity** | Name and persona. Fixed for the game. |
| **Role** | Mafia, Detective, Doctor, or Town. Determines private knowledge and actions. |
| **Memory** | Factual record of observations. Facts, not interpretations. |
| **Beliefs** | Player's interpretations: suspicions, trust levels, relationship maps. |
| **Reasoning** | Structured process for deciding actions. |

## Reasoning Approach

We use Schema-Guided Reasoning (SGR). The LLM fills a structured schema where field order matters: earlier fields become context for later fields. This forces a deliberate flow: observe → analyze → strategize → decide → output.

See `src/schemas/actions.py` for action schema definitions.

**Private vs Public:** Reasoning is private, output is public. A Mafia player might reason "deflect suspicion from partner" but say "Player 5's silence concerns me." Viewers see both (dramatic irony). Other players see only the speech.

## Memory

PlayerMemory has two parts: **facts** (engine-owned ground truth for that role) and
**beliefs** (player interpretations). Facts are written by the engine; agents update
beliefs. Public speeches and votes are provided via transcript, not stored in facts.

**What factual memory includes (engine-owned):**
- Mafia kill history (target + outcome)
- Doctor protection history (target + reasoning; no success flag)
- Detective investigation results/history (target + result; history includes reasoning)
- Latest night action snapshots (`last_*`) for the role
- Role-specific private info (investigation results for Detective)

**When memory updates:** Agents update beliefs only when called to act. The engine
may update factual memory after night resolution (kills, protections, results).

**No passive listening:** Players are only called when they need to act (speaking, voting, night action, last words). No LLM calls happen between turns. Listening, processing, and acting happen together in one call.

## Beliefs

Beliefs are interpretations built from memory. Engine provides facts; players construct beliefs.

| Belief Type | Description |
|-------------|-------------|
| Suspicion levels | How likely each player is Mafia |
| Trust levels | How much player trusts each other |
| Relationship map | Alliances, conflicts, voting blocs |
| Behavioral patterns | Aggressive, passive, position changes |
| Meta reads | Who plays well, who might be Detective |

Different players may form different beliefs from the same facts. This is intentional.

## Personas

Personas are the primary differentiator between agents and the main creative dimension for community submissions. A well-crafted persona balances entertainment value with strategic depth.

**Key principle:** Voice + approach define HOW they act. Role tactics define WHAT they do in a role, consistent with the persona.

**Target length:** 200-300 words. Under 180 feels thin; over 400 causes drift and contradictions.

### Persona Structure

All fields are sent to the LLM prompt. See `src/schemas/persona.py` for the `Persona` schema.

```yaml
persona:
  identity:
    name: str
    background: str  # 1-2 sentences, informs motivation
    core_traits: list[str]  # 3-5 role-neutral traits

  play_style:
    voice: str  # 25-40 words: vocabulary, rhythm, tone
    approach: str  # 40-60 words: decision style, risk posture, accuse/defend tendencies
    signature_phrases: list[str]  # 0-3 catchphrases
    signature_moves: list[str]  # 0-2 recurring behaviors

  tactics:  # role-specific, short, actionable bullets
    town: list[str]  # 2-5 bullets
    mafia: list[str]  # 2-5 bullets
    detective: list[str]  # 2-5 bullets
    doctor: list[str]  # 2-5 bullets (optional)

**Role tactics guidance**
- Use short, actionable moves that can actually be performed in a turn.
- Avoid flavor-only text; tactics should change decisions or timing.
- Don’t restate the generic role playbook; make it persona-specific.
```

### Persona as Prompt

The entire persona is rendered into the system prompt for every LLM call. The engine provides structured facts and stores memory/beliefs between turns. The persona instructs the LLM how to interpret facts, what to prioritize, and how to express itself.

## Player Actions

| Action | Input | Output |
|--------|-------|--------|
| Speaking | game state, current round transcript, memory, beliefs | speech, nomination, updated beliefs |
| Voting | game state, full day transcript, nominated players | vote choice, updated beliefs |
| Defense | game state, accusation context | defense speech |
| Last words | game state, full memory | final statement |
| Night kill (Mafia) | game state, Round 1 proposals (if Round 2) | target or skip + partner message |
| Investigation (Detective) | game state, all previous results | target |
| Protection (Doctor) | game state, previous protections | target |

All actions also include fixed context (role, persona, living/dead lists), plus role playbooks and SGR field guidance in the prompts. See [05_context_management.md](05_context_management.md) for full details.

## Mafia Coordination

See [05_context_management.md](05_context_management.md) for detailed coordination protocol.

Summary: Round 1 proposals; if 2/3+ agree, execute. If split, Round 2. If still split, lowest-seat Mafia decides. Coordination is private.

## Statelessness

LLMs are stateless. Engine manages continuity:
1. After each call, engine stores player's memory and beliefs
2. On next call, engine passes stored memory + beliefs + new events since last call
3. Player processes everything, produces action + updated beliefs
4. Engine stores beliefs and augments facts as needed

Each call is self-contained from player's perspective.

## What Differentiates Players

All players share the same:
- SGR reasoning structure
- Input/output interface
- Game engine and rules
- Base model (per game configuration)

Players differ only by **persona** - which includes identity, play style, and role tactics (see Personas section above).

This is intentional. The creative challenge is crafting personas that are both entertaining to watch and effective at the game. There are no separate "AI architecture" or "reasoning strategy" modules to customize - the persona IS the strategy.
