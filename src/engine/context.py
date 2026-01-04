"""Context building for player LLM calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.engine.prompts import (
    DEFENSE_PROMPT,
    RULES_SUMMARY,
    build_doctor_protect_prompt,
    build_investigation_prompt,
    build_last_words_prompt,
    build_night_kill_prompt,
    build_night_zero_prompt,
    build_role_playbook,
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
    - Role-specific info (Mafia partners, Detective results)
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
            extra: Role-specific or action-specific info (partners, defense context)

        Returns:
            Complete context string for LLM system prompt
        """
        sections = [
            self._build_identity_section(player_name, role, persona),
            self._build_role_specific_section(role, extra),
            self._build_mafia_coordination_section(extra),
            self._build_role_playbook_section(role),
            self._build_rules_section(),
            self._build_game_state_section(game_state),
            self._build_speaking_order_section(action_type, extra),
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
            f"Voice: {persona.play_style.voice}",
            f"Approach: {persona.play_style.approach}",
        ]

        if persona.play_style.signature_phrases:
            lines.append(
                f"Signature phrases: {', '.join(persona.play_style.signature_phrases)}"
            )

        if persona.play_style.signature_moves:
            lines.append(f"Signature moves: {', '.join(persona.play_style.signature_moves)}")

        tactics: list[str] | None = None
        if role == "town":
            tactics = persona.tactics.town
        elif role == "mafia":
            tactics = persona.tactics.mafia
        elif role == "detective":
            tactics = persona.tactics.detective
        elif role == "doctor":
            tactics = persona.tactics.doctor

        if tactics:
            lines.append("")
            lines.append("Role tactics:")
            lines.extend([f"- {item}" for item in tactics])

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

    def _build_speaking_order_section(
        self, action_type: ActionType, extra: dict | None
    ) -> str | None:
        """Build speaking order section for discussion/defense turns."""
        if action_type not in {ActionType.SPEAK, ActionType.DEFENSE}:
            return None
        if not extra or "speaking_order" not in extra:
            return None

        order = extra.get("speaking_order") or {}
        position = order.get("position")
        total = order.get("total")
        spoken = order.get("spoken") or []
        remaining = order.get("remaining") or []

        lines = ["[SPEAKING ORDER]"]
        if position and total:
            lines.append(f"You are speaker #{position} of {total}.")
        if spoken:
            lines.append(f"Spoken so far: {', '.join(spoken)}")
        else:
            lines.append("Spoken so far: None")
        if remaining:
            lines.append(f"Remaining speakers: {', '.join(remaining)}")
        else:
            lines.append("Remaining speakers: None")

        if action_type == ActionType.SPEAK:
            lines.append(
                "Avoid accusing players for being silent if they have not spoken yet."
            )

        return "\n".join(lines)

    def _build_role_specific_section(
        self, role: str, extra: dict | None
    ) -> str | None:
        """Build role-specific section (partner list, investigation results)."""
        if not extra:
            return None

        if role == "mafia" and "partners" in extra:
            partners = extra["partners"]
            if partners:
                partner_list = ", ".join(partners)
                return (
                    f"[MAFIA INFO]\nYour partners are: {partner_list}. "
                    "Protect each other's identity."
                )

        return None

    def _build_mafia_coordination_section(self, extra: dict | None) -> str | None:
        """Build Mafia coordination section for Night Zero and Night kills."""
        if not extra:
            return None

        lines = []

        # Night Zero: Mafia see prior partner strategies
        if "partner_strategies" in extra:
            strategies = extra.get("partner_strategies") or {}
            strategy_lines = [
                f"- {name}: {strategy}"
                for name, strategy in strategies.items()
                if strategy
            ]
            if strategy_lines:
                lines.append("[PARTNER STRATEGIES]")
                lines.extend(strategy_lines)
                lines.append("Consider this when formulating your response.")

        # Night Round 1: show prior proposals to later Mafia
        if extra.get("round") == 1 and "prior_proposals" in extra:
            lines.append("[COORDINATION ROUND 1]")
            prior_proposals = extra.get("prior_proposals") or {}
            prior_messages = extra.get("prior_messages") or {}
            if prior_proposals:
                lines.append("Prior proposals:")
                for name, proposal in prior_proposals.items():
                    lines.append(f"- {name}: {proposal}")
            if prior_messages:
                lines.append("Prior messages:")
                for name, message in prior_messages.items():
                    if message:
                        lines.append(f"- {name}: {message}")
            lines.append("Respond with your own proposal and reasoning.")

        # Night Round 2: show all round 1 proposals
        if extra.get("round") == 2 and "r1_proposals" in extra:
            lines.append("[COORDINATION ROUND 2]")
            r1_proposals = extra.get("r1_proposals") or {}
            r1_messages = extra.get("r1_messages") or {}
            if r1_proposals:
                lines.append("Round 1 proposals:")
                for name, proposal in r1_proposals.items():
                    lines.append(f"- {name}: {proposal}")
            if r1_messages:
                lines.append("Round 1 messages:")
                for name, message in r1_messages.items():
                    if message:
                        lines.append(f"- {name}: {message}")
            lines.append("You disagreed in Round 1. Try to reach consensus.")

        return "\n".join(lines) if lines else None

    def _build_role_playbook_section(self, role: str) -> str | None:
        """Build role playbook section."""
        return build_role_playbook(role)

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
                if item.vote_line:
                    lines.append(f"Votes: {item.vote_line}")
                if item.defense_note:
                    lines.append(item.defense_note)
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
        facts = memory.facts or {}
        beliefs_str = json.dumps(memory.beliefs, indent=2) if memory.beliefs else "{}"
        summary_lines = self._summarize_facts(facts)
        summary_block = "Fact summary: None yet."
        if summary_lines:
            summary_block = "Fact summary:\n" + "\n".join(
                f"- {line}" for line in summary_lines
            )
        elif facts:
            summary_block = "Facts (raw):\n" + json.dumps(facts, indent=2)

        return f"""[YOUR MEMORY]
{summary_block}

Your current beliefs:
{beliefs_str}"""

    def _summarize_facts(self, facts: dict) -> list[str]:
        """Summarize known fact keys into readable lines."""
        lines: list[str] = []

        investigations = facts.get("investigation_results") or []
        if investigations:
            formatted = ", ".join(
                f"{item.get('target', '?')} -> {item.get('result', '?')}"
                for item in investigations
                if isinstance(item, dict)
            )
            if formatted:
                lines.append(f"Investigations: {formatted}")
        elif isinstance(facts.get("last_investigation"), dict):
            last = facts["last_investigation"]
            lines.append(
                "Last investigation: "
                f"{last.get('target', '?')} -> {last.get('result', '?')}"
            )

        mafia_history = facts.get("mafia_kill_history") or []
        if mafia_history:
            formatted = ", ".join(
                f"{item.get('target', '?')} ({item.get('outcome', '?')})"
                for item in mafia_history
                if isinstance(item, dict)
            )
            if formatted:
                lines.append(f"Mafia kills: {formatted}")
        elif isinstance(facts.get("last_mafia_kill"), dict):
            last = facts["last_mafia_kill"]
            lines.append(
                "Last mafia kill: "
                f"{last.get('target', '?')} ({last.get('outcome', '?')})"
            )

        doctor_history = facts.get("doctor_protection_history") or []
        if doctor_history:
            formatted = ", ".join(
                item.get("target", "?")
                for item in doctor_history
                if isinstance(item, dict)
            )
            if formatted:
                lines.append(f"Doctor protections: {formatted}")
        elif isinstance(facts.get("last_doctor_protect"), dict):
            last = facts["last_doctor_protect"]
            lines.append(f"Last protection: {last.get('target', '?')}")

        return lines

    def _build_night_zero_prompt(self, extra: dict | None) -> str:
        """Build prompt for Night Zero Mafia coordination."""
        partner_strategies = None
        if extra:
            if "partner_strategies" in extra:
                partner_strategies = extra.get("partner_strategies")
        return build_night_zero_prompt(partner_strategies)

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

        # For Mafia night kill, exclude all Mafia (self and partners)
        mafia_members = set()
        if role == "mafia":
            mafia_members.add(player_name)
            if extra:
                if "partners" in extra:
                    mafia_members.update(extra["partners"])

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
        if extra and extra.get("game_over"):
            last_words_role_note = (
                "\nThis elimination ends the game. You can drop pretense and give a "
                "final reaction or analysis."
            )
        elif role == "mafia":
            last_words_role_note = (
                "\nAs Mafia: Do NOT reveal you are Mafia or name your partners. "
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
        if action_type == ActionType.DOCTOR_PROTECT:
            living_targets = ", ".join(state.living_players)
            return build_doctor_protect_prompt(living_targets)
        if action_type == ActionType.LAST_WORDS:
            return build_last_words_prompt(last_words_role_note)
        if action_type == ActionType.DEFENSE:
            return DEFENSE_PROMPT
        return "[YOUR TASK]\nTake your action."
