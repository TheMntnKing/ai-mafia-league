"""
AI Mafia Agent League - Schema Definitions

Schema-Guided Reasoning (SGR) schemas for player actions.
Field order matters: earlier fields become context for later fields.
Flow: observe → analyze → strategize → decide → output
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

# =============================================================================
# Core Types
# =============================================================================

class ActionType(str, Enum):
    """What action the player needs to take."""
    SPEAK = "speak"
    VOTE = "vote"
    DEFENSE = "defense"
    LAST_WORDS = "last_words"
    NIGHT_KILL = "night_kill"
    INVESTIGATION = "investigation"


class GameState(BaseModel):
    """Current game state passed to players."""
    phase: str  # "night_zero", "day_1", "night_1", "day_2", etc.
    round_number: int
    living_players: list[str]
    dead_players: list[str]  # Names only, no roles
    nominated_players: list[str]  # For voting phase, empty otherwise


class PlayerMemory(BaseModel):
    """
    Player's stored memory between calls.
    Structure is intentionally loose - implementation decides format.
    """
    facts: dict  # Observed events, claims, votes, deaths
    beliefs: dict  # Suspicions, relationships, patterns


class PlayerResponse(BaseModel):
    """What a player returns after acting."""
    output: dict  # Must match the action-specific schema (SpeakingOutput, VotingOutput, etc.)
    updated_memory: PlayerMemory


class Event(BaseModel):
    """Single game event in the log."""
    type: str  # See event types in Game Log Schema section
    timestamp: str  # ISO8601
    data: dict  # Type-specific fields
    private_fields: list[str] = Field(default_factory=list)  # Fields in data to filter for public view


# =============================================================================
# Persona Schemas
# =============================================================================

class PersonaIdentity(BaseModel):
    """Core identity of a persona."""
    name: str
    background: str  # 1-2 sentences, informs motivation
    core_traits: list[str] = Field(min_length=3, max_length=5)  # Role-neutral traits


class VoiceAndBehavior(BaseModel):
    """How the persona speaks, thinks, and acts. These are behavioral invariants."""
    speech_style: str  # vocabulary, structure, tone
    reasoning_style: str  # how they analyze (logical, intuitive, pattern-based, absurdist)
    accusation_style: str  # how/when they target others
    defense_style: str  # how they handle being accused
    trust_disposition: str  # paranoid, neutral, trusting, conditional
    risk_tolerance: str  # aggressive plays vs safe plays
    signature_phrases: list[str] = Field(default_factory=list, max_length=3)
    quirks: list[str] = Field(default_factory=list, max_length=3)


class RoleGuidance(BaseModel):
    """
    Brief contextualization of how traits apply to each role.
    1-2 sentences each. Tactics are allowed only if consistent with behavioral invariants.
    """
    town: str
    mafia: str
    detective: str


class Persona(BaseModel):
    """
    Complete persona definition. Entire structure is sent to LLM prompt.

    Target length: 250-400 words when rendered as prompt.
    Under 200 feels thin; over 500 causes drift and contradictions.

    Key principle: Behavioral invariants define HOW they act.
    Role guidance may include tactics only if they are consistent with behavioral invariants.
    """
    identity: PersonaIdentity
    voice_and_behavior: VoiceAndBehavior
    role_guidance: RoleGuidance | None = None  # Optional but recommended
    relationships: dict[str, str] = Field(default_factory=dict)  # persona_name -> relationship description


# =============================================================================
# SGR Output Schemas
# =============================================================================

class BaseThinking(BaseModel):
    """Common reasoning fields for all actions."""
    # Observation
    new_events: list[str]
    notable_changes: list[str]

    # Analysis
    suspicion_updates: dict[str, str]  # player -> assessment
    pattern_notes: list[str]

    # Strategy
    current_goal: str
    reasoning: str


class SpeakingOutput(BaseThinking):
    """Day phase: speaking turn."""
    information_to_share: list[str]
    information_to_hide: list[str]
    speech: str
    nomination: str


class VotingOutput(BaseThinking):
    """Day phase: voting."""
    vote_reasoning: str
    vote: str  # player name or "skip"


class NightKillOutput(BaseThinking):
    """Night phase: Mafia kill target."""
    target_reasoning: str
    target: str  # player name or "skip"


class InvestigationOutput(BaseThinking):
    """Night phase: Detective investigation."""
    target_reasoning: str
    target: str  # player name


class LastWordsOutput(BaseModel):
    """Eliminated player's final statement."""
    text: str


class DefenseOutput(BaseModel):
    """Revote: defense speech."""
    text: str


# =============================================================================
# Transcript Schemas
# =============================================================================

class Speech(BaseModel):
    """Single speech in discussion."""
    speaker: str
    text: str
    nomination: str


class DefenseSpeech(BaseModel):
    """Defense speech during revote (no nomination)."""
    speaker: str
    text: str


class DayRoundTranscript(BaseModel):
    """
    Full detail transcript for a day round.

    A "round" = one Day phase, includes preceding night's outcome.
    Round 1 = Day 1 (no night kill), Round 2 = Day 2 (includes Night 1 kill), etc.
    """
    round_number: int
    night_kill: str | None  # Who died preceding night, or None
    last_words: str | None  # Killed player's last words
    speeches: list[Speech]
    votes: dict[str, str]  # player -> target or "skip"
    # "eliminated:{name}", "no_elimination", "revote", or "pending" (in-progress)
    vote_outcome: str
    defense_speeches: list[DefenseSpeech] | None  # If revote
    revote: dict[str, str] | None
    revote_outcome: str | None


class CompressedRoundSummary(BaseModel):
    """Compressed summary for older rounds (2+ rounds ago)."""
    round_number: int
    night_death: str | None
    vote_death: str | None
    accusations: list[str]
    vote_result: str
    claims: list[str]


# =============================================================================
# Provider Interface
# =============================================================================

Transcript = list[DayRoundTranscript | CompressedRoundSummary]


class PlayerProvider(Protocol):
    """Common interface for all LLM providers."""
    async def act(
        self,
        action_type: ActionType,
        context: str
    ) -> dict:
        ...


# =============================================================================
# Game Log Schema
# =============================================================================

"""
Single JSON log per game. Each Event has private_fields listing which
data fields to filter out for public view.

Top-level:
{
  "schema_version": "1.0",
  "game_id": "uuid",
  "timestamp_start": "ISO8601",
  "timestamp_end": "ISO8601",
  "winner": "town" | "mafia",
  "players": [PlayerEntry],
  "events": [Event]
}

PlayerEntry:
{
  "seat": int,
  "persona_id": "uuid",
  "name": str,
  "role": "mafia" | "detective" | "town",
  "outcome": "survived" | "eliminated" | "killed"
}

Event types with private_fields:

| type          | data fields                              | private_fields           |
|---------------|------------------------------------------|--------------------------|
| phase_start   | phase, round_number                      | []                       |
| speech        | speaker, text, nomination, reasoning     | ["reasoning"]            |
| vote          | votes (dict), outcome, eliminated        | []                       |
| night_kill    | target (or null), reasoning              | ["reasoning"]            |
| investigation | target, result, reasoning                | ["target", "result", "reasoning"] |
| last_words    | speaker, text                            | []                       |
| defense       | speaker, text                            | []                       |
| game_end      | winner, final_roles                      | []                       |

To derive public view: for each event, delete data[field] for field in private_fields.
"""
