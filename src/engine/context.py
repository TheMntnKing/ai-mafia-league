"""Context building for player LLM calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.engine.prompts import (
    DEFENSE_PROMPT,
    RULES_SUMMARY,
    build_investigation_prompt,
    build_last_words_prompt,
    build_night_kill_prompt,
    build_night_zero_prompt,
    build_speak_prompt,
    build_vote_prompt,
)
from src.schemas import (
    ActionType,
    CompressedRoundSummary,
    DayRoundTranscript,
    GameState,
    Persona,
    PlayerMemory,
    Transcript,
)

if TYPE_CHECKING:
    pass


class ContextBuilder:
    """
    Builds context strings for player LLM calls.

    Assembles:
    - Identity (role, persona)
    - Rules summary
    - Game state
    - Role-specific info (Mafia partner, Detective results)
    - Recent public events since last turn
    - Transcript (2-round window)
    - Memory/beliefs
    - Action-specific prompt
    """

    def build_context(
        self,
        player_name: str,
        role: str,
        persona: Persona,
        game_state: GameState,
        transcript: Transcript,
        memory: PlayerMemory,
        action_type: ActionType,
        extra: dict | None = None,
    ) -> str:
        """
        Assemble full context string for LLM.

        Args:
            player_name: Name of the player
            role: Player's role (mafia, detective, town)
            persona: Player's persona definition
            game_state: Current game state
            transcript: Game transcript (may be compressed)
            memory: Player's memory state
            action_type: Type of action to take
            extra: Role-specific or action-specific info (partner, defense context)

        Returns:
            Complete context string for LLM system prompt
        """
        sections = [
            self._build_identity_section(player_name, role, persona),
            self._build_rules_section(),
            self._build_game_state_section(game_state),
            self._build_role_specific_section(role, extra),
            self._build_mafia_coordination_section(extra),
            self._build_defense_context_section(action_type, extra),
            self._build_transcript_section(transcript),
            self._build_memory_section(memory),
            self._build_action_prompt(action_type, game_state, player_name, role, extra),
        ]

        return "\n\n".join(filter(None, sections))

    def _build_identity_section(
        self, name: str, role: str, persona: Persona
    ) -> str:
        """Build identity section of context."""
        lines = [
            "[YOUR IDENTITY]",
            f"You are {name}. Your role is {role.upper()}.",
            "",
            f"Persona: {persona.identity.name}",
            f"Background: {persona.identity.background}",
            f"Core traits: {', '.join(persona.identity.core_traits)}",
            "",
            f"Speech style: {persona.voice_and_behavior.speech_style}",
            f"Reasoning style: {persona.voice_and_behavior.reasoning_style}",
            f"When accusing: {persona.voice_and_behavior.accusation_style}",
            f"When defending: {persona.voice_and_behavior.defense_style}",
            f"Trust disposition: {persona.voice_and_behavior.trust_disposition}",
            f"Risk tolerance: {persona.voice_and_behavior.risk_tolerance}",
        ]

        if persona.voice_and_behavior.signature_phrases:
            lines.append(
                f"Signature phrases: {', '.join(persona.voice_and_behavior.signature_phrases)}"
            )

        if persona.voice_and_behavior.quirks:
            lines.append(f"Quirks: {', '.join(persona.voice_and_behavior.quirks)}")

        # Add role-specific guidance if available
        if persona.role_guidance:
            lines.append("")
            if role == "town":
                lines.append(f"As Town: {persona.role_guidance.town}")
            elif role == "mafia":
                lines.append(f"As Mafia: {persona.role_guidance.mafia}")
            elif role == "detective":
                lines.append(f"As Detective: {persona.role_guidance.detective}")

        return "\n".join(lines)

    def _build_rules_section(self) -> str:
        """Build rules section of context."""
        return f"[GAME RULES]\n{RULES_SUMMARY}"

    def _build_game_state_section(self, state: GameState) -> str:
        """Build game state section of context."""
        dead_str = ", ".join(state.dead_players) if state.dead_players else "None"
        nominated_str = (
            ", ".join(state.nominated_players)
            if state.nominated_players
            else "None yet"
        )

        return f"""[CURRENT STATE]
Phase: {state.phase}
Round: {state.round_number}
Living players: {', '.join(state.living_players)}
Dead players: {dead_str}
Nominated for vote: {nominated_str}"""

    def _build_role_specific_section(
        self, role: str, extra: dict | None
    ) -> str | None:
        """Build role-specific section (partner info, investigation results)."""
        if not extra:
            return None

        if role == "mafia" and "partner" in extra:
            partner = extra["partner"]
            partner_alive = extra.get("partner_alive", True)
            alive_str = "" if partner_alive else " (dead)"
            return (
                f"[MAFIA INFO]\nYour partner is {partner}{alive_str}. "
                "Protect each other's identity."
            )

        if role == "detective" and "results" in extra:
            results = extra["results"]
            if results:
                result_lines = [
                    f"- {r['target']}: {r['result']}" for r in results
                ]
                return "[INVESTIGATION RESULTS]\n" + "\n".join(result_lines)
            return "[INVESTIGATION RESULTS]\nNo investigations completed yet."

        return None

    def _build_mafia_coordination_section(self, extra: dict | None) -> str | None:
        """Build Mafia coordination section for Night Zero and Night kills."""
        if not extra:
            return None

        lines = []

        # Night Zero: Second Mafia sees first Mafia's strategy
        if "partner_strategy" in extra:
            lines.append("[PARTNER'S STRATEGY]")
            lines.append(f"Your partner said: \"{extra['partner_strategy']}\"")
            lines.append("Consider this when formulating your response.")

        # Night Round 1: Second Mafia sees first Mafia's proposal
        if extra.get("round") == 1 and "partner_proposal" in extra:
            lines.append("[COORDINATION ROUND 1]")
            lines.append(f"Partner's proposal: {extra['partner_proposal']}")
            partner_message = extra.get("partner_message")
            if partner_message:
                lines.append(f"Partner's message: {partner_message}")
            lines.append("Respond with your own proposal and reasoning.")

        # Night Round 2: Both Mafia see partner's R1 proposal
        if extra.get("round") == 2 or "my_r1_proposal" in extra:
            lines.append("[COORDINATION ROUND 2]")
            if "my_r1_proposal" in extra:
                lines.append(f"Your Round 1 proposal: {extra['my_r1_proposal']}")
            if "partner_proposal" in extra:
                lines.append(f"Partner's Round 1 proposal: {extra['partner_proposal']}")
            if extra.get("my_r1_message"):
                lines.append(f"Your Round 1 message: {extra['my_r1_message']}")
            if extra.get("partner_message"):
                lines.append(f"Partner's Round 1 message: {extra['partner_message']}")
            lines.append("You disagreed in Round 1. Try to reach consensus.")

        return "\n".join(lines) if lines else None

    def _build_defense_context_section(
        self, action_type: ActionType, extra: dict | None
    ) -> str | None:
        """Build defense context when tied."""
        if action_type != ActionType.DEFENSE or not extra:
            return None

        defense_context = extra.get("defense_context")
        if not defense_context:
            return None

        tied_players = defense_context.get("tied_players", [])
        vote_counts = defense_context.get("vote_counts", {})
        votes = defense_context.get("votes", {})

        lines = ["[DEFENSE CONTEXT]"]
        if tied_players:
            lines.append(f"Tied players: {', '.join(tied_players)}")
        if vote_counts:
            counts_str = ", ".join(f"{p}:{c}" for p, c in vote_counts.items())
            lines.append(f"Vote counts: {counts_str}")
        if votes:
            vote_str = ", ".join(f"{voter}->{target}" for voter, target in votes.items())
            lines.append(f"Votes cast: {vote_str}")

        return "\n".join(lines)

    def _build_transcript_section(self, transcript: Transcript) -> str:
        """Build transcript section of context."""
        if not transcript:
            return "[TRANSCRIPT]\nNo previous discussion."

        lines = ["[TRANSCRIPT]"]

        for item in transcript:
            if isinstance(item, CompressedRoundSummary):
                lines.append(f"\n--- Day {item.round_number} (summary) ---")
                if item.night_death:
                    lines.append(f"Night kill: {item.night_death}")
                if item.vote_death:
                    lines.append(f"Vote elimination: {item.vote_death}")
                if item.accusations:
                    lines.append(f"Key accusations: {'; '.join(item.accusations)}")
                if item.claims:
                    lines.append(f"Role claims: {'; '.join(item.claims)}")
                lines.append(f"Vote result: {item.vote_result}")
            elif isinstance(item, DayRoundTranscript):
                lines.append(f"\n--- Day {item.round_number} (full) ---")
                if item.night_kill:
                    lines.append(f"Night kill: {item.night_kill}")
                else:
                    lines.append("No night kill")

                for speech in item.speeches:
                    lines.append(f"\n{speech.speaker}: \"{speech.text}\"")
                    lines.append(f"  Nominated: {speech.nomination}")

                if item.votes:
                    vote_summary = ", ".join(
                        f"{voter}->{target}" for voter, target in item.votes.items()
                    )
                    lines.append(f"\nVotes: {vote_summary}")
                    lines.append(f"Outcome: {item.vote_outcome}")

                if item.defense_speeches:
                    lines.append("\nDefense speeches:")
                    for defense in item.defense_speeches:
                        lines.append(f"  {defense.speaker}: \"{defense.text}\"")

                if item.revote:
                    revote_summary = ", ".join(
                        f"{voter}->{target}" for voter, target in item.revote.items()
                    )
                    lines.append(f"Revote: {revote_summary}")
                    lines.append(f"Final outcome: {item.revote_outcome}")

                # Last words only for day eliminations (voted out players)
                if item.last_words:
                    lines.append(f"Last words: \"{item.last_words}\"")

        return "\n".join(lines)

    def _build_memory_section(self, memory: PlayerMemory) -> str:
        """Build memory section of context."""
        facts_str = json.dumps(memory.facts, indent=2) if memory.facts else "{}"
        beliefs_str = json.dumps(memory.beliefs, indent=2) if memory.beliefs else "{}"

        return f"""[YOUR MEMORY]
Facts you've observed:
{facts_str}

Your current beliefs:
{beliefs_str}"""

    def _build_night_zero_prompt(self, extra: dict | None) -> str:
        """Build prompt for Night Zero Mafia coordination."""
        partner_strategy = (extra or {}).get("partner_strategy")
        return build_night_zero_prompt(partner_strategy)

    def _build_action_prompt(
        self,
        action_type: ActionType,
        state: GameState,
        player_name: str,
        role: str,
        extra: dict | None = None,
    ) -> str:
        """Build action-specific prompt."""
        # Special case: NightZero coordination uses SPEAK but needs different prompt
        if action_type == ActionType.SPEAK and (extra or {}).get("night_zero"):
            return self._build_night_zero_prompt(extra)

        living = ", ".join(state.living_players)

        # For Mafia night kill, exclude all Mafia (self and partner)
        mafia_members = set()
        if extra:
            mafia_members.add(player_name)
            if "partner" in extra:
                mafia_members.add(extra["partner"])

        living_targets = [
            p
            for p in state.living_players
            if p != player_name and p not in mafia_members
        ]
        living_except_self = ", ".join(living_targets) if living_targets else "skip"

        if state.nominated_players:
            nominated = ", ".join(state.nominated_players)
            vote_options = f"{nominated}, skip"
        else:
            vote_options = "skip"

        is_day_one = state.phase == "day_1" or (
            state.phase.startswith("day") and state.round_number == 1
        )
        day_one_note = ""
        if is_day_one:
            day_one_note = (
                "\nDay 1 guidance:\n"
                "- Include a brief self-introduction or opener (1-2 sentences).\n"
                "- Treat nominations as exploratory, not a hard accusation.\n"
                "- Focus on reactions and questions, not certainty.\n"
                "- If you have no lean yet, you may set nomination to \"skip\".\n"
            )

        # Build nomination targets (include "skip" on Day 1)
        nomination_targets = living
        if is_day_one:
            nomination_targets = f"{living}, skip"

        vote_day_one_note = ""
        if is_day_one:
            vote_day_one_note = (
                "\nDay 1 guidance:\n"
                "- A nomination alone is NOT a reason to eliminate someone.\n"
                "- If evidence is thin, it's acceptable to vote \"skip\".\n"
            )

        last_words_role_note = ""
        if role == "mafia":
            last_words_role_note = (
                "\nAs Mafia: Do NOT reveal you are Mafia or name your partner. "
                "Stay in character and try to misdirect suspicion."
            )
        elif role == "detective":
            last_words_role_note = (
                "\nAs Detective: Consider sharing investigation results to help Town."
            )
        elif role == "town":
            last_words_role_note = (
                "\nAs Town: Share your strongest suspicions and advice for the next vote."
            )

        if action_type == ActionType.SPEAK:
            return build_speak_prompt(nomination_targets, day_one_note)
        if action_type == ActionType.VOTE:
            return build_vote_prompt(vote_options, vote_day_one_note)
        if action_type == ActionType.NIGHT_KILL:
            return build_night_kill_prompt(living_except_self)
        if action_type == ActionType.INVESTIGATION:
            return build_investigation_prompt(living_except_self)
        if action_type == ActionType.LAST_WORDS:
            return build_last_words_prompt(last_words_role_note)
        if action_type == ActionType.DEFENSE:
            return DEFENSE_PROMPT
        return "[YOUR TASK]\nTake your action."
