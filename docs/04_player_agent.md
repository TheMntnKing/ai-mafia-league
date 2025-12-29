# Player Agent

How player agents work internally.

## Overview

A player agent is an LLM-powered entity that plays Mafia. It receives game information, maintains its own understanding, reasons about what to do, and produces actions.

All players share the same structural design but differ in persona and potentially in reasoning strategy.

## Player Components

| Component | Description |
|-----------|-------------|
| **Identity** | Name and persona. Fixed for the game. |
| **Role** | Mafia, Detective, or Town. Determines private knowledge and actions. |
| **Memory** | Factual record of observations. Facts, not interpretations. |
| **Beliefs** | Player's interpretations: suspicions, trust levels, relationship maps. |
| **Reasoning** | Structured process for deciding actions. |

## Reasoning Approach

We use Schema-Guided Reasoning (SGR). The LLM fills a structured schema where field order matters: earlier fields become context for later fields. This forces a deliberate flow: observe → analyze → strategize → decide → output.

See [schemas.py](schemas.py) for schema definitions.

**Private vs Public:** Reasoning is private, output is public. A Mafia player might reason "deflect suspicion from partner" but say "Player 5's silence concerns me." Viewers see both (dramatic irony). Other players see only the speech.

## Memory

Memory is facts, not judgments. "Player 3 accused Player 5 in round 2" is memory. "Player 3 is suspicious" is belief.

**What memory includes:**
- Speeches heard (who said what, in order)
- Nominations and votes
- Deaths (no role information)
- Own past reasoning and decisions
- Role-specific private info (partner identity for Mafia, investigation results for Detective)

**When memory updates:** Only when player is called to act. Between turns, engine accumulates events. On player's turn, they receive all new events, process them, reason, and produce action—all in one LLM call.

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

**Key principle:** Behavioral invariants define HOW they act. Role guidance only contextualizes, never introduces new tactics. This prevents role leakage.

**Target length:** 250-400 words. Under 200 feels thin; over 500 causes drift and contradictions. Aim for ~300-350.

### Persona Structure

All fields are sent to the LLM prompt. See `Persona` schema in [schemas.py](schemas.py).

```yaml
persona:
  identity:
    name: str
    background: str  # 1-2 sentences, informs motivation
    core_traits: list[str]  # 3-5 role-neutral traits

  voice_and_behavior:
    speech_style: str  # vocabulary, structure, tone
    reasoning_style: str  # how they analyze (logical, intuitive, pattern-based, absurdist)
    accusation_style: str  # how/when they target others
    defense_style: str  # how they handle being accused
    trust_disposition: str  # paranoid, neutral, trusting, conditional
    risk_tolerance: str  # aggressive plays vs safe plays
    signature_phrases: list[str]  # 0-3 catchphrases
    quirks: list[str]  # 0-3 recognizable behaviors

  role_guidance:  # optional, brief - contextualizes, doesn't introduce new tactics
    town: str  # 1-2 sentences applying traits
    mafia: str  # 1-2 sentences applying traits
    detective: str  # 1-2 sentences applying traits

  relationships:  # optional, fixed lore between personas
    other_persona_name: str  # relationship description
```

### Relationships

Relationships between personas can be:
- **Fixed lore** (in persona.relationships): Pre-existing rivalries or alliances that affect behavior. Sent to LLM.
- **Dynamic** (in memory): Built during games, tracked in player memory state between turns.

Example fixed lore: `{"Moriarty": "Ancient rival - always suspects, never trusts"}`

### Persona as Prompt

The entire persona is rendered into the system prompt for every LLM call. The engine provides structured facts and stores memory/beliefs between turns. The persona instructs the LLM how to interpret facts, what to prioritize, and how to express itself.

## Player Actions

| Action | Input | Output |
|--------|-------|--------|
| Speaking | game state, current round transcript, memory, beliefs | speech, nomination, updated beliefs |
| Voting | game state, full day transcript, nominated players | vote choice, updated beliefs |
| Defense | game state, accusation context | defense speech |
| Last words | game state, full memory | final statement |
| Night kill (Mafia) | game state, partner's proposal (if Round 2) | target or skip |
| Investigation (Detective) | game state, all previous results | target |

All actions also include fixed context (role, persona, living/dead lists). See [05_context_management.md](05_context_management.md) for full details.

## Mafia Coordination

See [05_context_management.md](05_context_management.md) for detailed 2-round coordination protocol.

Summary: Up to 2 rounds of discussion. If no consensus, first Mafia (by seat order) decides. Coordination is private.

## Statelessness

LLMs are stateless. Engine manages continuity:
1. After each call, engine stores player's memory and beliefs
2. On next call, engine passes stored memory + beliefs + new events since last call
3. Player processes everything, produces action + updated memory + updated beliefs
4. Engine stores the updates for next time

Each call is self-contained from player's perspective.

## What Differentiates Players

All players share the same:
- SGR reasoning structure
- Input/output interface
- Game engine and rules
- Base model (per game configuration)

Players differ only by **persona** - which includes identity, voice and behavior, role guidance, and relationships (see Personas section above).

This is intentional. The creative challenge is crafting personas that are both entertaining to watch and effective at the game. There are no separate "AI architecture" or "reasoning strategy" modules to customize - the persona IS the strategy.
