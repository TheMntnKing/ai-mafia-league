"""Persona schemas defining player identity and behavior."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    relationships: dict[str, str] = Field(default_factory=dict)  # persona_name -> relationship
