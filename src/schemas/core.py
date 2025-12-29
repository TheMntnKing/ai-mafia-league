"""Core types: ActionType, GameState, PlayerMemory, PlayerResponse, Event."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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

    output: dict  # Action-specific (speech, vote, target, etc.)
    updated_memory: PlayerMemory


class Event(BaseModel):
    """Single game event in the log."""

    type: str  # phase_start, speech, vote, night_kill, investigation, last_words, defense, game_end
    timestamp: str  # ISO8601
    data: dict  # Type-specific fields
    private_fields: list[str] = Field(default_factory=list)  # Fields to filter for public view
