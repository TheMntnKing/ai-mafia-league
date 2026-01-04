"""Persona schemas defining player identity and behavior."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PersonaIdentity(BaseModel):
    """Core identity of a persona."""

    name: str
    background: str  # 1-2 sentences, informs motivation
    core_traits: list[str] = Field(min_length=3, max_length=5)  # Role-neutral traits


class PlayStyle(BaseModel):
    """How the persona speaks and decides in play."""

    voice: str  # 30-40 words: vocabulary, rhythm, tone
    approach: str  # 40-60 words: decision style, risk posture, accuse/defend tendencies
    signature_phrases: list[str] = Field(default_factory=list, max_length=3)
    signature_moves: list[str] = Field(default_factory=list, max_length=2)


class RoleTactics(BaseModel):
    """
    Role-specific tactics; only the current role is shown to the LLM.

    Guidance:
    - Use short, actionable moves that can be observed in play.
    - Avoid flavor-only text; keep it tactical.
    - Do not restate the global role playbook.
    - Prefer concrete levers: timing, vote strategy, info sharing, ally/foe management.
    """

    town: list[str] = Field(min_length=2, max_length=5)
    mafia: list[str] = Field(min_length=2, max_length=5)
    detective: list[str] = Field(min_length=2, max_length=5)
    doctor: list[str] | None = Field(default=None, min_length=2, max_length=5)


class Persona(BaseModel):
    """
    Complete persona definition. Entire structure is sent to LLM prompt.

    Target length: 200-300 words when rendered as prompt.
    Under 180 feels thin; over 400 causes drift and contradictions.

    Key principle: Voice + approach define HOW they act.
    Role tactics define WHAT they do in a role, consistent with the persona.
    """

    identity: PersonaIdentity
    play_style: PlayStyle
    tactics: RoleTactics
