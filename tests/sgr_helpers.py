"""Helpers for building schema-valid mock SGR outputs in tests."""

from __future__ import annotations

from pydantic import BaseModel

from src.schemas import (
    DefenseOutput,
    DoctorProtectOutput,
    InvestigationOutput,
    LastWordsOutput,
    NightKillOutput,
    SpeakingOutput,
    VotingOutput,
)


def _validate(model: type[BaseModel], data: dict) -> dict:
    model(**data)
    return data


def make_speak_response(**overrides) -> dict:
    data = {
        "observations": "No major changes since my last turn.",
        "suspicions": "No strong suspicions.",
        "strategy": "Gather information and stay cautious.",
        "reasoning": "Default reasoning.",
        "speech": "Default speech content here.",
        "nomination": "Bob",
    }
    return _validate(SpeakingOutput, {**data, **overrides})


def make_vote_response(**overrides) -> dict:
    data = {
        "observations": "Discussion complete with no decisive evidence.",
        "suspicions": "No clear Mafia candidate.",
        "strategy": "Avoid a risky vote without evidence.",
        "reasoning": "Default reasoning.",
        "vote": "skip",
    }
    return _validate(VotingOutput, {**data, **overrides})


def make_night_kill_response(**overrides) -> dict:
    data = {
        "observations": "Night phase begins.",
        "suspicions": "Uncertain who poses the biggest threat.",
        "strategy": "Remove a key town voice.",
        "reasoning": "Default reasoning.",
        "message": "Default message to partner.",
        "target": "skip",
    }
    return _validate(NightKillOutput, {**data, **overrides})


def make_investigation_response(**overrides) -> dict:
    data = {
        "observations": "Night phase with limited information.",
        "suspicions": "No strong lead to follow.",
        "strategy": "Investigate to build future evidence.",
        "reasoning": "Default reasoning.",
        "target": "Bob",
    }
    return _validate(InvestigationOutput, {**data, **overrides})


def make_doctor_protect_response(**overrides) -> dict:
    data = {
        "observations": "Night phase with limited information.",
        "suspicions": "No strong lead to follow.",
        "strategy": "Protect likely night targets.",
        "reasoning": "Default reasoning.",
        "target": "Bob",
    }
    return _validate(DoctorProtectOutput, {**data, **overrides})


def make_last_words_response(**overrides) -> dict:
    data = {
        "reasoning": "Offer final guidance and close out respectfully.",
        "text": "Good luck to the remaining players.",
    }
    return _validate(LastWordsOutput, {**data, **overrides})


def make_defense_response(**overrides) -> dict:
    data = {
        "reasoning": "Refute the case and point to a weak accusation.",
        "text": "I am not Mafia. Please reconsider.",
    }
    return _validate(DefenseOutput, {**data, **overrides})
