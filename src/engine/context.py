"""Context building for player LLM calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from src.schemas import (
    ActionType,
    CompressedRoundSummary,
    DayRoundTranscript,
    Event,
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

    RULES_SUMMARY = """You are playing Mafia with 7 players: 2 Mafia, 1 Detective, 4 Town.

ROLES:
- Town: No special abilities. Win by eliminating both Mafia.
- Detective: Town-aligned. Can investigate one player per night to learn if they are Mafia.
- Mafia: Know each other. Can kill one player per night. Win when Mafia >= Town-aligned.

GAME FLOW:
1. Day Phase: All players discuss, each nominates one player. Then vote.
   - Majority vote eliminates a player. Ties trigger revote with defenses.
2. Night Phase: Mafia choose a kill target. Detective investigates.
3. Game ends when all Mafia are dead (Town wins) or Mafia >= Town-aligned (Mafia wins).

RULES:
- Each speech should be ~150 words.
- Votes must be for a nominated player or "skip".
- Never reveal other players' hidden information you don't have."""

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
        recent_events: list[Event] | None = None,
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
            recent_events: Public events since the player's last turn

        Returns:
            Complete context string for LLM system prompt
        """
        sections = [
            self._build_identity_section(player_name, role, persona),
            self._build_rules_section(),
            self._build_game_state_section(game_state),
            self._build_role_specific_section(role, extra),
            self._build_recent_events_section(recent_events),
            self._build_defense_context_section(action_type, extra),
            self._build_transcript_section(transcript),
            self._build_memory_section(memory),
            self._build_action_prompt(action_type, game_state, player_name, extra),
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
        return f"[GAME RULES]\n{self.RULES_SUMMARY}"

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

    def _build_recent_events_section(
        self, events: list[Event] | None
    ) -> str | None:
        """Build recent public events section.

        Defensively filters private_fields from event.data to prevent
        accidental leaks if caller passes unfiltered events.
        """
        if not events:
            return None

        lines = ["[RECENT EVENTS]"]
        for event in events:
            # Filter out private fields (defense in depth)
            public_data = {
                k: v for k, v in event.data.items() if k not in event.private_fields
            }
            payload = json.dumps(public_data, ensure_ascii=True)
            lines.append(f"- {event.type}: {payload}")
        return "\n".join(lines)

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
                    if item.last_words:
                        lines.append(f"Last words: \"{item.last_words}\"")
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

    def _build_action_prompt(
        self,
        action_type: ActionType,
        state: GameState,
        player_name: str,
        extra: dict | None = None,
    ) -> str:
        """Build action-specific prompt."""
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

        prompts = {
            ActionType.SPEAK: f"""[YOUR TASK: SPEAK]
It's your turn to speak in the discussion.

1. Observe what has happened and update your suspicions
2. Decide what information to share vs hide
3. Give a speech (~150 words) that fits your persona
4. You MUST nominate exactly one living player for potential elimination

Valid nomination targets: {living}

Fill out ALL fields in the schema. The reasoning fields come first to help you think,
then your actual speech and nomination.""",

            ActionType.VOTE: f"""[YOUR TASK: VOTE]
Discussion is complete. Time to vote.

1. Review the discussion and your suspicions
2. Consider who is most likely Mafia
3. Vote for one nominated player, or "skip" if uncertain

Valid vote options: {vote_options}

Fill out ALL fields in the schema, then provide your vote.""",

            ActionType.NIGHT_KILL: f"""[YOUR TASK: MAFIA NIGHT KILL]
It's night. Choose a target to kill.

1. Consider who threatens your team (Detective suspects, strong Town leaders)
2. Coordinate with your partner's suggestion if provided
3. Choose a target or "skip" to spare everyone tonight

Valid targets: {living_except_self}

Fill out ALL fields in the schema, then provide your target.""",

            ActionType.INVESTIGATION: f"""[YOUR TASK: DETECTIVE INVESTIGATION]
It's night. Choose someone to investigate.

1. Consider who is most suspicious
2. Think about how you'll use the information
3. Choose a target to learn if they are Mafia

Valid targets: {living_except_self}

Fill out ALL fields in the schema, then provide your target.""",

            ActionType.LAST_WORDS: """[YOUR TASK: LAST WORDS]
You have been eliminated from the game. This is your final statement.

You may:
- Share your suspicions about who is Mafia
- Reveal your role if you wish
- Give advice to remaining players
- Say goodbye in your persona's style

Keep it brief and impactful. Fill out the schema with your final message.""",

            ActionType.DEFENSE: """[YOUR TASK: DEFENSE]
You are tied in the vote and must defend yourself.

1. Address the accusations against you
2. Make your case for why you should stay
3. Redirect suspicion if appropriate

Give a brief but compelling defense speech in your persona's style.
Fill out ALL fields in the schema, then provide your defense.""",
        }

        return prompts.get(action_type, "[YOUR TASK]\nTake your action.")
