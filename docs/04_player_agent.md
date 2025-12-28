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

Each player has a persona defining personality and style:

- **Name:** Identity in the game
- **Personality traits:** Aggressive/cautious, logical/emotional, trusting/paranoid
- **Speech style:** Formal/casual, verbose/terse, direct/indirect
- **Strategic tendencies:** How they play as Town vs Mafia
- **Quirks:** Distinctive behaviors recognizable across games

**Consistency requirement:** Same personality whether Town or Mafia (otherwise role is obvious). Persona is injected into every LLM call.

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

## Skill Differentiation

**MVP:** All players use same reasoning structure, differ only by persona and model.

**Future competition:** Customizable elements become skill dimension:
- Reasoning schema design
- Memory strategy
- Belief formation
- Attention patterns

**Fixed:** Input/output interface, base model, game rules.
